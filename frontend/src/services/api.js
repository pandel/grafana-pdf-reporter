// src/services/api.js
import axios from 'axios'

// Create a single axios instance to be used throughout the app
//let apiURL = window.VITE_API_URL || import.meta.env.VITE_API_URL || 'http://localhost:8080/api'
let apiURL = window.VITE_API_URL || 'http://localhost:8080/api'
export const apiClient = axios.create({
  baseURL: apiURL,
  withCredentials: false,
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json'
  },
  timeout: 120000
})

// Initialize token from localStorage if it exists
const token = localStorage.getItem('token')
if (token) {
  apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`
}

// Define API methods using the apiClient instance
export default {
  // Authentication & User Management
  login(credentials) {
    const formData = new FormData()
    formData.append('username', credentials.username)
    formData.append('password', credentials.password)
    
    // Explicitly set Content-Type for login request
    return apiClient.post('/auth/token', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    })
  },
  
  setupUser(userData) {
    return apiClient.post('/auth/setup', {
      username: userData.username,
      password: userData.password,
      is_admin: true
    })
  },
  
  getUserInfo() {
    return apiClient.get('/auth/me')
  },
  
  checkSetupStatus() {
    return apiClient.get('/auth/setup-status')
  },
  
  getServers() {
    return apiClient.get('/servers');
  },
  
  getServer(serverId) {
    return apiClient.get(`/servers/${serverId}`);
  },
  
  createServer(server) {
    return apiClient.post('/servers', server);
  },
  
  updateServer(serverId, server) {
    return apiClient.put(`/servers/${serverId}`, server);
  },
  
  deleteServer(serverId) {
    return apiClient.delete(`/servers/${serverId}`);
  },
  
  testServerConnection(serverId, settings) {
    return apiClient.post(`/servers/${serverId}/test`, settings);
  },
  
  selectServer(serverId) {
    return apiClient.post(`/servers/${serverId}/select`);
  },
  

  getOrganizations(serverId = null) {
    const url = serverId ? `/servers/${serverId}/organizations` : '/organizations';
    return apiClient.get(url);
  },
  
  getDashboards(orgId, serverId = null) {
    const url = serverId ? 
      `/servers/${serverId}/organizations/${orgId}/dashboards` : 
      `/organizations/${orgId}/dashboards`;
    return apiClient.get(url);
  },
  
  getPanels(dashboardUid, serverId = null) {
    const url = serverId ? 
      `/servers/${serverId}/dashboards/${dashboardUid}/panels` : 
      `/dashboards/${dashboardUid}/panels`;
    return apiClient.get(url);
  },
  
  // Templates
  getTemplates() {
    return apiClient.get('/templates')
  },
  getTemplate(id) {
    return apiClient.get(`/templates/${id}`)
  },
  createTemplate(template) {
    return apiClient.post('/templates', template)
  },
  updateTemplate(template) {
    return apiClient.put(`/templates/${template.id}`, template)
  },
  deleteTemplate(id) {
    return apiClient.delete(`/templates/${id}`)
  },
  
  // Layouts
  getLayouts() {
    return apiClient.get('/layouts')
  },
  getLayout(id) {
    return apiClient.get(`/layouts/${id}`)
  },
  createLayout(layout) {
    return apiClient.post('/layouts', layout)
  },
  updateLayout(layout) {
    return apiClient.put(`/layouts/${layout.id}`, layout)
  },
  deleteLayout(id) {
    return apiClient.delete(`/layouts/${id}`)
  },
  
  // Report Generation
  generatePreview(reportConfig) {
    return apiClient.post('/preview', reportConfig, {
      responseType: 'blob',
      timeout: 120000
    });
  },
  
  exportPDF(reportConfig) {
    return apiClient.post('/export', reportConfig, {
      responseType: 'blob',
      timeout: 120000
    });
  },
  
  // Schedules
  getSchedules() {
    return apiClient.get('/schedules')
  },
  getSchedule(id) {
    return apiClient.get(`/schedules/${id}`)
  },
  createSchedule(schedule) {
    return apiClient.post('/schedules', schedule)
  },
  updateSchedule(schedule) {
    return apiClient.put(`/schedules/${schedule.id}`, schedule)
  },
  deleteSchedule(id) {
    return apiClient.delete(`/schedules/${id}`)
  },
  
  // Settings
  getSettings() {
    return apiClient.get('/settings')
  },
  updateSettings(settings) {
    return apiClient.post('/settings', settings)
  },
  testGrafanaConnection(settings) {
    return apiClient.post('/settings/test/grafana', settings)
  },
  testEmailSettings(settings) {
    return apiClient.post('/settings/test/email', settings)
  },
  applySettings() {
    return apiClient.post('/settings/apply')
  },
  checkSettingsInitialized() {
    return apiClient.get('/settings/initialized')
  },
  
  testLdapConnection(ldapSettings) {
    return apiClient.post('/settings/test/ldap', ldapSettings)
  },
  
  // User Management
  getUsers() {
    return apiClient.get('/auth/users');
  },
  
  getUser(username) {
    return apiClient.get(`/auth/users/${username}`);
  },
  
  createUser(userData) {
    return apiClient.post('/auth/users', userData);
  },
  
  updateUser(username, userData) {
    return apiClient.put(`/auth/users/${username}`, userData);
  },
  
  deleteUser(username) {
    return apiClient.delete(`/auth/users/${username}`);
  },

  changePassword(currentPassword, newPassword) {
    return apiClient.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword
    });
  },
  
  // Helper method to set auth token
  setAuthToken(token) {
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`
  },
  
  // Helper method to remove auth token
  removeAuthToken() {
    delete apiClient.defaults.headers.common['Authorization']
  }
}
