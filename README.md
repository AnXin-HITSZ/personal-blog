# AnXin Personal Blog

一个**三端分离**的个人博客系统，集成了 AI Agent 智能问答与自动化 CI/CD 部署能力。

---

## 版本

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0.0 | - | 初始版本：基础博客 + RAG Agent + CI/CD |
| **v1.0.1** | 2026-05-16 | **重排性能优化：INT8 动态量化 + 线程控制** |

---

## 项目概述 (STAR 法则)

### Situation（背景）

作为个人技术探索的实践项目，需要一个既能展示技术文章内容、又能体现 AI 工程能力的综合平台。目标是构建一个真正可用的生产级系统，将传统的博客内容管理与前沿的 AI 技术（RAG、Agent、自动化运维）有机结合。

### Task（任务）

设计并实现一个三端分离的个人博客系统：
- **内容管理**: 支持 Markdown 文章的 CRUD、语法高亮渲染
- **AI 智能问答**: 基于 RAG 技术，让读者能对博客内容进行自然语言提问
- **自动化部署**: 通过 AI Agent 驱动 CI/CD 流水线，实现一键部署与自修复
- **知识管理**: 支持文档上传、自动分块索引、语义检索

### Action（行动）

采用 **Vue 3 + Spring Boot + FastAPI** 三端分离架构：

1. **前端**: Vue 3 + TypeScript + Element Plus，SPA 单页应用，SSE 流式对话
2. **后端**: Spring Boot + MyBatis-Plus + JWT 鉴权，提供 RESTful API
3. **Agent 微服务**: FastAPI + LangGraph，集成 RAG 流水线、三层记忆系统、Skill 热插拔
4. **基础设施**: MySQL + Redis + Qdrant(向量库) + Docker Compose 6 服务编排

### Result（结果）

- 生产可用的个人博客系统，支持文章管理、用户系统、AI 问答
- RAG 问答准确率通过 Cross-Encoder 重排（INT8 量化 + 线程优化）保障
- Agent 驱动的 CI/CD 流水线（Plan-Execute-Replan），含自修复和人工审批
- 完整的 Docker 容器化部署，6 服务一键启动

---

## 核心功能

- **📝 文章管理**: Markdown 文章 CRUD，语法高亮渲染
- **🔐 用户系统**: 注册/登录，JWT 鉴权，管理员角色
- **🤖 AI 问答**: 基于 RAG 的智能对话，SSE 流式输出
- **🧠 记忆系统**: 三层架构（会话历史 → 摘要压缩 → 跨会话语义记忆）
- **🔧 Skill 热插拔**: 运行时启用/禁用 RAG/Time/MCP 能力
- **🚀 CI/CD 流水线**: Agent 驱动的 Plan-Execute-Replan 自动部署，含自修复和人工审批
- **📊 知识库管理**: 拖拽上传文档，自动分块索引

---

## 系统架构

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   Vue 3 SPA  │ ──> │ Spring Boot  │ ──> │ FastAPI Agent│
│  (Frontend)  │     │  (Backend)   │     │  (Microsvc)  │
└─────────────┘     └──────────────┘     └──────┬───────┘
       ▲                     ▲                   │
       │                     │              ┌────┴────┐
       └──────────┬──────────┘              │  Redis  │
                  │                         │ Qdrant  │
            ┌─────┴─────┐                  │ DeepSeek│
            │   Nginx   │                   └─────────┘
            │  (反向代理)│
            └───────────┘
```

### 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 前端 | Vue 3 + TypeScript + Vite | 3.5 / 5.7 / 6 |
| 前端 UI | Element Plus + Tailwind CSS | 2.9 / 3.4 |
| 后端 | Spring Boot + MyBatis-Plus | 4.0.6 / 3.5.15 |
| 后端安全 | Spring Security + JWT (Hutool) | - |
| 数据库 | MySQL 8.0 | - |
| Agent 框架 | FastAPI + LangGraph | 0.136 / 1.2 |
| 向量库 | Qdrant | 1.12 |
| 向量嵌入 | DashScope text-embedding-v4 | 1024 维 |
| 重排模型 | BGE-Reranker-v2-M3 | INT8 量化 |
| LLM | Qwen-Plus / DeepSeek | OpenAI 兼容 |
| 对话记忆 | Redis | 会话 + 语义记忆 |
| CI/CD | Docker Compose | 自动部署 6 服务 |

---

## 项目结构

```
personal-blog/
├── frontend/          # Vue 3 SPA
│   ├── src/
│   │   ├── views/          # 页面组件 (Home/Qa/Login/Admin等)
│   │   ├── api/            # Axios API 模块
│   │   ├── router/         # 路由配置
│   │   └── stores/         # Pinia 状态管理
│   └── ...
├── backend/           # Spring Boot
│   └── src/main/java/com/anxin_hitsz/
│       ├── controller/     # REST API 控制器
│       ├── service/        # 业务逻辑
│       ├── entity/         # JPA 实体 (User, Article)
│       ├── config/         # Security, JWT 配置
│       └── utils/          # 工具类
├── agent/             # FastAPI Agent 微服务
│   └── app/
│       ├── api/            # API 路由 (chat/rag/file/skill/deploy)
│       ├── services/       # 核心服务 (RAG/记忆/重排/CI/CD)
│       ├── core/           # 基础设施 (Qdrant/Redis/SkillRegistry)
│       ├── agent/          # LangGraph Agent (CI/CD节点/工具)
│       └── models/         # Pydantic 数据模型
└── deploy/            # 部署配置
    ├── docker-compose.yml  # 6 服务编排
    ├── nginx/              # Nginx 配置
    └── init.sql            # 数据库初始化
```

---

## 部署方式

### 前置条件

- Docker & Docker Compose
- Git
- 至少 4GB 内存，20GB 磁盘

### 快速部署

```bash
# 1. 克隆项目
git clone https://github.com/your-username/personal-blog.git
cd personal-blog

# 2. 配置环境变量
cp deploy/.env.example deploy/.env
# 编辑 deploy/.env，填写必要的密钥和 API Key

# 3. 一键部署
bash deploy/deploy.sh
```

### 环境变量说明

| 变量 | 必填 | 说明 |
|------|:---:|------|
| `JWT_SECRET_KEY` | ✅ | JWT 签名密钥 |
| `MYSQL_ROOT_PASSWORD` | ✅ | 数据库密码 |
| `LLM_API_KEY` | ✅ | LLM API Key (DeepSeek/Qwen) |
| `LLM_BASE_URL` | ✅ | LLM API 地址 |
| `DASHSCOPE_API_KEY` | ✅ | 向量嵌入 API Key |
| `DASHSCOPE_EMBEDDING_MODEL` | - | 嵌入模型名 (默认 text-embedding-v4) |

### 服务架构 (Docker)

| 服务 | 端口 | 说明 |
|------|:----:|------|
| Nginx | 80 | 前端静态资源 + API 反向代理 |
| Spring Boot | 8080 | 后端 API 服务 |
| FastAPI Agent | 8000 | AI Agent 微服务 |
| MySQL | 3306 | 持久化数据库 |
| Redis | 6379 | 缓存与对话记忆 |
| Qdrant | 6333 | 向量数据库 |

### 增量更新（推荐）

仅在代码变更后更新特定服务，避免全量重建：

```bash
# 1. 拉取最新代码
git fetch origin && git reset --hard origin/main

# 2. 只重建改动的服务（比 deploy.sh 快数倍）
cd deploy
docker compose up -d --build agent     # 仅 Agent 服务
docker compose up -d --build backend   # 仅后端
docker compose up -d --build frontend  # 仅前端
```

---

## 性能优化 (v1.0.1)

### 优化背景

在 RAG 流水线中，**BGE-Reranker-v2-M3**（568M 参数）作为 Cross-Encoder 对召回结果进行重排，确保检索质量。但重排阶段在 CPU 上推理延迟极高，且 PyTorch 占满所有 CPU 核心导致系统严重卡顿。

### 优化指标

| 指标 | 优化前 (v1.0.0) | 优化后 (v1.0.1) | 提升 |
|------|:---:|:---:|:---:|
| **重排推理延迟** (15 文档) | 22.88s | **14.20s** | **1.6x 加速** |
| **CPU 占用率** | 100% (20 核满载) | **~20%** (4 核) | **5x 降低** |
| **系统卡顿** | 笔记本电脑明显卡顿 | **后台流畅运行** | ✅ 消除 |
| **检索质量** | baseline | ≥99% baseline | ✅ 无损 |

### 优化内容

#### INT8 动态量化

对 HuggingFace 模型应用 PyTorch 动态量化，将 Linear 层权重精度从 FP32 降为 INT8：

```python
torch.quantization.quantize_dynamic(
    model.model,
    {torch.nn.Linear},
    dtype=torch.qint8,
    inplace=True,
)
```

**特点**: 精度损失 < 1%，无需校准数据，一行代码即插即用。

#### 线程数控制

```python
torch.set_num_threads(4)  # 从 20 → 4
```

同时限制 `OMP_NUM_THREADS` / `MKL_NUM_THREADS` / `OPENBLAS_NUM_THREADS` 环境变量。实测 4 线程是平衡点：推理速度与满线程基本持平，CPU 占用仅 20%。

#### 性能统计器

内置 `RerankTimingStats` 自动记录每次推理的延迟，在日志中输出 avg/min/max 指标：

```log
重排统计: 2 次调用 | 平均 14557ms | 最小 14203ms | 最大 14911ms | 吞吐 ~1.0 docs/s
```

### 基准测试

| 配置 | 推理耗时 | 相对提升 |
|:---|:---:|:---:|
| FP32 + 满线程 (20核) | 1.96s | baseline |
| FP32 + 4 线程 | 3.52s | 0.56x |
| **INT8 + 4 线程** | **1.40s** | **1.40x** ⬅ 最佳配置 |
| INT8 + 2 线程 | 2.39s | 0.82x |

---

## 许可

MIT License
