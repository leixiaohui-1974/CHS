import { createRouter, createWebHistory } from 'vue-router';
import MainLayout from '../layouts/MainLayout.vue';
import DecisionCockpitPage from '../pages/DecisionCockpitPage.vue';
import ProjectListPage from '../pages/ProjectListPage.vue';
import ProjectDetailPage from '../pages/ProjectDetailPage.vue';
import WorkbenchPage from '../pages/WorkbenchPage.vue';
import EdgeDeviceManagerPage from '../pages/EdgeDeviceManagerPage.vue';
import LoginPage from '../pages/LoginPage.vue';
import { useAuthStore } from '../store/authStore';

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: LoginPage,
  },
  {
    path: '/',
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'DecisionCockpit',
        component: DecisionCockpitPage,
      },
      {
        path: 'projects',
        name: 'ProjectList',
        component: ProjectListPage,
      },
      {
        path: 'projects/:id',
        name: 'ProjectDetail',
        component: ProjectDetailPage,
      },
      {
        path: 'devices',
        name: 'EdgeDeviceManager',
        component: EdgeDeviceManagerPage,
      },
    ],
  },
  {
    // Workbench has its own layout
    path: '/projects/:id/scenes/:sceneId',
    name: 'Workbench',
    component: WorkbenchPage,
    meta: { requiresAuth: true },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
