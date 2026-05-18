#!/bin/bash

# IELTS Vocabulary Backend 启动脚本

echo "======================================"
echo "  IELTS Vocabulary Backend"
echo "======================================"

# 切换到 backend 目录
cd /app/backend

# 创建日志目录
mkdir -p logs

echo "🚀 启动服务..."
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 2>&1 | tee logs/server.log

