// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { apiClient } from '../services/api'

// Lazy-loading components
const Home = () => import('../views/Home.vue')
const Login = () => import('../views/Login.vue')
const ReportDesigner = () => import('../views/ReportDesigner.vue')
const Templates = () => import('../views/Templates.vue')
const Layouts = () => import('../views/Layouts.vue')
const Schedules = () => import('../views/Schedules.vue')
const Settings = () => import('../views/Settings.vue')

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { requiresAuth: true }
  },
  {
    path: '/designer',
    name: 'ReportDesigner',
    component: ReportDesigner,
    meta: { requiresAuth: true }
  },
  {
    path: '/templates',
    name: 'Templates',
    component: Templates,
    meta: { requiresAuth: true }
  },
  {
    path: '/layouts',
    name: 'Layouts',
    component: Layouts,
    meta: { requiresAuth: true }
  },  
  {
    path: '/schedules',
    name: 'Schedules',
    component: Schedules,
    meta: { requiresAuth: true }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
    meta: { 
      requiresAuth: true,
      adminOnly: true
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard to check authentication
router.beforeEach(async (to, from) => {
  // Check if route requires authentication
  if (to.matched.some(record => record.meta.requiresAuth)) {
    try {
      // Check if we need to do first-time setup
      const response = await apiClient.get('/auth/setup-status');
      const data = response.data;
      
      if (data.needs_setup) {
        // First time setup needed.
        return { name: 'Login' }
      }
      
      // Get the auth store
      const authStore = useAuthStore()
      
      // Check if user is authenticated
      const isAuthenticated = authStore.isAuthenticated

      if (!isAuthenticated) {
        // Try to validate token
        const valid = await authStore.checkAuth()

        if (!valid) {
          // Not authenticated, redirect to login
          console.log('Not authenticated, redirecting to login')
          return { name: 'Login' }
        }
      }

      // Check if route requires admin permission
      if (to.matched.some(record => record.meta.adminOnly) && !authStore.user?.is_admin) {
        console.log('Admin permission required for this route, redirecting to home')
        return { name: 'Home' }
      }

      if (to.path !== '/settings') {
        try {
          const response = await apiClient.get('/settings/initialized')
          if (!response.data.initialized || response.data.reason === "default_settings") {
            console.log('Settings not properly initialized, redirecting to settings page')
            return { name: 'Settings' }
          }
        } catch (error) {
          console.error('Error checking settings:', error)
        }
      }
      
      // Authenticated, proceed
      return true
    } catch (error) {
      console.error('Authentication check error: ', error)
      // For severe errors, redirect to login so the user can restart
      return { name: 'Login' }
    }
  }
  
  // Route doesn't require auth, proceed
  return true
})

export default router
