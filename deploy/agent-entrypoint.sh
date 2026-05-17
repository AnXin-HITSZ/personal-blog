#!/bin/bash
# ============================================
# Agent 容器入口点
# 1. 按需下载重排模型（避免打包到镜像中）
# 2. 启动 uvicorn
# ============================================

set -e

MODEL_DIR=".model_cache/BAAI/bge-reranker-v2-m3"
MODEL_NAME="BAAI/bge-reranker-v2-m3"

# 检查模型是否已存在
if [ ! -f "$MODEL_DIR/model.safetensors" ] && [ ! -f "$MODEL_DIR/pytorch_model.bin" ]; then
    echo "============================================"
    echo " 重排模型未检测到，正在下载..."
    echo " 模型: $MODEL_NAME"
    echo " 目标: $MODEL_DIR"
    echo "============================================"

    pip install modelscope --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple

    python -c "
from modelscope.hub.snapshot_download import snapshot_download
import os
os.makedirs('$MODEL_DIR', exist_ok=True)
snapshot_download('$MODEL_NAME', local_dir='$MODEL_DIR')
print('模型下载完成')
"

    pip uninstall modelscope -y
    rm -rf /root/.cache/modelscope
    echo "============================================"
    echo " 模型下载完成"
    echo "============================================"
else
    echo "模型已存在，跳过下载"
fi

# 启动应用
echo "启动 Agent 服务..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
