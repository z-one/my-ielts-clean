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

### 从宿主机连接数据库（需暴露 5432 端口）
```bash
psql -h localhost -p 5432 -U ielts -d ielts_db
```

### 检查数据库是否就绪
```bash
docker exec -it ielts-postgres pg_isready -U ielts
```

### 查看数据库列表
```bash
docker exec -it ielts-postgres psql -U ielts -d ielts_db -c "\l"
```

### 查看所有表
```bash
docker exec -it ielts-postgres psql -U ielts -d ielts_db -c "\dt"
```

### 查看某张表结构
```bash
docker exec -it ielts-postgres psql -U ielts -d ielts_db -c "\d table_name"
```

### 查看数据库占用大小
```bash
docker exec -it ielts-postgres psql -U ielts -d ielts_db -c "SELECT pg_size_pretty(pg_database_size('ielts_db'));"
```

### 查看各表行数
```bash
docker exec -it ielts-postgres psql -U ielts -d ielts_db -c "
SELECT schemaname, relname, n_live_tup
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;
"
```

### 导出数据库备份
```bash
docker exec ielts-postgres pg_dump -U ielts ielts_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 恢复数据库备份
```bash
cat backup.sql | docker exec -i ielts-postgres psql -U ielts -d ielts_db
```

### 在容器内运行 Python 脚本
```bash
docker exec -it ielts-backend python backend/scripts/xxx.py --help
```

## 数据验证操作

### 验证后端服务健康状态
```bash
# 基础健康检查
curl -fsS http://localhost:8000/health

# 查看后端启动信息
curl -fsS http://localhost:8000/

# 查看后端健康检查日志
docker exec ielts-backend curl -fsS http://localhost:8000/health
```

### 验证数据库连接
```bash
# 检查 PostgreSQL 是否就绪
docker exec -it ielts-postgres pg_isready -U ielts

# 在后端容器内测试数据库连接
docker exec -it ielts-backend python -c "
from app.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('数据库连接成功' if result.scalar() == 1 else '数据库连接失败')
"
```

### 验证各表数据完整性
```bash
# 检查用户表数据量
docker exec -it ielts-postgres psql -U ielts -d ielts_db -c "SELECT COUNT(*) AS user_count FROM users;"

# 检查章节表数据量
docker exec -it ielts-postgres psql -U ielts -d ielts_db -c "SELECT COUNT(*) AS chapter_count FROM chapters;"

# 检查词汇表数据量
docker exec -it ielts-postgres psql -U ielts -d ielts_db -c "SELECT COUNT(*) AS word_count FROM words;"

# 检查用户词汇表数据量
docker exec -it ielts-postgres psql -U ielts -d ielts_db -c "SELECT COUNT(*) AS vocabulary_count FROM vocabularies;"

# 一键检查所有核心表数据量
docker exec -it ielts-postgres psql -U ielts -d ielts_db -c "
SELECT 'users' AS table_name, COUNT(*) FROM users
UNION ALL SELECT 'chapters', COUNT(*) FROM chapters
UNION ALL SELECT 'words', COUNT(*) FROM words
UNION ALL SELECT 'vocabularies', COUNT(*) FROM vocabularies
UNION ALL SELECT 'settings', COUNT(*) FROM settings
UNION ALL SELECT 'exams', COUNT(*) FROM exams;
"
```

### 验证外键关系完整性
```bash
# 检查是否有孤儿词汇记录（word_id 不存在于 words 表）
docker exec -it ielts-postgres psql -U ielts -d ielts_db -c "
SELECT COUNT(*) AS orphan_vocabularies
FROM vocabularies v
LEFT JOIN words w ON v.word_id = w.id
WHERE w.id IS NULL;
"

# 检查是否有孤儿章节记录
docker exec -it ielts-postgres psql -U ielts -d ielts_db -c "
SELECT COUNT(*) AS orphan_chapters
FROM chapters c
LEFT JOIN users u ON c.user_id = u.id
WHERE u.id IS NULL;
"
```

### 验证 API 接口可用性
```bash
# 测试根接口
curl -s http://localhost:8000/ | python -m json.tool

# 测试章节接口（需替换 TOKEN）
curl -s -H "Authorization: Bearer TOKEN" http://localhost:8000/api/chapters/ | python -m json.tool

# 测试词汇接口（需替换 TOKEN）
curl -s -H "Authorization: Bearer TOKEN" http://localhost:8000/api/words/ | python -m json.tool
```

### 验证前端服务可达性
```bash
curl -fsS -o /dev/null -w "HTTP状态码: %{http_code}\n" http://localhost:8080/
```

### 综合验证脚本（一键检查所有服务）
```bash
echo "=== 检查数据库状态 ==="
docker exec ielts-postgres pg_isready -U ielts

echo "=== 检查后端健康 ==="
curl -fsS http://localhost:8000/health

echo "=== 检查前端可达性 ==="
curl -fsS -o /dev/null -w "前端 HTTP状态码: %{http_code}\n" http://localhost:8080/

echo "=== 检查各表数据量 ==="
docker exec ielts-postgres psql -U ielts -d ielts_db -c "
SELECT schemaname, relname AS table_name, n_live_tup AS row_count
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;
"

echo "=== 所有服务状态 ==="
docker compose ps
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
