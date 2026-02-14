import { createRouter, createWebHashHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import AccountManagement from '../views/AccountManagement.vue'
import MaterialManagement from '../views/MaterialManagement.vue'
import PublishCenter from '../views/PublishCenter.vue'
import About from '../views/About.vue'

// AI 模块
import AICreateView from '../views/ai/AICreateView.vue'
import AIOutlineView from '../views/ai/AIOutlineView.vue'
import AIGenerateView from '../views/ai/AIGenerateView.vue'
import AIResultView from '../views/ai/AIResultView.vue'
import AISettingsView from '../views/ai/AISettingsView.vue'
import AIWizardView from '../views/ai/AIWizardView.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/account-management',
    name: 'AccountManagement',
    component: AccountManagement
  },
  {
    path: '/material-management',
    name: 'MaterialManagement',
    component: MaterialManagement
  },
  {
    path: '/publish-center',
    name: 'PublishCenter',
    component: PublishCenter
  },
  {
    path: '/about',
    name: 'About',
    component: About
  },
  // AI 内容创作
  {
    path: '/ai-create',
    name: 'AICreate',
    component: AICreateView
  },
  {
    path: '/ai-wizard',
    name: 'AIWizard',
    component: AIWizardView
  },
  {
    path: '/ai-create/outline',
    name: 'AIOutline',
    component: AIOutlineView
  },
  {
    path: '/ai-create/generate',
    name: 'AIGenerate',
    component: AIGenerateView
  },
  {
    path: '/ai-create/result',
    name: 'AIResult',
    component: AIResultView
  },
  {
    path: '/ai-settings',
    name: 'AISettings',
    component: AISettingsView
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router