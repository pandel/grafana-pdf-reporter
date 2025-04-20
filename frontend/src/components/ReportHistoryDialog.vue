<!-- src/components/ReportHistoryDialog.vue -->
<template>
  <v-dialog v-model="dialogVisible" max-width="800px">
    <v-card>
      <v-card-title>
        <span>{{ $t('schedules.historyTitle') }}</span>
        <v-spacer></v-spacer>
        <v-btn icon="mdi-close" @click="close"></v-btn>
      </v-card-title>
      
      <v-card-text>
        <v-data-table
          :headers="headers"
          :items="historyItems"
          :loading="loading"
          :items-per-page="10"
          class="elevation-1"
          :no-data-text="$t('schedules.noHistoryData')"
        >
          <template v-slot:item.timestamp="{ item }">
            {{ formatDateTime(item.timestamp) }}
          </template>
          
          <template v-slot:item.status="{ item }">
            <v-chip 
              :color="getStatusColor(item.status)" 
              size="small"
              text-color="white"
            >
              {{ getStatusText(item.status) }}
            </v-chip>
          </template>
          
          <template v-slot:item.email_sent="{ item }">
            <v-icon v-if="item.email_sent === true" color="success">
              mdi-check-circle
            </v-icon>
            <v-icon v-else-if="item.email_sent === false" color="error">
              mdi-alert-circle
            </v-icon>
            <span v-else>-</span>
          </template>
          
          <template v-slot:item.actions="{ item }">
            <v-btn 
              v-if="item.file_path" 
              icon="mdi-download"
              size="small" 
              color="primary"
              @click="downloadReport(item.file_path)"
              :title="$t('common.download')"
            ></v-btn>
          </template>
        </v-data-table>
      </v-card-text>
      
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="primary" variant="text" @click="close">
          {{ $t('common.close') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { emitter } from '@/plugins/emitter'
import { apiClient } from '@/services/api'
import { useI18n } from 'vue-i18n'


const i18n = useI18n()

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  scheduleId: {
    type: [String, null],
    required: true
  }
})

const emit = defineEmits(['update:modelValue'])

const loading = ref(false)
const historyItems = ref([])

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const headers = computed(() => [
  { title: i18n.t('schedules.historyTimestamp'), key: 'timestamp' },
  { title: i18n.t('common.status'), key: 'status' },
  { title: i18n.t('schedules.historyMessage'), key: 'message' },
  { title: i18n.t('schedules.historyEmailSent'), key: 'email_sent' },
  { title: i18n.t('common.actions'), key: 'actions', sortable: false }
])

const close = () => {
  dialogVisible.value = false
}

const formatDateTime = (dateString) => {
  if (!dateString) return '-'
  
  const date = new Date(dateString)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
}

const getStatusColor = (status) => {
  switch (status) {
    case 'completed':
      return 'success'
    case 'error':
      return 'error'
    case 'started':
      return 'info'
    default:
      return 'grey'
  }
}

const getStatusText = (status) => {
  switch (status) {
    case 'completed':
      return i18n.t('schedules.historyStatusCompleted')
    case 'error':
      return i18n.t('schedules.historyStatusError')
    case 'started':
      return i18n.t('schedules.historyStatusStarted')
    default:
      return status
  }
}

const downloadReport = async (filePath) => {
  try {
    // Show a notification that the download has started
    emitter.emit('show-notification', {
      type: 'info',
      text: i18n.t('schedules.downloadingReport'),
      timeout: 2000
    })
    
    // Axios will automatically add the Authorization header
    const response = await apiClient.get(`/schedules/history/${filePath}`, {
      responseType: 'blob'  // Important: blob response type for files
    })
    
    // Create blob URL and trigger download
    const blob = new Blob([response.data], { type: 'application/pdf' })
    const url = window.URL.createObjectURL(blob)
    
    const a = document.createElement('a')
    a.href = url
    a.download = `grafana-report-${filePath}`
    document.body.appendChild(a)
    a.click()
    
    // Clean up
    setTimeout(() => {
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    }, 0)
  } catch (error) {
    console.error('Error downloading report:', error)
    emitter.emit('show-notification', {
      type: 'error',
      text: i18n.t('schedules.errorDownloadingReport'),
      timeout: 5000
    })
  }
}

const loadHistory = async () => {
  if (!props.scheduleId) return
  
  loading.value = true
  try {
    const response = await apiClient.get(`/schedules/${props.scheduleId}/history`)
    
    // Sort history in reverse chronological order (newest first)
    historyItems.value = response.data.sort((a, b) => {
      return new Date(b.timestamp) - new Date(a.timestamp)
    })
  } catch (error) {
    console.error('Error loading report history:', error)
    emitter.emit('show-notification', {
      type: 'error',
      text: `${i18n.t('schedules.errorLoadingHistory')}: ${error.message || i18n.t('common.unknownError')}`
    })
  } finally {
    loading.value = false
  }
}

watch(() => dialogVisible.value, (val) => {
  if (val) {
    loadHistory()
  }
})

watch(() => props.scheduleId, () => {
  if (dialogVisible.value) {
    loadHistory()
  }
})
</script>
