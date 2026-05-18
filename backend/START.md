# 后端开发完成清单

## ✅ 已完成

### 阶段二：后端开发（Python + FastAPI）

- [x] **任务 2.1: 项目初始化**
  - [x] 创建 FastAPI 项目结构
  - [x] 配置数据库（SQLite）
  - [x] 配置环境变量
  - [x] 添加 CORS 配置

- [x] **任务 2.2: 用户认证模块**
  - [x] 用户注册 API（密码加密）
  - [x] 用户登录 API（JWT token 生成）
  - [x] Token 验证中间件
  - [ ] 密码重置功能（可选）

- [x] **任务 2.3: 章节进度 API**
  - [x] 获取章节进度列表 GET `/api/chapters/progress`
  - [x] 更新章节状态 PUT `/api/chapters/{chapter_name}/status`
  - [x] 批量更新章节状态 POST `/api/chapters/batch-update`

- [x] **任务 2.4: 单词进度 API**
  - [x] 获取单词进度 GET `/api/words/progress`
  - [x] 更新单词进度 PUT `/api/words/{word_id}/progress`
  - [x] 批量更新单词进度 POST `/api/words/batch-update`
  - [x] 同步本地进度到服务器 POST `/api/words/sync`

- [x] **任务 2.5: 用户设置 API**
  - [x] 获取用户设置 GET `/api/settings`
  - [x] 更新用户设置 PUT `/api/settings`

- [x] **任务 2.6: 数据库模型**
  - [x] SQLAlchemy 模型定义
  - [ ] 数据库迁移脚本（使用 Alembic）
  - [ ] 种子数据（可选）

---

## 🚀 启动后端服务器

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑 .env 文件，修改以下配置：
# - SECRET_KEY: 生产环境必须修改为随机字符串
# - CORS_ORIGINS: 设置为前端 URL
```

### 3. 启动服务器

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 访问 API 文档

打开浏览器访问：`http://localhost:8000/docs`

---

## 📋 前端开发待办清单

### 阶段一：前端基础

- [ ] **任务 1.1: 添加认证状态管理**
  - [x] 创建 `auth.js` store (Pinia)
  - [x] 添加登录/注册页面
  - [ ] 添加路由守卫
  - [ ] 修改 API 调用以包含 token

- [x] **任务 1.2: 创建注册/登录界面**
  - [x] 注册页面：用户名、邮箱、密码、确认密码
  - [x] 登录页面：邮箱/用户名、密码
  - [x] 表单验证
  - [ ] 记住我功能

- [ ] **任务 1.3: 修改现有页面集成认证**
  - [ ] 添加用户信息显示区域
  - [ ] 添加退出登录按钮
  - [ ] 未登录时隐藏学习进度相关功能

### 阶段三：前后端集成

- [x] **任务 3.1: API 客户端封装**
  - [x] 创建 `api.js` 封装 HTTP 请求
  - [x] 自动添加 Authorization header
  - [ ] Token 过期自动刷新
  - [x] 错误处理

- [ ] **任务 3.2: 数据同步机制**
  - [ ] 本地 localStorage 与服务器的同步策略
  - [ ] 离线模式支持
  - [ ] 冲突解决策略

- [ ] **任务 3.3: 前端页面改造**
  - [ ] 替换 localStorage 为 API 调用
  - [ ] 添加数据加载状态
  - [ ] 添加错误提示
  - [ ] 添加同步状态指示器

---

## 📝 下一步计划

### 1. 添加路由守卫
在 `main.ts` 中添加全局路由守卫，保护需要登录的页面

### 2. 修改 vocabulary 页面
- 集成 auth store
- 登录时同步数据到服务器
- 添加用户信息显示和退出按钮

### 3. 数据同步策略
- 本地优先（离线可用）
- 定时自动同步
- 冲突解决：以服务器为准或本地为准
