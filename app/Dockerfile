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
COPY api_server.py /app/
COPY run_server.py /app/
COPY data     /app/



# 安装Python依赖
RUN pip install --upgrade pip  -i https://mirrors.aliyun.com/pypi/simple && \
    pip install coloredlogs onnxruntime -i https://mirrors.aliyun.com/pypi/simple && \  
    pip install -e .  -i https://mirrors.aliyun.com/pypi/simple

# 复制启动脚本
COPY start.sh   /app/
RUN chmod +x /app/start.sh
COPY local_fonts/     /root/.cache/babeldoc/fonts/
# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["/app/start.sh"]