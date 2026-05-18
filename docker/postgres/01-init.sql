-- IELTS 词汇学习应用 - 数据库初始化脚本

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 创建表（如果不存在将由 Alembic 创建）
-- 这里可以放置初始化数据
