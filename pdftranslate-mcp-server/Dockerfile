# 使用官方Python运行时作为基础镜像
FROM python:3.11-slim

# 设置标签信息
LABEL maintainer="wwwzhouhui <75271002@qq.com>" \
      version="1.0.0" \
      description="PDFTranslate MCP Server - 基于BabelDOC的PDF文档翻译服务" \
      org.opencontainers.image.source="https://github.com/wwwzhouhui/pdftranslate_web"

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # MCP服务器配置
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8006 \
    # 翻译默认配置
    DEFAULT_LANG_IN=en \
    DEFAULT_LANG_OUT=zh \
    QPS=4 \
    WATERMARK_OUTPUT_MODE=no_watermark \
    NO_DUAL=false \
    NO_MONO=false \
    # 日志配置
    LOG_LEVEL=INFO

# 安装运行时系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 复制MCP服务器项目文件
COPY pyproject.toml /app/
COPY main.py /app/
COPY config.ini /app/
COPY .env.example /app/
COPY README.md /app/

# 安装Python依赖
RUN pip install --upgrade pip && \
    pip install . && \
    pip install cos-python-sdk-v5

# 创建非root用户和home目录
RUN groupadd -r mcpuser && useradd -r -g mcpuser -m mcpuser

# 创建必要的目录并设置权限
RUN mkdir -p /app/temp /app/uploads /app/downloads /app/logs \
    /home/mcpuser/.cache/babeldoc/tiktoken \
    && chown -R mcpuser:mcpuser /app /home/mcpuser

# 切换到非root用户
USER mcpuser

# 暴露MCP服务器端口
EXPOSE 8006

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${MCP_PORT:-8006}/sse || exit 1

# 启动MCP服务器
CMD ["python", "main.py"]