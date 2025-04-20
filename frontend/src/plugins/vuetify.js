// src/plugins/vuetify.js
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { setCookie, getCookie } from '@/utils/cookies'
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'

// Cookie and localStorage keys
const THEME_STORAGE_KEY = 'theme';
const THEME_COOKIE_KEY = 'grafana_pdf_theme';

// Get saved theme preference (cookie first, then localStorage, default to dark)
const getCookieTheme = () => getCookie(THEME_COOKIE_KEY);
const getStoredTheme = () => localStorage.getItem(THEME_STORAGE_KEY);

// Parse theme value to boolean
function parseThemeValue(value) {
  if (value === null || value === undefined) return true; // Default to dark
  return value === 'true' || value === true;
}

const isDarkTheme = parseThemeValue(getCookieTheme() || getStoredTheme());

// Create Vuetify instance
const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: isDarkTheme ? 'dark' : 'light',
    themes: {
      light: {
        colors: {
          primary: '#e2753b',
          secondary: '#424242',
          accent: '#82B1FF',
          error: '#FF5252',
          info: '#2196F3',
          success: '#4CAF50',
          warning: '#FFC107'
        }
      },
      dark: {
        colors: {
          primary: '#df653b',       // Grafana Orange
          secondary: '#212121',     // dunkleres Grau  
          accent: '#536DFE',        // dunkleres Akzentblau
          error: '#D32F2F',         // dunkleres Rot
          info: '#0D47A1',          // dunkleres Info-Blau
          success: '#388E3C',       // dunkleres Grün
          warning: '#F57F17',       // dunkleres Gelb
          background: '#121212',    // dunkler Hintergrund
          surface: '#1E1E1E'        // dunkle Oberfläche
        }
      }
    }
  }
})

// Export a function to toggle theme and save preference
export function toggleTheme() {
  const currentTheme = vuetify.theme.global.name.value;
  const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
  vuetify.theme.global.name.value = newTheme;
  
  // Save to both localStorage and cookie
  localStorage.setItem(THEME_STORAGE_KEY, newTheme === 'dark');
  setCookie(THEME_COOKIE_KEY, newTheme === 'dark');
  
  return newTheme === 'dark';
}

export default vuetify
