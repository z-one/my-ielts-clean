import { chaptersAPI, wordsAPI, settingsAPI, examsAPI } from '../api'
import { loadBackendVocabulary } from './vocabulary'

// 本地存储键名
const PROGRESS_KEY = 'vocabulary_progress'
const CHAPTER_STATUS_KEY = 'vocabulary_chapter_status'
const WORDS_PER_PAGE_KEY = 'vocabulary_words_per_page'
const EXAM_RECORDS_KEY = 'exam_records'

/**
 * 数据同步服务
 * 负责将 localStorage 数据同步到后端数据库
 */

// 检查是否已登录
function isAuthenticated() {
  return !!localStorage.getItem('access_token')
}

/**
 * 同步章节状态到后端
 */
export async function syncChapterStatus() {
  if (!isAuthenticated()) {
    console.log('未登录，跳过章节状态同步')
    return
  }

  const savedStatus = localStorage.getItem(CHAPTER_STATUS_KEY)
  if (!savedStatus) {
    console.log('没有本地章节状态数据')
    return
  }

  try {
    const chapterStatus = JSON.parse(savedStatus)
    const chapters = Object.keys(chapterStatus).map(chapterName => ({
      chapter_name: chapterName,
      status: chapterStatus[chapterName],
    }))

    if (chapters.length > 0) {
      await chaptersAPI.batchUpdate(chapters)
      console.log(`成功同步 ${chapters.length} 个章节状态`)
    }
  }
  catch (error) {
    console.error('同步章节状态失败:', error)
  }
}

/**
 * 从后端加载章节状态
 */
export async function loadChapterStatus() {
  if (!isAuthenticated()) {
    console.log('未登录，跳过加载章节状态')
    return
  }

  try {
    const progressList = await chaptersAPI.getAllProgress()
    const chapterStatus = {}

    for (const progress of progressList) {
      chapterStatus[progress.chapter_name] = progress.status
    }

    localStorage.setItem(CHAPTER_STATUS_KEY, JSON.stringify(chapterStatus))
    console.log(`成功加载 ${Object.keys(chapterStatus).length} 个章节状态`)

    return chapterStatus
  }
  catch (error) {
    console.error('加载章节状态失败:', error)
    return null
  }
}

/**
 * 驼峰转下划线命名
 */
function camelToSnake(str) {
  return str.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`)
}

/**
 * 将前端数据格式转换为后端数据库格式
 */
function transformWordData(wordData) {
  const transformed = {}
  for (const [key, value] of Object.entries(wordData)) {
    if (key === 'focusLevel' || key === 'focus_level')
      continue
    const dbKey = camelToSnake(key)
    transformed[dbKey] = value
  }
  return transformed
}

/**
 * 同步单词进度到后端
 * @param {string} chapterName - 章节名称
 * @param {Object} progressData - 可选的进度数据对象，如果不提供则从 vocabulary 收集
 */
export async function syncWordProgress(chapterName, progressData = null) {
  if (!isAuthenticated()) {
    console.log('未登录，跳过单词进度同步')
    return
  }

  try {
    const syncData = {
      chapter: chapterName,
      words: {},
    }

    // 如果没有提供进度数据，从统一词库服务中收集。
    if (!progressData) {
      const { vocabulary } = await loadBackendVocabulary({ includeProgress: true })
      const chapterData = vocabulary[chapterName]
      if (!chapterData || !chapterData.words) {
        console.log(`章节 "${chapterName}" 不存在或没有单词`)
        return
      }

      // 遍历所有单词，收集进度数据
      for (const group of chapterData.words) {
        for (const item of group) {
          const wordData = {
            spell_value: item.spellValue || '',
            spell_error: item.spellError || false,
            correct_count: item.correctCount || 0,
            error_count: item.errorCount || 0,
            show_source: item.showSource || false,
          }

          // 如果 spell_value 为空，使用单词原词
          if (!wordData.spell_value && item.word && item.word.length > 0) {
            wordData.spell_value = item.word[0]
          }

          syncData.words[item.id] = wordData
        }
      }
    }
    else {
      const fallbackResult = await loadBackendVocabulary({ includeProgress: false })
      const chapterData = fallbackResult.vocabulary[chapterName]
      // 使用提供的进度数据
      for (const [wordId, wordData] of Object.entries(progressData.words)) {
        const transformed = transformWordData(wordData)

        // 如果 spell_value 为空，从 vocabulary 中查找单词原词
        if (!transformed.spell_value || transformed.spell_value === '') {
          if (chapterData && chapterData.words) {
            for (const group of chapterData.words) {
              for (const item of group) {
                if (String(item.id) === String(wordId) && item.word && item.word.length > 0) {
                  transformed.spell_value = item.word[0]
                  break
                }
              }
            }
          }
        }

        syncData.words[wordId] = transformed
      }
    }

    console.log('同步到后端的数据:', JSON.stringify(syncData, null, 2))

    if (Object.keys(syncData.words).length > 0) {
      await wordsAPI.syncProgress(syncData)
      console.log(`成功同步章节 "${chapterName}" 的 ${Object.keys(syncData.words).length} 个单词进度`)
    }
  }
  catch (error) {
    console.error('同步单词进度失败:', error)
    throw error
  }
}

export async function updateWordFocusLevel(wordId, chapterName, focusLevel) {
  if (!isAuthenticated()) {
    console.log('未登录，跳过单词重点等级同步')
    return
  }

  return wordsAPI.updateProgress(wordId, {
    chapter_name: chapterName,
    focus_level: focusLevel,
  })
}

/**
 * 从后端加载单词进度
 */
export async function loadWordProgress(chapterName) {
  if (!isAuthenticated()) {
    console.log('未登录，跳过加载单词进度')
    return
  }

  try {
    const progressList = await wordsAPI.getChapterProgress(chapterName)

    if (progressList.length === 0) {
      console.log(`章节 "${chapterName}" 没有单词进度数据`)
      return null
    }

    console.log('从后端加载的进度数据:', progressList)

    // 转换为本地存储格式
    const progress = {
      chapter: chapterName,
      words: {},
    }

    for (const item of progressList) {
      progress.words[item.word_id] = {
        spellValue: item.spell_value || '',
        spellError: item.spell_error || false,
        correctCount: item.correct_count || 0,
        errorCount: item.error_count || 0,
        showSource: item.show_source || false,
        focusLevel: item.focus_level || 0,
      }
    }

    console.log(`成功加载章节 "${chapterName}" 的 ${Object.keys(progress.words).length} 个单词进度`)

    return progress
  }
  catch (error) {
    console.error('加载单词进度失败:', error)
    return null
  }
}

/**
 * 同步用户设置到后端
 */
export async function syncUserSettings() {
  if (!isAuthenticated()) {
    console.log('未登录，跳过用户设置同步')
    return
  }

  try {
    const wordsPerPage = localStorage.getItem(WORDS_PER_PAGE_KEY)
    if (!wordsPerPage) {
      console.log('没有本地用户设置数据')
      return
    }

    await settingsAPI.update({
      words_per_page: parseInt(wordsPerPage, 10) || 5,
    })
    console.log('成功同步用户设置')
  }
  catch (error) {
    console.error('同步用户设置失败:', error)
  }
}

/**
 * 从后端加载用户设置
 */
export async function loadUserSettings() {
  if (!isAuthenticated()) {
    console.log('未登录，跳过加载用户设置')
    return
  }

  try {
    const settings = await settingsAPI.get()

    if (settings) {
      if (settings.words_per_page) {
        localStorage.setItem(WORDS_PER_PAGE_KEY, settings.words_per_page.toString())
      }
      console.log('成功加载用户设置')
      return settings
    }
  }
  catch (error) {
    console.error('加载用户设置失败:', error)
    return null
  }
}

/**
 * 更新章节状态（本地 + 后端）
 */
export async function updateChapterStatus(chapterName, status) {
  // 先更新本地存储
  const savedStatus = localStorage.getItem(CHAPTER_STATUS_KEY) || '{}'
  const chapterStatus = JSON.parse(savedStatus)
  chapterStatus[chapterName] = status
  localStorage.setItem(CHAPTER_STATUS_KEY, JSON.stringify(chapterStatus))

  // 然后同步到后端
  if (isAuthenticated()) {
    try {
      await chaptersAPI.updateStatus(chapterName, status)
    }
    catch (error) {
      console.error('更新章节状态失败:', error)
    }
  }
}

/**
 * 初始化同步：登录后加载所有后端数据
 */
export async function initializeSync() {
  if (!isAuthenticated()) {
    console.log('未登录，跳过初始化同步')
    return
  }

  console.log('开始初始化数据同步...')

  // 并行加载所有数据
  await Promise.all([
    loadChapterStatus(),
    loadUserSettings(),
  ])

  console.log('初始化同步完成')
}

/**
 * 保存考试记录
 */
export function saveExamRecord(examData) {
  // 保存到本地存储
  const records = JSON.parse(localStorage.getItem(EXAM_RECORDS_KEY) || '[]')
  const newRecord = {
    id: Date.now(),
    timestamp: new Date().toISOString(),
    ...examData,
  }
  records.unshift(newRecord)
  localStorage.setItem(EXAM_RECORDS_KEY, JSON.stringify(records))
  console.log('考试记录已保存到本地')

  // 同步到后端
  if (isAuthenticated()) {
    syncExamRecord(newRecord).catch(error => {
      console.error('同步考试记录到后端失败:', error)
    })
  }

  return newRecord
}

/**
 * 同步考试记录到后端
 */
async function syncExamRecord(examData) {
  if (!isAuthenticated()) {
    console.log('未登录，跳过考试记录同步')
    return
  }

  try {
    await examsAPI.save(examData)
    console.log('考试记录已同步到后端')
  }
  catch (error) {
    console.error('同步考试记录失败:', error)
    throw error
  }
}

/**
 * 获取所有考试记录
 */
export function getExamRecords() {
  const records = JSON.parse(localStorage.getItem(EXAM_RECORDS_KEY) || '[]')
  return records
}

/**
 * 从后端加载考试记录
 */
export async function loadExamRecords() {
  if (!isAuthenticated()) {
    console.log('未登录，跳过加载考试记录')
    return null
  }

  try {
    const records = await examsAPI.getAll()
    localStorage.setItem(EXAM_RECORDS_KEY, JSON.stringify(records))
    console.log(`成功加载 ${records.length} 条考试记录`)
    return records
  }
  catch (error) {
    console.error('加载考试记录失败:', error)
    return null
  }
}

/**
 * 退出登录前的数据清理
 */
export function cleanupOnLogout() {
  // 退出登录时不清除本地进度数据，方便下次登录恢复
  // 只清除认证相关的数据
  localStorage.removeItem('access_token')
  localStorage.removeItem('user')
  console.log('退出登录清理完成')
}
