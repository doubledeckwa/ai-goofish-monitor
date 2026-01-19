import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'
import PublicLayout from '@/layouts/PublicLayout.vue'
import { useAuth } from '@/composables/useAuth'
import { useUser } from '@/composables/useUser'

const routes = [
  // Public routes
  {
    path: '/',
    component: PublicLayout,
    children: [
      {
        path: '',
        name: 'Marketplace',
        component: () => import('@/views/PublicMarketplaceView.vue'),
        meta: { title: 'Marketplace' },
      },
      {
        path: 'products/:id',
        name: 'ProductDetail',
        component: () => import('@/views/ProductDetailView.vue'),
        meta: { title: 'Product Details' },
      },
      {
        path: 'favorites',
        name: 'Favorites',
        component: () => import('@/views/UserFavoritesView.vue'),
        meta: { title: 'My Favorites' },
      },
    ],
  },
  {
    path: '/user/login',
    name: 'UserLogin',
    component: () => import('@/views/UserLoginView.vue'),
    meta: { title: 'User Login' },
  },
  {
    path: '/user/register',
    name: 'UserRegister',
    component: () => import('@/views/UserRegisterView.vue'),
    meta: { title: 'Register' },
  },

  // Admin routes
  {
    path: '/admin/login',
    name: 'AdminLogin',
    component: () => import('@/views/LoginView.vue'),
    meta: { title: 'Admin Login' },
  },
  {
    path: '/admin',
    component: MainLayout,
    redirect: '/admin/tasks',
    children: [
      {
        path: 'tasks',
        name: 'Tasks',
        component: () => import('@/views/TasksView.vue'),
        meta: { title: 'task management', requiresAuth: true },
      },
      {
        path: 'accounts',
        name: 'Accounts',
        component: () => import('@/views/AccountsView.vue'),
        meta: { title: 'Account management', requiresAuth: true },
      },
      {
        path: 'results',
        name: 'Results',
        component: () => import('@/views/ResultsView.vue'),
        meta: { title: 'View results', requiresAuth: true },
      },
      {
        path: 'logs',
        name: 'Logs',
        component: () => import('@/views/LogsView.vue'),
        meta: { title: 'Run log', requiresAuth: true },
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/SettingsView.vue'),
        meta: { title: 'System settings', requiresAuth: true },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const { isAuthenticated } = useAuth()
  const { isAuthenticated: isUserAuthenticated } = useUser()

  // Set document title
  document.title = `${to.meta.title} - Marketplace` || 'Marketplace'

  // Admin auth check
  if (to.meta.requiresAuth && !isAuthenticated.value) {
    next({ name: 'AdminLogin', query: { redirect: to.fullPath } })
  } else if (to.name === 'AdminLogin' && isAuthenticated.value) {
    next({ name: 'Tasks' })
  } else {
    next()
  }
})

export default router
