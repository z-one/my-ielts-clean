import { createApp } from 'vue'
import { createRouter, createWebHashHistory } from 'vue-router'
import { createPinia } from 'pinia'
import routes from 'virtual:generated-pages'
import App from './App.vue'

import '@unocss/reset/tailwind.css'
import './styles/main.css'
import 'uno.css'

const app = createApp(App)
const pinia = createPinia()

const router = createRouter({
  // 改成 Hash 模式
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes,
})

// 添加路由守卫，未登录跳转到登录页
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')

  // 如果不需要登录的页面，直接放行
  const publicPages = ['/login', '/register', '/', '/vocabulary/search']
  const isPublicPage = publicPages.some(page => to.path.startsWith(page))

  if (isPublicPage || to.path.startsWith('/#')) {
    next()
    return
  }

  // 如果没有 token 且访问的是需要登录的页面，跳转到登录页
  if (!token) {
    next('/login')
    return
  }

  next()
})

app.use(pinia)
app.use(router)
app.mount('#app')