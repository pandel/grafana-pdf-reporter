<!-- src/components/LanguageSwitcher.vue -->
<template>
  <v-menu
    offset
    location="bottom start"
    transition="slide-y-transition"
  >
    <template v-slot:activator="{ props }">
      <v-btn
        icon="mdi-translate"
        v-bind="props"
        :title="$t('app.language')"
      ></v-btn>
    </template>
    <v-list density="compact">
      <v-list-item
        v-for="lang in availableLanguages"
        :key="lang.code"
        :value="lang.code"
        @click="changeLanguage(lang.code)"
      >
        <template v-slot:prepend>
          <v-icon v-if="lang.code === currentLanguage">mdi-check</v-icon>
        </template>
        <v-list-item-title>{{ lang.name }}</v-list-item-title>
      </v-list-item>
    </v-list>
  </v-menu>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { setLanguage } from '@/plugins/i18n'
import { emitter } from '@/plugins/emitter'

const i18n = useI18n()

const availableLanguages = ref([
  { code: 'de', name: 'Deutsch' },
  { code: 'en', name: 'English' }
])

const currentLanguage = computed(() => i18n.locale.value)

const changeLanguage = (langCode) => {
  if (langCode !== currentLanguage.value) {
    setLanguage(langCode)
    
    emitter.emit('show-notification', {
      type: 'info',
      text: langCode === 'de' ? 'Sprache geändert' : 'Language changed'
    })
  }
}
</script>
