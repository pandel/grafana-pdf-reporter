<!-- src/views/Templates.vue -->
<template>
  <div class="templates">
    <v-alert v-if="hasError" type="error" variant="tonal" closable>
      {{ error }}
    </v-alert>
    
    <v-row>
      <v-col cols="12" md="4">
        <v-card>
          <v-card-title>{{ $t('templates.title') }}</v-card-title>
          <v-card-text>
            <v-list>
              <v-list-item
                v-for="template in templates"
                :key="template.id"
                :active="selectedTemplateId === template.id"
                @click="selectTemplate(template.id)"
              >
                <template v-slot:prepend>
                  <v-icon>mdi-format-paint</v-icon>
                </template>
                <v-list-item-title>{{ template.name }}</v-list-item-title>
                <v-list-item-subtitle>
                  {{ $t('common.modified') }}: {{ formatDate(template.modified) }}
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="primary" @click="createNewTemplate">
              <v-icon start>mdi-plus</v-icon>
              {{ $t('templates.newTemplate') }}
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
      
      <v-col cols="12" md="8">
        <v-card v-if="currentTemplate">
          <v-card-title>
            <v-text-field
              v-model="currentTemplate.name"
              :label="$t('common.name')"
              :disabled="isDefaultTemplate"
              :error-messages="isDefaultTemplate ? $t('templates.cannotRenameDefault') : ''"
            ></v-text-field>
          </v-card-title>
          
          <v-card-text>
            <v-tabs v-model="activeTab">
              <v-tab value="header">{{ $t('templates.header') }}</v-tab>
              <v-tab value="footer">{{ $t('templates.footer') }}</v-tab>
              <v-tab value="page">{{ $t('templates.page') }}</v-tab>
              <v-tab value="preview">{{ $t('templates.preview') }}</v-tab>
            </v-tabs>
            
            <v-window v-model="activeTab">
              <!-- Header Tab -->
              <v-window-item value="header">
                <v-card flat>
                  <v-card-text>
                    <v-row>
                      <v-col cols="12" sm="6">
                        <v-text-field
                          v-model="currentTemplate.header.title"
                          :label="$t('templates.headerTitle')"
                        ></v-text-field>
                      </v-col>
                      
                      <v-col cols="12" sm="6">
                        <v-row align="center">
                          <v-col>
                            <div class="current-logo d-flex align-center" v-if="currentTemplate.header.logoUrl">
                              <v-img 
                                :src="currentTemplate.header.logoUrl" 
                                max-height="50" 
                                max-width="100" 
                                contain
                                class="mr-2"
                              ></v-img>
                              <span class="text-caption text-truncate">
                                {{ currentTemplate.header.logoFileName || $t('templates.logoUploaded') }}
                              </span>
                            </div>
                            <div class="current-logo d-flex align-center" v-else>
                              <span class="text-caption text-truncate">
                                {{ $t('templates.noLogo') }}
                              </span>
                            </div>
                          </v-col>
                          <v-col cols="auto" v-if="currentTemplate.header.logoUrl">
                            <v-btn 
                              icon="mdi-delete"
                              color="error" 
                              @click="removeLogo" 
                              :title="$t('templates.removeLogo')"
                            ></v-btn>
                          </v-col>
                        </v-row>
                      </v-col>
                      
                      <v-col cols="12" sm="6">
                        <v-text-field
                          v-model.number="currentTemplate.header.height"
                          :label="$t('templates.headerHeight')"
                          type="number"
                          min="5"
                          max="100"
                        ></v-text-field>
                      </v-col>
                      
                      <v-col cols="12" sm="6">
                        <v-file-input
                          :label="$t('templates.uploadLogo')"
                          accept="image/*"
                          @update:model-value="handleLogoUpload"
                          prepend-icon="mdi-image"
                          :placeholder="currentTemplate.header.logoFileName || ''"
                          :clearable="false"
                          :hint="$t('templates.logoHint')"
                          persistent-hint
                        ></v-file-input>
                      </v-col>
                      
                      <v-col cols="12" sm="6">
                        <v-color-picker
                          v-model="currentTemplate.header.textColor"
                          mode="hexa"
                          hide-canvas
                          hide-inputs
                          show-swatches
                        ></v-color-picker>
                        <v-text-field
                          v-model="currentTemplate.header.textColor"
                          :label="$t('templates.textColor')"
                          prepend-icon="mdi-format-color-text"
                        ></v-text-field>
                      </v-col>

                      <v-col cols="12" sm="6">
                        <v-color-picker
                          v-model="currentTemplate.header.backgroundColor"
                          mode="hexa"
                          hide-canvas
                          hide-inputs
                          show-swatches
                        ></v-color-picker>
                        <v-text-field
                          v-model="currentTemplate.header.backgroundColor"
                          :label="$t('templates.backgroundColor')"
                          prepend-icon="mdi-palette"
                        ></v-text-field>
                      </v-col>
                    </v-row>
                  </v-card-text>
                </v-card>
              </v-window-item>
              
              <!-- Footer Tab -->
              <v-window-item value="footer">
                <v-card flat>
                  <v-card-text>
                    <v-row>
                      <v-col cols="12">
                        <v-text-field
                          v-model="currentTemplate.footer.text"
                          :label="$t('templates.footerText')"
                        ></v-text-field>
                      </v-col>
                    </v-row>

                    <v-row>
                      <v-col cols="12" sm="6">
                        <v-text-field
                          v-model="currentTemplate.footer.pageNumberFormat"
                          :label="$t('templates.pageNumberFormat')"
                          :hint="$t('templates.pageNumberFormatHint')"
                          persistent-hint
                        ></v-text-field>
                      </v-col>
                      <v-col cols="12" sm="6">
                        <v-text-field
                          v-model.number="currentTemplate.footer.height"
                          :label="$t('templates.footerHeight')"
                          type="number"
                          min="5"
                          max="100"
                        ></v-text-field>
                      </v-col>
                    </v-row>

                    <v-row>
                      <v-col cols="12" sm="6">
                        <v-color-picker
                          v-model="currentTemplate.footer.textColor"
                          mode="hexa"
                          hide-canvas
                          hide-inputs
                          show-swatches
                        ></v-color-picker>
                        <v-text-field
                          v-model="currentTemplate.footer.textColor"
                          :label="$t('templates.textColor')"
                          prepend-icon="mdi-format-color-text"
                        ></v-text-field>
                      </v-col>
                      
                      <v-col cols="12" sm="6">
                        <v-color-picker
                          v-model="currentTemplate.footer.backgroundColor"
                          mode="hexa"
                          hide-canvas
                          hide-inputs
                          show-swatches
                        ></v-color-picker>
                        <v-text-field
                          v-model="currentTemplate.footer.backgroundColor"
                          :label="$t('templates.backgroundColor')"
                          prepend-icon="mdi-palette"
                        ></v-text-field>
                      </v-col>
                    </v-row>
                  </v-card-text>
                </v-card>
              </v-window-item>

              <!-- Page Tab -->
              <v-window-item value="page">
                <v-card flat>
                  <v-card-text>
                    <v-row>
                      <v-col cols="12" sm="6">
                        <v-select
                          v-model="currentTemplate.page.size"
                          :items="pageSizes"
                          :label="$t('templates.pageSize')"
                        ></v-select>
                      </v-col>
                      
                      <v-col cols="12" sm="6">
                        <v-select
                          v-model="currentTemplate.page.orientation"
                          :items="orientations"
                          :label="$t('templates.orientation')"
                        ></v-select>
                      </v-col>
                      
                      <v-col cols="12" md="6">
                        <v-text-field
                          v-model.number="currentTemplate.page.marginTop"
                          :label="$t('templates.marginTop')"
                          type="number"
                          min="0"
                          max="50"
                        ></v-text-field>
                      </v-col>
                      
                      <v-col cols="12" md="6">
                        <v-text-field
                          v-model.number="currentTemplate.page.marginBottom"
                          :label="$t('templates.marginBottom')"
                          type="number"
                          min="0"
                          max="50"
                        ></v-text-field>
                      </v-col>
                      
                      <v-col cols="12" md="6">
                        <v-text-field
                          v-model.number="currentTemplate.page.marginLeft"
                          :label="$t('templates.marginLeft')"
                          type="number"
                          min="0"
                          max="50"
                        ></v-text-field>
                      </v-col>
                      
                      <v-col cols="12" md="6">
                        <v-text-field
                          v-model.number="currentTemplate.page.marginRight"
                          :label="$t('templates.marginRight')"
                          type="number"
                          min="0"
                          max="50"
                        ></v-text-field>
                      </v-col>
                    </v-row>
                  </v-card-text>
                </v-card>
              </v-window-item>
              
              <!-- Preview Tab -->
              <v-window-item value="preview">
                <v-card flat>
                  <v-card-text>
                    <template-preview
                      :template="currentTemplate"
                      current-page="1"
                      total-pages="5"
                    ></template-preview>
                  </v-card-text>
                </v-card>
              </v-window-item>
            </v-window>
          </v-card-text>
          
          <v-divider></v-divider>
          
          <v-card-actions>
            <v-btn
              color="error"
              variant="text"
              @click="deleteTemplate"
              :disabled="isDefaultTemplate || loading"
            >
              <v-icon start>mdi-delete</v-icon>
              {{ $t('common.delete') }}
            </v-btn>
            
            <v-spacer></v-spacer>
            
            <v-btn
              color="primary"
              @click="saveTemplate"
              :loading="loading"
              :disabled="isDefaultTemplate && !isAdmin"
            >
              <v-icon start>mdi-content-save</v-icon>
              {{ $t('common.save') }}
            </v-btn>
          </v-card-actions>
        </v-card>
        
        <v-card v-else class="d-flex flex-column align-center justify-center" height="100%">
          <v-icon size="x-large" color="grey-lighten-1">mdi-format-paint</v-icon>
          <div class="mt-4 text-subtitle-1 grey--text text--darken-1">
            {{ $t('templates.selectTemplate') }}
          </div>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useI18n } from 'vue-i18n'
import { storeToRefs } from 'pinia'
import { useAppStore } from '@/stores/index'
import TemplatePreview from '@/components/TemplatePreview.vue'
import { emitter } from '@/plugins/emitter'

const i18n = useI18n()
const appStore = useAppStore()
const { templates, loading, error } = storeToRefs(appStore)
const hasError = computed(() => !!error.value)

// Component state
const selectedTemplateId = ref(null)
const currentTemplate = ref(null)
const activeTab = ref('header')
const isAdmin = ref(true) // In a real app, this would come from auth store

// Select options
const pageSizes = ref([
  { title: 'A4', value: 'A4' },
  { title: 'A3', value: 'A3' },
  { title: 'Letter', value: 'Letter' }
])
const orientations = ref([])

// Computed properties
const isDefaultTemplate = computed(() => {
  return selectedTemplateId.value === 'default'
})

// Methods
const updateOrientationOptions = () => {
  orientations.value = [
    { title: i18n.t('templates.portrait'), value: 'portrait' },
    { title: i18n.t('templates.landscape'), value: 'landscape' }
  ]
}

const formatDate = (dateString) => {
  if (!dateString) return i18n.t('common.never')
  
  const date = new Date(dateString)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
}

const selectTemplate = async (templateId) => {
  selectedTemplateId.value = templateId
  
  try {
    // Fetch from API
    const templateData = await appStore.getTemplate(templateId)
    if (templateData) {
      currentTemplate.value = JSON.parse(JSON.stringify(templateData))
      
      // Explicitly add ID to the currentTemplate
      currentTemplate.value.id = templateId
      
      // Ensure the logoFileName property exists
      if (currentTemplate.value.header.logoUrl && !currentTemplate.value.header.logoFileName) {
        currentTemplate.value.header.logoFileName = i18n.t('templates.existingLogo')
      }
    }
  } catch (error) {
    console.error("Error fetching template:", error)
    emitter.emit('show-notification', {
      type: 'error',
      text: `${i18n.t('templates.errorLoadingTemplate')}: ${error.message || i18n.t('common.unknownError')}`
    })
  }
}

const createNewTemplate = () => {
  currentTemplate.value = {
    name: i18n.t('templates.defaultNewTemplateName'),
    header: {
      title: i18n.t('templates.defaultHeaderTitle'),
      logoUrl: '',
      logoFileName: '',
      backgroundColor: '#BCAAA4',
      textColor: '#000000',
      height: 15
    },
    footer: {
      text: i18n.t('templates.defaultFooterText'),
      pageNumberFormat: i18n.t('templates.defaultPageNumberFormat'),
      backgroundColor: '#ECEFF1',
      textColor: '#FFFFFF',
      height: 10
    },
    page: {
      size: 'A4',
      orientation: 'landscape',
      marginTop: 20,
      marginBottom: 20,
      marginLeft: 20,
      marginRight: 20
    }
  }
  
  selectedTemplateId.value = null
  
  // Show notification
  emitter.emit('show-notification', {
    type: 'info',
    text: i18n.t('templates.templateCreated')
  })
}

const handleLogoUpload = (file) => {
  if (!file) return
  
  // Save the original file name
  currentTemplate.value.header.logoFileName = file.name
  
  // Create a data URL for the logo image
  const reader = new FileReader()
  reader.onload = (e) => {
    currentTemplate.value.header.logoUrl = e.target.result
  }
  reader.readAsDataURL(file)
}

const removeLogo = () => {
  // Clear both logo URL and filename
  currentTemplate.value.header.logoUrl = ''
  currentTemplate.value.header.logoFileName = ''
  
  // Show notification
  emitter.emit('show-notification', {
    type: 'info',
    text: i18n.t('templates.logoRemoved')
  })
}

const ensureNumericValues = (template) => {
  // Convert header values
  template.header.height = Number(template.header.height)
  
  // Convert footer values
  template.footer.height = Number(template.footer.height)
  
  // Convert page margin values
  template.page.marginTop = Number(template.page.marginTop)
  template.page.marginBottom = Number(template.page.marginBottom)
  template.page.marginLeft = Number(template.page.marginLeft)
  template.page.marginRight = Number(template.page.marginRight)
  
  return template
}

const saveTemplate = async () => {
  try {
    // Clone the current template to avoid modifying the original
    const preparedTemplate = JSON.parse(JSON.stringify(currentTemplate.value))
    
    // Ensure all numeric values are actually numbers
    ensureNumericValues(preparedTemplate)
    
    // Add the template ID if we are editing an existing template
    if (selectedTemplateId.value) {
      preparedTemplate.id = selectedTemplateId.value
    }
    
    const result = await appStore.saveTemplate(preparedTemplate)

    // If it was a new template, select it now
    if (!selectedTemplateId.value && result && result.id) {
      selectedTemplateId.value = result.id
    }
    
    // Refresh templates
    await appStore.fetchTemplates()
    
    // Show success message
    emitter.emit('show-notification', {
      type: 'success',
      text: i18n.t('templates.templateSaved')
    })
  } catch (error) {
    console.error('Error saving template:', error)
    emitter.emit('show-notification', {
      type: 'error',
      text: `${i18n.t('templates.errorSavingTemplate')}: ${error.message || i18n.t('common.unknownError')}`
    })
  }
}

const deleteTemplate = () => {
  // Show confirmation dialog using emitter
  emitter.emit('show-confirm-dialog', {
    title: i18n.t('templates.deleteTemplate'),
    message: i18n.t('templates.deleteTemplateConfirm'),
    confirmText: i18n.t('common.delete'),
    cancelText: i18n.t('common.cancel'),
    confirmColor: 'error',
    onConfirm: confirmDelete
  })
}

const confirmDelete = async () => {
  try {
    await appStore.deleteTemplate(selectedTemplateId.value)
    
    // Refresh templates
    await appStore.fetchTemplates()
    
    // Reset the current template
    currentTemplate.value = null
    selectedTemplateId.value = null
    
    // If there are templates left, select the first one
    if (templates.value.length > 0) {
      selectTemplate(templates.value[0].id)
    }
    
    // Show success message
    emitter.emit('show-notification', {
      type: 'success',
      text: i18n.t('templates.templateDeleted')
    })
  } catch (error) {
    console.error('Error deleting template:', error)
    emitter.emit('show-notification', {
      type: 'error',
      text: `${i18n.t('templates.errorDeletingTemplate')}: ${error.message || i18n.t('common.unknownError')}`
    })
  }
}

// Lifecycle hooks
onMounted(() => {
  updateOrientationOptions()
  appStore.fetchTemplates().then(() => {
    if (templates.value.length > 0) {
      selectTemplate(templates.value[0].id)
    }
  })
  
  // Listen for language changes
  emitter.on('language-changed', updateOrientationOptions)
})

onBeforeUnmount(() => {
  // Remove event listeners
  emitter.off('language-changed', updateOrientationOptions)
})

// Watch for locale changes
watch(() => i18n.locale.value, () => {
  updateOrientationOptions()
})
</script>

<style scoped>
.current-logo {
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 4px;
  background-color: rgba(0, 0, 0, 0.05);
}
</style>
