# Docker 运维操作指南

## 环境说明
- 工作目录：`/opt/my-ielts-clean`
- 容器名称：ielts-frontend (8080), ielts-backend (8000), ielts-postgres (5432)

## 拉取最新代码并重启服务

```bash
cd /opt/my-ielts-clean
git pull
docker compose build frontend
docker compose up -d --no-deps frontend
docker compose restart backend
```

## 单独操作各服务

### 重启后端（代码已挂载 volume，改动自动生效）
```bash
docker compose restart backend
```

### 重启前端（需要重新构建）
```bash
docker compose build frontend
docker compose up -d frontend
```

### 重启所有服务
```bash
docker compose restart
```

### 停止所有服务
```bash
docker compose down
```

### 启动所有服务
```bash
docker compose up -d
```

## 查看日志

### 查看后端日志
```bash
docker logs -f ielts-backend --tail 50
```

### 查看前端日志
```bash
docker logs -f ielts-frontend --tail 50
```

### 查看数据库日志
```bash
docker logs -f ielts-postgres --tail 50
```

## 数据库操作

### 连接数据库
```bash
docker exec -it ielts-postgres psql -U ielts -d ielts_db
```

### 在容器内运行 Python 脚本
```bash
docker exec -it ielts-backend python backend/scripts/xxx.py --help
```

### 导入数据（需先进入容器）
```bash
docker exec -it ielts-backend bash
cd /app/backend/scripts

# 导入静态词汇（先 dry-run）
python import_static_vocabulary.py --dry-run

# 正式导入
python import_static_vocabulary.py --import-db

# 导入有道词汇（raw 格式）
python import_youdao_wordbook_raw.py --import-db --raw /app/data/youdao-wordbook-raw.json

# 导入有道词汇（cleaned 格式）
python import_youdao_wordbook_cleaned.py --import-db --cleaned /app/data/youdao-wordbook-cleaned.json

# 导入 SQLite 用户数据
python import_sqlite_user_data.py --import-db /app/data/ielts-production.db --clear-target

# 同步章节
python sync_vocabulary_chapters.py --dry-run
python sync_vocabulary_chapters.py --import-db
```

## 清理缓存

### 清除前端缓存（浏览器）
- 打开 DevTools → Application → Storage → Clear site data
- 或按 Ctrl+Shift+Delete

### 清除后端缓存（需重启）
```bash
docker compose restart backend
```

## 常见问题

### 后端启动失败
```bash
docker logs ielts-backend
```

### 前端无法访问
```bash
docker logs ielts-frontend
docker compose ps  # 查看服务状态
```

### 数据库连接失败
```bash
docker exec -it ielts-postgres pg_isready -U ielts
```
