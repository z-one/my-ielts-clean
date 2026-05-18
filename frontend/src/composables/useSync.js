/**
 * 数据同步组合式函数
 * 用于在组件中集成数据同步功能
 * 注意：数据同步在数据变化时触发，不再使用定时同步
 */

import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useAuthStore } from '../stores/auth'
import { loadChapterStatus, loadWordProgress, loadUserSettings } from '../services/sync'

export function useDataSync(currentChapter) {
  const authStore = useAuthStore()
  const isLoading = ref(false)

  /**
   * 加载用户的所有数据
   */
  async function loadUserData(chapterName) {
    if (!authStore.isAuthenticated) {
      return
    }

    isLoading.value = true
    try {
      await Promise.all([
        loadChapterStatus(),
        loadUserSettings(),
      ])

      if (chapterName) {
        await loadWordProgress(chapterName)
      }

      console.log('用户数据加载完成')
    }
    catch (error) {
      console.error('加载用户数据失败:', error)
    }
    finally {
      isLoading.value = false
    }
  }

  /**
   * 监听登录状态变化
   */
  function watchAuthState() {
    watch(
      () => authStore.isAuthenticated,
      (isAuth) => {
        if (isAuth) {
          // 登录后加载数据
          loadUserData(currentChapter.value)
        }
      },
      { immediate: true },
    )
  }

  /**
   * 监听章节变化
   */
  function watchChapterChange() {
    watch(currentChapter, (newChapter) => {
      if (newChapter && authStore.isAuthenticated) {
        loadWordProgress(newChapter)
      }
    })
  }

  onMounted(() => {
    watchAuthState()
    if (currentChapter) {
      watchChapterChange()
    }
  })

  return {
    isLoading,
    loadUserData,
  }
}
