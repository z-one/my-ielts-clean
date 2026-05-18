<script setup>
import { ref } from 'vue'
import { searchBackendVocabulary } from '../../services/vocabulary'

const searchQuery = ref('')
const searchResults = ref([])
const isSearching = ref(false)
const searchTime = ref(0)

// 搜索单词
async function searchWords() {
  if (!searchQuery.value.trim()) {
    searchResults.value = []
    return
  }

  isSearching.value = true
  const startTime = performance.now()
  try {
    searchResults.value = await searchBackendVocabulary(searchQuery.value.trim())
    searchTime.value = performance.now() - startTime
  }
  catch (error) {
    console.error('搜索单词失败:', error)
    searchResults.value = []
  }
  finally {
    isSearching.value = false
  }
}

// 播放单词音频
function playAudio(word) {
  // 尝试不同的音频路径
  const audioPaths = [
    `vocabulary/audio/${word.chapterName}/${word.word[0]}.mp3`,
    `179_audios/${word.word[0].toLowerCase()}.mp3`
  ]

  let currentIndex = 0
  const audio = new Audio()

  function tryNextPath() {
    if (currentIndex >= audioPaths.length) {
      console.log('所有音频路径都尝试失败')
      return
    }

    const audioPath = audioPaths[currentIndex]
    audio.src = audioPath

    audio.play().catch(error => {
      console.log(`音频播放失败 (${audioPath}):`, error)
      currentIndex++
      tryNextPath()
    })
  }

  tryNextPath()
}

// 复制单词信息
function copyWordInfo(word) {
  const text = `${word.word[0]} ${word.pos} ${word.meaning}\n${word.example}`
  navigator.clipboard.writeText(text).then(() => {
    alert('复制成功!')
  }).catch(error => {
    console.error('复制失败:', error)
    alert('复制失败,请重试')
  })
}

</script>

<template>
  <div class="px-2 pt-4 lg:px-0 sm:px-4 sm:pt-6">
    <div class="p-3 shadow-sm mobile-card lg:p-6 sm:p-4">
      <!-- 页面标题 -->
      <div class="mb-6">
        <h3 class="mb-2 text-xl font-bold text-gray-900 dark:text-white">
          单词查询
        </h3>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          搜索所有章节中的单词，支持按单词、释义或例句搜索
        </p>
      </div>

      <!-- 搜索框 -->
      <div class="mb-6">
        <div class="relative">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="输入单词、释义或例句进行搜索..."
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:placeholder-gray-400"
            @keyup.enter="searchWords"
          />
          <button
            @click="searchWords"
            class="absolute right-2 top-1/2 transform -translate-y-1/2 px-3 py-1 bg-blue-500 text-white rounded-md hover:bg-blue-600"
          >
            搜索
          </button>
        </div>
      </div>

      <!-- 搜索状态 -->
      <div v-if="isSearching" class="mb-4 text-center">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">正在搜索...</p>
      </div>

      <!-- 搜索结果统计 -->
      <div v-if="searchResults.length > 0" class="mb-4">
        <p class="text-sm text-gray-500 dark:text-gray-400">
          找到 {{ searchResults.length }} 个结果，用时 {{ searchTime.toFixed(2) }}ms
        </p>
      </div>

      <!-- 搜索结果 -->
      <div v-if="searchResults.length > 0" class="space-y-4">
        <div
          v-for="(word, index) in searchResults"
          :key="index"
          class="p-4 border border-gray-200 rounded-lg dark:border-gray-700 dark:bg-gray-800"
        >
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div class="flex items-center gap-2">
                <h4 class="text-lg font-semibold text-gray-900 dark:text-white">
                  {{ word.word[0] }}
                </h4>
                <span class="text-sm text-gray-500 dark:text-gray-400">{{ word.pos }}</span>
                <span class="text-xs px-2 py-1 bg-gray-100 text-gray-800 rounded-full dark:bg-gray-700 dark:text-gray-300">
                  {{ word.chapterName }}
                </span>
              </div>
              <p class="mt-1 text-gray-700 dark:text-gray-300">{{ word.meaning }}</p>
              <p v-if="word.example" class="mt-2 text-sm text-gray-500 dark:text-gray-400 italic">
                {{ word.example }}
              </p>
            </div>
            <div class="mt-3 sm:mt-0 flex gap-2">
              <button
                @click="playAudio(word)"
                class="px-3 py-1 bg-gray-100 text-gray-800 rounded-md hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
              >
                发音
              </button>
              <button
                @click="copyWordInfo(word)"
                class="px-3 py-1 bg-gray-100 text-gray-800 rounded-md hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
              >
                复制
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 无结果提示 -->
      <div v-if="!isSearching && searchQuery.trim() && searchResults.length === 0" class="text-center py-8">
        <p class="text-gray-500 dark:text-gray-400">未找到匹配的单词</p>
      </div>

      <!-- 初始状态提示 -->
      <div v-if="!isSearching && !searchQuery.trim()" class="text-center py-12">
        <p class="text-gray-500 dark:text-gray-400">请输入搜索词开始查询</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 可以添加自定义样式 */
</style>
