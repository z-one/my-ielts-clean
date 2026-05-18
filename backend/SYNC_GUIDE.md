# 数据同步功能说明

## 概述

本项目实现了前端 localStorage 与后端数据库的自动同步功能，确保用户的学习进度不会因为浏览器缓存清理或更换设备而丢失。

## 功能特性

1. **自动同步**: 登录后自动加载后端数据，定期（30秒）将本地数据同步到后端
2. **实时同步**: 数据修改时立即同步到后端
3. **断点续传**: 支持离线使用，联网后自动同步
4. **数据持久化**: 所有学习进度保存在数据库中

## 数据模型

### 章节进度表 (chapter_progress)
- `id`: 主键
- `user_id`: 用户ID
- `chapter_name`: 章节名称
- `status`: 学习状态 (not_learned/learned/completed/mastered)

### 单词进度表 (word_progress)
- `id`: 主键
- `user_id`: 用户ID
- `word_id`: 单词ID
- `chapter_name`: 章节名称
- `spell_value`: 拼写输入值
- `spell_error`: 拼写是否错误
- `correct_count`: 正确次数
- `error_count`: 错误次数
- `show_source`: 是否显示原文
- `focus_level`: 关注等级 (0/1/2)

### 用户设置表 (user_settings)
- `id`: 主键
- `user_id`: 用户ID
- `words_per_page`: 每页显示单词数
- `auto_play_audio`: 是否自动播放音频
- `show_meaning`: 是否显示释义

## API 接口

### 章节进度 API
```
GET    /api/chapters/progress           # 获取所有章节进度
GET    /api/chapters/{name}/progress     # 获取指定章节进度
PUT    /api/chapters/{name}/status       # 更新章节状态
POST   /api/chapters/batch-update       # 批量更新章节状态
```

### 单词进度 API
```
GET    /api/words/progress               # 获取所有单词进度
GET    /api/words/{chapter}/progress     # 获取指定章节单词进度
PUT    /api/words/{id}/progress          # 更新单词进度
POST   /api/words/batch-update           # 批量更新单词进度
POST   /api/words/sync                   # 同步本地进度
```

### 用户设置 API
```
GET    /api/settings                     # 获取用户设置
PUT    /api/settings                     # 更新用户设置
```

## 使用方式

### 1. 登录后自动加载数据

用户登录成功后，系统会自动：
1. 从后端加载章节状态
2. 从后端加载用户设置
3. 启动定时同步（每30秒同步一次）

### 2. 数据修改时自动同步

以下操作会触发数据同步：
- 保存单词练习进度
- 更新章节学习状态
- 修改用户设置（如每页单词数）

### 3. 手动同步（可选）

在词汇页面中，可以通过以下方式手动触发同步：
- 切换章节时
- 完成练习时

## 技术实现

### 前端服务

1. **sync.js**: 核心同步服务
   - `syncChapterStatus()`: 同步章节状态
   - `syncWordProgress()`: 同步单词进度
   - `syncUserSettings()`: 同步用户设置
   - `loadChapterStatus()`: 加载章节状态
   - `loadWordProgress()`: 加载单词进度
   - `loadUserSettings()`: 加载用户设置

2. **autoSync.js**: 自动同步服务
   - `startPeriodicSync()`: 启动定时同步
   - `stopPeriodicSync()`: 停止定时同步
   - `throttledSync()`: 节流同步

3. **useSync.js**: 组合式函数
   - `useDataSync()`: 在组件中使用数据同步

### 后端实现

后端已实现完整的 CRUD API 接口（见 `app/api/` 目录）。

## 配置项

```javascript
// 同步间隔（毫秒）
const SYNC_INTERVAL = 30000 // 30秒

// 后端 API 地址
const API_BASE_URL = 'http://localhost:8000'
```

## 注意事项

1. **离线使用**: 即使网络断开，应用仍可正常使用，数据暂存在 localStorage
2. **数据一致性**: 本地数据和服务器数据会自动合并，以最新修改为准
3. **多设备同步**: 同一账号在不同设备登录后，会自动同步学习进度
4. **清理缓存**: 清理浏览器缓存不会丢失数据，因为数据已同步到后端

## 测试

1. 启动后端服务: `python -m app.main`
2. 启动前端服务: `pnpm dev`
3. 登录账号后进行词汇练习
4. 检查数据库中的数据是否正确同步
