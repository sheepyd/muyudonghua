import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import PlayerView from '../views/PlayerView.vue'
import { getAuthStatus } from '../utils/auth'

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

router.beforeEach(async (to) => {
  if (to.name !== 'Player') return

  const authorized = await getAuthStatus()
  if (!authorized) {
    return { name: 'Home', query: { auth: '1', next: to.fullPath } }
  }
})

export default router
