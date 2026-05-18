#!/bin/bash

# IELTS 词汇学习应用 - Docker 启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 打印函数
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 获取环境参数
ENV=${1:-production}

print_step "启动 IELTS 词汇学习应用（${ENV} 环境）..."

# 检查环境变量文件
if [ ! -f ".env" ]; then
    print_warn ".env 文件不存在，从 .env.example 复制..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_info "已创建 .env 文件，请修改配置后重新运行"
        exit 0
    else
        print_error ".env.example 文件不存在"
        exit 1
    fi
fi

# 根据环境选择 compose 文件
case $ENV in
    production|prod)
        COMPOSE_FILE="docker-compose.yml"
        ;;
    development|dev)
        COMPOSE_FILE="docker-compose.dev.yml"
        ;;
    *)
        print_error "未知环境: $ENV"
        print_info "使用方法: bash start.sh [production|development]"
        exit 1
        ;;
esac

print_info "使用配置文件: $COMPOSE_FILE"

# 检查容器是否已存在
if docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
    print_warn "容器已在运行中"
    print_info "如需重启，请先运行: docker-compose -f $COMPOSE_FILE restart"
    exit 0
fi

# 创建必要的目录
print_step "创建必要的目录..."
mkdir -p backend/logs
mkdir -p postgres/init

# 启动服务
print_step "启动服务..."
docker-compose -f "$COMPOSE_FILE" up -d

# 等待服务启动
print_step "等待服务启动..."
sleep 5

# 显示服务状态
print_info "服务状态:"
docker-compose -f "$COMPOSE_FILE" ps

# 显示访问地址
echo ""
print_info "访问地址:"
case $ENV in
    production|prod)
        echo "  前端: http://localhost:8080"
        echo "  后端 API: http://localhost:8000"
        echo "  后端文档: http://localhost:8000/docs"
        echo "  数据库: localhost:5432"
        echo "  Redis: localhost:6379"
        ;;
    development|dev)
        echo "  前端: http://localhost:3000"
        echo "  后端 API: http://localhost:8000"
        echo "  后端文档: http://localhost:8000/docs"
        echo "  数据库: localhost:5432"
        echo "  Redis: localhost:6379"
        ;;
esac

echo ""
print_info "查看日志: docker-compose -f $COMPOSE_FILE logs -f"
print_info "停止服务: docker-compose -f $COMPOSE_FILE down"
