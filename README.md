# fastapi-fullstack-skill

FastAPI + Vue 模块化全栈脚手架模板。AI 驱动的项目生成器，一条指令生成生产级项目骨架。

## 安装

```bash
npx skills add digitallattice2023/fastapi-fullstack-skill
```

安装后获得 4 个 skills：

| Skill | 职责 |
|-------|------|
| **fullstack-starter** | 全栈统一生成器（推荐入口，一次生成后端+前端） |
| **backend-fastapi-starter** | 后端项目初始化（可独立使用） |
| **frontend-vue-starter** | 前端项目初始化（可独立使用） |
| **backend-dev-guide** | 后端开发规范（Feature Manifest 架构、分层约定等开发指导） |

## 使用

在 Claude Code 对话中描述你的需求即可触发，例如：

- "帮我创建一个 FastAPI 后端项目"
- "生成一个 Vue 前端，连接后端 API"
- "我要做一个全栈项目"

AI 会自动匹配对应的 skill，引导你选择功能模块并生成项目。

**推荐流程**：直接说"我要创建一个全栈项目"，触发 `fullstack-starter`，一次选择所有需要的模块。

## 生成的项目结构

```
<项目目录>/
├── backend/                  # 后端项目
│   ├── app/
│   │   ├── main.py           # 入口：自动路由注册
│   │   ├── core/             # 配置、数据库、Redis
│   │   ├── shared/           # 通用工具、模型、健康检查
│   │   └── features/         # 按业务领域划分的模块
│   │       └── auth/         # 示例：auth 模块
│   │           ├── manifest.py
│   │           ├── router.py
│   │           ├── models.py
│   │           └── service/
│   ├── alembic/              # 数据库迁移
│   ├── .env                  # 环境变量
│   ├── docker-compose.yml    # 服务编排
│   └── pyproject.toml        # 依赖管理
└── frontend/                 # 前端项目
    ├── src/
    │   ├── views/            # 页面
    │   ├── stores/           # Pinia 状态管理
    │   └── components/       # 组件
    ├── package.json
    └── vite.config.ts
```

## 可选功能模块（后端）

| 模块 | 说明 | 依赖 |
|------|------|------|
| `auth` | JWT 认证（登录/注册/密码重置） | 无 |
| `admin` | SQLAdmin 管理面板（可独立使用，搭配 auth 启用 JWT 保护） | 无 |
| `redis` | 缓存层 + Celery 消息代理 | 无 |
| `celery` | 异步任务队列 + Beat 调度器 | redis |
| `storage` | 对象存储（Cloudflare R2 / AWS S3） | 无 |
| `email` | 邮件服务（Resend） | 无 |
| `radar` | HTTP 监控面板（`/__radar`） | 无 |

## 生成项目后的开发

项目生成后，`backend/` 目录的 `.claude/skills/` 下自动包含以下辅助 skill：

| Skill | 触发场景 | 作用 |
|-------|----------|------|
| `/feature <name>` | "创建 XX 模块" | 生成符合规范的 feature 骨架（manifest + router + models + service） |
| `/bootstrap` | "启动项目" | uv lock → docker compose up → 迁移 → 状态报告 |
| `/project-status` | "项目状态" | 输出已启用模块、API 路由、健康检查、容器状态 |

## 技术栈

- **后端**：Python 3.12 | FastAPI | SQLModel | Pydantic v2 | uv | asyncpg | redis.asyncio | celery | alembic | loguru
- **前端**：Vue 3 | Vite | TypeScript | Pinia | Tailwind CSS
- **部署**：Docker Compose | PostgreSQL | Redis
