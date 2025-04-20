// src/App.vue
<template>
  <v-app>
    <v-app-bar app color="primary" dark v-if="isAuthenticated">
      <div class="d-flex align-center mr-3 ml-3">
        <img src="/favicon-96x96.png" alt="Logo" height="60" width="60">
      </div>
      <v-toolbar-title>{{ $t('app.title') }}</v-toolbar-title>
      <v-spacer></v-spacer>
      <v-btn 
        v-for="item in visibleMenuItems" 
        :key="item.title" 
        :to="item.path" 
        variant="text"
      >
        <v-icon start>{{ item.icon }}</v-icon>
        {{ $t(item.title) }}
      </v-btn>

      <!-- Language Switcher -->
      <language-switcher class="mr-2" />

      <!-- Theme Toggle Button -->
      <v-btn icon="mdi-weather-sunny" @click="toggleAppTheme" :title="$t('app.darkMode')" v-if="isDark"></v-btn>
      <v-btn icon="mdi-weather-night" @click="toggleAppTheme" :title="$t('app.darkMode')" v-else></v-btn>
      
      <!-- Change password -->
      <v-btn icon="mdi-key-change" @click="openChangePasswordDialog" :title="$t('user.changePassword')"></v-btn>

      <!-- Logout Button -->
      <v-btn icon="mdi-logout" @click="confirmLogout" :title="$t('login.logout')"></v-btn>
    </v-app-bar>

    <v-main>
      <v-container fluid>
        <router-view></router-view>
      </v-container>
    </v-main>

    <v-footer app v-if="isAuthenticated">
      <span>&copy; {{ new Date().getFullYear() }} - {{ $t('app.footer') }} - v{{ appVersion }}</span>
      <v-spacer></v-spacer>
      <span>{{ $t('app.loggedInAs') }}: {{ user ? (user.display_name || user.username) : '' }}</span>
    </v-footer>
    
    <!-- Notification component -->
    <notification :message="notification" />
    
    <!-- Confirm Dialog component -->
    <confirm-dialog
      v-model="confirmDialog.show"
      :title="confirmDialog.title"
      :message="confirmDialog.message"
      :confirm-text="confirmDialog.confirmText"
      :cancel-text="confirmDialog.cancelText"
      :confirm-color="confirmDialog.confirmColor"
      :loading="loading"
      @confirm="confirmDialog.onConfirm"
      @cancel="confirmDialog.onCancel"
    />

    <v-dialog
      v-model="changePasswordDialog.show"
      max-width="500px"
    >
      <v-card>
        <v-card-title>
          {{ $t('user.changePassword') }}
        </v-card-title>
        
        <v-card-text>
          <v-form ref="passwordForm" v-model="changePasswordDialog.valid">
            <v-text-field
              v-model="changePasswordDialog.currentPassword"
              :label="$t('user.currentPassword')"
              :rules="[v => !!v || $t('user.currentPasswordRequired')]"
              :type="showCurrentPassword ? 'text' : 'password'"
              :append-icon="showCurrentPassword ? 'mdi-eye-off' : 'mdi-eye'"
              @click:append="showCurrentPassword = !showCurrentPassword"
              required
            ></v-text-field>

            <v-text-field
              v-model="changePasswordDialog.newPassword"
              :label="$t('user.newPassword')"
              :rules="[
                v => !!v || $t('user.newPasswordRequired'),
                v => v.length >= 8 || $t('login.passwordLength')
              ]"
              :type="showNewPassword ? 'text' : 'password'"
              :append-icon="showNewPassword ? 'mdi-eye-off' : 'mdi-eye'"
              @click:append="showNewPassword = !showNewPassword"
              required
            ></v-text-field>

            <v-text-field
              v-model="changePasswordDialog.confirmPassword"
              :label="$t('user.confirmNewPassword')"
              :rules="[
                v => !!v || $t('user.confirmPasswordRequired'),
                v => v === changePasswordDialog.newPassword || $t('login.passwordsDoNotMatch')
              ]"
              :type="showNewPassword ? 'text' : 'password'"
              required
            ></v-text-field>
          </v-form>
        </v-card-text>
        
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="changePasswordDialog.show = false">
            {{ $t('common.cancel') }}
          </v-btn>
          <v-btn 
            color="primary" 
            @click="changePassword" 
            :disabled="!changePasswordDialog.valid || passwordChanging"
            :loading="passwordChanging"
          >
            {{ $t('common.save') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-app>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { storeToRefs } from 'pinia'
import { useAppStore } from './stores/index'
import { useAuthStore } from './stores/auth'
import { toggleTheme } from './plugins/vuetify'
import { emitter } from './plugins/emitter'
import Notification from './components/Notification.vue'
import ConfirmDialog from './components/ConfirmDialog.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'

// Setup hooks
const i18n = useI18n()
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const appStore = useAppStore()

// Get reactive state from auth store
const { user, isAuthenticated, loading } = storeToRefs(authStore)

// App state
const appVersion = ref('1.1.3')
const notification = ref(null)
const settingsChecked = ref(false)
const settingsCheckTimer = ref(null)
const isDark = ref(false)

// Menu items
const menuItems = ref([
  { title: 'menu.dashboard', path: '/', icon: 'mdi-view-dashboard' },
  { title: 'menu.reportDesigner', path: '/designer', icon: 'mdi-file-document-edit' },
  { title: 'menu.templates', path: '/templates', icon: 'mdi-format-paint' },
  { title: 'menu.layouts', path: '/layouts', icon: 'mdi-page-layout-body' },
  { title: 'menu.schedules', path: '/schedules', icon: 'mdi-clock-outline' },
  { title: 'menu.settings', path: '/settings', icon: 'mdi-cog' }
])

// Confirmation dialog state
const confirmDialog = ref({
  show: false,
  title: '',
  message: '',
  confirmText: 'Confirm',
  cancelText: 'Cancel',
  confirmColor: 'primary',
  onConfirm: () => {},
  onCancel: () => {}
})

// Change password dialog state
const changePasswordDialog = ref({
  show: false,
  valid: false,
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})
const passwordChanging = ref(false)
const showCurrentPassword = ref(false)
const showNewPassword = ref(false)

// Form refs
const passwordForm = ref(null)

// Computed properties
const visibleMenuItems = computed(() => {
  // Show all menu items for admins
  if (user.value && user.value.is_admin) {
    return menuItems.value
  }
  
  // Filter settings menu item for normal users
  return menuItems.value.filter(item => item.path !== '/settings')
})

// Add router guard
router.beforeEach(async (to, from) => {
  // If settings have not been checked yet and we are not already on the settings page
  if (!settingsChecked.value && to.path !== '/settings' && to.path !== '/login') {
    try {
      const initialized = await checkSettingsInitialized()
      if (!initialized) {
        return { path: '/settings' }
      }
    } catch (error) {
      console.error('Router guard error:', error)
    }
  }
  return true
})

// Methods
const toggleAppTheme = () => {
  isDark.value = toggleTheme()
}

const openChangePasswordDialog = () => {
  changePasswordDialog.value = {
    show: true,
    valid: false,
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  }
  showCurrentPassword.value = false
  showNewPassword.value = false
}

const changePassword = async () => {
  if (!passwordForm.value || !changePasswordDialog.value.valid) return
  
  passwordChanging.value = true
  
  try {
    // API call to change password
    await authStore.changePassword({
      currentPassword: changePasswordDialog.value.currentPassword,
      newPassword: changePasswordDialog.value.newPassword
    })
    
    // Close dialog
    changePasswordDialog.value.show = false
    
    // Show success notification
    emitter.emit('show-notification', {
      type: 'success',
      text: i18n.t('user.passwordChangeSuccess')
    })
  } catch (error) {
    // Show error notification
    emitter.emit('show-notification', {
      type: 'error',
      text: `${i18n.t('user.passwordChangeError')}: ${error.message || i18n.t('common.unknownError')}`
    })
  } finally {
    passwordChanging.value = false
  }
}

const confirmLogout = () => {
  showConfirmDialog({
    title: i18n.t('login.logout'),
    message: i18n.t('login.confirmLogout'),
    confirmText: i18n.t('login.logoutButton'),
    cancelText: i18n.t('common.cancel'),
    confirmColor: 'primary',
    onConfirm: () => {
      authStore.logout()
    }
  })
}

const showNotification = (message) => {
  notification.value = message
}

const showConfirmDialog = (options) => {
  confirmDialog.value = {
    show: true,
    title: options.title || i18n.t('common.confirm'),
    message: options.message || i18n.t('common.confirm'),
    confirmText: options.confirmText || i18n.t('common.confirm'),
    cancelText: options.cancelText || i18n.t('common.cancel'),
    confirmColor: options.confirmColor || 'primary',
    onConfirm: () => {
      if (typeof options.onConfirm === 'function') {
        options.onConfirm()
      }
      confirmDialog.value.show = false
    },
    onCancel: options.onCancel || (() => {
      confirmDialog.value.show = false
    })
  }
}

const initialSettingsCheck = () => {
  try {
    // Add a delay to ensure the app is fully loaded
    settingsCheckTimer.value = setTimeout(async () => {
      const initialized = await checkSettingsInitialized()
      settingsChecked.value = true // Mark as checked, regardless of the result
      
      // If we are not on the settings page and settings are not initialized
      if (!initialized && route.path !== '/settings' && route.path !== '/login') {
        router.push('/settings')
      }
    }, 1000)
  } catch (error) {
    console.error('Error in initial settings check:', error)
    settingsChecked.value = true // Mark as checked, so we don't try endlessly
  }
}

const checkSettingsInitialized = async () => {
  try {
    const result = await appStore.checkSettingsInitialized()
    console.log('Settings initialization check result:', result)
    
    if (!result.initialized || (result.reason === "default_settings")) {
      console.log('Settings not properly initialized, redirecting to settings page')
      
      showNotification({
        type: 'info',
        text: i18n.t('settings.welcomeMessage'),
        timeout: 10000
      })
      
      return false
    }
    
    return true
  } catch (error) {
    console.error('Error checking settings:', error)
    return false
  }
}

// Lifecycle hooks
onMounted(() => {
  // Listen for notification events
  emitter.on('show-notification', (message) => {
    notification.value = message
  })
  
  // Listen for confirm dialog events
  emitter.on('show-confirm-dialog', (options) => {
    showConfirmDialog(options)
  })

  initialSettingsCheck()
  
  emitter.on('settings-updated', () => {
    settingsChecked.value = true
  })

  // Check theme
  isDark.value = document.documentElement.getAttribute('data-theme') === 'dark'
})

onBeforeUnmount(() => {
  // Remove event listeners
  emitter.off('show-notification')
  emitter.off('show-confirm-dialog')
  emitter.off('settings-updated')
  
  if (settingsCheckTimer.value) {
    clearTimeout(settingsCheckTimer.value)
  }
})
</script>