"""
Auth 模块 Feature Manifest
统一声明此模块与框架的所有集成点。
"""

from dataclasses import dataclass, field


@dataclass
class FeatureManifest:
    """Feature 集成点声明"""

    # 路由注册
    router_module: str | None = None
    router_prefix: str | None = None
    router_tags: list[str] | None = None

    # Celery 任务
    tasks_package: str | None = None
    beat_schedule: dict = field(default_factory=dict)

    # Admin 视图
    admin_views_module: str | None = None

    # 数据库模型（alembic 自动导入）
    models_module: str | None = None

    # 健康检查
    health_checks: dict = field(default_factory=dict)


manifest = FeatureManifest(
    router_module="app.features.auth.router",
    router_prefix="/api/auth",
    router_tags=["Authentication"],
    tasks_package="app.features.auth",
    admin_views_module="app.features.auth.admin_views",
    models_module="app.features.auth.models",
)
