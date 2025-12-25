import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Detail from '../views/Detail.vue'
import PlayerView from '../views/PlayerView.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/detail/:id',
    name: 'Detail',
    component: Detail,
    props: (route) => ({ 
      id: route.params.id, 
      type: route.query.type, 
      title: route.query.title,
      backdrop: route.query.backdrop
    })
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