import { createRouter, createWebHistory } from 'vue-router';
import MainLayout from '../layouts/MainLayout.vue';
import DashboardPage from '../pages/DashboardPage.vue';
import ProjectDetailPage from '../pages/ProjectDetailPage.vue';
import WorkbenchPage from '../pages/WorkbenchPage.vue';
import EdgeDeviceManagerPage from '../pages/EdgeDeviceManagerPage.vue';

const routes = [
  {
    path: '/',
    component: MainLayout,
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: DashboardPage,
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
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
