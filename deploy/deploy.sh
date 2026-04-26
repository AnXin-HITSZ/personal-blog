#!/bin/bash
# ============================================
# Personal Blog 部署脚本
# 使用方法:
#   1. 复制 .env.example 为 .env 并填入真实配置
#   2. 在项目根目录运行: bash deploy/deploy.sh
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "========================================"
echo " Personal Blog 部署脚本"
echo "========================================"

cd "$PROJECT_DIR"

# ----- Step 1: 检查环境变量 -----
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo "[!] 未找到 .env 文件，正在从 .env.example 创建..."
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
    echo "[!] 请编辑 deploy/.env 文件，填入实际的配置值，然后重新运行此脚本"
    exit 1
fi

echo "[✓] 已加载 .env 文件"

# ----- Step 2: 构建前端 -----
echo ""
echo "[1/3] 构建前端..."

cd "$PROJECT_DIR/frontend"
npm install --frozen-lockfile 2>/dev/null || npm install

# 使用 vue-tsc 进行类型检查，失败时回退到纯 vite build
npx vue-tsc --noEmit 2>/dev/null && npx vite build || npx vite build
echo "[✓] 前端构建完成"

# ----- Step 3: 启动 Docker 服务 -----
echo ""
echo "[2/3] 启动 Docker 服务..."

cd "$PROJECT_DIR/deploy"
docker compose --env-file .env down 2>/dev/null || true
docker compose --env-file .env up -d --build
echo "[✓] Docker 服务已启动"

# ----- Step 4: 检查服务状态 -----
echo ""
echo "[3/3] 检查服务状态..."
sleep 5

echo ""
echo "========================================"
echo " 服务部署完成！"
echo "========================================"
echo ""
echo "服务访问地址:"
echo "  - 前端:      http://3.135.60.136"
echo "  - 后端 API:  http://3.135.60.136/api/"
echo "  - Agent API: http://3.135.60.136/api/agent/"
echo ""
echo "Docker 服务状态:"
docker compose ps
echo ""
echo "查看日志:"
echo "  docker compose logs -f backend"
echo "  docker compose logs -f agent"
echo "  docker compose logs -f nginx"
