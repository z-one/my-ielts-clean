const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

// 从 localStorage 获取 token
function getToken() {
  return localStorage.getItem('access_token')
}

// 设置 token
function setToken(token) {
  localStorage.setItem('access_token', token)
}

// 清除 token
function clearToken() {
  localStorage.removeItem('access_token')
}

// 通用请求函数
async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`
  const token = getToken()

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const config = {
    ...options,
    headers,
  }

  try {
    const response = await fetch(url, config)
    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.detail || '请求失败')
    }

    return data
  }
  catch (error) {
    console.error('API request failed:', error)
    throw error
  }
}

// GET 请求
export function get(endpoint, options = {}) {
  return request(endpoint, { ...options, method: 'GET' })
}

// POST 请求
export function post(endpoint, data, options = {}) {
  return request(endpoint, { ...options, method: 'POST', body: JSON.stringify(data) })
}

// PUT 请求
export function put(endpoint, data, options = {}) {
  return request(endpoint, { ...options, method: 'PUT', body: JSON.stringify(data) })
}

// DELETE 请求
export function del(endpoint, options = {}) {
  return request(endpoint, { ...options, method: 'DELETE' })
}

// 认证 API
export const authAPI = {
  // 用户注册
  register: (userData) => post('/api/auth/register', userData),

  // 用户登录
  login: async (username, password) => {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)

    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: 'POST',
      body: formData,
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.detail || '登录失败')
    }

    // 保存 token
    if (data.access_token) {
      setToken(data.access_token)
    }

    return data
  },

  // 获取当前用户信息
  getCurrentUser: () => get('/api/auth/me'),

  // 退出登录
  logout: () => {
    clearToken()
    window.location.href = '/login'
  },
}

// 章节 API
export const chaptersAPI = {
  // 获取所有章节进度
  getAllProgress: () => get('/api/chapters/progress'),

  // 获取指定章节进度
  getProgress: (chapterName) => get(`/api/chapters/${chapterName}/progress`),

  // 更新章节状态
  updateStatus: (chapterName, status) => put(`/api/chapters/${chapterName}/status`, { status }),

  // 批量更新章节状态
  batchUpdate: (chapters) => post('/api/chapters/batch-update', chapters),
}

// 单词 API
export const wordsAPI = {
  // 获取所有单词进度
  getAllProgress: () => get('/api/words/progress'),

  // 获取指定章节单词进度
  getChapterProgress: (chapterName) => get(`/api/words/${chapterName}/progress`),

  // 更新单词进度
  updateProgress: (wordId, progressData) => put(`/api/words/${wordId}/progress`, progressData),

  // 批量更新单词进度
  batchUpdate: (wordsData) => post('/api/words/batch-update', wordsData),

  // 同步本地进度
  syncProgress: (syncData) => post('/api/words/sync', syncData),
}

// 词库 API
export const vocabularyAPI = {
  getChapters: () => get('/api/vocabulary/chapters'),
  getChapterDetails: (source) => get(`/api/vocabulary/chapter-details${source ? `?source=${encodeURIComponent(source)}` : ''}`),
  getWords: (params = {}) => {
    const query = new URLSearchParams()
    if (params.chapterName)
      query.set('chapter_name', params.chapterName)
    if (params.source)
      query.set('source', params.source)
    const suffix = query.toString() ? `?${query.toString()}` : ''
    return get(`/api/vocabulary/words${suffix}`)
  },
  search: query => get(`/api/vocabulary/search?q=${encodeURIComponent(query)}`),
  createCustomWord: wordData => post('/api/vocabulary/custom-words', wordData),
  updateCustomWord: (wordId, wordData) => put(`/api/vocabulary/custom-words/${wordId}`, wordData),
  deleteCustomWord: wordId => del(`/api/vocabulary/custom-words/${wordId}`),
}

// 用户设置 API
export const settingsAPI = {
  // 获取用户设置
  get: () => get('/api/settings'),

  // 更新用户设置
  update: (settingsData) => put('/api/settings', settingsData),
}

// 考试记录 API
export const examsAPI = {
  // 保存考试记录
  save: (examData) => post('/api/exams', examData),

  // 获取所有考试记录
  getAll: () => get('/api/exams'),

  // 获取指定考试记录
  getById: (examId) => get(`/api/exams/${examId}`),
}
