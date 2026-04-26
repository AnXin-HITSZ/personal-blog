# ============================================
# Agent - FastAPI Python 服务
# ============================================
FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装
COPY agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY agent/ .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
