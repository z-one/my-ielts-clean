import { chaptersAPI, vocabularyAPI, wordsAPI } from '../api'
import fallbackVocabulary from '../pages/vocabulary/vocabulary'

const CHAPTER_CACHE_KEY = 'vocabulary_chapter_details_cache_v1'
const CHAPTER_CACHE_VERSION = 1
const CHAPTER_CACHE_TTL = 7 * 24 * 60 * 60 * 1000

const CUSTOM_CHAPTER_NAME = '23 - 自添加生词'

export function normalizeBackendWord(item) {
  return {
    id: item.id,
    spellError: false,
    spellValue: '',
    showSource: false,
    correctCount: 0,
    errorCount: 0,
    focusLevel: 0,
    word: Array.isArray(item.word) && item.word.length ? item.word : [item.word],
    pos: item.pos || '',
    meaning: item.meaning || '',
    example: item.example || '',
    extra: item.extra || '',
    label: item.group_name || '',
    chapterName: item.chapter_name,
    source: item.source,
    metadata: item.metadata || '',
  }
}

export function buildVocabularyFromBackend(words, chapterDetails = []) {
  const detailMap = new Map(chapterDetails.map(item => [item.chapter_name, item]))
  const vocabulary = {}
  const groupIndexes = new Map()

  for (const rawWord of words) {
    const word = normalizeBackendWord(rawWord)
    const chapterName = word.chapterName
    const detail = detailMap.get(chapterName)

    if (!vocabulary[chapterName]) {
      vocabulary[chapterName] = {
        label: detail?.label || chapterName,
        audio: detail?.audio || '',
        groupCount: 0,
        wordCount: 0,
        words: [],
      }
      groupIndexes.set(chapterName, new Map())
    }

    const groupName = rawWord.group_name || `${chapterName} 默认组`
    const chapterGroups = groupIndexes.get(chapterName)
    let groupIndex = chapterGroups.get(groupName)

    if (groupIndex === undefined) {
      groupIndex = vocabulary[chapterName].words.length
      chapterGroups.set(groupName, groupIndex)
      const group = []
      group.label = groupName
      vocabulary[chapterName].words.push(group)
    }

    vocabulary[chapterName].words[groupIndex].push(word)
    vocabulary[chapterName].wordCount += 1
  }

  for (const chapter of Object.values(vocabulary))
    chapter.groupCount = chapter.words.length

  return vocabulary
}

function isAuthenticated() {
  return !!localStorage.getItem('access_token')
}

function readChapterCache() {
  try {
    const rawCache = localStorage.getItem(CHAPTER_CACHE_KEY)
    if (!rawCache)
      return null

    const cache = JSON.parse(rawCache)
    if (
      cache.version !== CHAPTER_CACHE_VERSION
      || !Array.isArray(cache.data)
      || Date.now() - cache.savedAt > CHAPTER_CACHE_TTL
    ) {
      localStorage.removeItem(CHAPTER_CACHE_KEY)
      return null
    }

    return cache.data
  }
  catch (error) {
    console.warn('读取章节缓存失败，已忽略缓存:', error)
    localStorage.removeItem(CHAPTER_CACHE_KEY)
    return null
  }
}

function writeChapterCache(data) {
  try {
    localStorage.setItem(CHAPTER_CACHE_KEY, JSON.stringify({
      version: CHAPTER_CACHE_VERSION,
      savedAt: Date.now(),
      data,
    }))
  }
  catch (error) {
    console.warn('写入章节缓存失败，已忽略:', error)
  }
}

export function clearVocabularyChapterCache() {
  localStorage.removeItem(CHAPTER_CACHE_KEY)
}

async function loadChapterDetailsWithCache() {
  const cached = readChapterCache()
  if (cached)
    return cached

  const chapterDetails = await vocabularyAPI.getChapterDetails()
  writeChapterCache(chapterDetails)
  return chapterDetails
}

function normalizeWordProgress(progress) {
  return {
    spellValue: progress.spell_value || '',
    spellError: progress.spell_error || false,
    correctCount: progress.correct_count || 0,
    errorCount: progress.error_count || 0,
    showSource: progress.show_source || false,
    focusLevel: progress.focus_level ?? 0,
  }
}

export function applyVocabularyProgress(vocabulary, wordProgressList = []) {
  const progressMap = new Map(wordProgressList.map(progress => [progress.word_id, normalizeWordProgress(progress)]))

  for (const chapter of Object.values(vocabulary)) {
    for (const group of chapter.words || []) {
      for (const word of group) {
        const progress = progressMap.get(word.id)
        if (progress)
          Object.assign(word, progress)
      }
    }
  }

  return vocabulary
}

export function buildChapterStatusMap(progressList = []) {
  return progressList.reduce((result, item) => {
    result[item.chapter_name] = item.status
    return result
  }, {})
}

export async function loadBackendVocabulary({ includeProgress = isAuthenticated() } = {}) {
  try {
    const baseRequests = [
      loadChapterDetailsWithCache(),
      vocabularyAPI.getWords(),
    ]

    if (includeProgress) {
      baseRequests.push(chaptersAPI.getAllProgress())
      baseRequests.push(wordsAPI.getAllProgress())
    }

    const [chapterDetails, words, chapterProgress = [], wordProgress = []] = await Promise.all(baseRequests)
    const vocabulary = applyVocabularyProgress(buildVocabularyFromBackend(words, chapterDetails), wordProgress)
    const chapterStatus = buildChapterStatusMap(chapterProgress)

    for (const detail of chapterDetails) {
      if (vocabulary[detail.chapter_name])
        vocabulary[detail.chapter_name].status = chapterStatus[detail.chapter_name]
    }

    return {
      vocabulary,
      chapterStatus,
      fromFallback: false,
    }
  }
  catch (error) {
    console.error('加载后端词库失败，使用静态词库兜底:', error)
    return {
      vocabulary: structuredClone(fallbackVocabulary),
      chapterStatus: {},
      fromFallback: true,
    }
  }
}

export async function searchBackendVocabulary(query) {
  const words = await vocabularyAPI.search(query)
  return words.map(normalizeBackendWord)
}

export async function createBackendCustomWords({ words, pos, meaning, example }) {
  const created = []
  const existing = []
  const groupName = `自定义组 ${new Date().toISOString().slice(0, 10)}`

  for (const word of words) {
    const result = await vocabularyAPI.createCustomWord({
      chapter_name: CUSTOM_CHAPTER_NAME,
      group_name: groupName,
      word: [word],
      word_variants: [word],
      pos,
      meaning,
      example: example || '',
      extra: '',
      metadata: JSON.stringify({ source: 'frontend-custom-word' }),
    })
    const normalized = normalizeBackendWord(result.word || result)
    if (result.already_exists)
      existing.push(normalized)
    else
      created.push(normalized)
  }

  return { created, existing }
}

export { CUSTOM_CHAPTER_NAME }
