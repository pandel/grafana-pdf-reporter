// src/main.js
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'
import vuetify from './plugins/vuetify'
import i18n from './plugins/i18n'
import { emitter } from './plugins/emitter'
import { apiClient } from './services/api'
import './utils/cookies'

// Erstelle die App-Instanz
const app = createApp(App)
const pinia = createPinia()

// Globalen Eventbus einrichten
app.config.globalProperties.$eventBus = emitter

// Plugins und Stores registrieren
app.use(router)
app.use(pinia)
app.use(vuetify)
app.use(i18n)

// API-Client global verfügbar machen
app.config.globalProperties.$http = apiClient

// Anwendung starten
app.mount('#app')

// Token-Check für die automatische Anmeldung
const token = localStorage.getItem('token')
if (token) {
  // Auth-Store importieren und Benutzerinfos laden
  import('./stores/auth').then(module => {
    const authStore = module.useAuthStore()
    authStore.getUserInfo().catch(() => {
      authStore.logout()
    })
  })
}
