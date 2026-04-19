---
name: backend-dev-guide
description: >
  FastAPI 后端项目开发规范指南。提供 Feature Manifest 架构、分层约定、响应格式等开发指导。
  Triggers when: user wants to understand the backend project architecture, add features to an
  existing backend, or needs development guidelines for the FastAPI project.
---

# FastAPI 后端项目开发规范

本文档为已生成的 FastAPI 后端项目提供开发指导。**不生成任何文件**，仅作开发参考。

## 适用场景

- 用户询问"这个后端项目怎么开发的？"
- 用户要在已有项目中添加新 feature
- 用户需要了解架构约定（分层、响应格式、路由注册等）

## 常用命令

```bash
# 安装依赖后锁定版本（宿主机执行）
uv lock

# 启动全部服务
docker-compose up -d

# 查看 API 容器日志
docker-compose logs -f api

# 进入容器执行 alembic 迁移
docker-compose exec api alembic upgrade head
docker-compose exec api alembic revision --autogenerate -m "描述"

# 运行测试
docker-compose exec api pytest tests/ -v
```

> **注意**：除 `uv lock` 外，所有操作都在容器内执行。

## 架构概览

```
app/
├── main.py                     # 入口：lifespan、异常处理、CORS、自动路由注册
├── celery_app.py               # Celery 配置（Manifest 自动发现任务）
├── core/
│   ├── config.py               # Pydantic BaseSettings，按模块 Mixin 组合
│   ├── postgresql.py           # 异步/同步 DB 管理器
│   ├── redis.py                # 异步/同步 Redis 管理器
│   └── init_db.py              # 启动时自动 alembic + admin 创建
├── shared/
│   ├── models.py               # BaseMixin、BaseResponse[T]
│   ├── utils.py                # ULID/UTC 时间工具
│   ├── logs.py                 # Loguru 配置
│   └── health.py               # 健康检查（Manifest 自动注册）
└── features/                   # 按业务领域划分
    └── [feature]/
        ├── manifest.py           # Feature Manifest（路由、任务、模型声明）
        ├── router.py
        ├── models.py
        ├── dependencies.py
        ├── tasks.py
        └── service/
```

## 核心约定

### Feature Manifest 模式

每个 feature 目录下应包含 `manifest.py`，统一声明：

```python
from . import router as feature_router
# from . import tasks as feature_tasks
# from . import models as feature_models

# 路由注册
router_module = feature_router
router_prefix = "/api/v1/feature"
router_tags = ["Feature"]

# Celery 任务（如启用 celery）
# tasks_package = feature_tasks
# beat_schedule = {...}

# 数据库模型
# models_module = feature_models

# 健康检查
# health_checks = {"feature": check_function}
```

主应用（`main.py`）通过 manifest 自动发现并注册路由、任务、模型、健康检查。

**不需要手动修改 `main.py`**，只需在 feature 目录创建 `manifest.py` 即可。

### 导入规范

- **同一 feature 内**：相对导入（如 `from .service import login_service`）
- **跨 feature / 共享模块**：绝对导入（如 `from app.shared.models import BaseMixin`）

### 分层职责

#### Router 层

- 无 `try-except`，直接调用 service
- 负责请求参数校验和返回响应
- 使用 Pydantic 模型定义请求/响应体

```python
@router.post("/login", response_model=BaseResponse[LoginResponse])
async def login(request: LoginRequest):
    result = await login_service.login(request)
    return BaseResponse(data=result, message="登录成功")
```

#### Service 层

- 业务验证通过抛 `HTTPException` 失败
- 数据库操作使用 `try-except SQLAlchemyError` 捕获
- 返回纯数据，不负责响应格式化

```python
async def login(request: LoginRequest) -> LoginResponse:
    user = await find_user(request.email)
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    token = create_access_token(user.id)
    return LoginResponse(access_token=token)
```

#### 全局异常处理器

在 `main.py` 中捕获所有 `HTTPException` 和未捕获异常，格式化为 `BaseResponse`。

### 响应格式

所有端点统一返回 `BaseResponse[T]`：

```python
class BaseResponse(BaseModel, Generic[T]):
    data: T | None = None
    message: str = "success"
```

前端收到的响应结构：
```json
{
    "data": {...},
    "message": "success"
}
```

### Redis 缓存

- 键命名：`{project_slug}:模块:功能:参数`（如 `myapp:auth:user:123`）
- 过期时间通过 `.env` 中的 `*_EXPIRE_MINUTES` 配置
- 写入使用 `model_dump_json()`，读取使用 `model_validate_json()`

### 模型构建（BaseMixin 模式）

- **BaseMixin**（无 `table=True`）：通用字段（id, created_at, updated_at）
- **业务 Mixin**（无 `table=True`）：业务字段
- **表模型**（`table=True`）：继承 BaseMixin + 业务 Mixin

```python
class BaseMixin(SQLModel):
    id: str = Field(default_factory=lambda: str(ulid.ULID()), primary_key=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

class UserMixin(SQLModel):
    email: str
    username: str
    hashed_password: str
    is_active: bool = True

class User(UserMixin, BaseMixin, table=True):
    pass
```

## 添加新 Feature 的步骤

1. 在 `app/features/` 下创建新目录（如 `app/features/products/`）
2. 创建 `manifest.py` 声明路由、任务、模型
3. 创建 `router.py`、`models.py`、`service/` 等文件
4. 重启 API 容器，路由自动注册

## 服务端口

- FastAPI API: 宿主机端口由 `api_host_port` 配置（容器内固定 `8000`）
- PostgreSQL: 宿主机端口由 `db_port` 配置（容器内固定 `5432`）
- Redis: 宿主机端口由 `redis_host_port` 配置（容器内固定 `6379`）
