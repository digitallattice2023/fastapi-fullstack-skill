# modular-fullstack-starter

FastAPI 全栈后端脚手架。一条命令生成生产级项目骨架，开箱即用。

## 一句话

```
/modular-fullstack-starter
```

AI 会问你选哪些模块（auth / admin / redis / celery / storage / email / radar），然后生成完整的 FastAPI 项目。

## 生成后自带 3 个本地 Skill

项目生成后，`.claude/skills/` 下自动包含以下 skill，后续开发中直接调用：


| Skill             | 触发词                              | 作用                                                                |
| ----------------- | ----------------------------------- | ------------------------------------------------------------------- |
| `/feature <name>` | "创建 XX 模块"、"/feature projects" | 生成符合规范的 feature 骨架（manifest + router + models + service） |
| `/bootstrap`      | "启动项目"、"初始化"、"一键启动"    | uv lock → docker compose up → 迁移 → 状态报告                    |
| `/project-status` | "项目状态"、"能力矩阵"、"查看功能"  | 输出已启用模块、API 路由、健康检查、Docker 容器状态                 |

## 生成项目的能力矩阵

- **Feature Manifest 自动发现** — 新增 feature 零配置，自动注册路由/任务/模型
- **统一异常处理 + 错误码** — 所有端点返回 `BaseResponse`，自动附加 `error_code` 和修复建议
- **分层架构** — Router 无 try-except，Service 抛 HTTPException，全局处理器统一格式化
- **Redis 缓存** — 标准缓存流程（读缓存 → 未命中查 DB → 写入）
- **Contract Tests** — 生成即带响应格式、错误码、Manifest 完整性测试
- **AI 上下文卡** — `.claude/CONTEXT.md` 压缩所有开发约定，AI 读取后自动遵循规范

## 可选功能模块

| 模块 | 说明 | 依赖 |
|------|------|------|
| `auth` | JWT 认证（登录/注册/密码重置） | 无 |
| `admin` | SQLAdmin 管理面板（可独立使用，搭配 auth 可启用 JWT 保护） | 无 |
| `redis` | 缓存层 + Celery 消息代理 | 无 |
| `celery` | 异步任务队列 + Beat 调度器 | redis |
| `storage` | 对象存储（Cloudflare R2 / AWS S3） | 无 |
| `email` | 邮件服务（Resend） | 无 |
| `radar` | HTTP 监控面板（`/__radar`） | 无 |

## 技术栈

Python 3.12 | FastAPI | SQLModel | Pydantic v2 | uv | asyncpg | redis.asyncio | celery | alembic | loguru
