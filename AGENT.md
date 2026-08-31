# AGENT.md — 星辰书城（网文书城课设）

React 19 + Vite + Router v7 前端 / FastAPI + SQLAlchemy 2.0 async + Redis 后端 / PostgreSQL 16。中文界面文案与注释。

## 项目结构

```
├── docker-compose.yml      # PG16 + Redis7 + pgAdmin（backend/frontend 服务未启用）
├── .env                    # 根：Docker 端口/口令（宿主机 5432 被占，PG 映射 5433）
├── db/init/01_schema.sql   # 17 张表 + 触发器 + 视图（首次启动自动建表）
├── db/init/02_seed.sql     # 种子数据（3 个演示账号，密码均 123456）
├── backend/
│   ├── .env                # DATABASE_URL / REDIS_URL（连宿主机 localhost:5433）
│   └── app/
│       ├── main.py         # 入口：CORS + 注册全部 router
│       ├── config.py       # Settings（env 读取）
│       ├── database.py     # async engine / get_db
│       ├── redis_client.py # async redis / get_redis
│       ├── models/         # ORM：user / novel / chapter / interaction
│       ├── schemas/        # 全部 Pydantic 模型（单文件）
│       ├── core/           # security.py（bcrypt+JWT）、deps.py（鉴权依赖）
│       ├── services/       # cache.py（Redis 封装）、purchase.py（购章事务）
│       └── api/            # 每模块一个 router 文件
└── frontend/src/
    ├── api/client.js       # axios：token 注入 + 401 跳登录
    ├── api/index.js        # 后端接口函数（与路由一一对应）
    ├── stores/AuthContext.jsx
    ├── components/         # Header / NovelCard / ChapterList
    ├── pages/              # Home/NovelDetail/Reader/Bookshelf/Profile/Author/Admin/Auth
    └── styles/global.css   # 设计令牌（CSS 变量）+ 全局样式
```

## 环境配置

- Windows 环境：后端虚拟环境在 `backend/.venv`，用 `.venv/Scripts/python`
- 宿主机 PostgreSQL 18 占用 5432 → Docker PG 映射 **5433**；Redis 6379
- 根 `.env` 控制 docker-compose；`backend/.env` 控制后端连接；`frontend/vite.config.js` 代理 `/api` → 8000
- 无 ORM 迁移工具：改库结构需同步 `db/init/01_schema.sql`

## 启动命令

```bash
docker compose up -d                     # 启动 PG + Redis（首次自动建表+种子）
bash scripts/dev-backend.sh              # 后端 http://localhost:8000/docs
cd frontend && npm install && npm run dev  # 前端 http://localhost:5173
```

## 代码风格

后端：
- 全程 async（FastAPI + SQLAlchemy 2.0），无同步 DB 代码
- 路由按模块一个文件，prefix `/api/xxx`；中文 docstring + summary + 业务文案
- 依赖注入 `get_db` / `get_redis` / `get_current_user`（core/deps.py），禁止手写连接
- Schema 集中 `schemas/__init__.py`；接口必须声明 `response_model`
- Redis 缓存统一走 `services/cache.py`（cache_key/get_json/set_json/delete_keys），不手拼 key
- 扣费/写库事务放 services 层（参考 purchase.py：行锁 + 唯一约束防重复扣费）

前端：
- 函数组件 + hooks；页面局部样式用组件内 `<style>{...}</style>`，色彩/间距全用 `global.css` 的 CSS 变量（--paper/--accent/--ink-*），禁止写死颜色
- 站内跳转一律 `Link` / `useNavigate`，禁止 `<a href>`
- 接口函数加在 `src/api/index.js`（自动带 token），页面不直接 import axios
- 文案中文、不加 emoji；阅读页排版遵循 skill：novel-reading-ui

新增接口链路：models → schemas → api/xxx.py → main.py 注册 → frontend/src/api/index.js 加函数。

## 注意

- Windows 保留设备名（nul/con/prn/com1 等）禁止用作文件名
- `.env` 含口令，勿提交；演示账号密码 123456（seed 内 bcrypt 哈希）
