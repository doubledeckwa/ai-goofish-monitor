#!/bin/bash

# 闲鱼监控系统本地启动脚本
# 功能：清理旧构建、安装依赖、构建前端、启动服务

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}闲鱼监控系统 - 本地启动脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# 1. 清理旧的 dist 目录
echo -e "\n${YELLOW}[1/5] 清理旧的构建产物...${NC}"
if [ -d "dist" ]; then
    rm -rf dist
    echo -e "${GREEN}✓ 已删除旧的 dist 目录${NC}"
else
    echo -e "${GREEN}✓ dist 目录不存在，跳过清理${NC}"
fi

# 2. 检查并安装 Python 依赖
echo -e "\n${YELLOW}[2/5] 检查 Python 依赖...${NC}"
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}✗ 错误: requirements.txt 文件不存在${NC}"
    exit 1
fi

echo "正在安装 Python 依赖..."
pip install -r requirements.txt --quiet
echo -e "${GREEN}✓ Python 依赖安装完成${NC}"

# 3. 构建前端
echo -e "\n${YELLOW}[3/5] 构建前端项目...${NC}"
if [ ! -d "web-ui" ]; then
    echo -e "${RED}✗ 错误: web-ui 目录不存在${NC}"
    exit 1
fi

cd web-ui

# 检查 node_modules 是否存在
if [ ! -d "node_modules" ]; then
    echo "首次运行，正在安装前端依赖..."
    npm install
fi

echo "正在构建前端..."
npm run build

if [ ! -d "dist" ]; then
    echo -e "${RED}✗ 错误: 前端构建失败，dist 目录未生成${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 前端构建完成${NC}"

# 4. 复制构建产物到项目根目录
echo -e "\n${YELLOW}[4/5] 复制构建产物...${NC}"
cd "$SCRIPT_DIR"
cp -r web-ui/dist ./
echo -e "${GREEN}✓ 构建产物已复制到项目根目录${NC}"

# 5. 启动后端服务
echo -e "\n${YELLOW}[5/5] 启动后端服务...${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}服务启动中...${NC}"
echo -e "${GREEN}访问地址: http://localhost:8000${NC}"
echo -e "${GREEN}API 文档: http://localhost:8000/docs${NC}"
echo -e "${GREEN}========================================${NC}\n"

python -m src.app
