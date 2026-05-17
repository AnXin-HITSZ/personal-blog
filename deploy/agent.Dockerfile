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

# 入口脚本：按需下载模型后启动服务（避免模型打包到镜像中）
COPY deploy/agent-entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

CMD ["/app/entrypoint.sh"]
