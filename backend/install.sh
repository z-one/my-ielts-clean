#!/bin/bash

# IELTS Vocabulary Backend 安装脚本

echo "======================================"
echo "  IELTS Vocabulary Backend - 安装"
echo "======================================"

# 检查 Python3
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3"
    echo "正在安装 Python3..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-venv
else
    echo "✅ Python3 已安装: $(python3 --version)"
fi

# 检查 pip3
if ! command -v pip3 &> /dev/null; then
    echo "❌ 未找到 pip3"
    echo "正在安装 pip3..."
    sudo apt-get install -y python3-pip
else
    echo "✅ pip3 已安装: $(pip3 --version)"
fi

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
    if [ $? -eq 0 ]; then
        echo "✅ 虚拟环境创建成功"
    else
        echo "❌ 虚拟环境创建失败"
        exit 1
    fi
else
    echo "✅ 虚拟环境已存在"
fi

# 激活虚拟环境
echo ""
echo "🔌 激活虚拟环境..."
source venv/bin/activate

# 升级 pip
echo "📥 升级 pip..."
pip install --upgrade pip -q

# 安装依赖
echo ""
echo "📥 安装项目依赖..."
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo "✅ 依赖安装成功"
else
    echo "❌ 依赖安装失败"
    exit 1
fi

# 创建 .env 文件
if [ ! -f ".env" ]; then
    echo ""
    echo "📝 创建 .env 文件..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ 已从 .env.example 创建 .env 文件"
        echo "⚠️  请根据需要修改 .env 中的配置"
    else
        echo "❌ 错误: 找不到 .env.example 文件"
    fi
else
    echo "✅ .env 文件已存在"
fi

echo ""
echo "======================================"
echo "✅ 安装完成！"
echo "======================================"
echo ""
echo "🚀 运行以下命令启动服务器:"
echo "   ./start.sh"
echo ""
