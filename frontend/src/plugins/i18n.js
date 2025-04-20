// src/plugins/i18n.js
import { createI18n } from 'vue-i18n'
import en from '@/locales/en.json'
import de from '@/locales/de.json'
import { emitter } from './emitter'
import { setCookie, getCookie } from '@/utils/cookies'

// Cookie and localStorage keys
const LANGUAGE_STORAGE_KEY = 'language';
const LANGUAGE_COOKIE_KEY = 'grafana_pdf_language';

// Get browser language
const getBrowserLanguage = () => {
  const browserLang = navigator.language || navigator.userLanguage
  return browserLang.split('-')[0]
}

// Check cookie first, then localStorage, then browser language with fallback to de
const getCookieLanguage = () => getCookie(LANGUAGE_COOKIE_KEY);
const getStoredLanguage = () => localStorage.getItem(LANGUAGE_STORAGE_KEY);

const preferredLanguage = getCookieLanguage() || getStoredLanguage() || getBrowserLanguage() || 'de';

const i18n = createI18n({
  legacy: false, // Use Composition API
  locale: preferredLanguage,
  fallbackLocale: 'de',
  messages: {
    en,
    de
  },
  silentTranslationWarn: process.env.NODE_ENV === 'production'
})

// Set HTML lang attribute
document.documentElement.setAttribute('lang', i18n.global.locale.value)

// Create a method to change language and save it
export const setLanguage = (lang) => {
  i18n.global.locale.value = lang
  
  // Save to both localStorage and cookie
  localStorage.setItem(LANGUAGE_STORAGE_KEY, lang)
  setCookie(LANGUAGE_COOKIE_KEY, lang)
  
  document.documentElement.setAttribute('lang', lang)
  
  // Emit event for components to update
  emitter.emit('language-changed', lang)
}

export default i18n
