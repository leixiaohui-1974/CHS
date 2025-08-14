import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';
import router from './router';
import Antd from 'ant-design-vue';
import { useAuthStore } from './store/authStore';

import 'ant-design-vue/dist/reset.css';
import './style.css';

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);

// Auth guard must be after pinia is used
router.beforeEach((to, from, next) => {
    const authStore = useAuthStore();
    const isAuthenticated = !!authStore.token;

    if (to.meta.requiresAuth && !isAuthenticated) {
        next({ name: 'Login' });
    } else if (to.name === 'Login' && isAuthenticated) {
        next({ name: 'DecisionCockpit' });
    } else {
        next();
    }
});

app.use(router);
app.use(Antd);

app.mount('#app');
