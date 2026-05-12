# ============================================
# Stage 1: 构建前端
# ============================================
FROM node:20-alpine AS builder

WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .
RUN npx vite build

# ============================================
# Stage 2: Nginx 服务（静态文件 + 反向代理）
# ============================================
FROM nginx:alpine

# 前端静态文件
COPY --from=builder /build/dist /usr/share/nginx/html

# Nginx 配置
COPY deploy/nginx/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
