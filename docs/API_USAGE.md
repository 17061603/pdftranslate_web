# BabelDOC API 使用说明

## 配置说明

### 环境变量配置

服务器通过环境变量进行配置。创建 `.env` 文件或直接设置环境变量：

```bash
# OpenAI配置 (必填)
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=deepseek-ai/DeepSeek-V3
OPENAI_BASE_URL=https://api.siliconflow.cn/v1

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
QPS=4

# 翻译配置
DEFAULT_LANG_IN=en
DEFAULT_LANG_OUT=zh
WATERMARK_OUTPUT_MODE=no_watermark
NO_DUAL=false
NO_MONO=false
```
- `OPENAI_API_KEY`: OpenAI API密钥 (必需)
- `OPENAI_MODEL`: OpenAI模型名称
- `OPENAI_BASE_URL`: OpenAI API基础URL
- `SERVER_HOST`: 服务器主机地址
- `SERVER_PORT`: 服务器端口
- `QPS`: 每秒请求数限制
- `DEFAULT_LANG_IN`: 默认源语言
- `DEFAULT_LANG_OUT`: 默认目标语言
- `WATERMARK_OUTPUT_MODE`: 水印模式
- `NO_DUAL`: 不生成双语PDF
- `NO_MONO`: 不生成单语PDF

## 服务端部署

### 安装依赖
```bash
# 安装必要的依赖包
uv sync
# 或者 pip install fastapi uvicorn python-multipart toml
```

### 启动服务器
```bash
# 方法1：直接运行启动脚本
uv run python babeldoc/run_server.py

# 方法2：使用API服务器模块
uv run python -m babeldoc.api_server

# 方法3：自定义主机和端口
uv run python babeldoc/run_server.py --host 0.0.0.0 --port 8000
```

服务器启动后会监听在 `http://0.0.0.0:8000`，可以通过浏览器访问 `http://localhost:8000/docs` 查看API文档。

## API接口说明

### 1. 翻译PDF文档
- **接口**: `POST /translate`
- **功能**: 上传PDF文件进行翻译
- **参数**:
  - `file`: PDF文件 (必需)
  - `lang_in`: 源语言代码 (可选，使用服务器默认配置)
  - `lang_out`: 目标语言代码 (可选，使用服务器默认配置)
  - `qps`: 每秒请求数限制 (可选，使用服务器默认配置)
  - `no_dual`: 不生成双语PDF (可选，使用服务器默认配置)
  - `no_mono`: 不生成单语PDF (可选，使用服务器默认配置)
  - `watermark_output_mode`: 水印模式 (可选，使用服务器默认配置)

### 2. 查询翻译状态
- **接口**: `GET /status/{task_id}`
- **功能**: 查询翻译任务的当前状态和进度

### 3. 下载翻译结果
- **接口**: `GET /download/{task_id}/{file_type}`
- **功能**: 下载翻译完成的PDF文件
- **参数**:
  - `file_type`: "dual" (双语版本) 或 "mono" (单语版本)

### 4. 健康检查
- **接口**: `GET /health`
- **功能**: 检查服务是否正常运行

### 5. 获取服务器配置
- **接口**: `GET /`
- **功能**: 获取服务器当前配置信息

## 客户端使用

### Python客户端库
```python
from babeldoc.api_client import BabelDOCClient

# 创建客户端
client = BabelDOCClient("http://localhost:8000")

# 翻译PDF文档 (使用服务器默认配置)
downloaded_files = client.translate_and_download(
    pdf_path="example.pdf",
    output_dir="./output"
)

# 翻译PDF文档 (自定义参数)
downloaded_files = client.translate_and_download(
    pdf_path="example.pdf",
    output_dir="./output",
    lang_in="en",
    lang_out="zh"
)

print("翻译完成，文件保存至:", downloaded_files)
```

### 命令行客户端
```bash
# 使用服务器默认配置翻译
uv run python babeldoc/api_client.py example.pdf --output-dir ./output

# 自定义翻译参数
uv run python babeldoc/api_client.py example.pdf \
    --output-dir ./output \
    --lang-in en \
    --lang-out zh \
    --server-url http://localhost:8000
```

### cURL示例
```bash
# 1. 提交翻译任务 (使用服务器默认配置)
curl -X POST "http://localhost:8000/translate" \
  -F "file=@example.pdf"

# 2. 提交翻译任务 (自定义参数)
curl -X POST "http://localhost:8000/translate" \
  -F "file=@example.pdf" \
  -F "lang_in=en" \
  -F "lang_out=zh"

# 3. 查询任务状态
curl "http://localhost:8000/status/{task_id}"

# 4. 下载翻译结果
curl "http://localhost:8000/download/{task_id}/dual" -o translated.pdf

# 5. 获取服务器配置
curl "http://localhost:8000/"
```

## 部署说明

### 生产环境部署
```bash
# 使用Gunicorn部署
pip install gunicorn
gunicorn babeldoc.api_server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# 使用Docker部署
# Dockerfile示例:
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -e .
COPY .env /app/
EXPOSE 8000
CMD ["python", "babeldoc/run_server.py"]
```

## 配置优势

1. **安全性提升**: OpenAI API密钥只需在服务器端配置一次，客户端无需传递敏感信息
2. **配置集中**: 所有翻译相关配置在服务器端统一管理
3. **客户端简化**: 客户端只需上传文件，其他参数可选
4. **灵活性**: 支持配置文件和环境变量两种配置方式
5. **默认值**: 客户端可以使用服务器默认配置，也可以覆盖特定参数

## 注意事项

1. **环境变量优先**: 所有配置均通过环境变量设置
2. **API密钥安全**: 确保 `.env` 文件权限设置正确，避免泄露API密钥
3. **文件存储**: 翻译过程中的临时文件会自动清理
4. **并发限制**: 服务器会根据配置的QPS参数限制API调用频率
5. **超时设置**: 大文件翻译可能需要较长时间，建议适当调整客户端超时时间

## 故障排除

### 常见问题
1. **服务器无法启动**: 
   - 检查环境变量是否正确设置
   - 确认 OpenAI API密钥已正确配置
   - 检查端口是否被占用
2. **翻译失败**: 
   - 检查服务器日志中的错误信息
   - 确认网络连接正常
   - 验证OpenAI API配置是否正确
3. **下载失败**: 确认任务已完成且文件类型正确

### 日志查看
服务器运行时会输出详细日志，包括：
- 使用的OpenAI模型信息
- 默认语言配置
- 任务处理状态
- 错误详情