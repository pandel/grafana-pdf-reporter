<!-- src/views/Home.vue -->
<template>
  <div class="home">
    <v-card>
      <v-card-title>
        <h1>{{ $t('home.welcome') }}</h1>
      </v-card-title>
      <v-card-text>
        <p>{{ $t('home.description') }}</p>
        
        <v-row class="mt-6">
          <v-col cols="12" md="4">
            <v-card variant="outlined" height="100%">
              <v-card-title>{{ $t('home.reportDesigner.title') }}</v-card-title>
              <v-card-text>
                {{ $t('home.reportDesigner.description') }}
              </v-card-text>
              <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn color="primary" to="/designer">
                  <v-icon start>mdi-file-document-edit</v-icon>
                  {{ $t('home.reportDesigner.title') }}
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-col>
          
          <v-col cols="12" md="4">
            <v-card variant="outlined" height="100%">
              <v-card-title>{{ $t('home.templates.title') }}</v-card-title>
              <v-card-text>
                {{ $t('home.templates.description') }}
              </v-card-text>
              <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn color="primary" to="/templates">
                  <v-icon start>mdi-format-paint</v-icon>
                  {{ $t('home.templates.title') }}
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-col>
          
          <v-col cols="12" md="4">
            <v-card variant="outlined" height="100%">
              <v-card-title>{{ $t('home.schedules.title') }}</v-card-title>
              <v-card-text>
                {{ $t('home.schedules.description') }}
              </v-card-text>
              <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn color="primary" to="/schedules">
                  <v-icon start>mdi-clock-outline</v-icon>
                  {{ $t('home.schedules.title') }}
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
    
    <v-card class="mt-6">
      <v-card-title>{{ $t('home.quickStartGuide') }}</v-card-title>
      <v-card-text>
        <v-stepper non-linear>
          <template v-slot:default="{ prev, next }">
          <v-stepper-header>
            <v-stepper-item
              :title="$t('home.step1')"
              value="1"
            ></v-stepper-item>

            <v-divider></v-divider>

            <v-stepper-item
              :title="$t('home.step2')"
              value="2"
            ></v-stepper-item>

            <v-divider></v-divider>

            <v-stepper-item
              :title="$t('home.step3')"
              value="3"
            ></v-stepper-item>

            <v-divider></v-divider>

            <v-stepper-item
             :title="$t('home.step4')"
              value="4"
            ></v-stepper-item>

            <v-divider></v-divider>

            <v-stepper-item
              :title="$t('home.step5')"
              value="5"
            ></v-stepper-item>
          </v-stepper-header>

          <v-stepper-window direction="vertical">
            <v-stepper-window-item
              value="1"
              eager
            >
              <p>{{ $t('home.step1Description') }}</p>
            </v-stepper-window-item>

            <v-stepper-window-item
              value="2"
              eager
            >
              <p>{{ $t('home.step2Description') }}</p>
            </v-stepper-window-item>

            <v-stepper-window-item
              value="3"
              eager
            >
              <p>{{ $t('home.step3Description') }}</p>
            </v-stepper-window-item>

            <v-stepper-window-item
              value="4"
              eager
            >
              <p>{{ $t('home.step4Description') }}</p>
            </v-stepper-window-item>

            <v-stepper-window-item
              value="5"
              eager
            >
              <p>{{ $t('home.step5Description') }}</p>
            </v-stepper-window-item>
          </v-stepper-window>
          <v-stepper-actions
            @click:prev="prev"
            @click:next="next"
            :next-text="$t('common.next')"
            :prev-text="$t('common.back')"
          >
          </v-stepper-actions>
          </template>
        </v-stepper>
      </v-card-text>
    </v-card>
    <v-card class="mt-6" v-if="isAdmin">
      <v-card-title>{{ $t('settings.servers') }}</v-card-title>
      <v-card-text>
        <v-list v-if="servers.length">
          <v-list-item
            v-for="server in servers"
            :key="server.id"
            :title="server.name"
            :subtitle="server.url"
          >
            <template v-slot:prepend>
              <v-icon :color="server.is_default ? 'success' : ''">
                {{ server.is_default ? 'mdi-server-network' : 'mdi-server' }}
              </v-icon>
            </template>
          </v-list-item>
        </v-list>
        <div v-else class="text-center pa-4">
          {{ $t('settings.noServersConfigured') }}
        </div>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="primary" to="/settings?tab=servers">
          {{ $t('settings.manageServers') }}
        </v-btn>
      </v-card-actions>
    </v-card>    
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useAppStore } from '@/stores/index'
import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'

const appStore = useAppStore()
const authStore = useAuthStore()
const { user } = storeToRefs(authStore)

const servers = computed(() => appStore.servers)
const isAdmin = computed(() => user.value && user.value.is_admin)

onMounted(() => {
  // Bestehender Code...
  appStore.fetchServers()
  console.log("Available servers:", servers.value);
})
</script>
