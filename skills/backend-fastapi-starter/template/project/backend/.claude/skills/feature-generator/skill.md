<!-- 此文件不使用 .jinja 后缀，请勿改为 .jinja -->
---
name: feature-generator
description: >
  Create a new feature module with correct directory structure, manifest,
  and boilerplate files. Triggers when: user wants to add a new feature,
  create a new module, scaffold a new business domain, e.g. "/feature projects",
  "/feature orders", "/feature payments", "创建一个 XX 模块".
---

# Feature 模块生成器

通过本 skill 可以快速创建符合项目规范的 feature 模块骨架。

## 用法

用户输入 `/feature <name>` 或口头描述"创建 XX 模块"时触发。

## 工作流

### Step 1: 确认 Feature 名称

从用户输入提取 feature 名称（小写英文，如 `projects`, `orders`）。
如用户未明确，用 AskUserQuestion 确认。

### Step 2: 创建目录结构

在 `app/features/<name>/` 下创建以下文件:

```
app/features/<name>/
├── __init__.py
├── manifest.py
├── router.py
├── models.py
├── dependencies.py
└── service/
    ├── __init__.py
    └── crud.py
```

### Step 3: 生成文件内容

#### `manifest.py`
```python
"""
<Feature名称> 模块 Feature Manifest
统一声明此模块与框架的所有集成点。
"""

from dataclasses import dataclass, field


@dataclass
class FeatureManifest:
    """Feature 集成点声明"""
    router_module: str | None = None
    router_prefix: str | None = None
    router_tags: list[str] | None = None
    tasks_package: str | None = None
    beat_schedule: dict = field(default_factory=dict)
    admin_views_module: str | None = None
    models_module: str | None = None
    health_checks: dict = field(default_factory=dict)


manifest = FeatureManifest(
    router_module="app.features.<name>.router",
    router_prefix="/api/<name>",
    router_tags=["<FeatureName>"],
    models_module="app.features.<name>.models",
)
```

#### `__init__.py`
```python
# <Feature名称> 模块
```

#### `router.py`
```python
"""
<Feature名称>模块 API 路由
包含 <Feature名称> 相关的端点定义
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.postgresql import get_db
from app.shared.models import BaseResponse
# from .models import <Model>Create, <Model>Response
# from . import service

router = APIRouter()


# @router.post("/<name>", response_model=BaseResponse[...], status_code=201)
# async def create_<name>(...):
#     logger.info("创建<name>请求")
#     ...
```

#### `models.py`
```python
"""
<Feature名称>模块 数据模型
定义 SQLModel 表模型、请求/响应模型
"""

from sqlmodel import SQLModel, Field
# from app.shared.models import BaseMixin, BaseResponse

# class <Model>(BaseMixin, table=True):
#     """<Model>表"""
#     pass

# class <Model>Create(SQLModel):
#     """创建请求模型"""
#     pass

# class <Model>Response(SQLModel):
#     """响应模型"""
#     pass
```

#### `dependencies.py`
```python
"""
<Feature名称>模块 依赖注入
提供本模块对外依赖（如权限检查、资源加载）
"""

# from fastapi import Depends, HTTPException
# from sqlalchemy.ext.asyncio import AsyncSession
# from app.core.postgresql import get_db

# async def get_<name>(<name>_id: str, db: AsyncSession = Depends(get_db)):
#     """加载指定 <name> 资源"""
#     pass
```

#### `service/__init__.py`
```python
"""
<Feature名称>服务模块统一接口
"""

from .crud import (
    # create_<name>,
    # get_<name>_by_id,
    # update_<name>,
    # delete_<name>,
)

__all__ = [
    # "create_<name>",
    # "get_<name>_by_id",
    # "update_<name>",
    # "delete_<name>",
]
```

#### `service/crud.py`
```python
"""
<Feature名称>模块 标准 CRUD 操作
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from loguru import logger

# from ..models import <Model>


# async def create_<name>(db: AsyncSession, data) -> <Model>:
#     """创建 <name>"""
#     pass


# async def get_<name>_by_id(db: AsyncSession, <name>_id: str) -> <Model> | None:
#     """根据 ID 获取 <name>"""
#     pass
```

### Step 4: 提醒后续步骤

生成完成后提醒用户:
1. 在 `models.py` 中定义具体模型字段
2. 在 `router.py` 中实现端点
3. 在 `service/crud.py` 中实现 CRUD 逻辑
4. 更新 `alembic/env.py` 导入新模型
5. 运行 `docker-compose exec api alembic revision --autogenerate -m "add <name>"`
6. 运行 `docker-compose exec api alembic upgrade head`
