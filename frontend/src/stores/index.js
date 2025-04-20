// src/stores/index.js
import { defineStore } from 'pinia'
import api from '../services/api'
import { emitter } from '../plugins/emitter'

export const useAppStore = defineStore('app', {
  state: () => ({
    organizations: [],
    dashboards: [],
    panels: [],
    templates: [],
    layouts: [],
    schedules: [],
    servers: [],
    selectedServerId: null,
    timeRange: {
      from: "now-6h",
      to: "now"
    },
    selectedOrganization: null,
    selectedDashboard: null,
    reportLayout: {
      rows: 2,
      columns: 2,
      panels: []
    },
    selectedTemplate: null,
    loading: false,
    error: null
  }),
  
  getters: {
    hasError: (state) => !!state.error
  },
  
  actions: {
    async fetchServers() {
      this.loading = true;
      try {
        const response = await api.getServers();
        this.servers = response.data;
        console.log('Fetched servers:', this.servers)
        // If we have servers but no selectedServerId, select the first one
        if (this.servers.length > 0 && !this.selectedServerId) {
          // Find default server
          const defaultServer = this.servers.find(server => server.is_default);
          if (defaultServer) {
            this.selectedServerId = defaultServer.id;
          } else {
            this.selectedServerId = this.servers[0].id;
          }
        }
      } catch (error) {
        this.error = error.message;
      } finally {
        this.loading = false;
      }
    },

    async fetchOrganizations(serverId = null) {
      this.loading = true;
      try {
        const serverToUse = serverId || this.selectedServerId;
        const response = await api.getOrganizations(serverToUse);
        this.organizations = response.data;
      } catch (error) {
        this.error = error.message;
      } finally {
        this.loading = false;
      }
    },
    
    async fetchDashboards(organizationId) {
      this.loading = true;
      try {
        const response = await api.getDashboards(organizationId, this.selectedServerId);
        this.dashboards = response.data;
        this.selectedOrganization = organizationId;
      } catch (error) {
        this.error = error.message;
      } finally {
        this.loading = false;
      }
    },
    
    async fetchPanels(dashboardId) {
      this.loading = true;
      try {
        const response = await api.getPanels(dashboardId, this.selectedServerId);
        this.panels = response.data;
        this.selectedDashboard = dashboardId;
      } catch (error) {
        this.error = error.message;
      } finally {
        this.loading = false;
      }
    },
    
    async fetchTemplates() {
      this.loading = true
      try {
        const response = await api.getTemplates()
        this.templates = response.data
      } catch (error) {
        this.error = error.message
      } finally {
        this.loading = false
      }
    },
    
    async fetchSchedules() {
      this.loading = true
      try {
        const response = await api.getSchedules()
        this.schedules = response.data
      } catch (error) {
        this.error = error.message
      } finally {
        this.loading = false
      }
    },

    async getServer(serverId) {
      this.loading = true;
      try {
        const response = await api.getServer(serverId);
        return response.data;
      } catch (error) {
        this.error = error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },
    
    async createServer(server) {
      this.loading = true;
      try {
        const response = await api.createServer(server);
        await this.fetchServers(); // Refresh server list
        return response.data;
      } catch (error) {
        this.error = error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },
    
    async updateServer(serverId, server) {
      this.loading = true;
      try {
        const response = await api.updateServer(serverId, server);
        await this.fetchServers(); // Refresh server list
        return response.data;
      } catch (error) {
        this.error = error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },
    
    async deleteServer(serverId) {
      this.loading = true;
      try {
        await api.deleteServer(serverId);
        await this.fetchServers(); // Refresh server list
      } catch (error) {
        this.error = error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },
  
    async getTemplate(templateId) {
      this.loading = true
      try {
        const response = await api.getTemplate(templateId)
        this.selectedTemplate = templateId
        return response.data
      } catch (error) {
        this.error = error.message
      } finally {
        this.loading = false
      }
    },
    
    async saveTemplate(template) {
      this.loading = true
      try {
        let response
        if (template.id) {
          response = await api.updateTemplate(template)
        } else {
          response = await api.createTemplate(template)
        }
        return response.data
      } catch (error) {
        this.error = error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async deleteTemplate(templateId) {
      this.loading = true
      try {
        await api.deleteTemplate(templateId)
      } catch (error) {
        this.error = error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async fetchLayouts() {
      this.loading = true
      try {
        const response = await api.getLayouts()
        this.layouts = response.data
      } catch (error) {
        this.error = error.message
      } finally {
        this.loading = false
      }
    },
    
    async getLayout(layoutId) {
      this.loading = true
      try {
        const response = await api.getLayout(layoutId)
        return response.data
      } catch (error) {
        this.error = error.message
      } finally {
        this.loading = false
      }
    },
    
    async saveLayout(layout) {
      this.loading = true;
      try {
        // If no server_id is set, use the currently selected server
        if (!layout.server_id) {
          layout.server_id = this.selectedServerId;
        }
        
        let response;
        if (layout.id) {
          response = await api.updateLayout(layout);
        } else {
          response = await api.createLayout(layout);
        }
        return response.data;
      } catch (error) {
        this.error = error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },
    
    async deleteLayout(layoutId) {
      this.loading = true
      try {
        await api.deleteLayout(layoutId)
      } catch (error) {
        this.error = error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async saveSchedule(schedule) {
      this.loading = true
      try {
        let response
        if (schedule.id) {
          response = await api.updateSchedule(schedule)
        } else {
          response = await api.createSchedule(schedule)
        }
        return response.data
      } catch (error) {
        this.error = error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async deleteSchedule(scheduleId) {
      this.loading = true
      try {
        await api.deleteSchedule(scheduleId)
      } catch (error) {
        this.error = error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    
    // Report Layout Actions
    setReportLayout(layout) {
      this.reportLayout = layout
    },
    
    updateReportGrid({ rows, columns }) {
      this.reportLayout.rows = rows
      this.reportLayout.columns = columns
    },
    
    addPanelToLayout(panel) {
      this.reportLayout.panels.push(panel)
    },
    
    removePanelFromLayout(panelIndex) {
      this.reportLayout.panels.splice(panelIndex, 1)
    },
    
    updatePanelPosition({ index, x, y, w, h }) {
      const panel = this.reportLayout.panels[index]
      panel.x = x
      panel.y = y
      panel.w = w
      panel.h = h
    },
    
    setSelectedTemplate(templateId) {
      this.selectedTemplate = templateId
    },
    
    setTimeRange(timeRange) {
      this.timeRange = timeRange
    },
    
    // Settings Actions
    async getSettings() {
      this.loading = true
      try {
        const response = await api.getSettings()
        return response.data
      } catch (error) {
        this.error = error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async updateSettings(settings) {
      this.loading = true
      try {
        const response = await api.updateSettings(settings)
        
        // Emit settings-updated event
        emitter.emit('settings-updated', settings)
        
        return response.data
      } catch (error) {
        this.error = error.message
        throw error
      } finally {
        this.loading = false
      }
    },

    async selectServer(serverId) {
      this.loading = true;
      try {
        await api.selectServer(serverId);
        this.selectedServerId = serverId;
        
        // Reset selections when changing server
        this.selectedOrganization = null;
        this.selectedDashboard = null;
        this.panels = [];
        
        // Force refresh of organizations for new server
        await this.fetchOrganizations(this.selectedServerId);
      } catch (error) {
        this.error = error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async testServerConnection(serverId, settings) {
      this.loading = true;
      try {
        const response = await api.testServerConnection(serverId, settings);
        return response.data;
      } catch (error) {
        this.error = error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async testGrafanaConnection(settings) {
      this.loading = true
      try {
        const response = await api.testGrafanaConnection(settings)
        return response.data
      } catch (error) {
        this.error = error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async testEmailSettings(settings) {
      this.loading = true
      try {
        const response = await api.testEmailSettings(settings)
        return response.data
      } catch (error) {
        this.error = error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async applySettings() {
      this.loading = true
      try {
        const response = await api.applySettings()
        return response.data
      } catch (error) {
        this.error = error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async checkSettingsInitialized() {
      try {
        const response = await api.checkSettingsInitialized()
        return response.data
      } catch (error) {
        this.error = error.message
        throw error
      }
    },
    
    async testLdapConnection(settings) {
      this.loading = true
      try {
        const response = await api.testLdapConnection(settings)
        return response.data
      } catch (error) {
        this.error = error.message
        throw error
      } finally {
        this.loading = false
      }
    }
  }
})
