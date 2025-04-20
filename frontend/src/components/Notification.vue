<!-- src/components/Notification.vue -->
<template>
  <v-snackbar
    v-model="snackbar"
    :color="color"
    :timeout="timeout"
    location="top right"
  >
    {{ text }}
    
    <template v-slot:actions>
      <v-btn
        icon="mdi-close"
        variant="text"
        @click="snackbar = false"
        :aria-label="$t('common.close')"
      ></v-btn>
    </template>
  </v-snackbar>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  message: {
    type: Object,
    default: null
  }
})

const snackbar = ref(false)
const color = ref('success')
const text = ref('')
const timeout = ref(4000)

// Watch for changes in message prop
watch(() => props.message, (newMessage) => {
  if (newMessage) {
    showNotification(newMessage)
  }
})

// Function to show notification
const showNotification = ({ type = 'info', text: notificationText, timeout: notificationTimeout = 4000 }) => {
  color.value = type
  text.value = notificationText
  timeout.value = notificationTimeout
  snackbar.value = true
}
</script>
