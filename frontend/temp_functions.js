function shouldShowWord(item) {
  // 非练习模式：显示所有单词
  if (!isTrainingModel.value) return true
  
  // 练习模式下的过滤逻辑
  if (isOnlyShowErrors.value && !item.spellError) return false
  
  // 隐藏已掌握的单词（正确10次以上）
  if (isHideMastered.value && (item.correctCount || 0) >= MASTERY_COUNT) return false
  
  return true
}

function clearProgress() {
  // 清除当前章节的练习状态
  const words = refVocabulary[category.value].words
  for (const group of words) {
    for (const item of group) {
      item.spellValue = ''
      item.spellError = false
      item.correctCount = 0
    }
  }
  
  // 清除本地存储
  localStorage.removeItem(PROGRESS_KEY)
  trainingStats.value = calcStats()
}