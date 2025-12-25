import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import PlayerView from '../views/PlayerView.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/play/:id',
    name: 'Player',
    component: PlayerView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
