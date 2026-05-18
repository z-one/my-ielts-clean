<!-- eslint-disable eslint-comments/no-unlimited-disable -->
<script setup>
import { syncWordProgress } from '../../services/sync'
import { loadBackendVocabulary } from '../../services/vocabulary'
import { useAuthStore } from '~/stores/auth'

const authStore = useAuthStore()

const isTrainingModel = ref(false)
const isShowMeaning = ref(false)
const isShowSource = ref(false)
const isAutoPlayWordAudio = ref(false)
const isHideMastered = ref(false)
const isOnlyErrorProne = ref(false)
const currentPage = ref(1)
const wordsPerPage = ref(Math.max(1, Number.parseInt(localStorage.getItem('important_words_per_page') || '10', 10)))
const wordShowSourceMap = reactive(new Map())
const wordHasInputMap = reactive(new Map())

const trainingStats = ref('')
const loaded = ref(false)
const refVocabulary = shallowReactive({})
let audio = null

function replaceVocabulary(nextVocabulary) {
  for (const key of Object.keys(refVocabulary))
    delete refVocabulary[key]
  Object.assign(refVocabulary, nextVocabulary)
}

async function loadVocabularyData() {
  const result = await loadBackendVocabulary({ includeProgress: authStore.isAuthenticated })
  if (Object.keys(result.vocabulary).length > 0)
    replaceVocabulary(result.vocabulary)
}

// 从后端获取所有重点单词（focusLevel === 2）
const allImportantWords = ref([])

// 加载重点单词数据
async function loadImportantWords() {
  loaded.value = false
  const importantWords = []
  const chapters = Object.keys(refVocabulary)

  for (const chapter of chapters) {
    const words = refVocabulary[chapter]?.words || []
    for (const group of words) {
      for (const item of group) {
        if (item.focusLevel === 2) {
          importantWords.push(item)
          // 保存章节信息到原始对象中
          item.chapterName = chapter
        }
      }
    }
  }

  // 打乱顺序
  for (let i = importantWords.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[importantWords[i], importantWords[j]] = [importantWords[j], importantWords[i]]
  }

  allImportantWords.value = importantWords
  loaded.value = true
  console.log('加载了', importantWords.length, '个重点单词')
}

function isErrorProneWord(item) {
  const correctCount = item.correctCount || 0
  const errorCount = item.errorCount || 0
  return errorCount > 0 && errorCount >= correctCount
}

const filteredImportantWords = computed(() => {
  let words = [...allImportantWords.value]

  // 隐藏已掌握的单词（正确10次）
  if (isHideMastered.value) {
    words = words.filter(item => (item.correctCount || 0) < 10)
  }

  if (isOnlyErrorProne.value) {
    words = words.filter(isErrorProneWord)
  }

  return words
})

// 获取当前显示的重点单词
const currentWords = computed(() => {
  const words = filteredImportantWords.value

  // 分页
  const start = (currentPage.value - 1) * wordsPerPage.value
  const end = start + wordsPerPage.value
  return words.slice(start, end)
})

// 总页数
const totalPages = computed(() => {
  return Math.ceil(filteredImportantWords.value.length / wordsPerPage.value)
})

// 加载进度
async function loadProgress() {
  if (!authStore.isAuthenticated) {
    loaded.value = true
    return
  }

  try {
    for (const chapter of Object.values(refVocabulary)) {
      for (const group of chapter.words || []) {
        for (const item of group)
          wordShowSourceMap.set(item.id, item.showSource || false)
      }
    }
    // 加载完进度后，重新构建重点单词列表
    await loadImportantWords()
  }
  catch (error) {
    console.error('从后端加载进度失败:', error)
    await loadImportantWords()
  }
}

// 保存进度
async function saveProgress() {
  if (!authStore.isAuthenticated) {
    return
  }

  const chapters = Object.keys(refVocabulary)

  for (const chapter of chapters) {
    const words = refVocabulary[chapter]?.words || []
    const chapterProgress = {
      chapter,
      words: {},
    }

    for (const group of words) {
      for (const item of group) {
        chapterProgress.words[item.id] = {
          spellValue: item.spellValue || '',
          spellError: item.spellError || false,
          correctCount: item.correctCount || 0,
          errorCount: item.errorCount || 0,
          showSource: wordShowSourceMap.get(item.id) || false,
        }
      }
    }

    try {
      await syncWordProgress(chapter, chapterProgress)
    }
    catch (error) {
      console.error(`同步章节 "${chapter}" 的单词进度失败:`, error)
    }
  }
}

// 切换显示原词
function toggleShowSource(item) {
  const currentValue = wordShowSourceMap.get(item.id) || false
  wordShowSourceMap.set(item.id, !currentValue)
  item.showSource = !currentValue
  saveProgress()
}

// 是否显示原词
function shouldShowWordSource(item) {
  // 非练习模式：总是显示
  if (!isTrainingModel.value)
    return true
  // 练习模式：根据 Map 中的 showSource 或全局 isShowSource 判断
  return !!(wordShowSourceMap.get(item.id) || isShowSource.value)
}

// 获取输入框样式
function getInputStyleClass(item) {
  const hasInput = wordHasInputMap.get(item.id)
  if (!hasInput)
    return 'h-8 w-64 border border-gray-300 rounded px-2 text-sm text-gray-700 dark:text-gray-200'

  if (item.spellError)
    return 'h-8 w-64 border border-red-500 bg-red-50 rounded px-2 text-sm text-red-700 dark:bg-red-900 dark:text-red-200'

  return 'h-8 w-64 border border-green-500 bg-green-50 rounded px-2 text-sm text-green-700 dark:bg-green-900 dark:text-green-200'
}

// 输入框失去焦点
function onInputFocusOut(e, item) {
  const inputValue = e.target.value.trim()
  if (inputValue) {
    wordHasInputMap.set(item.id, true)
    checkSpell(item, e.target)
  }
  else {
    wordHasInputMap.delete(item.id)
    item.spellValue = ''
    item.spellError = false
  }
}

// 输入框获得焦点
function onInputFocusIn(e) {
  console.log('输入框获得焦点，自动播放:', isAutoPlayWordAudio.value)
  if (isAutoPlayWordAudio.value) {
    const wordId = e.target.id
    const word = currentWords.value.find(w => String(w.id) === String(wordId))
    console.log('查找的 ID:', wordId, '类型:', typeof wordId)
    console.log('找到单词:', word)
    if (word)
      playWordAudio(word)
  }
}

// 自动聚焦第一个输入框
function focusFirstInput() {
  setTimeout(() => {
    const firstInput = document.querySelector('input[type="text"]')
    if (firstInput) {
      firstInput.focus()
    }
  }, 100)
}

// 检查拼写
function checkSpell(item, inputEl) {
  const inputValue = inputEl.value.trim()
  const word = Array.isArray(item.word) ? item.word[0] : item.word
  const correctAnswer = word.toLowerCase()
  const isCorrect = inputValue.toLowerCase() === correctAnswer

  if (isCorrect) {
    item.spellError = false
    item.correctCount = (item.correctCount || 0) + 1
    item.spellValue = correctAnswer
  }
  else {
    item.spellError = true
    item.errorCount = (item.errorCount || 0) + 1
  }

  saveProgress()
}

// 播放单词音频
function playWordAudio(item) {
  const word = Array.isArray(item.word) ? item.word[0] : item.word
  const wordString = word || ''

  console.log('尝试播放单词:', wordString)

  // 优先使用语音合成
  if ('speechSynthesis' in window) {
    try {
      window.speechSynthesis.cancel()
      const utterance = new SpeechSynthesisUtterance(wordString)
      utterance.lang = 'en-US'
      utterance.rate = 0.8
      utterance.pitch = 1
      utterance.volume = 1

      utterance.onstart = () => {
        console.log('语音合成开始播放:', wordString)
      }
      utterance.onerror = (event) => {
        console.error('语音合成错误:', event)
      }
      utterance.onend = () => {
        console.log('语音合成播放完成:', wordString)
      }

      window.speechSynthesis.speak(utterance)
      console.log('语音合成已调用')
      return
    }
    catch (error) {
      console.error('语音合成失败:', error)
    }
  }
  else {
    console.log('浏览器不支持语音合成')
  }

  // 备用方案：尝试使用音频文件
  const wordData = currentWords.value.find(w => w.id === item.id)
  if (!wordData)
    return

  const chapterName = wordData.chapterName
  const audioPath = `vocabulary/audio/${chapterName}/${wordString}.mp3`

  console.log('尝试播放音频文件:', audioPath)

  if (audio) {
    audio.pause()
    audio.currentTime = 0
  }

  try {
    audio = new Audio()
    audio.src = audioPath
    audio.play().then(() => {
      console.log('音频文件播放成功')
    }).catch((error) => {
      console.log('音频文件播放失败:', error)
    })
  }
  catch (error) {
    console.log('音频播放错误:', error)
  }
}

// 复制文本
function copyText(item) {
  console.log('copyText 被调用 (important.vue):', item)
  const text = `${item.en}\n${item.pos}\n${item.meaning}\n${item.example}\n${item.extra || ''}`
  console.log('准备复制的内容:', text)

  if (navigator.clipboard && navigator.clipboard.writeText) {
    console.log('使用 Clipboard API')
    navigator.clipboard.writeText(text)
      .then(() => {
        console.log('复制成功 (Clipboard API)')
        alert('已复制到剪贴板')
      })
      .catch((error) => {
        console.error('复制失败 (Clipboard API):', error)
        alert('复制失败,请重试')
      })
  } else {
    console.log('Clipboard API 不可用,使用降级方案')
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    try {
      const success = document.execCommand('copy')
      console.log('execCommand copy 返回值:', success)
      if (success) {
        alert('已复制到剪贴板')
      } else {
        alert('复制失败,请重试')
      }
    }
    catch (error) {
      console.error('复制失败 (降级方案):', error)
      alert('复制失败,请重试')
    }
    document.body.removeChild(textarea)
  }
}

// 剔除单个单词（从错词列表中移除，但不清除拼写错误标记）
function removeSingleWord(item) {
  item.spellError = false
  wordHasInputMap.delete(item.id)
  item.spellValue = ''
  saveProgress()
}

// 计算统计信息
function updateStats() {
  const total = allImportantWords.value.length
  const mastered = allImportantWords.value.filter(w => (w.correctCount || 0) >= 10).length
  const inProgress = total - mastered
  const errorProne = allImportantWords.value.filter(isErrorProneWord).length
  trainingStats.value = `总计 ${total} 个重点单词，已掌握 ${mastered} 个，学习中 ${inProgress} 个，易错/易忘 ${errorProne} 个`
}

// 分页导航
function prevPage() {
  if (currentPage.value > 1)
    currentPage.value--
}

function nextPage() {
  if (currentPage.value < totalPages.value)
    currentPage.value++
}

function goToPage(page) {
  currentPage.value = page
}

function getVisiblePages() {
  const pages = []
  const maxVisible = 7
  const total = totalPages.value
  const current = currentPage.value

  if (total <= maxVisible) {
    for (let i = 1; i <= total; i++)
      pages.push(i)
  }
  else {
    if (current <= 4) {
      for (let i = 1; i <= 5; i++)
        pages.push(i)
      pages.push('...')
      pages.push(total)
    }
    else if (current >= total - 3) {
      pages.push(1)
      pages.push('...')
      for (let i = total - 4; i <= total; i++)
        pages.push(i)
    }
    else {
      pages.push(1)
      pages.push('...')
      for (let i = current - 1; i <= current + 1; i++)
        pages.push(i)
      pages.push('...')
      pages.push(total)
    }
  }

  return pages
}

watch([isHideMastered, isOnlyErrorProne], () => {
  currentPage.value = 1
})

watch(wordsPerPage, (newVal) => {
  localStorage.setItem('important_words_per_page', newVal.toString())
  currentPage.value = 1
})

watch(currentPage, () => {
  if (isTrainingModel.value && isAutoPlayWordAudio.value) {
    focusFirstInput()
  }
})

watch([isTrainingModel], () => {
  if (isTrainingModel.value && isAutoPlayWordAudio.value) {
    focusFirstInput()
  }
})

onMounted(async () => {
  loaded.value = false
  await loadVocabularyData()

  // 初始化语音合成（需要用户交互后才能使用）
  if ('speechSynthesis' in window) {
    console.log('浏览器支持语音合成')
    // 尝试初始化
    window.speechSynthesis.getVoices()
  }
  else {
    console.log('浏览器不支持语音合成')
  }

  if (authStore.isAuthenticated) {
    await loadProgress()
  }
  else {
    await loadImportantWords()
  }
  updateStats()
  watch(allImportantWords, updateStats, { deep: true })
  // 练习模式下自动聚焦第一个输入框
  if (isTrainingModel.value && isAutoPlayWordAudio.value) {
    focusFirstInput()
  }
})
</script>

<template>
  <div class="container mx-auto px-4 py-8">
    <div class="mb-6 rounded-lg bg-white p-6 shadow dark:bg-gray-800">
      <h1 class="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
        🔥 重点单词打乱练习
      </h1>
      <p class="text-gray-600 dark:text-gray-400">
        所有章节的 <span class="font-bold text-red-600">重点单词</span> 已随机打乱，专注于重点词汇练习
      </p>
      <p v-if="trainingStats" class="mt-2 text-sm text-gray-500 dark:text-gray-500">
        {{ trainingStats }}
      </p>
    </div>

    <!-- 控制面板 -->
    <div class="mb-6 rounded-lg bg-white p-4 shadow dark:bg-gray-800">
      <div class="flex flex-wrap items-center gap-4">
        <label class="ml-2 inline-flex cursor-pointer items-center">
          <input v-model="isTrainingModel" type="checkbox" class="peer sr-only">
          <div
            class="peer relative h-6 w-11 rounded-full bg-gray-200 after:absolute after:start-[2px] after:top-[2px] after:h-5 after:w-5 after:border after:border-gray-300 dark:border-gray-600 after:rounded-full after:bg-white dark:bg-gray-700 peer-checked:bg-blue-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 after:transition-all after:content-[''] peer-checked:after:translate-x-full peer-checked:after:border-white dark:peer-focus:ring-blue-800 rtl:peer-checked:after:-translate-x-full"
          />
          <span class="ms-3 text-sm font-medium text-blue-600 dark:text-blue-400">练习模式</span>
        </label>

        <label v-if="isTrainingModel" class="ml-2 inline-flex cursor-pointer items-center">
          <input v-model="isShowMeaning" type="checkbox" class="peer sr-only">
          <div
            class="peer relative h-6 w-11 rounded-full bg-gray-200 after:absolute after:start-[2px] after:top-[2px] after:h-5 after:w-5 after:border after:border-gray-300 dark:border-gray-600 after:rounded-full after:bg-white dark:bg-gray-700 peer-checked:bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-gray-300 after:transition-all after:content-[''] peer-checked:after:translate-x-full peer-checked:after:border-white dark:peer-focus:ring-gray-800 rtl:peer-checked:after:-translate-x-full"
          />
          <span class="ms-3 text-sm font-medium text-gray-700 dark:text-gray-300">显示释义</span>
        </label>

        <label v-if="isTrainingModel" class="ml-2 inline-flex cursor-pointer items-center">
          <input v-model="isShowSource" type="checkbox" class="peer sr-only">
          <div
            class="peer relative h-6 w-11 rounded-full bg-gray-200 after:absolute after:start-[2px] after:top-[2px] after:h-5 after:w-5 after:border after:border-gray-300 dark:border-gray-600 after:rounded-full after:bg-white dark:bg-gray-700 peer-checked:bg-purple-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 after:transition-all after:content-[''] peer-checked:after:translate-x-full peer-checked:after:border-white dark:peer-focus:ring-purple-800 rtl:peer-checked:after:-translate-x-full"
          />
          <span class="ms-3 text-sm font-medium text-purple-600 dark:text-purple-400">显示原词</span>
        </label>

        <label v-if="isTrainingModel" class="ml-2 inline-flex cursor-pointer items-center">
          <input v-model="isAutoPlayWordAudio" type="checkbox" class="peer sr-only">
          <div
            class="peer relative h-6 w-11 rounded-full bg-gray-200 after:absolute after:start-[2px] after:top-[2px] after:h-5 after:w-5 after:border after:border-gray-300 dark:border-gray-600 after:rounded-full after:bg-white dark:bg-gray-700 peer-checked:bg-orange-600 peer-focus:outline-none peer-focus:ring-4 peer:focus:ring-orange-300 after:transition-all after:content-[''] peer-checked:after:translate-x-full peer-checked:after:border-white dark:peer-focus:ring-orange-800 rtl:peer-checked:after:-translate-x-full"
          />
          <span class="ms-3 text-sm font-medium text-orange-600 dark:text-orange-400">自动播放</span>
        </label>

        <label v-if="isTrainingModel" class="ml-2 inline-flex cursor-pointer items-center">
          <input v-model="isHideMastered" type="checkbox" class="peer sr-only">
          <div
            class="peer relative h-6 w-11 rounded-full bg-gray-200 after:absolute after:start-[2px] after:top-[2px] after:h-5 after:w-5 after:border after:border-gray-300 dark:border-gray-600 after:rounded-full after:bg-white dark:bg-gray-700 peer-checked:bg-green-600 peer-focus:outline-none peer-focus:ring-4 peer:focus:ring-green-300 after:transition-all after:content-[''] peer-checked:after:translate-x-full peer-checked:after:border-white dark:peer-focus:ring-green-800 rtl:peer-checked:after:-translate-x-full"
          />
          <span class="ms-3 text-sm font-medium text-green-600 dark:text-green-400">隐藏已掌握</span>
        </label>

        <label v-if="isTrainingModel" class="ml-2 inline-flex cursor-pointer items-center">
          <input v-model="isOnlyErrorProne" type="checkbox" class="peer sr-only">
          <div
            class="peer relative h-6 w-11 rounded-full bg-gray-200 after:absolute after:start-[2px] after:top-[2px] after:h-5 after:w-5 after:border after:border-gray-300 dark:border-gray-600 after:rounded-full after:bg-white dark:bg-gray-700 peer-checked:bg-red-600 peer-focus:outline-none peer-focus:ring-4 peer:focus:ring-red-300 after:transition-all after:content-[''] peer-checked:after:translate-x-full peer-checked:after:border-white dark:peer-focus:ring-red-800 rtl:peer-checked:after:-translate-x-full"
          />
          <span class="ms-3 text-sm font-medium text-red-600 dark:text-red-400">易错/易忘</span>
        </label>

        <div class="ml-4 flex items-center gap-2">
          <span class="text-sm text-gray-700 dark:text-gray-300">每页单词：</span>
          <select
            v-model="wordsPerPage"
            class="rounded-lg border border-gray-300 bg-gray-50 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500"
          >
            <option :value="10">
              10 个
            </option>
            <option :value="20">
              20 个
            </option>
            <option :value="50">
              50 个
            </option>
            <option :value="100">
              100 个
            </option>
          </select>
        </div>
      </div>
    </div>

    <!-- 单词表格 -->
    <div v-if="loaded && currentWords.length > 0" class="overflow-x-auto rounded-lg border border-gray-200 shadow dark:border-gray-700">
      <table class="min-w-full divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-800">
        <thead class="bg-gray-50 dark:bg-gray-700">
          <tr>
            <th class="p-4 text-left text-xs font-medium tracking-wider text-gray-500 dark:text-white">
              序号
            </th>
            <th class="w-[20%] min-w-56 p-4 text-left text-xs font-medium tracking-wider text-gray-500 dark:text-white">
              单词
            </th>
            <th class="p-4 text-left text-xs font-medium tracking-wider text-gray-500 dark:text-white">
              词性
            </th>
            <th class="p-4 text-left text-xs font-medium tracking-wider text-gray-500 dark:text-white">
              词义
            </th>
            <th class="p-4 text-left text-xs font-medium tracking-wider text-gray-500 dark:text-white">
              例句
            </th>
            <th class="p-4 text-left text-xs font-medium tracking-wider text-gray-500 dark:text-white">
              拓展
            </th>
            <th class="p-4 text-left text-xs font-medium tracking-wider text-gray-500 dark:text-white">
              章节
            </th>
            <th v-if="isTrainingModel" class="p-4 text-left text-xs font-medium tracking-wider text-gray-500 dark:text-white">
              统计
            </th>
            <th v-if="isTrainingModel" class="p-4 text-left text-xs font-medium tracking-wider text-gray-500 dark:text-white">
              操作
            </th>
          </tr>
        </thead>
        <tbody class="bg-white dark:bg-gray-800">
          <tr
            v-for="(item, index) in currentWords"
            :key="item.id"
            :class="{ 'bg-gray-50 dark:bg-gray-700': index % 2 === 0 }"
            class="text-sm text-gray-900 dark:text-white"
          >
            <td class="p-4">
              {{ (currentPage - 1) * wordsPerPage + index + 1 }}
            </td>
            <td class="w-[20%] min-w-56 p-4">
              <i
                class="i-ph-speaker-simple-high-bold inline-block cursor-pointer align-middle"
                @click="playWordAudio(item)"
              />

              <template v-if="isTrainingModel">
                <i
                  class="ml-4 inline-block cursor-pointer"
                  :class="[wordShowSourceMap.get(item.id) ? 'i-ph-eye-slash-bold' : 'i-ph-eye-bold']"
                  title="显示原词"
                  @click.stop="toggleShowSource(item)"
                />
                <input
                  :id="item.id"
                  autocomplete="off"
                  placeholder="请输入单词"
                  :class="getInputStyleClass(item)"
                  type="text"
                  @input="item.spellValue = $event.target.value; wordHasInputMap.set(item.id, true)"
                  @focusout="onInputFocusOut($event, item)"
                  @focusin="onInputFocusIn($event)"
                >
              </template>

              <div v-if="!isTrainingModel" class="relative group ml-3 inline-block align-middle">
                <p v-for="w in item.word" :key="w" class="font-bold">
                  <a
                    class="hover:underline"
                    :title="`在剑桥词典中查询 ${w}`"
                    target="_blank"
                    :href="`https://dictionary.cambridge.org/dictionary/english-chinese-simplified/${w}`"
                  >{{ w }}</a>
                </p>
                <div
                  class="absolute right-0 top-0 hidden h-full items-center group-hover:flex"
                  @click="copyText(item)"
                >
                  <i class="i-ph-copy block cursor-pointer px-4" />
                </div>
              </div>

              <div v-if="isTrainingModel && shouldShowWordSource(item)" class="relative group ml-3 inline-block align-middle">
                <p v-for="w in item.word" :key="w" class="font-bold">
                  <a
                    class="hover:underline"
                    :title="`在剑桥词典中查询 ${w}`"
                    target="_blank"
                    :href="`https://dictionary.cambridge.org/dictionary/english-chinese-simplified/${w}`"
                  >{{ w }}</a>
                </p>
                <div
                  class="absolute right-0 top-0 hidden h-full items-center group-hover:flex"
                  @click="copyText(item)"
                >
                  <i class="i-ph-copy block cursor-pointer px-4" />
                </div>
              </div>
            </td>
            <td style="font-style: italic; font-family: times;">
              {{ !isTrainingModel || shouldShowWordSource(item) ? item.pos : '' }}
            </td>
            <td class="p-4">
              {{ (isShowMeaning || shouldShowWordSource(item)) ? item.meaning : '' }}
            </td>
            <td class="p-4">
              {{ shouldShowWordSource(item) ? item.example : '' }}
            </td>
            <td class="p-4">
              {{ shouldShowWordSource(item) ? item.extra : '' }}
            </td>
            <td class="p-4">
              <span class="rounded bg-gray-100 px-2 py-1 text-xs font-medium text-gray-600 dark:bg-gray-700 dark:text-gray-400">
                {{ item.chapterName }}
              </span>
            </td>
            <td v-if="isTrainingModel" class="p-4">
              <div class="text-xs">
                <span class="text-green-600 dark:text-green-400">
                  ✓ {{ item.correctCount || 0 }}
                </span>
                <span class="ml-2 text-red-600 dark:text-red-400">
                  ✗ {{ item.errorCount || 0 }}
                </span>
              </div>
            </td>
            <td v-if="isTrainingModel" class="p-4">
              <button
                v-if="item.spellError"
                type="button"
                class="rounded-lg bg-red-600 px-3 py-1.5 text-xs font-medium text-white dark:bg-red-500 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 dark:hover:bg-red-600"
                @click="removeSingleWord(item)"
              >
                🗑️ 剔除
              </button>
              <span v-else class="text-xs text-gray-500 dark:text-gray-400">
                -
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 如果没有重点单词 -->
    <div v-if="loaded && currentWords.length === 0" class="rounded-lg bg-yellow-50 p-8 text-center dark:bg-yellow-900/20">
      <p class="text-lg text-gray-700 dark:text-gray-300">
        还没有重点单词！
      </p>
      <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">
        请先在词汇页面将单词标记为"重点"等级
      </p>
      <router-link
        to="/vocabulary"
        class="mt-4 inline-block rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white dark:bg-blue-500 hover:bg-blue-700 dark:hover:bg-blue-600"
      >
        去词汇页面
      </router-link>
    </div>

    <!-- 分页导航 -->
    <div v-if="totalPages > 1 && loaded" class="mt-4">
      <div class="flex items-center justify-center space-x-2">
        <button
          :disabled="currentPage === 1"
          class="rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white disabled:cursor-not-allowed hover:bg-blue-700 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          @click="prevPage"
        >
          上一页
        </button>

        <div class="flex space-x-1">
          <button
            v-for="page in getVisiblePages()"
            :key="page"
            :class="{
              'bg-blue-600 text-white': currentPage === page,
              'bg-gray-200 text-gray-700 hover:bg-gray-300': currentPage !== page,
              'cursor-default': page === '...',
              'px-3 py-2 text-sm font-medium rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500': typeof page === 'number',
              'px-2 text-gray-500': page === '...',
            }"
            :disabled="page === '...'"
            @click="typeof page === 'number' ? goToPage(page) : null"
          >
            {{ page }}
          </button>
        </div>

        <button
          :disabled="currentPage === totalPages"
          class="rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white disabled:cursor-not-allowed hover:bg-blue-700 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          @click="nextPage"
        >
          下一页
        </button>
      </div>
    </div>

    <!-- 加载中 -->
    <div v-if="!loaded" class="flex items-center justify-center py-12">
      <div class="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent dark:border-blue-400" />
    </div>
  </div>
</template>
