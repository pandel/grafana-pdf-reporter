<!-- src/views/Schedules.vue -->
<template>
  <div class="schedules">
    <v-alert v-if="hasError" type="error" variant="tonal" closable>
      {{ error }}
    </v-alert>
    
    <v-card>
      <v-card-title>
        {{ $t('schedules.title') }}
        <v-spacer></v-spacer>
        <v-btn color="primary" @click="createSchedule">
          <v-icon start>mdi-plus</v-icon>
          {{ $t('schedules.newSchedule') }}
        </v-btn>
      </v-card-title>
      
      <v-data-table
        :headers="headers"
        :items="schedules"
        :loading="loading"
        item-value="id"
        :items-per-page="10"
      >
        <template v-slot:item.name="{ item }">
          <div>{{ item.name }}</div>
        </template>

        <template v-slot:item.server_id="{ item }">
          <div>{{ getServerName(item.server_id) }}</div>
        </template>

        <template v-slot:item.schedule="{ item }">
          <div>{{ formatSchedule(item.schedule) }}</div>
        </template>
        
        <template v-slot:item.lastRun="{ item }">
          <div>{{ formatDateTime(item.lastRun) }}</div>
        </template>
        
        <template v-slot:item.nextRun="{ item }">
          <div>{{ formatDateTime(item.nextRun) }}</div>
        </template>
        
        <template v-slot:item.created_by="{ item }">
          <span>{{ item.created_by || $t('common.unknown') }}</span>
        </template>
        
        <template v-slot:item.status="{ item }">
          <v-chip :color="getStatusColor(item.status)" size="small">
            {{ getStatusText(item.status) }}
          </v-chip>
        </template>
        
        <template v-slot:item.actions="{ item }">
          <v-btn icon="mdi-history" size="small" @click="viewHistory(item)" :title="$t('schedules.viewHistory')"></v-btn>
          <v-btn icon="mdi-pencil" size="small" @click="editSchedule(item)" :title="$t('common.edit')"></v-btn>
          <v-btn icon="mdi-delete" size="small" @click="confirmDelete(item)" :title="$t('common.delete')"></v-btn>
        </template>
      </v-data-table>
    </v-card>
    
    <!-- Schedule Dialog -->
    <v-dialog v-model="dialog" max-width="800px">
      <v-card>
        <v-card-title>
          <span>{{ formTitle }}</span>
        </v-card-title>
        
        <v-card-text>
          <v-container>
            <v-form ref="form" v-model="valid">
              <v-row>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="editedItem.name"
                    :label="$t('schedules.scheduleName')"
                    required
                    :rules="[v => !!v || $t('common.name') + ' ' + $t('common.isRequired')]"
                  ></v-text-field>
                </v-col>
                
                <v-col cols="12" sm="6">
                  <v-select
                    v-model="editedItem.status"
                    :items="statusItems"
                    :label="$t('common.status')"
                    required
                  ></v-select>
                </v-col>
              </v-row>
              
              <v-divider class="my-4"></v-divider>
              <h3 class="text-subtitle-1">{{ $t('schedules.reportConfig') }}</h3>

              <v-row>
                <v-col cols="12">
                  <v-select
                    v-model="editedItem.layoutId"
                    :items="layouts"
                    item-title="name"
                    item-value="id"
                    :label="$t('schedules.selectLayout')"
                    :rules="[v => !!v || $t('schedules.selectLayout') + ' ' + $t('common.isRequired')]"
                    @update:model-value="loadLayoutDetails"
                  ></v-select>
                  <p v-if="!layouts.length" class="text-caption text-error">
                    {{ $t('schedules.noLayoutsFound') }}
                  </p>
                </v-col>
              </v-row>
              <v-row>
                <v-col cols="12">
                  <v-select
                    v-model="editedItem.server_id"
                    :items="servers"
                    item-title="name"
                    item-value="id"
                    :label="$t('reportDesigner.server')"
                    :disabled="!servers.length"
                  ></v-select>
                  <div v-if="showServerWarning" class="text-error text-caption mt-1">
                    <v-icon size="small" color="warning">mdi-alert</v-icon> 
                    {{ $t('schedules.serverOverrideWarning') }}
                  </div>
                </v-col>
              </v-row>

              <v-row v-if="editedItem.layoutId">
                <v-col cols="12">
                  <v-card variant="outlined">
                    <v-card-title>{{ $t('schedules.layoutDetails') }}</v-card-title>
                    <v-card-text>
                      <v-row>
                        <v-col cols="6">
                          <div class="font-weight-medium">{{ $t('schedules.organization') }}:</div>
                          <div>{{ getOrganizationName(currentLayoutDetails.organizationId) }}</div>
                        </v-col>
                        <v-col cols="6">
                          <div class="font-weight-medium">{{ $t('schedules.template') }}:</div>
                          <div>{{ getTemplateName(currentLayoutDetails.templateId) }}</div>
                        </v-col>
                      </v-row>
                      <v-row>
                        <v-col cols="6">
                          <div class="font-weight-medium">{{ $t('schedules.grid') }}:</div>
                          <div>{{ $t('schedules.rowsAndColumns', { rows: currentLayoutDetails.rows, columns: currentLayoutDetails.columns }) }}</div>
                        </v-col>
                        <v-col cols="6">
                          <div class="font-weight-medium">{{ $t('schedules.panels') }}:</div>
                          <div>{{ $t('schedules.panelCount', { count: currentLayoutDetails.panels ? currentLayoutDetails.panels.length : 0 }) }}</div>
                        </v-col>
                      </v-row>
                    </v-card-text>
                  </v-card>
                </v-col>
              </v-row>
              
              <v-divider class="my-4"></v-divider>
              <h3 class="text-subtitle-1">{{ $t('schedules.scheduleConfig') }}</h3>
              
              <v-row>
                <v-col cols="12" sm="6">
                  <v-select
                    v-model="editedItem.schedule.frequency"
                    :items="frequencyOptions"
                    :label="$t('schedules.frequency')"
                    @update:model-value="updateCronExpression"
                  ></v-select>
                </v-col>
                
                <template v-if="editedItem.schedule.frequency === 'daily'">
                  <v-col cols="12" sm="6">
                    <v-text-field
                      v-model="editedItem.schedule.dailyTime"
                      type="time"
                      :label="$t('schedules.time')"
                      @update:model-value="updateCronExpression"
                    ></v-text-field>
                  </v-col>
                </template>
                
                <template v-if="editedItem.schedule.frequency === 'weekly'">
                  <v-col cols="12" sm="6">
                    <v-select
                      v-model="editedItem.schedule.weeklyDay"
                      :items="daysOfWeek"
                      :label="$t('schedules.dayOfWeek')"
                      @update:model-value="updateCronExpression"
                    ></v-select>
                  </v-col>
                  <v-col cols="12" sm="6">
                    <v-text-field
                      v-model="editedItem.schedule.weeklyTime"
                      type="time"
                      :label="$t('schedules.time')"
                      @update:model-value="updateCronExpression"
                    ></v-text-field>
                  </v-col>
                </template>
                
                <template v-if="editedItem.schedule.frequency === 'monthly'">
                  <v-col cols="12" sm="6">
                    <v-select
                      v-model="editedItem.schedule.monthlyDay"
                      :items="daysOfMonth"
                      :label="$t('schedules.dayOfMonth')"
                      @update:model-value="updateCronExpression"
                    ></v-select>
                  </v-col>
                  <v-col cols="12" sm="6">
                    <v-text-field
                      v-model="editedItem.schedule.monthlyTime"
                      type="time"
                      :label="$t('schedules.time')"
                      @update:model-value="updateCronExpression"
                    ></v-text-field>
                  </v-col>
                </template>
                
                <template v-if="editedItem.schedule.frequency === 'custom'">
                  <v-col cols="12">
                    <v-text-field
                      v-model="editedItem.schedule.cronExpression"
                      :label="$t('schedules.cronExpression')"
                      :hint="$t('schedules.cronExpressionHint')"
                      persistent-hint
                    ></v-text-field>
                  </v-col>
                </template>
              </v-row>
              
              <v-divider class="my-4"></v-divider>
              <h3 class="text-subtitle-1">{{ $t('schedules.emailConfig') }}</h3>
              
              <v-row>
                <v-col cols="12">
                  <v-switch
                    v-model="editedItem.schedule.email.enabled"
                    :label="$t('schedules.sendEmail')"
                  ></v-switch>
                </v-col>
              </v-row>
              
              <v-row v-if="editedItem.schedule.email.enabled">
                <v-col cols="12">
                  <v-combobox
                    v-model="editedItem.schedule.email.recipients"
                    :label="$t('schedules.recipients')"
                    multiple
                    chips
                    :hint="$t('schedules.recipientsHint')"
                    persistent-hint
                  ></v-combobox>
                </v-col>
                
                <v-col cols="12">
                  <v-text-field
                    v-model="editedItem.schedule.email.subject"
                    :label="$t('schedules.emailSubject')"
                  ></v-text-field>
                </v-col>
                
                <v-col cols="12">
                  <v-textarea
                    v-model="editedItem.schedule.email.body"
                    :label="$t('schedules.emailBody')"
                    rows="3"
                  ></v-textarea>
                </v-col>
              </v-row>
            </v-form>
          </v-container>
        </v-card-text>
        
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="blue-darken-1" variant="text" @click="close">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="blue-darken-1" variant="text" @click="save" :disabled="!valid">{{ $t('common.save') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    
    <report-history-dialog
      v-model="historyDialog"
      :schedule-id="currentScheduleId"
    />    
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { storeToRefs } from 'pinia'
import { useAppStore } from '@/stores/index'
import { emitter } from '@/plugins/emitter'
import ReportHistoryDialog from '@/components/ReportHistoryDialog.vue'

const i18n = useI18n()
const appStore = useAppStore()
const { organizations, templates, layouts, schedules, loading, error } = storeToRefs(appStore)
const hasError = computed(() => !!error.value)

// Form refs
const form = ref(null)

// Component state
const dialog = ref(false)
const valid = ref(true)
const editedIndex = ref(-1)
const currentScheduleId = ref(null)
const historyDialog = ref(false)

// Form options
const frequencyOptions = ref([])
const daysOfWeek = ref([])
const daysOfMonth = ref([])
const statusItems = ref([])
const headers = ref([])

// Form data
const editedItem = ref({
  name: '',
  status: 'active',
  layoutId: null,
  reportLayout: null,
  schedule: {
    frequency: 'daily',
    dailyTime: '00:00',
    weeklyDay: 1,
    weeklyTime: '00:00',
    monthlyDay: 1,
    monthlyTime: '00:00',
    cronExpression: '0 0 * * *',
    email: {
      enabled: false,
      recipients: [],
      subject: '',
      body: ''
    }
  }
})

const defaultItem = {
  name: '',
  status: 'active',
  layoutId: null,
  reportLayout: null,
  schedule: {
    frequency: 'daily',
    dailyTime: '00:00',
    weeklyDay: 1,
    weeklyTime: '00:00',
    monthlyDay: 1,
    monthlyTime: '00:00',
    cronExpression: '0 0 * * *',
    email: {
      enabled: false,
      recipients: [],
      subject: '',
      body: ''
    }
  }
}

const currentLayoutDetails = ref({
  organizationId: null,
  templateId: null,
  rows: 0,
  columns: 0,
  panels: []
})

// Computed values
const formTitle = computed(() => {
  return editedIndex.value === -1 
    ? i18n.t('schedules.newSchedule') 
    : i18n.t('common.edit') + ' ' + editedItem.value.name
})

const servers = computed(() => appStore.servers)

const showServerWarning = computed(() => {
  return currentLayoutDetails.value.server_id && 
         editedItem.value.server_id && 
         currentLayoutDetails.value.server_id !== editedItem.value.server_id;
});

// Methods
const updateTranslatedOptions = () => {
  // Update translations for frequency options
  frequencyOptions.value = [
    { title: i18n.t('schedules.daily'), value: 'daily' },
    { title: i18n.t('schedules.weekly'), value: 'weekly' },
    { title: i18n.t('schedules.monthly'), value: 'monthly' },
    { title: i18n.t('schedules.custom'), value: 'custom' }
  ]
  
  // Update translations for weekdays
  daysOfWeek.value = [
    { title: i18n.t('schedules.monday'), value: 1 },
    { title: i18n.t('schedules.tuesday'), value: 2 },
    { title: i18n.t('schedules.wednesday'), value: 3 },
    { title: i18n.t('schedules.thursday'), value: 4 },
    { title: i18n.t('schedules.friday'), value: 5 },
    { title: i18n.t('schedules.saturday'), value: 6 },
    { title: i18n.t('schedules.sunday'), value: 0 }
  ]
  
  // Days of month (no specific translations needed)
  daysOfMonth.value = Array.from({ length: 31 }, (_, i) => ({ title: `${i + 1}`, value: i + 1 }))
  
  // Status items
  statusItems.value = [
    { title: i18n.t('common.active'), value: 'active' },
    { title: i18n.t('common.paused'), value: 'paused' }
  ]
  
  // Update headers
  headers.value = [
    { title: i18n.t('common.name'), key: 'name' },
    { title: i18n.t('reportDesigner.server'), key: 'server_id' },
    { title: i18n.t('schedules.schedule'), key: 'schedule' },
    { title: i18n.t('schedules.lastRun'), key: 'lastRun' },
    { title: i18n.t('schedules.nextRun'), key: 'nextRun' },
    { title: i18n.t('common.status'), key: 'status' },
    { title: i18n.t('schedules.createdBy'), key: 'created_by' },
    { title: i18n.t('common.actions'), key: 'actions', sortable: false }
  ]
}

const initialize = () => {
  Promise.all([
    appStore.fetchOrganizations(),
    appStore.fetchTemplates(),
    appStore.fetchSchedules(),
    appStore.fetchLayouts()
  ])
}

function getServerName(serverId) {
  if (!serverId) return i18n.t('common.default');
  
  const server = servers.value.find(s => s.id === serverId);
  return server ? server.name : i18n.t('common.unknown');
}

const formatDateTime = (dateString) => {
  if (!dateString) return i18n.t('common.never')
  
  const date = new Date(dateString)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
}

const formatSchedule = (schedule) => {
  if (!schedule) return i18n.t('common.unknown')
  
  switch (schedule.frequency) {
    case 'daily': {
      return `${i18n.t('schedules.daily')} ${i18n.t('schedules.at')} ${schedule.dailyTime}`
    }
    case 'weekly': {
      const day = getDayName(schedule.weeklyDay)
      return `${i18n.t('schedules.everyWeekday', { day })} ${i18n.t('schedules.at')} ${schedule.weeklyTime}`
    }
    case 'monthly': {
      return `${i18n.t('schedules.monthly')} ${i18n.t('schedules.onDay')} ${schedule.monthlyDay} ${i18n.t('schedules.at')} ${schedule.monthlyTime}`
    }
    case 'custom': {
      return `${i18n.t('schedules.custom')}: ${schedule.cronExpression}`
    }
    default: {
      return schedule.cronExpression
    }
  }
}

const getDayName = (dayValue) => {
  const day = daysOfWeek.value.find(d => d.value === dayValue)
  return day ? day.title : i18n.t('common.unknown')
}

const getStatusText = (status) => {
  switch (status) {
    case 'active':
      return i18n.t('common.active')
    case 'paused':
      return i18n.t('common.paused')
    default:
      return status
  }
}

const getStatusColor = (status) => {
  return status === 'active' ? 'success' : 'grey'
}

const updateCronExpression = () => {
  const schedule = editedItem.value.schedule
  
  switch (schedule.frequency) {
    case 'daily': {
      const timeParts = schedule.dailyTime.split(':')
      const hours = timeParts[0]
      const minutes = timeParts[1]
      schedule.cronExpression = `${minutes} ${hours} * * *`
      break
    }
    case 'weekly': {
      const timeParts = schedule.weeklyTime.split(':')
      const hours = timeParts[0]
      const minutes = timeParts[1]
      schedule.cronExpression = `${minutes} ${hours} * * ${schedule.weeklyDay}`
      break
    }
    case 'monthly': {
      const timeParts = schedule.monthlyTime.split(':')
      const hours = timeParts[0]
      const minutes = timeParts[1]
      schedule.cronExpression = `${minutes} ${hours} ${schedule.monthlyDay} * *`
      break
    }
    // For 'custom', we don't update the cron expression automatically
  }
}

const createSchedule = () => {
  editedIndex.value = -1
  editedItem.value = JSON.parse(JSON.stringify(defaultItem))
  // Set default values for email
  editedItem.value.schedule.email.subject = i18n.t('schedules.defaultEmailSubject')
  editedItem.value.schedule.email.body = i18n.t('schedules.defaultEmailBody')
  currentLayoutDetails.value = {
    organizationId: null,
    templateId: null,
    rows: 0,
    columns: 0,
    panels: []
  }
  dialog.value = true
  
  // Reset form validation on next tick
  nextTick(() => {
    if (form.value) {
      form.value.resetValidation()
    }
  })
}

const editSchedule = (item) => {
  editedIndex.value = schedules.value.findIndex(s => s.id === item.id)
  editedItem.value = JSON.parse(JSON.stringify(item))
  
  // Load layout details if layoutId exists
  if (editedItem.value.layoutId) {
    loadLayoutDetails(editedItem.value.layoutId)
  } else {
    currentLayoutDetails.value = {
      organizationId: null,
      templateId: null,
      rows: 0,
      columns: 0,
      panels: []
    }
  }
  dialog.value = true
  
  // Reset form validation on next tick
  nextTick(() => {
    if (form.value) {
      form.value.resetValidation()
    }
  })
}

const close = () => {
  dialog.value = false
  // Wait for dialog to close before resetting
  setTimeout(() => {
    editedItem.value = JSON.parse(JSON.stringify(defaultItem))
    editedIndex.value = -1
  }, 300)
}

const save = async () => {
  if (form.value && !valid.value) return
  
  try {
    // Make sure we have the correct cron expression
    updateCronExpression()
    
    // Transform the edited item to match the expected format
    const scheduleData = {
      ...editedItem.value,
      reportLayout: editedItem.value.reportLayout
    }
    
    // Save the schedule
    await appStore.saveSchedule(scheduleData)
    
    // Refresh schedules
    await appStore.fetchSchedules()
    
    // Close the dialog
    close()
    
    // Show notification
    emitter.emit('show-notification', {
      type: 'success',
      text: editedIndex.value === -1 
        ? i18n.t('schedules.scheduleCreated') 
        : i18n.t('schedules.scheduleUpdated')
    })
  } catch (error) {
    console.error('Error saving schedule:', error)
    emitter.emit('show-notification', {
      type: 'error',
      text: `${i18n.t('schedules.errorSavingSchedule')}: ${error.message || i18n.t('common.unknownError')}`
    })
  }
}

const confirmDelete = (item) => {
  emitter.emit('show-confirm-dialog', {
    title: i18n.t('schedules.deleteSchedule'),
    message: i18n.t('schedules.deleteScheduleConfirm', { name: item.name }),
    confirmText: i18n.t('common.delete'),
    cancelText: i18n.t('common.cancel'),
    confirmColor: 'error',
    onConfirm: () => deleteScheduleConfirmed(item.id)
  })
}

const deleteScheduleConfirmed = async (scheduleId) => {
  try {
    await appStore.deleteSchedule(scheduleId)
    
    // Refresh schedules
    await appStore.fetchSchedules()
    
    // Show notification
    emitter.emit('show-notification', {
      type: 'success',
      text: i18n.t('schedules.scheduleDeleted')
    })
  } catch (error) {
    console.error('Error deleting schedule:', error)
    emitter.emit('show-notification', {
      type: 'error',
      text: `${i18n.t('schedules.errorDeletingSchedule')}: ${error.message || i18n.t('common.unknownError')}`
    })
  }
}

const loadLayoutDetails = async (layoutId) => {
  if (!layoutId) {
    currentLayoutDetails.value = {
      organizationId: null,
      templateId: null,
      rows: 0,
      columns: 0,
      panels: [],
      server_id: null
    }
    return
  }
  
  try {
    const layoutData = await appStore.getLayout(layoutId)
    if (layoutData) {
      currentLayoutDetails.value = layoutData
      
      // Update the edited item with layout details
      editedItem.value.reportLayout = {
        organizationId: layoutData.organizationId,
        templateId: layoutData.templateId,
        rows: layoutData.rows, 
        columns: layoutData.columns,
        panels: layoutData.panels
      }

      // Hier die neue Logik: Server-ID aus dem Layout übernehmen, falls vorhanden
      if (layoutData.server_id) {
        editedItem.value.server_id = layoutData.server_id;
      }
    }
  } catch (error) {
    console.error('Error loading layout details:', error)
    emitter.emit('show-notification', {
      type: 'error',
      text: `${i18n.t('schedules.errorLoadingLayout')}: ${error.message || i18n.t('common.unknownError')}`
    })
  }
}

const getOrganizationName = (orgId) => {
  if (!orgId) return i18n.t('schedules.notSelected')
  const org = organizations.value.find(o => o.id === orgId)
  return org ? org.name : `${i18n.t('schedules.organization')} ${orgId}`
}

const getTemplateName = (templateId) => {
  if (!templateId) return i18n.t('schedules.default')
  const template = templates.value.find(t => t.id === templateId)
  return template ? template.name : `${i18n.t('schedules.template')} ${templateId}`
}

const viewHistory = (item) => {
  currentScheduleId.value = item.id
  historyDialog.value = true
}

// Lifecycle hooks
onMounted(() => {
  initialize()
  updateTranslatedOptions()
  
  appStore.fetchServers()

  // Listen for language changes
  emitter.on('language-changed', updateTranslatedOptions)
})

watch(() => i18n.locale.value, () => {
  updateTranslatedOptions()
})

watch(() => dialog.value, (val) => {
  if (val) {
    // When dialog opens, check if we should set default email values
    if (!editedItem.value.schedule.email.subject) {
      editedItem.value.schedule.email.subject = i18n.t('schedules.defaultEmailSubject')
    }
    if (!editedItem.value.schedule.email.body) {
      editedItem.value.schedule.email.body = i18n.t('schedules.defaultEmailBody')
    }
  }
})
</script>
