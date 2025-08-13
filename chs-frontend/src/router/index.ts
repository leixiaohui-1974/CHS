import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '../views/DashboardView.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import WorkbenchView from '../views/WorkbenchView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/workbench/:id',
      name: 'workbench',
      component: WorkbenchView,
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: DashboardView, // This will be the main project dashboard
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
    },
    {
      path: '/',
      redirect: '/dashboard'
    }
  ],
})

export default router
