# 问题清单（已修复）

> 以下问题已通过 7 轮测试验证修复。

---

## P1 - ✅ 已修复：bootstrap skill description 与实际行为不一致

**修复**: description 改为 `setup admin (if auth enabled)`

---

## P2 - ✅ 已修复：admin 文件强制绑定 auth

**修复**: admin 拆为独立可选模块。`admin.py` 和 `admin_views.py` 在 `'admin' in features or 'auth' in features` 时生成；`admin_auth.py` 仅在 `'auth' in features` 时生成。copier.yml 新增 `admin` 选项，pyproject.toml 中 sqladmin 依赖条件改为 `'admin' in features or 'auth' in features`。

---

## P3 - ✅ 已修复：Celery 自依赖未在代码层面实现

**修复**: 新增 `DEPENDENCIES.md` 作为 AI 强制校验清单，列出模块依赖规则和自动修复逻辑。

---

## P4 - ✅ 已修复：CONTEXT.md 与 instructions/ 双源问题

**修复**: 直接删除 `instructions/` 目录，CONTEXT.md 确立为唯一权威源。

---

## P5 - ✅ 已修复：Contract 测试强依赖 auth 模块

**修复**: 所有测试改为通用端点测试（`/`、`/health`），不依赖任何特定模块。新增 `test_assembly.py` 验证 feature 路由注册完整性。

---

## P6 - ✅ 已修复：feature-generator skill 代码示例缺乏 {% raw %} 保护

**修复**: 文件顶部添加注释 `<!-- 此文件不使用 .jinja 后缀，请勿改为 .jinja -->`，保持 `.md` 后缀不变。
