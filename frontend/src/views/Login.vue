<!-- src/views/Login.vue -->
<template>
  <div class="login-page">
    <v-container fluid fill-height>
      <v-row align="center" justify="center">
        <v-col cols="12" sm="8" md="6" lg="4">
          <v-card elevation="12">
            <v-toolbar color="primary" dark flat>
              <div class="d-flex align-center mr-2 ml-2">
                <img src="/favicon-96x96.png" alt="Logo" height="48" width="48">
              </div>
              <v-toolbar-title>{{ isSetup ? $t('login.setupTitle') : $t('login.title') }}</v-toolbar-title>
              <v-spacer></v-spacer>
              <v-btn icon="mdi-translate" @click="toggleLanguage"></v-btn>
            </v-toolbar>
            <v-card-text>
              <v-alert v-if="error" type="error" variant="tonal" closable>
                {{ error }}
              </v-alert>
              <v-alert v-if="isSetup" type="info" variant="tonal" class="mb-4">
                {{ $t('login.setupInfo') }}
              </v-alert>
              <v-form ref="form" v-model="valid" @submit.prevent="submitForm">
                <v-text-field
                  ref="usernameField"
                  v-model="username"
                  :label="$t('login.username')"
                  name="username"
                  prepend-icon="mdi-account"
                  type="text"
                  :rules="[v => !!v || $t('login.usernameRequired')]"
                  required
                ></v-text-field>

                <v-text-field
                  @keyup.enter="submitForm"
                  v-model="password"
                  :label="$t('login.password')"
                  name="password"
                  prepend-icon="mdi-lock"
                  :type="showPassword ? 'text' : 'password'"
                  :rules="passwordRules"
                  :append-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
                  @click:append="showPassword = !showPassword"
                  required
                ></v-text-field>

                <v-text-field
                  v-if="isSetup"
                  v-model="confirmPassword"
                  :label="$t('login.confirmPassword')"
                  name="confirmPassword"
                  prepend-icon="mdi-lock-check"
                  :type="showPassword ? 'text' : 'password'"
                  :rules="confirmPasswordRules"
                  required
                ></v-text-field>
              </v-form>
            </v-card-text>
            <v-card-actions>
              <v-spacer></v-spacer>
              <v-btn 
                color="primary" 
                @click="submitForm" 
                :loading="loading" 
                :disabled="!valid"
              >
                {{ isSetup ? $t('login.setupButton') : $t('login.loginButton') }}
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { apiClient } from '@/services/api'
import { emitter } from '@/plugins/emitter'
import { setLanguage } from '@/plugins/i18n'

const router = useRouter()
const i18n = useI18n()
const authStore = useAuthStore()

const form = ref(null)
const usernameField = ref(null)
const valid = ref(false)
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const error = ref(null)
const loading = ref(false)
const isSetup = ref(false)

const passwordRules = computed(() => {
  const rules = [v => !!v || i18n.t('login.passwordRequired')];
  
  if (isSetup.value) {
    rules.push(v => v.length >= 8 || i18n.t('login.passwordLength'));
  }
  
  return rules;
})

const confirmPasswordRules = computed(() => [
  v => !!v || i18n.t('login.confirmPasswordRequired'),
  v => v === password.value || i18n.t('login.passwordsDoNotMatch')
])

onMounted(() => {
  checkSetupStatus()
  
  // Set focus to username field
  nextTick(() => {
    if (usernameField.value) {
      usernameField.value.focus()
    }
  })
})

const checkSetupStatus = async () => {
  try {
    loading.value = true
    const response = await apiClient.get('/auth/setup-status')
    isSetup.value = response.data.needs_setup
    
    error.value = null
  } catch (err) {
    // If errors occur, assume setup mode
    isSetup.value = true
    
    error.value = null
    
    emitter.emit('show-notification', {
      type: 'info',
      text: i18n.t('login.startingFirstTimeSetup'),
      timeout: 6000
    })
  } finally {
    loading.value = false
  }
}

const submitForm = async () => {
  if (!valid.value) return
  
  loading.value = true
  error.value = null
  
  try {
    
    if (isSetup.value) {
      // Setup new user (initial admin)
      await authStore.setupUser({
        username: username.value,
        password: password.value
      })
      
      // Ensure token is set in axios headers
      const token = localStorage.getItem('token')
      if (token) {
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`
      }
      
      // Add a small delay to allow backend to process
      await new Promise(resolve => setTimeout(resolve, 500))
    } else {
      // Regular login
      await authStore.login({
        username: username.value,
        password: password.value
      })
    }
    
    // Explicitly check if authentication succeeded
    if (authStore.isAuthenticated) {
      // Redirect to home on success
      router.push('/')
    } else {
      error.value = i18n.t('login.invalidCredentials')
    }
  } catch (err) {
    // Improved error handling with more details
    if (err.response?.data) {
      if (err.response.data.detail) {
        error.value = err.response.data.detail
      } else if (typeof err.response.data === 'string') {
        error.value = err.response.data
      } else {
        error.value = JSON.stringify(err.response.data)
      }
    } else if (err.message) {
      error.value = err.message
    } else {
      error.value = i18n.t('login.invalidCredentials')
    }
    
    // Show notification for network errors
    if (err.message === 'Network Error') {
      emitter.emit('show-notification', {
        type: 'error',
        text: 'Could not connect to server. Please check if the backend is running.',
        timeout: 10000
      })
    }
  } finally {
    loading.value = false
  }
}

const toggleLanguage = () => {
  const newLang = i18n.locale.value === 'de' ? 'en' : 'de'
  setLanguage(newLang)
}
</script>

<style scoped>
.login-page {
  height: 100vh;
  width: 100%;
  background-color: #f5f5f5;
}
</style>
