---
name: frontend-vue-starter
description: >
  Interactive frontend project generator for Vue 3 + Vite + TypeScript + Pinia + Tailwind CSS.
  Uses Copier for deterministic file generation (NOT manual file creation).
  Triggers when: user wants to create a Vue frontend project, set up Vue+Vite+TS project,
  add Pinia state management, or initialize a Tailwind CSS frontend.
---

# Vue 前端项目脚手架

通过 Copier 模板确定性生成 Vue 3 + TypeScript 前端项目。**Skill 不直接生成任何文件**，所有文件生成由 Copier 负责。

生成的前端项目位于 `frontend/` 目录下，可与后端 `backend/` 目录并存。

## 核心原则

- **确定性的事交给代码**：文件生成、条件分支、依赖解析 → Copier (Jinja2)
- **创造性的事交给 Claude**：用户交互、环境检查、定制建议 → Skill

## 工作流

### Step 0: 环境校验

检查 Node.js 是否安装：

```bash
node --version    # 需要 v18+
npm --version
```

如缺失，引导用户安装 Node.js。

### Step 1: 收集项目参数（必须使用 AskUserQuestion）

**⚠️ 必须按顺序调用 AskUserQuestion 工具收集以下信息，不得跳过或硬编码默认值。**

**第一轮 AskUserQuestion**（项目身份）：
- header: "项目信息"
- multiSelect: false
- 问题: "请配置前端项目信息"
- options:
  - label: "项目名称" / description: "用于 package.json name 字段" / default: "myapp"
  - label: "项目描述" / description: "用于 package.json description 字段" / default: "Vue 3 Frontend Application"

**第二轮 AskUserQuestion**（后端连通）：
- header: "后端连通"
- multiSelect: false
- 问题: "是否需要连接后端 API？连接后可在初始化页面显示 API 健康状态"
- options:
  - label: "有后端" / description: "生成包含 API 连通性检查的初始化页面，自动调用后端 /health 接口"
  - label: "纯前端" / description: "生成纯静态初始化页面，仅显示前端技术栈信息"
- 默认: 纯前端

如果选择"有后端"，额外询问：
- header: "API 配置"
- 问题: "后端 API 地址是什么？"
- 默认: "http://localhost:8002"

### Step 2: 调用 Copier 生成项目

使用 Copier Python API（预填答案，无需二次交互）：

**⚠️ Windows 兼容注意**：Copier 在 Windows 下遇到缺失参数时会尝试打开交互式 prompt 导致报错。必须传 `defaults=True`。

**⚠️ 模板路径查找**：AI 需要通过 glob 搜索找到模板路径：
```python
import glob, os
search_dirs = [os.path.expanduser("~/.claude/skills"), os.path.join(os.getcwd(), ".claude", "skills"), os.path.join(os.getcwd(), "skills"), os.getcwd()]
for sd in search_dirs:
    if os.path.exists(sd):
        m = glob.glob(os.path.join(sd, "frontend-vue-starter", "template"))
        if m:
            src_path = os.path.abspath(m[0])
            break
```

```python
from copier import run_copy

run_copy(
    src_path=src_path,
    dst_path=".",  # 当前工作目录，模板的 _subdirectory: project 会在当前目录生成 frontend/
    data={
        "project_name": "<用户输入>",
        "project_description": "<用户输入>",
        "has_backend": True/False,
        # 如果有后端:
        # "backend_api_url": "<用户输入>",
    },
    unsafe=True,
)
```

### Step 3: 生成后审查

生成完成后：
1. 展示生成的文件树
2. 展示 `.copier-answers.yml` 确认所有参数

### Step 4: 安装 & 启动

```bash
cd <目标目录>/frontend
npm install
npm run dev
```

等待 Vite 启动，确认页面可访问。

### Step 5: 状态报告

展示给用户：
- 前端地址: `http://localhost:5173`
- 技术栈: Vue 3 + Vite + TypeScript + Pinia + Tailwind CSS
- API 连通状态: 已连接 / 未连接（取决于选择）

## 模板位置

Copier 模板位于 skill 目录下的 `template/` 子目录中：
`<skill目录>/template/`

模板是项目生成的唯一权威来源。**不要手动创建任何项目文件**。

## 初始化成功页面

页面位于 `src/views/WelcomePage.vue`，显示内容：
- 恭喜图标和"初始化成功"标题
- 前端技术栈列表（Vue 3 / Vite / TypeScript / Pinia / Tailwind CSS）
- 如果连接后端 API，显示后端技术栈和健康检查状态
- 前后端地址信息

## 后续开发

项目生成后，用户可：
- 在 `frontend/src/components/` 下创建 Vue 组件
- 在 `frontend/src/stores/` 下创建 Pinia stores
- 在 `frontend/src/views/` 下创建页面视图
- 使用 Tailwind CSS 进行样式开发
