# CLAUDE.md

本文档为 Claude Code 提供 FastAPI 全栈模板仓库的开发指南。

## 项目概况

FastAPI + Vue 模块化全栈脚手架模板仓库

通过 `npx skills add digitallattice2023/fastapi-fullstack-skill` 安装以下 skills：
- **fullstack-starter** — FastAPI + Vue 全栈统一生成器（推荐，一次生成后端+前端）
- **backend-fastapi-starter** — FastAPI 模块化后端生成器（Copier 模板，可独立使用）
- **frontend-vue-starter** — Vue 3 + Vite + TS + Pinia + Tailwind 前端生成器（Copier 模板，可独立使用）

生成后的项目结构：
```
<项目目录>/
├── backend/                  # 后端项目（由 backend-fastapi-starter 生成）
│   ├── app/
│   ├── alembic/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── pyproject.toml
└── frontend/                 # 前端项目（由 frontend-vue-starter 生成）
    ├── src/
    ├── package.json
    └── vite.config.ts
```

## 仓库结构

```
skills/
├── fullstack-starter/           # 全栈统一生成器（推荐入口）
│   ├── skill.md
│   └── template/                # 占位目录
├── backend-fastapi-starter/     # 后端 skill（可独立使用）
│   ├── skill.md
│   └── template/
│       ├── copier.yml
│       └── project/
│           └── backend/         # 后端模板文件
└── frontend-vue-starter/        # 前端 skill（可独立使用）
    ├── skill.md
    └── template/
        ├── copier.yml
        └── project/
            └── frontend/        # 前端模板文件
```

## Skills 开发约定

### Copier 模板
- 使用 `_subdirectory: project` 作为模板根
- 模板文件使用 `.jinja` 后缀
- 条件文件使用 Jinja2 语法：`{% if 'auth' in features %}name{% endif %}.py`

## Skill 工作流

### fullstack-starter（推荐）
- 统一入口：用户只需触发一次 skill
- 支持三种模式：仅后端、仅前端、全栈（同时生成）
- 全栈模式下自动联动前后端参数（如后端端口 → 前端 API URL）

### backend-fastapi-starter
- Skill 不直接生成文件，所有文件生成由 Copier 负责
- Skill 负责：环境检查、收集用户参数、调用 Copier、生成后审查

### 后端 skill (backend-fastapi-starter)
- Feature-based 架构，按业务领域划分代码
- 支持模块：auth, admin, redis, celery, storage, email, radar
- Feature Manifest 模式自动发现路由/任务/模型

### 前端 skill (frontend-vue-starter)
- 技术栈固定：Vue 3 + Vite + TypeScript + Pinia + Tailwind CSS
- 初始化成功页面（WelcomePage.vue）支持纯前端/全栈两种模式
- 全栈模式下自动调用后端 /health 接口检测连通性

## 服务端口
- FastAPI API: `8002`（容器内 `8000`）
- PostgreSQL: `5434`（容器内 `5432`）
- Redis: `6381`（容器内 `6379`）
- Vite Dev Server: `5173`
