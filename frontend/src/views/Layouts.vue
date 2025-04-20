<!-- src/views/Layouts.vue -->
<template>
  <div class="layouts">
    <v-alert v-if="hasError" type="error" variant="tonal" closable>
      {{ error }}
    </v-alert>
    
    <v-card>
      <v-card-title>
        {{ $t('layouts.title') }}
        <v-spacer></v-spacer>
        <v-btn color="primary" to="/designer">
          <v-icon start>mdi-plus</v-icon>
          {{ $t('layouts.newLayout') }}
        </v-btn>
      </v-card-title>
      
      <v-data-table
        :headers="headers"
        :items="layouts"
        :loading="loading"
        item-value="id"
        :items-per-page="10"
      >
        <template v-slot:item.name="{ item }">
          <div>{{ item.name }}</div>
        </template>
        
        <template v-slot:item.description="{ item }">
          <div>{{ item.description || '-' }}</div>
        </template>

        <template v-slot:item.server_id="{ item }">
          <div>{{ getServerName(item.server_id) }}</div>
        </template>

        <template v-slot:item.modified="{ item }">
          <div>{{ formatDate(item.modified) }}</div>
        </template>

        <template v-slot:item.created_by="{ item }">
          <span>{{ item.created_by || $t('common.unknown') }}</span>
        </template>

        <template v-slot:item.actions="{ item }">
          <v-btn 
            icon="mdi-pencil" 
            size="small" 
            @click="editLayout(item)" 
            :title="$t('layouts.editLayout')"
          ></v-btn>
          <v-btn 
            icon="mdi-content-copy" 
            size="small" 
            @click="duplicateLayout(item)" 
            :title="$t('layouts.duplicateLayout')"
          ></v-btn>
          <v-btn 
            icon="mdi-delete" 
            size="small" 
            @click="confirmDelete(item)" 
            :title="$t('layouts.deleteLayout')"
          ></v-btn>
        </template>
      </v-data-table>
    </v-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/index'
import { emitter } from '@/plugins/emitter'
import { storeToRefs } from 'pinia'
import { useI18n } from 'vue-i18n'

const i18n = useI18n()
const router = useRouter()
const appStore = useAppStore()
const { layouts, loading, error } = storeToRefs(appStore)
const hasError = computed(() => !!error.value)

const servers = computed(() => appStore.servers)

// Table headers
const headers = ref([
  { title: 'Name', key: 'name' },
  { title: 'Description', key: 'description' },
  { title: 'Last Modified', key: 'modified' },
  { title: 'Created By', key: 'created_by' },
  { title: 'Server', key: 'server_id' },
  { title: 'Actions', key: 'actions', sortable: false }
])

const updateHeaders = () => {
  headers.value = [
    { title: i18n.t('common.name'), key: 'name' },
    { title: i18n.t('common.description'), key: 'description' },
    { title: i18n.t('layouts.lastModified'), key: 'modified' },
    { title: i18n.t('layouts.createdBy'), key: 'created_by' },
    { title: i18n.t('reportDesigner.server'), key: 'server_id' },
    { title: i18n.t('common.actions'), key: 'actions', sortable: false }
  ]
}

onMounted(() => {
  appStore.fetchLayouts().then(() => {
    console.log('Layouts in component:', layouts.value)
  })
  updateHeaders()
  appStore.fetchServers()
    
  // Update headers when language changes
  emitter.on('language-changed', updateHeaders)
})

function getServerName(serverId) {
  if (!serverId) return i18n.t('common.default');
  
  const server = servers.value.find(s => s.id === serverId)
  return server ? server.name : i18n.t('common.unknown')
}

const formatDate = (dateString) => {
  if (!dateString) return i18n.t('common.never')
  
  const date = new Date(dateString)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
}

const editLayout = (layout) => {
  // Navigate to ReportDesigner with layoutId
  router.push(`/designer?layoutId=${layout.id}`)
}

const duplicateLayout = (layout) => {
  // Get the layout and create a copy in the ReportDesigner
  appStore.getLayout(layout.id)
    .then(layoutData => {
      if (layoutData) {
        // Remove id to create a new layout
        const newLayout = {...layoutData}
        delete newLayout.id
        newLayout.name = `${i18n.t('layouts.copyPrefix')} ${newLayout.name}`
        
        // Store in localStorage temporarily and redirect to designer
        localStorage.setItem('duplicateLayout', JSON.stringify(newLayout))
        router.push('/designer?duplicate=true')
      }
    })
    .catch(error => {
      emitter.emit('show-notification', {
        type: 'error',
        text: `${i18n.t('layouts.duplicateError')}: ${error.message || i18n.t('common.unknownError')}`
      })
    })
}

const confirmDelete = (layout) => {
  emitter.emit('show-confirm-dialog', {
    title: i18n.t('layouts.deleteLayout'),
    message: i18n.t('layouts.deleteLayoutConfirm', { name: layout.name }),
    confirmText: i18n.t('common.delete'),
    cancelText: i18n.t('common.cancel'),
    confirmColor: 'error',
    onConfirm: () => deleteLayoutConfirmed(layout.id)
  })
}

const deleteLayoutConfirmed = async (layoutId) => {
  try {
    await appStore.deleteLayout(layoutId)
    
    // Refresh layouts
    await appStore.fetchLayouts()
    
    // Show notification
    emitter.emit('show-notification', {
      type: 'success',
      text: i18n.t('layouts.layoutDeleted')
    })
  } catch (error) {
    console.error('Error deleting layout:', error)
    emitter.emit('show-notification', {
      type: 'error',
      text: `${i18n.t('layouts.deleteError')}: ${error.message || i18n.t('common.unknownError')}`
    })
  }
}
</script>
