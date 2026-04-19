---
name: fullstack-starter
description: >
  FastAPI + Vue 全栈项目脚手架。统一入口生成后端、前端或全栈项目。
  Triggers when: user wants to create a fullstack project, both backend and frontend,
  or isn't sure which part they need yet.
---

# FastAPI + Vue 全栈项目脚手架

统一编排器 Skill。不直接生成任何文件，根据用户选择委托给现有 Copier 模板：
- 后端模板：`../backend-fastapi-starter/template`
- 前端模板：`../frontend-vue-starter/template`

## 核心原则

- **Skill 负责**：环境检查、参数收集、Copier 调度、生成后审查
- **Copier 负责**：文件生成、条件分支、模板渲染
- **不重复模板文件**：两个子 skill 的模板保持独立，本 skill 仅做编排

## 工作流

### Phase 0: 环境校验

根据用户最终选择的项目类型按需检查：

```bash
# 后端或全栈模式
docker --version
uv --version

# 前端或全栈模式
node --version
```

如缺失，引导用户安装。

### Phase 1: 项目类型选择

**AskUserQuestion**：
- header: "项目类型"
- multiSelect: true
- 问题: "请选择要生成的项目类型（可多选，同时选中即为全栈模式）"
- options:
  - label: "后端" / description: "FastAPI 模块化后端（API + 数据库 + 可选功能模块）"
  - label: "前端" / description: "Vue 3 + Vite + TypeScript + Pinia + Tailwind"
- 默认都不勾选

**模式判定**：
- 只选"后端" → backend-only 模式
- 只选"前端" → frontend-only 模式
- 两者都选 → fullstack 模式

### Phase 2: 参数收集

#### 2.1 共享参数（所有模式）

**AskUserQuestion**：
- header: "项目名称"
- multiSelect: false
- 问题: "请输入项目名称"
- 用户通过 Other 输入，不填则默认 "myapp"

其余参数使用默认值：
- project_description: "myapp 全栈应用"
- project_version: "0.1.0"
- author_name: "Dev Team"
- author_email: "dev@example.com"

#### 2.2 后端参数（backend-only 或 fullstack 模式）

**第一轮功能选择 AskUserQuestion**（基础架构）：
- header: "基础架构"
- multiSelect: true
- 问题: "请选择要启用的基础架构模块"
- options:
  - label: "auth" / description: "JWT 认证（登录/注册/密码重置/管理员初始化）"
  - label: "redis" / description: "缓存层 + Celery 消息代理"
  - label: "celery" / description: "异步任务队列 + Beat 调度器（自动启用 redis）"
  - label: "都不需要" / description: "跳过基础架构模块"

**第二轮功能选择 AskUserQuestion**（外部服务）：
- header: "外部服务"
- multiSelect: true
- 问题: "请选择要集成的外部服务"
- options:
  - label: "storage" / description: "对象存储（Cloudflare R2 / AWS S3）"
  - label: "email" / description: "邮件服务（Resend）"
  - label: "都不需要" / description: "跳过外部服务"

**第三轮功能选择 AskUserQuestion**（辅助工具）：
- header: "辅助工具"
- multiSelect: true
- 问题: "请选择要启用的辅助工具"
- options:
  - label: "admin" / description: "SQLAdmin 管理面板（数据库可视化增删改查）"
  - label: "radar" / description: "HTTP 监控面板（/__radar 性能/路由/健康监控）"
  - label: "都不需要" / description: "跳过辅助工具"

**模块合并**：将三轮选择的模块合并为最终 `features` 列表（排除"都不需要"选项）。

**依赖自动解析**（Claude 自动处理）：
- 选了 celery → 自动在 Copier data 中加 redis

**条件配置**（仅在选了 auth 时问）：
- header: "Auth 配置"
- 管理员邮箱（默认 "admin@example.com"）
- 管理员密码（默认 "changeme"）
- JWT 密钥（默认 "dev-secret-key-change-in-production"）

**数据库配置**（使用默认值，不额外询问）：
- db_name: "{{ project_slug }}"
- db_port: 5434
- db_user: "postgres"
- db_password: "postgres"
- api_host_port: 8002
- redis_host_port: 6381（仅在选了 redis 或 celery 时需要）

**国内镜像源**：Claude 自动判断网络环境，设置 `use_china_mirrors: true`（国内）或 `false`（海外）。

#### 2.3 前端参数（frontend-only 或 fullstack 模式）

**AskUserQuestion**（仅 frontend-only 模式需要）：
- 是否有后端：否（默认），frontend-only 模式默认 false
- 后端 API URL：仅在 has_backend=true 时询问，默认 "http://localhost:8002"

**fullstack 模式自动推断**：
- has_backend: true
- backend_api_url: "http://localhost:{api_host_port}"（从后端参数中获取端口）

### Phase 3: Copier 执行

获取当前 skill 所在目录，计算后端和前端模板路径。
`dst_path` 始终设为当前工作目录 `.`，模板的 `_subdirectory: project` 会在当前目录直接生成 `backend/` 和 `frontend/`，无需额外嵌套项目名目录。

```python
from copier import run_copy
import os

# 当前 skill 目录路径（用于计算相对路径）
skill_dir = os.path.dirname(__file__)  # 或由 Claude 推断当前文件路径
backend_template = os.path.join(skill_dir, "..", "backend-fastapi-starter", "template")
frontend_template = os.path.join(skill_dir, "..", "frontend-vue-starter", "template")
# 当前工作目录（用户在执行 skill 时所在的目录）
target_dir = "."
```

**后端 Copier 调用**（backend-only 或 fullstack）：
```python
run_copy(
    src_path=backend_template,
    dst_path=target_dir,
    data={
        "project_name": "<值>",
        "project_description": "<值>",
        "project_version": "0.1.0",
        "author_name": "<值>",
        "author_email": "<值>",
        "use_china_mirrors": True,
        "features": ["<选中的模块>", ...],
        "db_name": "<值>",
        "db_port": 5434,
        "db_user": "postgres",
        "db_password": "postgres",
        "api_host_port": 8002,
        # 如果选了 auth:
        # "admin_email": "<值>",
        # "admin_password": "<值>",
        # "secret_key": "<值>",
        # 如果选了 celery:
        # "celery_concurrency": 4,
        # 如果选了 email:
        # "resend_api_key": "re_xxx",
        # "resend_from_email": "noreply@example.com",
        # 如果选了 storage:
        # "r2_endpoint_url": "...",
        # "r2_bucket_name": "...",
        # "r2_access_key_id": "...",
        # "r2_secret_access_key": "...",
        # 如果选了 redis/celery:
        # "redis_host_port": 6381,
    },
    unsafe=True,
    defaults=True,    # 跳过交互式 prompt（Windows 终端兼容）
)
```

**前端 Copier 调用**（frontend-only 或 fullstack）：
```python
run_copy(
    src_path=frontend_template,
    dst_path=target_dir,
    data={
        "project_name": "<值>",
        "project_description": "<值>",
        "has_backend": True,          # fullstack 模式
        "backend_api_url": "<值>",    # fullstack 模式自动填入
    },
    unsafe=True,
    defaults=True,    # 跳过交互式 prompt（Windows 终端兼容）
)
```

**⚠️ Windows 兼容注意**：Copier 在 Windows 下遇到缺失参数时会尝试打开交互式 prompt 导致报错。必须传 `defaults=True` 并使用 `unsafe=True` 确保所有参数由 `data` 字典提供，不触发 fallback 交互。

**部分失败处理**：
- 如果后端成功但前端失败：告知用户前端生成失败，可单独重新运行前端 Copier
- 如果前端成功但后端失败：同上

### Phase 4: 生成后审查

1. 展示生成的文件树
   - backend-only: 仅展示 `backend/`
   - frontend-only: 仅展示 `frontend/`
   - fullstack: 展示 `backend/` 和 `frontend/`
2. 展示 `.copier-answers.yml` 确认参数
3. 提醒用户修改 `.env` 中的占位符凭据

### Phase 5: 安装 & 启动

**后端**（backend-only 或 fullstack）：
```bash
cd <目标目录>/backend
uv lock
docker compose up -d
```
轮询 `/health` 端点直到所有服务 healthy（最多 60 秒）。

**前端**（frontend-only 或 fullstack）：
```bash
cd <目标目录>/frontend
npm install
npm run dev
```

### Phase 6: 状态报告

**后端服务**（如果启用了后端）：
- API: `http://localhost:<api_host_port>/`
- Swagger: `http://localhost:<api_host_port>/docs`
- Admin: `http://localhost:<api_host_port>/admin`（如果启用 auth 或 admin）
- Health: `http://localhost:<api_host_port>/health`

**前端服务**（如果启用了前端）：
- Dev Server: `http://localhost:5173`

## 模板位置

Copier 模板位于 skill 目录下的相对路径：
- 后端模板：`<本skill目录>/../backend-fastapi-starter/template/`
- 前端模板：`<本skill目录>/../frontend-vue-starter/template/`

**不要手动创建任何项目文件**，所有文件由 Copier 模板生成。

## 后续添加功能

用户想给已有项目添加新功能时：

```bash
# 更新后端
cd <项目目录>/backend
copier update

# 更新前端
cd <项目目录>/frontend
copier update
```

每个子项目有独立的 `.copier-answers.yml`，需要分别运行 `copier update`。
