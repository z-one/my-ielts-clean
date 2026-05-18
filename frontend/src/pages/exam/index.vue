<template>
  <div class="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
    <div class="mb-6 rounded-lg bg-white p-6 shadow dark:bg-gray-800">
      <div class="mb-6 flex flex-col items-center justify-between gap-4 sm:flex-row">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
            🎯 考试抽检模式
          </h1>
          <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">
            针对重点及关注单词的跨类别随机大抽检
          </p>
        </div>
        <div class="flex gap-3">
          <button
            type="button"
            class="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-300 dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800"
            @click="startExam"
          >
            🔄 重新抽检 (100词)
          </button>
          <button
            v-if="!examStarted"
            type="button"
            class="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 focus:outline-none focus:ring-4 focus:ring-green-300 dark:bg-green-600 dark:hover:bg-green-700 dark:focus:ring-green-800"
            @click="startExam"
          >
            开始考试
          </button>
          <button
            v-else
            type="button"
            class="rounded-lg bg-orange-600 px-4 py-2 text-sm font-medium text-white hover:bg-orange-700 focus:outline-none focus:ring-4 focus:ring-orange-300 dark:bg-orange-600 dark:hover:bg-orange-700 dark:focus:ring-orange-800"
            @click="finishExam"
          >
            提交考试
          </button>
        </div>
      </div>

      <!-- 考试统计信息 -->
      <div v-if="examStarted" class="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div class="rounded-lg bg-blue-50 p-4 text-center dark:bg-blue-900/20">
          <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">
            {{ examStats.total }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-400">总题数</div>
        </div>
        <div class="rounded-lg bg-green-50 p-4 text-center dark:bg-green-900/20">
          <div class="text-2xl font-bold text-green-600 dark:text-green-400">
            {{ examStats.correct }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-400">正确</div>
        </div>
        <div class="rounded-lg bg-red-50 p-4 text-center dark:bg-red-900/20">
          <div class="text-2xl font-bold text-red-600 dark:text-red-400">
            {{ examStats.wrong }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-400">错误</div>
        </div>
        <div class="rounded-lg bg-gray-50 p-4 text-center dark:bg-gray-700">
          <div class="text-2xl font-bold text-gray-600 dark:text-gray-400">
            {{ examStats.remaining }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-400">剩余</div>
        </div>
      </div>

      <!-- 单词分布统计 -->
      <div v-if="examWords.length > 0" class="mb-4 rounded-lg bg-gray-50 p-4 dark:bg-gray-700">
        <div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
          单词分布 (共{{ Object.keys(chapterLearnStatus).filter(ch => chapterLearnStatus[ch] !== 'not_learned').length }}个已学习章节):
        </div>
        <div class="flex flex-wrap gap-2">
          <span v-for="count in wordDistribution" :key="count.chapter" class="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-sm text-blue-800 dark:bg-blue-900 dark:text-blue-300">
            {{ count.chapter }}: {{ count.count }}个
          </span>
        </div>
      </div>
    </div>

    <!-- 考试结果弹窗 -->
    <div v-if="showResult" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div class="mx-4 max-w-md rounded-lg bg-white p-6 shadow dark:bg-gray-800">
        <h2 class="mb-4 text-xl font-bold text-gray-900 dark:text-white">
          🎉 考试完成
        </h2>
        <div class="mb-4 space-y-3">
          <div class="flex justify-between">
            <span class="text-gray-600 dark:text-gray-400">总题数:</span>
            <span class="font-semibold text-gray-900 dark:text-white">{{ resultStats.total }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-600 dark:text-gray-400">正确:</span>
            <span class="font-semibold text-green-600 dark:text-green-400">{{ resultStats.correct }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-600 dark:text-gray-400">错误:</span>
            <span class="font-semibold text-red-600 dark:text-red-400">{{ resultStats.wrong }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-600 dark:text-gray-400">正确率:</span>
            <span class="font-semibold text-blue-600 dark:text-blue-400">{{ resultStats.accuracy }}%</span>
          </div>
        </div>
        <div class="flex gap-3">
          <button
            type="button"
            class="flex-1 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-300 dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800"
            @click="startExam"
          >
            重新考试
          </button>
          <button
            type="button"
            class="flex-1 rounded-lg bg-gray-600 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700 focus:outline-none focus:ring-4 focus:ring-gray-300 dark:bg-gray-600 dark:hover:bg-gray-700 dark:focus:ring-gray-800"
            @click="showResult = false"
          >
            关闭
          </button>
        </div>
      </div>
    </div>

    <!-- 考试题单 -->
    <div v-if="examWords.length > 0" class="space-y-4">
      <div
        v-for="(word, index) in examWords"
        :key="word.id"
        class="rounded-lg bg-white p-6 shadow dark:bg-gray-800"
      >
        <!-- 单词信息头部 -->
        <div class="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div class="flex items-center gap-3">
            <span class="text-lg font-semibold text-gray-700 dark:text-gray-300">
              {{ index + 1 }}.
            </span>
            <span
              v-if="word.focusLevel === 2"
              class="inline-flex items-center rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-medium text-red-800 dark:bg-red-900 dark:text-red-300"
            >
              ⭐ 重点
            </span>
            <span
              v-else-if="word.focusLevel === 1"
              class="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800 dark:bg-blue-900 dark:text-blue-300"
            >
              👁️ 关注
            </span>
            <span class="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-800 dark:bg-gray-700 dark:text-gray-300">
              {{ word.chapterName }}
            </span>
          </div>
          <div class="flex items-center gap-2">
            <button
              type="button"
              class="rounded-lg bg-purple-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-300 dark:bg-purple-600 dark:hover:bg-purple-700 dark:focus:ring-purple-800"
              @click="playAudio(word)"
            >
              🔊 播放
            </button>
          </div>
        </div>

        <!-- 单词释义 -->
        <div class="mb-4">
          <p class="mt-1 text-base text-gray-600 dark:text-gray-400">
            <span class="font-medium text-gray-700 dark:text-gray-300">{{ word.pos }}</span> {{ word.meaning }}
          </p>
          <p v-if="word.example" class="mt-2 text-sm text-gray-500 dark:text-gray-500 italic">
            "{{ word.example }}"
          </p>
        </div>

        <!-- 输入框 -->
        <div class="mb-4">
          <input
            :id="word.id"
            type="text"
            :class="[
              'w-full rounded-lg border px-4 py-3 text-gray-900 dark:text-white',
              word.answered
                ? word.isCorrect
                  ? 'border-green-500 bg-green-50 focus:ring-green-300 dark:bg-green-900/20 dark:focus:ring-green-800'
                  : 'border-red-500 bg-red-50 focus:ring-red-300 dark:bg-red-900/20 dark:focus:ring-red-800'
                : 'border-gray-300 bg-gray-50 focus:border-blue-500 focus:ring-blue-300 dark:border-gray-600 dark:bg-gray-700 dark:focus:border-blue-500 dark:focus:ring-blue-800',
            ]"
            placeholder="请输入单词拼写"
            :disabled="word.answered || examFinished"
            @keydown="handleInputKeydown($event, word)"
          >
        </div>

        <!-- 答题结果提示 -->
        <div v-if="word.answered" class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span v-if="word.isCorrect" class="text-green-600 dark:text-green-400">
              ✓ 正确!
            </span>
            <span v-else class="text-red-600 dark:text-red-400">
              ✗ 错误! 正确答案: {{ word.word.join(', ') }}
            </span>
          </div>
          <span class="text-sm text-gray-500 dark:text-gray-400">
            已答对{{ word.correctCount || 0 }}次 / 答错{{ word.errorCount || 0 }}次
          </span>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="rounded-lg bg-white p-12 text-center shadow dark:bg-gray-800">
      <div class="text-6xl">
        📝
      </div>
      <h3 class="mt-4 text-xl font-semibold text-gray-900 dark:text-white">
        还没有开始考试
      </h3>
      <p class="mt-2 text-gray-600 dark:text-gray-400">
        点击"开始考试"按钮开始随机抽检
      </p>
      <button
        type="button"
        class="mt-6 rounded-lg bg-blue-600 px-6 py-3 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-300 dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800"
        @click="startExam"
      >
        开始考试
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '~/stores/auth'
import { saveExamRecord } from '../../services/sync'
import { CUSTOM_CHAPTER_NAME, loadBackendVocabulary } from '../../services/vocabulary'

const authStore = useAuthStore()

const CHAPTER_KEY = 'vocabulary_chapter'
const CHAPTER_STATUS_KEY = 'vocabulary_chapter_status' // 章节学习状态

// 章节学习状态枚举
const ChapterStatus = {
  NOT_LEARNED: 'not_learned', // 未学习
  LEARNED: 'learned', // 已学习
  COMPLETED: 'completed', // 已完成
  MASTERED: 'mastered', // 已熟练
}

const EXAM_WORDS_COUNT = 100 // 每次抽检100个单词
const chapterLearnStatus = ref({}) // 章节学习状态映射
const vocabularyData = shallowReactive({})

// 考试状态
const examStarted = ref(false)
const examFinished = ref(false)
const showResult = ref(false)
const examWords = ref([])
const examStats = ref({
  total: 0,
  correct: 0,
  wrong: 0,
  remaining: 0,
})
const resultStats = ref({
  total: 0,
  correct: 0,
  wrong: 0,
  accuracy: 0,
})

let audio = null

function replaceVocabulary(nextVocabulary) {
  for (const key of Object.keys(vocabularyData))
    delete vocabularyData[key]
  Object.assign(vocabularyData, nextVocabulary)
}

async function loadExamVocabulary() {
  const result = await loadBackendVocabulary({ includeProgress: authStore.isAuthenticated })
  replaceVocabulary(result.vocabulary)
  if (authStore.isAuthenticated) {
    chapterLearnStatus.value = result.chapterStatus || {}
    localStorage.setItem(CHAPTER_STATUS_KEY, JSON.stringify(chapterLearnStatus.value))
  }
}

// 单词分布统计
const wordDistribution = computed(() => {
  const distribution = {}
  examWords.value.forEach((word) => {
    if (!distribution[word.chapterName]) {
      distribution[word.chapterName] = 0
    }
    distribution[word.chapterName]++
  })
  return Object.entries(distribution)
    .map(([chapter, count]) => ({ chapter, count }))
    .sort((a, b) => b.count - a.count)
})

// 从所有章节收集重点和关注单词
function collectFocusWords() {
  const focusWords = []

  // 遍历所有章节
  for (const [chapterName, chapterData] of Object.entries(vocabularyData)) {
    if (chapterName === CUSTOM_CHAPTER_NAME)
      continue

    // 只收集已学习、已完成或已熟练章节的单词
    const status = chapterLearnStatus.value[chapterName]
    if (!status || status === ChapterStatus.NOT_LEARNED) {
      continue // 跳过未学习的章节
    }

    if (chapterData.words) {
      for (const group of chapterData.words) {
        for (const item of group) {
          // 只收集关注等级为1或2的单词
          if (item.focusLevel === 1 || item.focusLevel === 2) {
            focusWords.push({
              id: item.id,
              chapterName,
              audio: chapterData.audio,
              word: item.word,
              pos: item.pos,
              meaning: item.meaning,
              example: item.example,
              focusLevel: item.focusLevel || 0,
              correctCount: item.correctCount || 0,
              errorCount: item.errorCount || 0,
              answered: false,
              isCorrect: false,
            })
          }
        }
      }
    }
  }

  return focusWords
}

// Fisher-Yates 洗牌算法
function shuffleArray(array) {
  const shuffled = [...array]
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
  }
  return shuffled
}

// 加载章节学习状态
function loadChapterStatus() {
  const saved = localStorage.getItem(CHAPTER_STATUS_KEY)
  if (saved) {
    try {
      chapterLearnStatus.value = JSON.parse(saved)
    }
    catch (error) {
      console.error('加载章节状态失败:', error)
    }
  }
}

// 开始考试
function startExam() {
  // 先加载章节学习状态
  loadChapterStatus()

  examStarted.value = true
  examFinished.value = false
  showResult.value = false

  // 收集所有重点和关注单词(仅从已学习章节)
  const focusWords = collectFocusWords()

  if (focusWords.length === 0) {
    // 统计各章节状态,给用户友好提示
    const totalChapters = Object.keys(vocabularyData).filter(k => k !== CUSTOM_CHAPTER_NAME).length
    const learnedChapters = Object.keys(chapterLearnStatus.value).filter(
      chapter => chapterLearnStatus.value[chapter] !== ChapterStatus.NOT_LEARNED
    ).length

    if (learnedChapters === 0) {
      alert('您还没有学习任何章节,请先学习一些章节后再进行考试!')
    }
    else {
      alert(`已学习章节中没有找到重点或关注单词!请在已学习的章节中设置单词的关注等级。\n\n已学习章节: ${learnedChapters}/${totalChapters}`)
    }
    examStarted.value = false
    return
  }

  // 随机打乱
  const shuffled = shuffleArray(focusWords)

  // 如果单词数量超过100,取前100个
  examWords.value = shuffled.slice(0, EXAM_WORDS_COUNT)

  // 重置统计
  examStats.value = {
    total: examWords.value.length,
    correct: 0,
    wrong: 0,
    remaining: examWords.value.length,
  }

  // 滚动到顶部
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// 处理输入
function handleInputKeydown(event, word) {
  if (event.key === 'Enter') {
    event.preventDefault()
    validateAnswer(word)
  }
}

// 验证答案
function validateAnswer(word) {
  const input = document.getElementById(word.id)
  const spellValue = input.value.toLowerCase().trim()

  if (spellValue.length === 0) {
    return
  }

  const isCorrect = word.word.some(w => w.toLowerCase().trim() === spellValue)

  word.answered = true
  word.isCorrect = isCorrect

  if (isCorrect) {
    word.correctCount = (word.correctCount || 0) + 1
    examStats.value.correct++
  }
  else {
    word.errorCount = (word.errorCount || 0) + 1
    examStats.value.wrong++
  }

  examStats.value.remaining--

  // 禁用输入框
  input.disabled = true
}

// 播放音频
function playAudio(word) {
  if (audio) {
    audio.pause()
    audio.currentTime = 0
  }

  try {
    // 构建音频路径: vocabulary/audio/章节名/单词.mp3
    const audioPath = `/vocabulary/audio/${word.chapterName}/${word.word[0]}.mp3`
    audio = new Audio(audioPath)
    audio.play().catch((error) => {
      console.error('音频播放失败:', error)
      console.log('尝试的音频路径:', audioPath)
    })
  }
  catch (error) {
    console.error('音频创建失败:', error)
  }
}

// 完成考试
function finishExam() {
  const remaining = examWords.value.filter(w => !w.answered).length

  if (remaining > 0) {
    const confirmResult = confirm(`还有 ${remaining} 个题目未完成,确定要提交考试吗?`)
    if (!confirmResult) {
      return
    }
  }

  examFinished.value = true
  showResult.value = true

  resultStats.value = {
    total: examStats.value.total,
    correct: examStats.value.correct,
    wrong: examStats.value.wrong,
    accuracy: examStats.value.total > 0
      ? Math.round((examStats.value.correct / examStats.value.total) * 100)
      : 0,
  }

  // 保存考试记录
  const examRecord = {
    total: examStats.value.total,
    correct: examStats.value.correct,
    wrong: examStats.value.wrong,
    accuracy: resultStats.value.accuracy,
    words: examWords.value.map(word => ({
      wordId: word.id,
      chapterName: word.chapterName,
      word: word.word.join(', '),
      isCorrect: word.isCorrect,
      correctCount: word.correctCount,
      errorCount: word.errorCount,
      focusLevel: word.focusLevel,
    })),
  }

  try {
    saveExamRecord(examRecord)
    console.log('考试记录已保存')
  }
  catch (error) {
    console.error('保存考试记录失败:', error)
  }
}

onMounted(async () => {
  await loadExamVocabulary()
  if (!authStore.isAuthenticated)
    loadChapterStatus()
  // 自动开始考试
  startExam()
})
</script>
