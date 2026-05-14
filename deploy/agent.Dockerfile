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

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
