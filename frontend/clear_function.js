// 临时函数，需要插入到文件中
function clearProgress() {
  // 清除当前章节的练习状态
  const words = refVocabulary[category.value].words
  for (const group of words) {
    for (const item of group) {
      item.spellValue = ''
      item.spellError = false
    }
  }
  
  // 清除本地存储
  localStorage.removeItem(PROGRESS_KEY)
  trainingStats.value = calcStats()
}