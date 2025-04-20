<!-- src/views/ReportDesigner.vue -->
<template>
  <div class="report-designer">
    <v-alert v-if="hasError" type="error" variant="tonal" closable>
      {{ error }}
    </v-alert>
    
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title>{{ $t('reportDesigner.title') }}</v-card-title>
          <v-card-text>
            <v-row>
              <!-- Left Panel: Selectors and Available Panels -->
              <v-col cols="12" md="4">
                <v-card variant="outlined">
                  <v-card-title>{{ $t('reportDesigner.dataSource') }}</v-card-title>
                  <v-card-text>
                    <v-select
                      v-model="selectedServer"
                      :items="servers"
                      item-title="name"
                      item-value="id"
                      :label="$t('reportDesigner.server')"
                      @update:model-value="onServerChange"
                      :loading="loading"
                    ></v-select>
                    
                    <v-select
                      v-model="selectedOrganization"
                      :items="organizations"
                      item-title="name"
                      item-value="id"
                      :label="$t('reportDesigner.organization')"
                      @update:model-value="loadDashboards"
                      :loading="loading"
                      :disabled="!selectedServer"
                    ></v-select>                    
                    <v-select
                      v-model="selectedDashboard"
                      :items="dashboards"
                      item-title="title"
                      item-value="uid"
                      :label="$t('reportDesigner.dashboard')"
                      @update:model-value="loadPanels"
                      :loading="loading"
                      :disabled="!selectedOrganization"
                    ></v-select>
                  </v-card-text>
                </v-card>
                
                <v-card variant="outlined" class="mt-4" v-if="panels.length > 0">
                  <v-card-title>{{ $t('reportDesigner.availablePanels') }}</v-card-title>
                  <v-card-text style="max-height: 400px; overflow-y: auto;">
                    <v-list>
                      <v-list-item
                        v-for="panel in panels"
                        :key="panel.id"
                        @click="addPanelToLayout(panel)"
                        :disabled="loading"
                      >
                        <template v-slot:prepend>
                          <v-icon>{{ getPanelIcon(panel.type) }}</v-icon>
                        </template>
                        <v-list-item-title>{{ panel.title }}</v-list-item-title>
                        <v-list-item-subtitle>{{ panel.type }}</v-list-item-subtitle>
                        <template v-slot:append>
                          <v-btn icon="mdi-plus"></v-btn>
                        </template>
                      </v-list-item>
                    </v-list>
                  </v-card-text>
                </v-card>
              </v-col>
              
              <!-- Right Panel: Report Layout -->
              <v-col cols="12" md="8">
                <v-card variant="outlined">
                  <v-card-title>{{ $t('reportDesigner.reportLayout') }}</v-card-title>
                  <v-card-text>
                    <v-row>
                      <v-col cols="12" sm="6">
                        <v-select
                          v-model="selectedTemplate"
                          :items="templates"
                          item-title="name"
                          item-value="id"
                          :label="$t('reportDesigner.template')"
                          :loading="loading"
                        ></v-select>
                      </v-col>
                      <v-col cols="12" sm="3">
                        <v-select
                          v-model="reportLayout.rows"
                          :items="[1, 2, 3, 4, 5, 6]"
                          :label="$t('reportDesigner.rowsPerPage')"
                          @update:model-value="updateGridLayout"
                        ></v-select>
                      </v-col>
                      <v-col cols="12" sm="3">
                        <v-select
                          v-model="reportLayout.columns"
                          :items="[1, 2, 3, 4]"
                          :label="$t('reportDesigner.columns')"
                          @update:model-value="updateGridLayout"
                        ></v-select>
                      </v-col>
                    </v-row>
                                        
                    <v-row>
                      <v-col cols="12" sm="6">
                        <v-text-field
                          v-model="timeRange.from"
                          :label="$t('reportDesigner.timeFrom')"
                          :hint="$t('reportDesigner.timeRangeHintFrom')"
                          persistent-hint
                          :error-messages="!validateTimeRangeInput(timeRange.from) ? $t('reportDesigner.timeFormatError') : ''"
                          @input="timeRangeErrors.from = !validateTimeRangeInput(timeRange.from)"
                        ></v-text-field>
                      </v-col>
                      <v-col cols="12" sm="6">
                        <v-text-field
                          v-model="timeRange.to"
                          :label="$t('reportDesigner.timeTo')"
                          :hint="$t('reportDesigner.timeRangeHintTo')"
                          persistent-hint
                          :error-messages="!validateTimeRangeInput(timeRange.to) ? $t('reportDesigner.timeFormatError') : ''"
                          @input="timeRangeErrors.to = !validateTimeRangeInput(timeRange.to)"
                         ></v-text-field>
                      </v-col>
                    </v-row>                    
                    <v-row class="mt-1">
                    <v-col cols="12">
                      <div class="caption mb-1">{{ $t('reportDesigner.quickTimeRanges') }}:</div>
                      <v-chip-group>
                        <v-chip 
                          size="small" 
                          :color="isSelectedTimeRange('now-1h', 'now') ? 'primary' : ''"
                          :variant="!isSelectedTimeRange('now-1h', 'now') ? 'outlined' : 'elevated'"
                          @click="setTimeRange('now-1h', 'now')"
                        >
                          {{ $t('reportDesigner.lastHour') }}
                        </v-chip>
                        <v-chip 
                          size="small" 
                          :color="isSelectedTimeRange('now-6h', 'now') ? 'primary' : ''"
                          :variant="!isSelectedTimeRange('now-6h', 'now') ? 'outlined' : 'elevated'"
                          @click="setTimeRange('now-6h', 'now')"
                        >
                          {{ $t('reportDesigner.last6Hours') }}
                        </v-chip>
                        <v-chip 
                          size="small" 
                          :color="isSelectedTimeRange('now-24h', 'now') ? 'primary' : ''"
                          :variant="!isSelectedTimeRange('now-24h', 'now') ? 'outlined' : 'elevated'"
                          @click="setTimeRange('now-24h', 'now')"
                        >
                          {{ $t('reportDesigner.lastDay') }}
                        </v-chip>
                        <v-chip 
                          size="small" 
                          :color="isSelectedTimeRange('now-7d', 'now') ? 'primary' : ''"
                          :variant="!isSelectedTimeRange('now-7d', 'now') ? 'outlined' : 'elevated'"
                          @click="setTimeRange('now-7d', 'now')"
                        >
                          {{ $t('reportDesigner.lastWeek') }}
                        </v-chip>
                        <v-chip 
                          size="small" 
                          :color="isSelectedTimeRange('now-30d', 'now') ? 'primary' : ''"
                          :variant="!isSelectedTimeRange('now-30d', 'now') ? 'outlined' : 'elevated'"
                          @click="setTimeRange('now-30d', 'now')"
                        >
                          {{ $t('reportDesigner.lastMonth') }}
                        </v-chip>
                        <v-chip 
                          size="small" 
                          :color="isSelectedTimeRange('now-90d', 'now') ? 'primary' : ''"
                          :variant="!isSelectedTimeRange('now-90d', 'now') ? 'outlined' : 'elevated'"
                          @click="setTimeRange('now-90d', 'now')"
                        >
                          {{ $t('reportDesigner.last3Months') }}
                        </v-chip>
                      </v-chip-group>
                    </v-col>
                  </v-row>
                    <div class="grid-container">
                      <div class="report-grid mt-4" :style="gridStyle">
                        <!-- Grid background -->
                        <div class="grid-background" :style="gridBackgroundStyle"></div>
                        
                        <!-- Panels -->
                        <panel-item
                          v-for="(panel, index) in reportLayout.panels" 
                          :key="index"
                          :panel="panel"
                          :grid-config="{ columns: reportLayout.columns, rows: totalGridRows }"
                          :is-active="dragInfo.panelIndex === index"
                          @drag-start="startDrag(index, $event)"
                          @resize-start="startResize(index, $event)"
                          @remove="removePanel(index)"
                        ></panel-item>

                        <!-- Page break indicators -->
                        <div 
                          v-for="page in totalPages" 
                          :key="`page-break-${page}`"
                          class="page-break-indicator"
                          :style="getPageBreakStyle(page)"
                        >
                          <span class="page-number">{{ $t('reportDesigner.page') }} {{ page }}</span>
                        </div>
                      </div>
                    </div>
                  </v-card-text>
                </v-card>

                <v-card variant="outlined" class="mt-4">
                  <v-card-title>{{ $t('reportDesigner.reportActions') }}</v-card-title>
                  <v-card-actions>
                    <v-btn 
                      color="error" 
                      variant="text"
                      @click="clearAllPanels" 
                      :disabled="reportLayout.panels.length === 0 || loading"
                    >
                      <v-icon start>mdi-delete-sweep</v-icon>
                      {{ $t('reportDesigner.removeAllPanels') }}
                    </v-btn>
                    <v-spacer></v-spacer>
                    <v-btn 
                      color="primary" 
                      @click="generatePreview" 
                      :loading="loading"
                      :disabled="!canGenerateReport"
                    >
                      <v-icon start>mdi-eye</v-icon>
                      {{ $t('common.preview') }}
                    </v-btn>
                    <v-btn 
                      color="success" 
                      @click="exportPDF" 
                      :loading="loading"
                      :disabled="!canGenerateReport"
                    >
                      <v-icon start>mdi-file-pdf-box</v-icon>
                      {{ $t('common.export') }}
                    </v-btn>
                    <v-btn 
                      color="primary" 
                      variant="outlined"
                      @click="openSaveLayoutDialog" 
                      :loading="loading"
                      :disabled="!canGenerateReport"
                    >
                      <v-icon start>mdi-content-save</v-icon>
                      {{ $t('reportDesigner.saveLayout') }}
                    </v-btn>
                  </v-card-actions>
                </v-card>
                <save-layout-dialog
                  v-model="saveLayoutDialog"
                  :layout="layoutForSaving"
                  :loading="loading"
                  @save="saveLayoutConfirmed"
                />                
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    
    <!-- PDF Preview Dialog -->
    <v-dialog v-model="previewDialog" fullscreen>
      <v-card>
        <v-toolbar dark color="primary">
          <v-btn icon="mdi-close" @click="previewDialog = false"></v-btn>
          <v-toolbar-title>{{ $t('reportDesigner.previewPDF') }}</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="downloadPreview">
            <v-icon start>mdi-download</v-icon>
            {{ $t('common.download') }}
          </v-btn>
        </v-toolbar>
        <v-card-text class="pa-0" pdf-container>
          <div v-if="isEdgeBrowser && previewUrl" class="edge-fallback">
            <p>{{ $t('reportDesigner.edgeBrowserNotice') }}</p>
            <v-btn color="primary" @click="downloadPreview">
              <v-icon start>mdi-download</v-icon>
              {{ $t('common.download') }}
            </v-btn>
          </div>
          <object 
            v-else-if="previewUrl" 
            :data="previewUrl" 
            type="application/pdf" 
            class="pdf-viewer"
          >
            <div class="pdf-not-supported">
              <p>{{ $t('reportDesigner.pdfViewerNotSupported') }}</p>
              <v-btn color="primary" @click="downloadPreview">
                {{ $t('common.download') }}
              </v-btn>
            </div>
          </object>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Progress Dialog -->
    <v-dialog v-model="progressDialog" persistent :max-width="400">
      <v-card>
        <v-card-title class="text-h5">
          {{ $t('reportDesigner.generatingReport') }}
        </v-card-title>
        <v-card-text>
          <div v-if="!progressStatus.error">
            <p>{{ progressStatus.message }}</p>
            <v-progress-linear 
              v-model="progressStatus.percentage" 
              color="primary" 
              height="25" 
              :striped="true"
            >
              <template v-slot:default>
                <span class="white--text">{{ progressStatus.percentage }}%</span>
              </template>
            </v-progress-linear>
          </div>
          <div v-else class="text-error">
            <p>{{ $t('reportDesigner.generationError') }}</p>
            <p>{{ progressStatus.error }}</p>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" variant="text" @click="progressDialog = false" v-if="progressStatus.error || progressStatus.percentage >= 100">
            {{ $t('common.close') }}
          </v-btn>
          <v-btn color="error" variant="text" @click="cancelReportGeneration()" v-if="!progressStatus.error && progressStatus.percentage < 100">
            {{ $t('common.cancel') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { storeToRefs } from 'pinia'
import { useAppStore } from '@/stores/index'
import { useTheme } from 'vuetify'
import PanelItem from '@/components/PanelItem.vue'
import SaveLayoutDialog from '@/components/SaveLayoutDialog.vue'
import { emitter } from '@/plugins/emitter'
import { apiClient } from '@/services/api'

// Hooks
const i18n = useI18n()
const route = useRoute()
const router = useRouter()
const theme = useTheme()
const appStore = useAppStore()

// Store refs for reactivity
const { 
  organizations, 
  dashboards, 
  panels, 
  templates, 
  reportLayout, 
  loading, 
  error 
} = storeToRefs(appStore)

// Component state
const currentLayoutId = ref(null)
const saveLayoutDialog = ref(false)
const layoutMetadata = ref({
  name: '',
  description: ''
})
const selectedOrganization = ref(null)
const selectedDashboard = ref(null)
const selectedTemplate = ref(null)
const timeRange = ref({
  from: "now-6h",
  to: "now"
})
const timeRangeErrors = ref({
  from: false,
  to: false
})
const dragInfo = ref({
  dragging: false,
  resizing: false,
  panelIndex: null,
  startX: 0,
  startY: 0,
  startLeft: 0,
  startTop: 0,
  startWidth: 0,
  startHeight: 0
})
const progressDialog = ref(false)
const progressStatus = ref({
  percentage: 0,
  message: '',
  error: null
})
const currentJobId = ref(null)
const progressEventSource = ref(null)
const downloadStarted = ref(false)
const previewDialog = ref(false)
const previewUrl = ref(null)
const previewBlob = ref(null)
const isEdgeBrowser = ref(/Edge\/|Edg\//.test(navigator.userAgent))

const selectedServer = ref(null)

// Computed properties
const hasError = computed(() => !!error.value)
const servers = computed(() => appStore.servers)

// Calculate maximum row occupied by any panel
const maxRow = computed(() => {
  if (!reportLayout.value.panels.length) return 0
  
  return Math.max(...reportLayout.value.panels.map(panel => panel.y + panel.h)) || 0
})

// Calculate total number of rows needed for all panels
const totalGridRows = computed(() => {
  // Always show at least the configured number of rows, more if needed
  return Math.max(reportLayout.value.rows, maxRow.value)
})

// Calculate total number of pages based on rows per page and total rows needed
const totalPages = computed(() => {
  if (reportLayout.value.rows <= 0) return 1
  return Math.max(1, Math.ceil(maxRow.value / reportLayout.value.rows))
})

const isDark = computed(() => theme.global.current.value.dark)

const gridStyle = computed(() => {
  const rowHeight = 150 // Height per row in pixels
  return {
    position: 'relative',
    height: `${totalGridRows.value * rowHeight}px`,
    border: isDark.value ? '1px solid #444' : '1px solid #ccc',
    backgroundColor: isDark.value ? '#121212' : '#f5f5f5',
    minHeight: `${reportLayout.value.rows * rowHeight}px` // Ensure minimum height for initial rows
  }
})

const gridBackgroundStyle = computed(() => {
  const { columns } = reportLayout.value
  return {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundImage: isDark.value ?
      `repeating-linear-gradient(#444 0 1px, transparent 1px 100%),
      repeating-linear-gradient(90deg, #444 0 1px, transparent 1px 100%)` :
      `repeating-linear-gradient(#ccc 0 1px, transparent 1px 100%),
      repeating-linear-gradient(90deg, #ccc 0 1px, transparent 1px 100%)`,
    backgroundSize: `${100 / columns}% 150px`,
    pointerEvents: 'none'
  }
})

const layoutForSaving = computed(() => {
  return {
    id: currentLayoutId.value,
    name: layoutMetadata.value.name || '',
    description: layoutMetadata.value.description || '',
    organizationId: selectedOrganization.value,
    rows: reportLayout.value.rows,
    columns: reportLayout.value.columns,
    panels: reportLayout.value.panels.map(panel => ({
      dashboardUid: panel.dashboardUid,
      panelId: panel.panelId,
      title: panel.title,
      type: panel.type,
      x: panel.x,
      y: panel.y,
      w: panel.w,
      h: panel.h
    })),
    templateId: selectedTemplate.value,
    theme: isDark.value ? "dark" : "light",
    timeRange: timeRange.value
  }
})

const timeRangeValid = computed(() => {
  return isTimeRangeValid()
})

// Die canGenerateReport Property für die Prüfung der Button-Aktivierung
const canGenerateReport = computed(() => {
  return selectedOrganization.value && 
         reportLayout.value.panels.length > 0 && 
         timeRangeValid.value
})

// Methods
function onServerChange(serverId) {
  // Server wechseln und Organisationen neu laden
  appStore.selectServer(serverId).then(() => {
    // Bestehende Auswahlen zurücksetzen
    selectedOrganization.value = null
    selectedDashboard.value = null
    panels.value = []
  })
}

function getPanelIcon(type) {
  const icons = {
    'graph': 'mdi-chart-line',
    'bargauge': 'mdi-gauge',
    'gauge': 'mdi-gauge',
    'singlestat': 'mdi-numeric',
    'table': 'mdi-table',
    'text': 'mdi-format-text',
    'heatmap': 'mdi-grid',
    'stat': 'mdi-numeric',
    'timeseries': 'mdi-chart-timeline'
  }
  
  return icons[type] || 'mdi-chart-box'
}

async function loadDashboards(organizationId) {
  selectedDashboard.value = null
  try {
    await appStore.fetchDashboards(organizationId, selectedServer.value)
    console.log(`Dashboards loaded for org ${organizationId} on server ${selectedServer.value}`)
  } catch (error) {
    console.error('Error loading dashboards:', error)
  }
}

function loadPanels(dashboardId) {
  appStore.fetchPanels(dashboardId)
}

function updateGridLayout() {
  appStore.updateReportGrid({
    rows: reportLayout.value.rows,
    columns: reportLayout.value.columns
  })
}

// Get style for page break indicator
function getPageBreakStyle(pageNumber) {
  // Calculate position: page breaks occur after every 'rows' number of rows
  // Subtract 1 from pageNumber because we want the line after the last row of each page
  const rowPosition = pageNumber * reportLayout.value.rows
  const positionPercentage = (rowPosition / totalGridRows.value) * 100
  
  return {
    position: 'absolute',
    left: 0,
    right: 0,
    top: `${positionPercentage}%`,
    borderTop: isDark.value ? '2px dashed rgba(255,255,255,0.4)' : '2px dashed rgba(0,0,0,0.4)',
    textAlign: 'center',
    pointerEvents: 'none',
    zIndex: 2,
    // Don't show the last page break if it's at the bottom of the grid
    display: rowPosition >= totalGridRows.value ? 'none' : 'block'
  }
}

async function loadLayout(layoutId) {
  try {
    const layoutData = await appStore.getLayout(layoutId)
    if (layoutData) {
      setupLayout(layoutData)
      currentLayoutId.value = layoutId

      // Show notification
      emitter.emit('show-notification', {
        type: 'info',
        text: i18n.t('reportDesigner.layoutLoadedForEditing', { name: layoutData.name })
      })
    }
  } catch (error) {
    console.error('Error loading layout:', error)
    emitter.emit('show-notification', {
      type: 'error',
      text: `${i18n.t('reportDesigner.errorLoadingLayout')}: ${error.message || i18n.t('common.unknownError')}`
    })
  }
}

async function setupLayout(layoutData) {
  try {
    // 1. Server wechseln über appStore.selectServer, um den API-Aufruf auszulösen
    if (layoutData.server_id) {
      await appStore.selectServer(layoutData.server_id)
      selectedServer.value = layoutData.server_id
    }
    
    // 2. Dann die Organisation auswählen
    selectedOrganization.value = layoutData.organizationId
    selectedTemplate.value = layoutData.templateId
    
    // 3. Dashboards laden mit expliziter Wartezeit
    await new Promise(resolve => setTimeout(resolve, 500)) // Kurze Verzögerung
    await loadDashboards(layoutData.organizationId)
    
    // 4. Grid und Panels aktualisieren
    appStore.updateReportGrid({
      rows: layoutData.rows,
      columns: layoutData.columns
    });
    
    appStore.setReportLayout({
      rows: layoutData.rows,
      columns: layoutData.columns,
      panels: layoutData.panels
    });
    
    // 5. Layout-Metadaten speichern
    layoutMetadata.value = {
      name: layoutData.name,
      description: layoutData.description
    };
    
    // 6. Zeitbereich setzen, falls vorhanden
    if (layoutData.timeRange) {
      timeRange.value = layoutData.timeRange
    }
    
    // 7. Signalisiere, dass das Setup abgeschlossen ist
    console.log(`Layout setup completed for server: ${layoutData.server_id}, org: ${layoutData.organizationId}`)
  } catch (error) {
    console.error('Error in setupLayout:', error)
    emitter.emit('show-notification', {
      type: 'error',
      text: `Error setting up layout: ${error.message || 'Unknown error'}`
    })
  }
}

function openSaveLayoutDialog() {
  saveLayoutDialog.value = true
}

async function saveLayoutConfirmed(layoutData) {
  console.log("Saving layout:", layoutData)
  
  try {
    // Create or update layout
    const result = await appStore.saveLayout(layoutData)
    
    if (result && result.id) {
      currentLayoutId.value = result.id
      console.log("Layout saved with ID:", currentLayoutId.value)
    }
    
    // Close dialog
    saveLayoutDialog.value = false
    
    // Show notification
    emitter.emit('show-notification', {
      type: 'success',
      text: i18n.t('reportDesigner.layoutSaved')
    })
  } catch (error) {
    console.error('Error saving layout:', error)
    console.error('Error details:', {
      message: error.message,
      response: error.response ? {
        status: error.response.status,
        data: error.response.data
      } : 'No response data'
    })
    
    emitter.emit('show-notification', {
      type: 'error',
      text: `${i18n.t('reportDesigner.errorSavingLayout')}: ${error.message || i18n.t('common.unknownError')}`
    })
  }
}

function addPanelToLayout(panel) {
  // Find first empty cell in the grid
  const { columns } = reportLayout.value
  const totalRows = totalGridRows.value
  
  // Create a 2D array representing the grid
  const grid = Array(totalRows).fill().map(() => Array(columns).fill(false))
  
  // Mark used cells
  for (const p of reportLayout.value.panels) {
    for (let r = p.y; r < p.y + p.h; r++) {
      for (let c = p.x; c < p.x + p.w; c++) {
        if (r < totalRows && c < columns) {
          grid[r][c] = true
        }
      }
    }
  }
  
  // Find first empty cell
  let x = 0, y = 0, found = false
  for (let r = 0; r < totalRows; r++) {
    for (let c = 0; c < columns; c++) {
      if (!grid[r][c]) {
        x = c
        y = r
        found = true
        break
      }
    }
    if (found) break
  }
  
  // If no empty cell found, add to the end
  if (!found) {
    y = totalRows
    x = 0
  }
  
  // Add panel to layout
  appStore.addPanelToLayout({
    dashboardUid: selectedDashboard.value,
    panelId: panel.id,
    title: panel.title,
    type: panel.type,
    x: x,
    y: y,
    w: 1,
    h: 1
  })
  
  // Show notification
  emitter.emit('show-notification', {
    type: 'success',
    text: i18n.t('reportDesigner.panelAdded', { title: panel.title })
  })
}

function clearAllPanels() {
  // Show confirmation dialog
  emitter.emit('show-confirm-dialog', {
    title: i18n.t('reportDesigner.removeAllPanels'),
    message: i18n.t('reportDesigner.removeAllPanelsConfirm'),
    confirmText: i18n.t('common.delete'),
    cancelText: i18n.t('common.cancel'),
    confirmColor: 'error',
    onConfirm: () => {
      // Reset panels array to empty
      appStore.setReportLayout({
        ...reportLayout.value,
        panels: []
      })
      
      // Show notification
      emitter.emit('show-notification', {
        type: 'info',
        text: i18n.t('reportDesigner.allPanelsRemoved')
      })
    }
  })
}

function removePanel(index) {
  const panelTitle = reportLayout.value.panels[index].title
  appStore.removePanelFromLayout(index)
  
  // Show notification
  emitter.emit('show-notification', {
    type: 'info',
    text: i18n.t('reportDesigner.panelRemoved', { title: panelTitle })
  })
}

function startDrag(panelIndex, event) {
  const panel = reportLayout.value.panels[panelIndex]
  
  dragInfo.value = {
    dragging: true,
    resizing: false,
    panelIndex,
    startX: event.clientX,
    startY: event.clientY,
    startLeft: panel.x,
    startTop: panel.y,
    startWidth: panel.w,
    startHeight: panel.h
  }
}

function startResize(panelIndex, event) {
  const panel = reportLayout.value.panels[panelIndex]
  
  dragInfo.value = {
    dragging: false,
    resizing: true,
    panelIndex,
    startX: event.clientX,
    startY: event.clientY,
    startLeft: panel.x,
    startTop: panel.y,
    startWidth: panel.w,
    startHeight: panel.h
  }
}

function onMouseMove(event) {
  if (!dragInfo.value.dragging && !dragInfo.value.resizing) return
  
  const { columns } = reportLayout.value
  const totalRows = totalGridRows.value
  const gridRect = document.querySelector('.report-grid').getBoundingClientRect()
  const cellWidth = gridRect.width / columns
  const cellHeight = gridRect.height / totalRows
  
  // Calculate delta movement in grid cells
  const deltaX = Math.round((event.clientX - dragInfo.value.startX) / cellWidth)
  const deltaY = Math.round((event.clientY - dragInfo.value.startY) / cellHeight)
  
  if (dragInfo.value.dragging) {
    // Update panel position
    let newX = Math.max(0, Math.min(columns - dragInfo.value.startWidth, dragInfo.value.startLeft + deltaX))
    let newY = Math.max(0, dragInfo.value.startTop + deltaY)
    
    appStore.updatePanelPosition({
      index: dragInfo.value.panelIndex,
      x: newX,
      y: newY,
      w: dragInfo.value.startWidth,
      h: dragInfo.value.startHeight
    })
  } else if (dragInfo.value.resizing) {
    // Update panel size
    let newW = Math.max(1, Math.min(columns - dragInfo.value.startLeft, dragInfo.value.startWidth + deltaX))
    let newH = Math.max(1, dragInfo.value.startHeight + deltaY)
    
    appStore.updatePanelPosition({
      index: dragInfo.value.panelIndex,
      x: dragInfo.value.startLeft,
      y: dragInfo.value.startTop,
      w: newW,
      h: newH
    })
  }
}

function onMouseUp() {
  dragInfo.value.dragging = false
  dragInfo.value.resizing = false
}

async function generatePreview() {
  try {
    // Alte SSE-Verbindung schließen, falls vorhanden
    if (progressEventSource.value) {
      progressEventSource.value.close()
      progressEventSource.value = null
    }

    // Download-Flag zurücksetzen
    downloadStarted.value = false

    // Fortschrittsdialog anzeigen
    progressStatus.value = {
      percentage: 0,
      message: i18n.t('reportDesigner.startingPreviewGeneration'),
      error: null
    }
    progressDialog.value = true

    // Set template
    appStore.setSelectedTemplate(selectedTemplate.value)

    // Explicitly set time range
    appStore.setTimeRange(timeRange.value)

    // Generiere eine neue temporäre Job-ID vor der API-Anfrage
    currentJobId.value = "preview_" + Date.now() + "_" + Math.random().toString(36).substring(2, 9)
    
    // SOFORT den Progress-Stream verbinden, noch bevor der API-Aufruf stattfindet
    connectToProgressStream(currentJobId.value)
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // Daten für die API-Anfrage vorbereiten
    const requestData = {
      organizationId: selectedOrganization.value,
      rows: reportLayout.value.rows,
      columns: reportLayout.value.columns,
      panels: reportLayout.value.panels,
      templateId: selectedTemplate.value,
      timeRange: timeRange.value,
      // Neue server_id mitschicken
      server_id: selectedServer.value,
      // Die generierte Job-ID mitschicken
      client_job_id: currentJobId.value
    }
    // Jetzt erst den API-Aufruf starten
    try {
      const response = await apiClient.post('/preview', requestData, { timeout: 120000 })
      
      // Update unsere Job-ID, falls das Backend eine andere vergeben hat
      if (response.data.job_id && response.data.job_id !== currentJobId.value) {
        // Alte SSE-Verbindung schließen
        if (progressEventSource.value) {
          progressEventSource.value.close()
        }
        
        // Neue ID verwenden und neue Verbindung herstellen
        currentJobId.value = response.data.job_id
        connectToProgressStream(currentJobId.value)
      }
      
      // Wenn der Job direkt als abgeschlossen zurückgegeben wird
      if (response.data.status === 'completed') {
        downloadPdfFile(response.data.download_url, true)
      }
    } catch (error) {
      // Fehlerbehandlung
      progressStatus.value.error = error.response?.data?.detail || error.message || i18n.t('reportDesigner.errorGeneratingPreview')
      
      console.error('Error generating preview:', error)
      emitter.emit('show-notification', {
        type: 'error',
        text: `${i18n.t('reportDesigner.errorGeneratingPreview')}: ${error.response?.data?.detail || error.message || i18n.t('common.unknownError')}`
      })
    }
      
  } catch (error) {
    // Allgemeine Fehlerbehandlung
    progressStatus.value.error = error.message || i18n.t('reportDesigner.errorGeneratingPreview')
    console.error('Error in preview generation:', error)
  }
}

async function exportPDF() {
  try {
    // Alte SSE-Verbindung schließen, falls vorhanden
    if (progressEventSource.value) {
      progressEventSource.value.close()
      progressEventSource.value = null
    }

    // Download-Flag zurücksetzen
    downloadStarted.value = false

    // Fortschrittsdialog anzeigen
    progressStatus.value = {
      percentage: 0,
      message: i18n.t('reportDesigner.startingPdfExport'),
      error: null
    }
    progressDialog.value = true

    // Set template
    appStore.setSelectedTemplate(selectedTemplate.value)
    
    // Explicitly set time range
    appStore.setTimeRange(timeRange.value)

    // Generiere eine neue temporäre Job-ID vor der API-Anfrage
    currentJobId.value = "export_" + Math.random().toString(36).substring(2, 15)
    
    // SOFORT den Progress-Stream verbinden, noch bevor der API-Aufruf stattfindet
    connectToProgressStream(currentJobId.value)
    
    // Daten für die API-Anfrage vorbereiten
    const requestData = {
      organizationId: selectedOrganization.value,
      rows: reportLayout.value.rows,
      columns: reportLayout.value.columns,
      panels: reportLayout.value.panels,
      templateId: selectedTemplate.value,
      timeRange: timeRange.value,
      // Neue server_id mitschicken
      server_id: selectedServer.value,
      // Die generierte Job-ID mitschicken
      client_job_id: currentJobId.value
    }

    // Jetzt erst den API-Aufruf starten
    try {
      const response = await apiClient.post('/export', requestData, { timeout: 120000 })
      
      // Update unsere Job-ID, falls das Backend eine andere vergeben hat
      if (response.data.job_id && response.data.job_id !== currentJobId.value) {
        // Alte SSE-Verbindung schließen
        if (progressEventSource.value) {
          progressEventSource.value.close()
        }
        
        // Neue ID verwenden und neue Verbindung herstellen
        currentJobId.value = response.data.job_id
        connectToProgressStream(currentJobId.value)
      }
      
      // Wenn der Job direkt als abgeschlossen zurückgegeben wird
      if (response.data.status === 'completed') {
        downloadPdfFile(response.data.download_url, false)
      }
    } catch (error) {
      // Fehlerbehandlung
      progressStatus.value.error = error.response?.data?.detail || error.message || i18n.t('reportDesigner.errorExportingPDF')
      
      console.error('Error exporting PDF:', error)
      emitter.emit('show-notification', {
        type: 'error',
        text: `${i18n.t('reportDesigner.errorExportingPDF')}: ${error.response?.data?.detail || error.message || i18n.t('common.unknownError')}`
      })
    }
  } catch (error) {
    // Allgemeine Fehlerbehandlung
    progressStatus.value.error = error.message || i18n.t('reportDesigner.errorExportingPDF')
    console.error('Error in PDF export:', error)
  }
}

// Methode zur Verbindung mit dem SSE-Stream
function connectToProgressStream(jobId) {
  console.log("Connecting to progress stream:", jobId)
  // Bestehende Verbindung schließen falls vorhanden
  if (progressEventSource.value) {
    progressEventSource.value.close()
  }
  
  // Token aus dem Store oder localStorage holen
  const token = localStorage.getItem('token')
  if (!token) {
    console.error("No authentication token available")
    progressStatus.value.error = i18n.t('reportDesigner.authenticationError')
    return
  }

  // URL mit angehängtem Token-Parameter erstellen
  const baseUrl = `${apiClient.defaults.baseURL}/progress/${jobId}`
  const eventSourceUrl = `${baseUrl}?token=${encodeURIComponent(token)}`
  console.log("EventSource URL (with token):", baseUrl + "?token=***")
  
  const eventSource = new EventSource(eventSourceUrl)

  // Event-Handler für Fortschrittsupdates
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data)
    console.log('Progress update:', data)
    
    // Fortschrittsstatus aktualisieren
    progressStatus.value.percentage = data.percentage
    if (data.message) {
      progressStatus.value.message = data.message
    }
    
    if (data.status === 'cancelled') {
      console.log("Job was cancelled, closing event source")
      eventSource.close()
      progressEventSource.value = null
      progressDialog.value = false
      return
    }
    
    // Wenn der Job abgeschlossen oder fehlgeschlagen ist
    if (data.status === 'completed' || data.percentage >= 100) {
      // Sofort die Verbindung schließen, um weitere Events zu verhindern
      eventSource.close()
      progressEventSource.value = null
      
      // Wir warten einen Moment, bevor wir das PDF herunterladen
      setTimeout(() => {
        // PDF herunterladen - nur wenn wir es noch nicht getan haben
        if (!downloadStarted.value) {
          downloadStarted.value = true
          downloadPdfFile(`${apiClient.defaults.baseURL}/download/${currentJobId.value}`, 
                        currentJobId.value.startsWith('preview_'))
        }
                      
        // Fortschrittsdialog erst nach dem Download-Start schließen
        setTimeout(() => {
          progressDialog.value = false
        }, 500)
        
        // Erfolgsmeldung anzeigen
        emitter.emit('show-notification', {
          type: 'success',
          text: currentJobId.value.startsWith('preview_') ? 
            i18n.t('reportDesigner.previewGenerated') : 
            i18n.t('reportDesigner.pdfExported')
        })
      }, 1000) // 1 Sekunde warten
    }
  }
  
  // Event-Handler für Fehler
  eventSource.onerror = (error) => {
    console.error('EventSource error:', error)
    console.error('EventSource readyState:', eventSource.readyState)
    
    // Verschiedene Fehlerzustände unterscheiden
    if (eventSource.readyState === EventSource.CLOSED) {
        console.log("Connection was closed")
    } else if (eventSource.readyState === EventSource.CONNECTING) {
        console.log("Connection is trying to reconnect")
        return // Keine Fehlermeldung anzeigen, wenn die Verbindung versucht sich wiederherzustellen
    }
    
    progressStatus.value.error = i18n.t('reportDesigner.lostConnectionToServer')
    
    // Verbindung schließen
    eventSource.close()
    progressEventSource.value = null
    
    // Trotzdem versuchen, das PDF herunterzuladen, falls es bereits fertig ist
    if (progressStatus.value.percentage >= 90) {
      console.log("Attempting download despite connection error")
      setTimeout(() => {
          downloadPdfFile(`${apiClient.defaults.baseURL}/download/${jobId}`, 
                            jobId.startsWith('preview_'))
      }, 1000)
    }
  }

  // Verbindung speichern
  progressEventSource.value = eventSource
}

// Methode zum Herunterladen des PDFs
async function downloadPdfFile(url, isPreview) {
  if (downloadStarted.value && previewBlob.value && isPreview) {
    console.log("PDF already downloaded, skipping")
    return
  }
  
  downloadStarted.value = true
  let retryCount = 0
  const maxRetries = 3      

  const tryDownload = async () => {
    try {
      // PDF-Datei über die API herunterladen
      if (!url.startsWith('http')) {
        // Wenn es ein relativer Pfad ist, stelle sicher, dass er mit / beginnt
        if (!url.startsWith('/')) {
          url = '/' + url
        }
        // Wenn der Pfad nicht mit /api beginnt, füge es hinzu
        if (!url.startsWith('/api')) {
          url = '/api' + url
        }
        // Verwende den Host aus dem baseURL
        const baseUrl = apiClient.defaults.baseURL
        const urlObj = new URL(baseUrl)
        const origin = urlObj.origin
        url = origin + url
      }

      console.log("Attempting to download PDF from:", url)
      
      // PDF-Datei über die API herunterladen
      const response = await apiClient.get(url, { 
          responseType: 'blob',
          timeout: 30000  // 30 Sekunden Timeout für den Download
      })
      
      // Wenn wir ein Vorschau-PDF haben
      if (isPreview) {
        // PDF für die Vorschau speichern
        previewBlob.value = response.data
        previewUrl.value = URL.createObjectURL(previewBlob.value)
        
        // Vorschau-Dialog anzeigen
        previewDialog.value = true
      } else {
        // Download-Link erstellen für Export
        const downloadUrl = URL.createObjectURL(response.data)
        const a = document.createElement('a')
        a.href = downloadUrl
        a.download = `grafana-report-${new Date().toISOString().replace(/[-:]/g, '').replace('T', '-').slice(0, 15)}.pdf`
        document.body.appendChild(a)
        a.click()
        
        // Aufräumen
        setTimeout(() => {
          document.body.removeChild(a)
          URL.revokeObjectURL(downloadUrl)
        }, 0)
      }
    } catch (error) {
      // Wenn der Fehler 404 ist und wir noch Versuche übrig haben, warten und erneut versuchen
      if (error.response && error.response.status === 404 && retryCount < maxRetries) {
        console.log(`PDF not ready yet (404), retrying in 1 second... (${retryCount + 1}/${maxRetries})`)
        retryCount++
        setTimeout(() => tryDownload(), 1000)  // Nach 1 Sekunde erneut versuchen
        return
      }
      
      // Wenn wir bereits eine Vorschau haben, zeigen wir keine Fehlermeldung an
      if (isPreview && previewBlob.value) {
        console.log("PDF preview already exists, ignoring download error")
        return
      }
      
      console.error('Error downloading PDF:', error)
      emitter.emit('show-notification', {
        type: 'error',
        text: `${i18n.t('reportDesigner.errorDownloadingPdf')}: ${error.message || i18n.t('common.unknownError')}`
      })
      // Trotz Fehler den Fortschrittsdialog schließen
      progressDialog.value = false
    }
  }
  
  // Ersten Downloadversuch starten
  await tryDownload()
}

function downloadPreview() {
  if (previewBlob.value) {
    const url = URL.createObjectURL(previewBlob.value)
    const a = document.createElement('a')
    a.href = url
    a.download = `grafana-report-${new Date().toISOString().replace(/[-:]/g, '').replace('T', '-').slice(0, 15)}.pdf`
    document.body.appendChild(a)
    a.click()
    
    // Clean up
    setTimeout(() => {
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    }, 0)
    
    // Show notification
    emitter.emit('show-notification', {
      type: 'success',
      text: i18n.t('reportDesigner.previewDownloaded')
    })
  }
}

async function loadDefaultTemplateFromSettings() {
  try {
    // Get app settings
    const response = await apiClient.get('/settings')
    if (response.data && response.data.general && response.data.general.defaultTemplate) {
      // Set the default template
      selectedTemplate.value = response.data.general.defaultTemplate
      console.log("Default template loaded from settings:", selectedTemplate.value)
    }
  } catch (error) {
    console.error("Error loading default template from settings:", error)
  }
}

async function cancelReportGeneration() {
  try {
    // API aufrufen, um den Job zu beenden
    await apiClient.delete(`/job/${currentJobId.value}`)
    
    // EventSource-Verbindung schließen, falls vorhanden
    if (progressEventSource.value) {
      progressEventSource.value.close()
      progressEventSource.value = null
    }
    
    emitter.emit('show-notification', {
      type: 'info',
      text: i18n.t('reportDesigner.generationCancelled')
    })
  } catch (error) {
    console.error('Error cancelling job:', error)
  } finally {
    // Dialog schließen
    progressDialog.value = false
  }
}

function validateTimeRangeInput(value) {
  // Prüfen auf "now" oder "now-XYZ" Format (relatives Format)
  if (value === 'now' || /^now-\d+[smhdwMy]$/.test(value)) {
    return true
  }
  
  // Prüfen auf absolute Zeitangabe im Format YYYY-MM-DD HH:MM:SS oder YYYY-MM-DD
  if (/^\d{4}-\d{2}-\d{2}( \d{2}:\d{2}:\d{2})?$/.test(value)) {
    return true
  }
  
  return false
}

function isTimeRangeValid() {
  return validateTimeRangeInput(timeRange.value.from) && 
         validateTimeRangeInput(timeRange.value.to)
}

function setTimeRange(from, to) {
  timeRange.value.from = from
  timeRange.value.to = to
  
  // Optional: Fehlerzustände zurücksetzen, da wir gültige Werte setzen
  timeRangeErrors.value.from = false
  timeRangeErrors.value.to = false
}

function isSelectedTimeRange(from, to) {
  return timeRange.value.from === from && timeRange.value.to === to
}

// Lifecycle hooks
onMounted(() => {
  // Servers laden
  appStore.fetchServers().then(() => {
    // Default Server auswählen, wenn einer existiert
    if (appStore.servers.length > 0) {
      const defaultServer = appStore.servers.find(s => s.is_default)
      selectedServer.value = defaultServer ? defaultServer.id : appStore.servers[0].id
      
      // Organisationen für den ausgewählten Server laden
      appStore.fetchOrganizations(selectedServer.value)
    } else {
      // Falls keine Server konfiguriert sind, normale Organisations-Abfrage
      appStore.fetchOrganizations()
    }
  })
  
  appStore.fetchTemplates()

  loadDefaultTemplateFromSettings()

  emitter.on('settings-updated', () => {
    // Wenn Einstellungen geändert wurden, Server neu laden
    appStore.fetchServers().then(() => {
      // Organisationsdaten für den aktuellen Server neu laden
      if (selectedServer.value) {
        appStore.fetchOrganizations(selectedServer.value)
      } else {
        appStore.fetchOrganizations()
      }
    })
    
    loadDefaultTemplateFromSettings()
  })

  // Add event listeners for drag and resize
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)

  const layoutId = route.query.layoutId
  if (layoutId) {
    loadLayout(layoutId)
  }
  
  // Check if we're duplicating a layout
  const isDuplicating = route.query.duplicate === 'true'
  if (isDuplicating) {
    const duplicateLayout = localStorage.getItem('duplicateLayout')
    if (duplicateLayout) {
      try {
        const layoutData = JSON.parse(duplicateLayout)
        setupLayout(layoutData)
        localStorage.removeItem('duplicateLayout')

        // Show notification
        emitter.emit('show-notification', {
          type: 'info',
          text: i18n.t('reportDesigner.layoutLoaded', { name: layoutData.name })
        })
      } catch (error) {
        console.error('Error loading duplicated layout:', error)
      }
    }
  }
})

onBeforeUnmount(() => {
  document.removeEventListener('mousemove', onMouseMove)
  document.removeEventListener('mouseup', onMouseUp)
  emitter.off('settings-updated')
  
  if (progressEventSource.value) {
    progressEventSource.value.close()
    progressEventSource.value = null
  }
})
</script>

<style scoped>
.grid-container {
  overflow-y: auto;
  max-height: 600px;
  border: 1px solid rgba(0,0,0,0.1);
}

.report-grid {
  min-height: 450px;
  position: relative;
}

.page-break-indicator {
  height: 0;
}

.page-number {
  display: inline-block;
  background-color: rgba(0, 0, 0, 0.6);
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  transform: translateY(-50%);
}

.pdf-container {
  position: absolute;
  top: 64px; /* Höhe der Toolbar */
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
}

.pdf-viewer {
  position: absolute;
  top: 64px;
  left: 0;
  width: 100%;
  height: 100%;
  border: none;
}

.pdf-not-supported {
  text-align: center;
  padding: 20px;
}
</style>