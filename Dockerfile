# 使用官方Python运行时作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY pyproject.toml /app/
COPY src/ /app/src/
COPY scripts/ /app/scripts/
COPY simaple/ /app/simaple/
COPY README.md /app/

# 安装Python依赖
RUN pip install --upgrade pip && \
    pip install -e .

# 复制启动脚本
COPY docker/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# 暴露端口
EXPOSE 8000 7860

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["/app/start.sh"]