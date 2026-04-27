import { createRouter, createWebHistory } from 'vue-router'

import ApiCasesView from '../views/ApiCasesView.vue'
import ExecutionReportView from '../views/ExecutionReportView.vue'
import ProjectDetailView from '../views/ProjectDetailView.vue'
import ProjectsView from '../views/ProjectsView.vue'
import UiCasesView from '../views/UiCasesView.vue'

const routes = [
  {
    path: '/',
    redirect: '/projects',
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
