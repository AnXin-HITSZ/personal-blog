# ============================================
# Agent - FastAPI Python 服务
# ============================================
FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖（含 git 用于部署流水线）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装
# 使用国内 PyPI 镜像（清华）加速下载，同时设置重试和超时应对网络波动
COPY agent/requirements.txt .
RUN pip install --no-cache-dir \
    --retries 5 \
    --default-timeout=120 \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    -r requirements.txt

# 复制应用代码
COPY agent/ .

# 设置 HuggingFace 镜像站（运行时降级使用）
ENV HF_ENDPOINT=https://hf-mirror.com

# 构建时通过阿里云 ModelScope 预下载重排模型（国内网络友好）
RUN pip install modelscope --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    python -c "from modelscope.hub.snapshot_download import snapshot_download; snapshot_download('BAAI/bge-reranker-v2-m3', local_dir='.model_cache/BAAI/bge-reranker-v2-m3')" && \
    echo "Model downloaded successfully from ModelScope" && \
    pip uninstall modelscope -y && \
    rm -rf /root/.cache/modelscope

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
