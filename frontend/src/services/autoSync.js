import { syncChapterStatus, syncUserSettings } from './sync'

/**
 * 自动同步服务
 * 在数据变化时触发同步,而不是定时同步
 * 这样可以避免不必要的网络请求和数据覆盖
 */

const CHANGELISTEN_EVENT = 'sync-needed' // 自定义事件名称

/**
 * 初始化自动同步
 */
export function initAutoSync() {
  // 监听自定义事件,当数据变化时触发同步
  window.addEventListener(CHANGELISTEN_EVENT, handleSyncNeeded)
}

/**
 * 停止自动同步
 */
export function stopAutoSync() {
  window.removeEventListener(CHANGELISTEN_EVENT, handleSyncNeeded)
}

/**
 * 设置当前章节(用于自动同步)
 */
export function setCurrentChapter(_chapterName) {
  // 单词进度改为在 Enter/Tab 切换单词时按单词同步。
  // 保留这个入口，避免旧调用方报错。
}

/**
 * 触发同步事件(当数据变化时调用)
 */
export function triggerSync() {
  window.dispatchEvent(new Event(CHANGELISTEN_EVENT))
}

/**
 * 处理同步请求
 */
async function handleSyncNeeded() {
  // 检查是否已登录
  const token = localStorage.getItem('access_token')
  if (!token) {
    return
  }

  try {
    // 同步章节状态
    await syncChapterStatus()

    // 同步用户设置
    await syncUserSettings()
  }
  catch (error) {
    console.error('自动同步失败:', error)
  }
}

/**
 * 节流同步函数
 * 避免短时间内多次触发同步
 */
let syncThrottleTimer = null
export function throttledSync(delay = 1000) {
  if (syncThrottleTimer) {
    return
  }

  syncThrottleTimer = setTimeout(async () => {
    await handleSyncNeeded()
    syncThrottleTimer = null
  }, delay)
}
