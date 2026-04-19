---
name: backend-fastapi-starter
description: >
  Interactive modular backend project generator for FastAPI base templates.
  Uses Copier for deterministic file generation (NOT manual file creation).
  Triggers when: user wants to scaffold a new FastAPI backend project,
  select modules for a backend, set up Celery/Redis/Auth/R2/Email,
  or initialize a new feature-based FastAPI backend.
---

# FastAPI 后端项目脚手架

通过 Copier 模板确定性生成 FastAPI 后端项目。**Skill 不直接生成任何文件**，所有文件生成由 Copier 负责。

生成的后端项目位于 `backend/` 目录下，可与前端项目并存于同一仓库。

## 核心原则

- **确定性的事交给代码**：文件生成、条件分支、依赖解析 → Copier (Jinja2)
- **创造性的事交给 Claude**：用户交互、环境检查、定制建议 → Skill

## 工作流

### Step 0: 环境校验

执行前检查必要工具是否安装：

```bash
docker --version    # 容器编排（必需）
uv --version        # 依赖管理（必需）
```

如缺失，引导用户安装：
- Docker Desktop: https://www.docker.com/products/docker-desktop/
- uv: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`

### Step 1: 收集项目参数（必须使用 AskUserQuestion）

**⚠️ 必须按顺序调用 AskUserQuestion 工具收集以下信息，不得跳过或硬编码默认值。**

**第一轮 AskUserQuestion**（项目身份）：
- header: "项目名称"
- multiSelect: false
- 问题: "请输入后端项目名称"
- options:
  - label: "自定义名称" / description: "输入项目名称，其余参数使用默认值（描述=FastAPI 后端应用, 作者=Dev Team, 邮箱=dev@example.com）"
- 用户通过 Other 选项输入自定义名称，不填则使用默认值 "myapp"

**国内镜像源确认**（Claude 自动判断，不需要用户知道）：
- 检测用户网络环境（尝试 ping docker.io 或 pypi.org）
- 如果在国内环境，自动设置 `use_china_mirrors: true`
- 如果用户明确指定，则按用户意愿设置
- 默认值: `true`（国内环境）

**第二轮 AskUserQuestion**（基础架构）：
- header: "基础架构"
- multiSelect: true
- 问题: "请选择要启用的基础架构模块"
- options:
  - label: "auth" / description: "JWT 认证（登录/注册/密码重置/管理员初始化）"
  - label: "redis" / description: "缓存层 + Celery 消息代理"
  - label: "celery" / description: "异步任务队列 + Beat 调度器（自动启用 redis）"
  - label: "都不需要" / description: "跳过基础架构模块"

**第三轮 AskUserQuestion**（外部服务）：
- header: "外部服务"
- multiSelect: true
- 问题: "请选择要集成的外部服务"
- options:
  - label: "storage" / description: "对象存储（Cloudflare R2 / AWS S3）"
  - label: "email" / description: "邮件服务（Resend）"
  - label: "都不需要" / description: "跳过外部服务"

**第四轮 AskUserQuestion**（辅助工具）：
- header: "辅助工具"
- multiSelect: true
- 问题: "请选择要启用的辅助工具"
- options:
  - label: "admin" / description: "SQLAdmin 管理面板（数据库可视化增删改查）"
  - label: "radar" / description: "HTTP 监控面板（/__radar 性能/路由/健康监控）"
  - label: "都不需要" / description: "跳过辅助工具"

**模块合并**：将三轮选择的模块合并为最终 `features` 列表（排除"都不需要"选项）。

**依赖自动解析**（Claude 自动处理，不需要用户知道）：
- 选了 celery → 自动在 Copier data 中加 redis
- 选了 email → 提醒用户考虑加 redis（非强制）

**第五轮 AskUserQuestion**（条件触发，仅当用户选了 auth）：
- header: "Auth 配置"
- multiSelect: false
- 问题: "请配置初始管理员账户"
- options:
  - 管理员邮箱（默认 "admin@example.com"）
  - 管理员密码（默认 "changeme"）
  - JWT 密钥（默认 "dev-secret-key-change-in-production"）

### Step 2: 调用 Copier 生成项目

使用 Copier Python API（预填答案，无需二次交互）：

```python
from copier import run_copy

run_copy(
    src_path="<skill目录>/template",
    dst_path="<用户指定的目标目录>",
    data={
        "project_name": "<用户输入>",
        "project_description": "<用户输入>",
        "author_name": "<用户输入>",
        "author_email": "<用户输入>",
        "use_china_mirrors": True,  # 国内环境默认 true
        "features": ["<用户选中的模块>", ...],
        # 如果选了 auth，额外传入:
        # "admin_email": "<值>",
        # "admin_password": "<值>",
        # "secret_key": "<值>",
    },
    unsafe=True,
)
```

如果用户偏好交互式问答，也可使用 CLI：
```bash
copier run "<skill目录>/template" "<目标目录>"
```

### Step 3: 生成后审查

生成完成后：
1. 展示生成的文件列表
2. 提醒用户修改 `.env` 中的占位符凭据（SECRET_KEY、ADMIN_PASSWORD、R2 凭据等）
3. 展示 `.copier-answers.yml` 确认所有参数

### Step 4: 安装 & 启动

```bash
cd <目标目录>/backend
uv lock
docker compose up -d
```

轮询 `/health` 端点直到所有服务 healthy（最多 60 秒）。

### Step 5: 状态报告

展示给用户：
- API: `http://localhost:<api_host_port>/`
- Swagger: `http://localhost:<api_host_port>/docs`
- Admin: `http://localhost:<api_host_port>/admin`（如果启用 auth）
- Health: `http://localhost:<api_host_port>/health`
- 服务状态表（从 /health 解析）

## 模板位置

Copier 模板位于 skill 目录下的 `template/` 子目录中：
`<skill目录>/template/`

模板是项目生成的唯一权威来源。**不要手动创建任何项目文件**。

## 后续添加功能

用户想给已有项目添加新功能时：

```bash
cd <已有项目目录>
copier update
```

Copier 通过 `.copier-answers.yml` 记住之前的选择，3-way merge 保留用户代码。

## Feature Manifest 模式

生成的项目中，每个 feature 目录下包含 `manifest.py`，统一声明：
- `router_module` / `router_prefix` / `router_tags` — 路由注册
- `tasks_package` / `beat_schedule` — Celery 任务
- `models_module` — 数据库模型（alembic 自动导入）
- `admin_views_module` — Admin 视图
- `health_checks` — 健康检查

主应用通过 manifest 自动发现并注册，不需要手动修改 `main.py`。
