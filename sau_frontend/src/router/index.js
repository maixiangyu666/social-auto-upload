import { createRouter, createWebHashHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import AccountManagement from '../views/AccountManagement.vue'
import MaterialManagement from '../views/MaterialManagement.vue'
import PublishCenter from '../views/PublishCenter.vue'
import ProxyManagement from '../views/ProxyManagement.vue'
import About from '../views/About.vue'

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
    path: '/proxy-management',
    name: 'ProxyManagement',
    component: ProxyManagement
  },
  {
    path: '/task-management',
    name: 'TaskManagement',
    component: () => import('../views/TaskManagement/index.vue'),
    children: [
      {
        path: '',
        name: 'TaskList',
        component: () => import('../views/TaskManagement/TaskList.vue')
      },
      {
        path: 'history',
        name: 'PublishHistory',
        component: () => import('../views/TaskManagement/PublishHistory.vue')
      },
      {
        path: ':id',
        name: 'TaskDetail',
        component: () => import('../views/TaskManagement/TaskDetail.vue')
      }
    ]
  },
  {
    path: '/analytics',
    name: 'Analytics',
    component: () => import('../views/Analytics/index.vue')
  },
  {
    path: '/about',
    name: 'About',
    component: About
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router