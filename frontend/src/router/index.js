import { createRouter, createWebHistory } from 'vue-router'

import ApiCasesView from '../views/ApiCasesView.vue'
import ExecutionReportView from '../views/ExecutionReportView.vue'
import LoginView from '../views/LoginView.vue'
import ProjectDetailView from '../views/ProjectDetailView.vue'
import ProjectsView from '../views/ProjectsView.vue'
import UiCasesView from '../views/UiCasesView.vue'

const routes = [
  {
    path: '/',
    redirect: '/login',
  },
  {
    path: '/login',
    name: 'login',
    component: LoginView,
  },
  {
    path: '/projects',
    name: 'projects',
    component: ProjectsView,
  },
  {
    path: '/projects/:id',
    name: 'project-detail',
    component: ProjectDetailView,
    props: true,
  },
  {
    path: '/projects/:id/api-cases',
    name: 'project-api-cases',
    component: ApiCasesView,
    props: true,
  },
  {
    path: '/projects/:id/ui-cases',
    name: 'project-ui-cases',
    component: UiCasesView,
    props: true,
  },
  {
    path: '/projects/:id/executions',
    name: 'project-executions',
    component: ExecutionReportView,
    props: true,
  },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const isLoggedIn = localStorage.getItem('aits_logged_in') === '1'
  if (to.path !== '/login' && !isLoggedIn) {
    return '/login'
  }
  if (to.path === '/login' && isLoggedIn) {
    return '/projects'
  }
  return true
})
