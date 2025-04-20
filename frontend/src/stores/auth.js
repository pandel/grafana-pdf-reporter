// src/stores/auth.js
import { defineStore } from 'pinia'
import api from '../services/api'
import router from '../router'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    user: null,
    isAuthenticated: !!localStorage.getItem('token'),
    loading: false,
    error: null
  }),
  
  getters: {
    // Getters are automatically computed in Pinia
  },
  
  actions: {
    // Login action
    async login(credentials) {
      this.loading = true
      this.error = null
      
      try {
        // Use api service for login
        const response = await api.login(credentials)
        
        const token = response.data.access_token
        
        // Save token to localStorage
        localStorage.setItem('token', token)
        
        // Set authorization header for future requests
        api.setAuthToken(token)
        
        // Update state
        this.token = token
        this.isAuthenticated = true
        
        // Get user info
        await this.getUserInfo()
        
        return response.data
      } catch (error) {
        console.error('Login error:', error)
        this.error = error.response?.data?.detail || 'Invalid credentials'
        throw error
      } finally {
        this.loading = false
      }
    },
    
    // Setup initial admin user
    async setupUser(userData) {
      this.loading = true
      this.error = null
      
      try {
        // Use api service for setup
        const response = await api.setupUser(userData)
        
        const token = response.data.access_token
        
        // Save token to localStorage
        localStorage.setItem('token', token)
        
        // Set authorization header for future requests
        api.setAuthToken(token)
        
        // Update state
        this.token = token
        this.isAuthenticated = true
        
        // Get user info
        await this.getUserInfo()
        
        return response.data
      } catch (error) {
        console.error('Setup error:', error)
        this.error = error.response?.data?.detail || 'Setup failed'
        throw error
      } finally {
        this.loading = false
      }
    },
    
    // Get user info
    async getUserInfo() {
      this.loading = true
      
      try {
        // Use api service for getting user info
        const response = await api.getUserInfo()
        this.user = response.data
        return response.data
      } catch (error) {
        console.error('Get user info error:', error)
        this.error = error.response?.data?.detail || 'Failed to get user info'
        throw error
      } finally {
        this.loading = false
      }
    },
    
    // Check if token is valid and user is authenticated
    async checkAuth() {
      // If no token in state or localStorage, user is not authenticated
      if (!this.token && !localStorage.getItem('token')) {
        this.isAuthenticated = false
        return false
      }

      try {
        // Try to get user info to validate token
        await this.getUserInfo()
        this.isAuthenticated = true
        return true
      } catch (error) {
        console.error('Auth check failed:', error)
        // If API call fails, token is probably invalid or expired
        this.logout()
        return false
      }
    },

    async fetchUsers() {
      try {
        const response = await api.getUsers();
        return response.data;
      } catch (error) {
        this.error = error.message;
        throw error;
      }
    },
    
    async createUser(userData) {
      try {
        const response = await api.createUser(userData);
        return response.data;
      } catch (error) {
        this.error = error.message;
        throw error;
      }
    },
    
    async updateUser({ username, userData }) {
      try {
        const response = await api.updateUser(username, userData);
        return response.data;
      } catch (error) {
        this.error = error.message;
        throw error;
      }
    },
    
    async deleteUser(username) {
      try {
        await api.deleteUser(username);
      } catch (error) {
        this.error = error.message;
        throw error;
      }
    },

    // Change password
    async changePassword({ currentPassword, newPassword }) {
      this.loading = true;
      this.error = null;
      
      try {
        // API call to change password
        await api.changePassword(currentPassword, newPassword);
        return true;
      } catch (error) {
        console.error('Change password error:', error);
        this.error = error.response?.data?.detail || 'Failed to change password';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    // Logout action
    logout() {
      // Remove token from localStorage
      localStorage.removeItem('token')
      
      // Remove authorization header using api helper
      api.removeAuthToken()
      
      // Reset state
      this.token = null
      this.user = null
      this.isAuthenticated = false
      
      // Redirect to login page
      router.push('/login')
    }
  }
})
