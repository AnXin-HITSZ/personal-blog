#!/bin/bash
# ============================================
# Personal Blog 部署脚本（全 Docker 方案）
# 使用方法:
#   1. 将项目上传到服务器
#   2. 在 deploy/ 目录下创建 .env 文件（参考 .env.example）
#   3. 在项目根目录运行: bash deploy/deploy.sh
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
    echo ""
    echo "请编辑 deploy/.env 文件，填入实际的配置值："
    echo "  - JWT_SECRET_KEY (必填)"
    echo "  - LLM_MODEL_ID, LLM_API_KEY, LLM_BASE_URL (必填，Agent 用)"
    echo "然后重新运行此脚本。"
    exit 1
fi

echo "[✓] 已加载 .env 文件"

# ----- Step 2: 检查 Docker -----
if ! command -v docker &> /dev/null; then
    echo "[✗] 未安装 Docker，请先安装 Docker"
    echo "  参考: https://docs.docker.com/engine/install/"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo "[✗] 未安装 Docker Compose，请先安装"
    exit 1
fi

echo "[✓] Docker: $(docker --version)"
echo "[✓] Compose: $(docker compose version --short 2>/dev/null || echo 'ok')"

# ----- Step 3: 停止旧服务 -----
echo ""
echo "[1/3] 停止旧服务..."
cd "$SCRIPT_DIR"
docker compose --env-file .env down 2>/dev/null || true
echo "[✓] 旧服务已停止"

# ----- Step 4: 构建并启动新服务 -----
echo ""
echo "[2/3] 构建并启动 Docker 服务..."
docker compose --env-file .env up -d --build
echo "[✓] Docker 服务已启动"

# ----- Step 5: 检查服务状态 -----
echo ""
echo "[3/3] 检查服务状态..."
sleep 8

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
echo "  docker compose logs -f frontend"
echo ""
echo "常用命令:"
echo "  重启服务:   docker compose restart"
echo "  停止服务:   docker compose down"
echo "  更新服务:   git pull && docker compose up -d --build"
