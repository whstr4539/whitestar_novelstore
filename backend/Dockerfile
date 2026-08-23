# 星辰书城后端镜像
FROM python:3.12-slim

WORKDIR /app

# 依赖层（利用 Docker 缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 应用代码
COPY app ./app

EXPOSE 8000

# 生产/容器环境变量（覆盖本地开发配置）
ENV DATABASE_URL=postgresql+asyncpg://novel_user:novel_pass_2024@postgres:5432/novel_db \
    REDIS_URL=redis://:redis_pass_2024@redis:6379/0 \
    DEBUG=false

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
