import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { authAPI } from '../api'
import { initializeSync, cleanupOnLogout } from '../services/sync'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('access_token') || null)
  const isLoading = ref(false)

  const isAuthenticated = computed(() => !!token.value)

  // 监听 token 变化，同步到 localStorage
  watch(token, (newToken) => {
    if (newToken) {
      localStorage.setItem('access_token', newToken)
    } else {
      localStorage.removeItem('access_token')
    }
  })

  // 初始化时如果有 token，自动获取用户信息
  if (token.value) {
    fetchUser()
  }

  // 登录
  async function login(username, password) {
    isLoading.value = true
    try {
      const data = await authAPI.login(username, password)
      token.value = data.access_token
      // 获取用户信息
      await fetchUser()
      // 初始化数据同步：从后端加载进度数据
      await initializeSync()
      return { success: true }
    }
    catch (error) {
      return { success: false, error: error.message }
    }
    finally {
      isLoading.value = false
    }
  }

  // 注册
  async function register(userData) {
    isLoading.value = true
    try {
      await authAPI.register(userData)
      return { success: true }
    }
    catch (error) {
      return { success: false, error: error.message }
    }
    finally {
      isLoading.value = false
    }
  }

  // 获取用户信息
  async function fetchUser() {
    if (!token.value) {
      return
    }
    try {
      const userData = await authAPI.getCurrentUser()
      user.value = userData
    }
    catch (error) {
      console.error('获取用户信息失败:', error)
      // token 可能已过期
      logout()
    }
  }

  // 退出登录
  function logout() {
    user.value = null
    token.value = null
    cleanupOnLogout()
    // 不需要手动 window.location.href，让路由处理
  }

  return {
    user,
    token,
    isLoading,
    isAuthenticated,
    login,
    register,
    fetchUser,
    logout,
  }
})
