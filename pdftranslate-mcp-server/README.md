# PDFTranslate MCP Server

基于BabelDOC的PDF文档翻译模型上下文协议(MCP)服务器，为AI助手提供标准化的PDF翻译功能。

## 功能特性

- 🚀 **多语言PDF翻译**: 支持12+种语言间的PDF文档翻译
- 🔄 **异步任务处理**: 非阻塞的翻译任务管理
- 📊 **实时进度反馈**: 翻译进度实时更新
- 🎯 **双模式输出**: 支持双语对照和单语翻译版本
- ☁️ **云存储集成**: 自动上传翻译结果到腾讯云COS，返回直接下载链接
- 🛠️ **MCP协议兼容**: 支持Cherry Studio、Dify、N8N等MCP客户端
- ⚙️ **灵活配置**: 支持自定义QPS、水印模式、COS配置等参数
- 🔧 **动态配置**: 支持通过MCP参数动态更新配置，无需重启服务

## 安装要求

- Python 3.12+
- UV包管理器 (推荐) 或 pip
- OpenAI兼容的API密钥
- 腾讯云COS SDK (可选，用于文件上传功能)

## 快速开始

### 方式一：Docker部署 (推荐)

#### 1. 克隆项目

```bash
git clone <repository-url>
cd pdftranslate-mcp-server
```

#### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.docker .env

# 编辑 .env 文件，填入你的配置
nano .env
```

必须配置的环境变量：
```bash
OPENAI_API_KEY=your-api-key-here
```

#### 3. 使用Docker Compose启动 (推荐)

```bash
# 构建并启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

#### 4. 或者使用Docker命令

```bash
# 构建镜像
docker build -t pdftranslate-mcp-server .

# 运行容器
docker run -d \
  --name pdftranslate-mcp-server \
  -p 8006:8006 \
  -e OPENAI_API_KEY=your-api-key-here \
  -e OPENAI_MODEL=deepseek-ai/DeepSeek-V3 \
  -e OPENAI_BASE_URL=https://api.siliconflow.cn/v1 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/temp:/app/temp \
  pdftranslate-mcp-server

# 查看日志
docker logs -f pdftranslate-mcp-server

# 停止容器
docker stop pdftranslate-mcp-server
docker rm pdftranslate-mcp-server
```

### 方式二：本地安装

#### 1. 克隆项目

```bash
git clone <repository-url>
cd pdftranslate-mcp-server
```

#### 2. 安装依赖

使用UV (推荐):
```bash
uv venv
uv pip install .
# 安装COS SDK (可选，用于文件上传功能)
uv pip install cos-python-sdk-v5
```

或使用pip:
```bash
pip install -r requirements.txt
# 安装COS SDK (可选，用于文件上传功能)
pip install cos-python-sdk-v5
```

#### 3. 安装BabelDOC

```bash
# 使用UV
uv pip install babeldoc

# 或使用pip
pip install babeldoc
```

#### 4. 配置环境变量

复制环境变量模板:
```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的配置:
```env
# OpenAI API配置
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=deepseek-ai/DeepSeek-V3
OPENAI_BASE_URL=https://api.siliconflow.cn/v1

# 翻译配置
DEFAULT_LANG_IN=en
DEFAULT_LANG_OUT=zh
QPS=4
WATERMARK_OUTPUT_MODE=no_watermark
NO_DUAL=false
NO_MONO=false

# 服务器配置
MCP_HOST=0.0.0.0
MCP_PORT=8003

# 腾讯云COS配置 (可选，用于文件上传功能)
COS_REGION=ap-nanjing
COS_SECRET_ID=your_cos_secret_id
COS_SECRET_KEY=your_cos_secret_key
COS_BUCKET=your_cos_bucket
```

### 5. 配置文件设置 (可选)

除了环境变量，您也可以通过 `config.ini` 文件配置COS参数:

```ini
[common]
cos_region = ap-nanjing
cos_secret_id = your_cos_secret_id
cos_secret_key = your_cos_secret_key
cos_bucket = your_cos_bucket
```

> **注意**: 环境变量的优先级高于config.ini配置

### 6. 启动服务器

```bash
# 使用UV
uv run main.py

# 或直接运行
python main.py
```

服务器将在 `http://0.0.0.0:8006/sse` 启动（SSE模式）。

**注意**: 默认使用SSE传输方式，适合云部署和远程客户端访问。如果需要STDIO模式（适合本地开发），请修改main.py中的`mcp.run(transport="stdio")`。

## Docker镜像构建详解

### 镜像特性

- **多阶段构建**：优化镜像大小，减少最终镜像体积
- **非root用户**：使用专用的`mcpuser`用户运行服务，提高安全性
- **环境变量配置**：支持通过环境变量动态配置所有参数
- **健康检查**：内置健康检查机制，确保服务正常运行
- **数据持久化**：支持挂载卷保存日志、临时文件等

### 环境变量配置

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `OPENAI_API_KEY` | - | OpenAI API密钥 (必填) |
| `OPENAI_MODEL` | `deepseek-ai/DeepSeek-V3` | 使用的AI模型 |
| `OPENAI_BASE_URL` | `https://api.siliconflow.cn/v1` | API基础URL |
| `MCP_HOST` | `0.0.0.0` | MCP服务器监听地址 |
| `MCP_PORT` | `8006` | MCP服务器端口 |
| `DEFAULT_LANG_IN` | `en` | 默认源语言 |
| `DEFAULT_LANG_OUT` | `zh` | 默认目标语言 |
| `QPS` | `4` | 每秒查询数限制 |
| `WATERMARK_OUTPUT_MODE` | `no_watermark` | 水印模式 |
| `NO_DUAL` | `false` | 是否禁用双语版本 |
| `NO_MONO` | `false` | 是否禁用单语版本 |
| `COS_REGION` | - | 腾讯云COS地域 |
| `COS_SECRET_ID` | - | 腾讯云COS密钥ID |
| `COS_SECRET_KEY` | - | 腾讯云COS密钥Key |
| `COS_BUCKET` | - | 腾讯云COS存储桶 |
| `LOG_LEVEL` | `INFO` | 日志级别 |

### 数据卷挂载

推荐挂载以下目录：

```bash
# 日志目录
-v ./logs:/app/logs

# 临时文件目录
-v ./temp:/app/temp

# 上传文件目录
-v ./uploads:/app/uploads

# 下载文件目录
-v ./downloads:/app/downloads

# 配置文件 (可选)
-v ./config.ini:/app/config.ini:ro
```

### 生产环境部署

#### 使用Docker Compose (推荐)

```yaml
version: '3.8'

services:
  pdftranslate-mcp:
    image: pdftranslate-mcp-server:latest
    container_name: pdftranslate-mcp-server
    restart: unless-stopped
    ports:
      - "8006:8006"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_MODEL=${OPENAI_MODEL}
      - OPENAI_BASE_URL=${OPENAI_BASE_URL}
    volumes:
      - ./logs:/app/logs
      - ./temp:/app/temp
    networks:
      - pdftranslate-network

networks:
  pdftranslate-network:
    driver: bridge
```

#### 使用Docker Swarm

```bash
# 创建Docker Secret存储API密钥
echo "your-api-key" | docker secret create openai_api_key -

# 部署服务
docker service create \
  --name pdftranslate-mcp \
  --publish 8006:8006 \
  --secret openai_api_key \
  --env OPENAI_API_KEY_FILE=/run/secrets/openai_api_key \
  --mount type=volume,source=pdftranslate-logs,target=/app/logs \
  --mount type=volume,source=pdftranslate-temp,target=/app/temp \
  pdftranslate-mcp-server:latest
```

### 镜像管理

```bash
# 构建镜像
docker build -t pdftranslate-mcp-server:latest .

# 构建指定版本
docker build -t pdftranslate-mcp-server:1.0.0 .

# 推送到镜像仓库
docker tag pdftranslate-mcp-server:latest your-registry/pdftranslate-mcp-server:latest
docker push your-registry/pdftranslate-mcp-server:latest

# 清理未使用的镜像
docker image prune -f
```

### 容器监控和维护

```bash
# 查看容器状态
docker ps
docker stats pdftranslate-mcp-server

# 查看容器日志
docker logs -f pdftranslate-mcp-server
docker logs --tail 100 pdftranslate-mcp-server

# 进入容器调试
docker exec -it pdftranslate-mcp-server /bin/bash

# 重启容器
docker restart pdftranslate-mcp-server

# 更新容器
docker pull pdftranslate-mcp-server:latest
docker stop pdftranslate-mcp-server
docker rm pdftranslate-mcp-server
docker run -d --name pdftranslate-mcp-server ...
```

## MCP工具说明

### translate_pdf
翻译PDF文档 - 支持多种文件输入方式

**参数:**
- `file_input` (str): 文件输入内容
  - 当`input_type="base64"`时，为base64编码的文件内容
  - 当`input_type="url"`时，为文件下载URL
  - 当`input_type="path"`时，为本地文件路径（仅限本地开发）
- `input_type` (str, 可选): 输入类型，可选值: "base64", "url", "path"，默认为 "base64"
- `filename` (str, 可选): 文件名称（用于识别和存储），默认为 "document.pdf"
- `lang_in` (str, 可选): 源语言代码，默认为 "en"
- `lang_out` (str, 可选): 目标语言代码，默认为 "zh"
- `qps` (int, 可选): 每秒查询数限制，默认为 4
- `no_dual` (bool, 可选): 是否禁用双语对照版本，默认为 False
- `no_mono` (bool, 可选): 是否禁用单语翻译版本，默认为 False
- `watermark_output_mode` (str, 可选): 水印模式，可选值: "no_watermark", "watermarked", "both"

**使用示例:**

1. **Base64文件上传（推荐用于SSE方式）:**
```json
{
    "file_input": "JVBERi0xLjQKJcOkw7zDtsOfCjIgMCBvYmoKPDwKL...",
    "input_type": "base64",
    "filename": "my_document.pdf",
    "lang_in": "en",
    "lang_out": "zh"
}
```

2. **URL文件下载:**
```json
{
    "file_input": "https://example.com/document.pdf",
    "input_type": "url",
    "filename": "remote_document.pdf"
}
```

3. **本地文件路径（仅限本地开发）:**
```json
{
    "file_input": "/path/to/local/document.pdf",
    "input_type": "path"
}
```

**返回:**
```json
{
    "task_id": "uuid-string",
    "message": "翻译任务已创建，正在从en翻译到zh",
    "status": "pending",
    "file_name": "document.pdf",
    "file_size_mb": 2.5,
    "input_type": "base64",
    "settings": {
        "source_language": "en",
        "target_language": "zh",
        "qps": 4,
        "dual_output": true,
        "mono_output": true,
        "watermark_mode": "no_watermark"
    }
}
```

### get_translation_status
查询翻译任务状态

**参数:**
- `task_id` (str): 翻译任务ID

**返回:**
```json
{
    "task_id": "uuid-string",
    "status": "processing",
    "progress": 45.5,
    "message": "正在翻译文档...",
    "result_files": {},
    "cos_urls": {},
    "created_at": "2025-07-28T10:00:00",
    "updated_at": "2025-07-28T10:05:00"
}
```

### get_translation_result_cos_url
获取翻译结果文件的COS云存储URL（推荐用于文件分发）

**参数:**
- `task_id` (str): 翻译任务ID
- `file_type` (str, 可选): 文件类型，"dual" 或 "mono"，默认为 "dual"

**返回:**
```json
{
    "success": true,
    "file_type": "dual",
    "cos_url": "https://your-bucket.cos.ap-nanjing.myqcloud.com/dual_document_20250128_143022.pdf",
    "download_url": "https://your-bucket.cos.ap-nanjing.myqcloud.com/dual_document_20250128_143022.pdf",
    "message": "成功获取dual类型的翻译结果文件COS URL"
}
```

### get_translation_result_base64
获取翻译结果文件的base64编码内容（推荐用于SSE方式）

**参数:**
- `task_id` (str): 翻译任务ID
- `file_type` (str, 可选): 文件类型，"dual" 或 "mono"，默认为 "dual"

**返回:**
```json
{
    "success": true,
    "file_name": "translated_document.pdf",
    "file_size": 1024000,
    "file_size_mb": 1.0,
    "file_type": "dual",
    "base64_content": "JVBERi0xLjQKJcOkw7zDtsOfCjIgMCBvYmoKPDwKL...",
    "data_url": "data:application/pdf;base64,JVBERi0xLjQK...",
    "message": "成功获取dual类型的翻译结果文件base64编码"
}
```

### download_translation_result
获取翻译结果文件信息

**参数:**
- `task_id` (str): 翻译任务ID
- `file_type` (str, 可选): 文件类型，"dual" 或 "mono"，默认为 "dual"

**返回:**
```json
{
    "file_path": "/path/to/translated.pdf",
    "file_name": "translated.pdf",
    "file_size": 1024000,
    "file_type": "dual"
}
```

### list_all_tasks
列出所有翻译任务

**返回:**
```json
{
    "total_tasks": 5,
    "tasks": [...]
}
```

### get_supported_languages
获取支持的语言列表

**返回:**
```json
{
    "languages": {
        "zh": "中文",
        "en": "English",
        "ja": "日本語",
        ...
    },
    "default_lang_in": "en",
    "default_lang_out": "zh"
}
```

### update_cos_config
动态更新COS配置参数（无需重启服务）

**参数:**
- `cos_region` (str, 可选): COS地域，如 "ap-nanjing"
- `cos_secret_id` (str, 可选): COS密钥ID
- `cos_secret_key` (str, 可选): COS密钥Key
- `cos_bucket` (str, 可选): COS存储桶名称

**返回:**
```json
{
    "success": true,
    "message": "COS配置已更新: region, bucket",
    "updated_fields": ["region", "bucket"],
    "config_complete": true,
    "cos_upload_ready": true,
    "current_config": {
        "region": "ap-nanjing",
        "secret_id": "已配置",
        "secret_key": "已配置",
        "bucket": "my-bucket"
    }
}
```

### check_system_status
检查系统状态和依赖（已增强COS支持检查）

**返回:**
```json
{
    "service_name": "PDFTranslate MCP Server",
    "version": "1.0.0",
    "babeldoc_available": true,
    "cos_available": true,
    "api_key_configured": true,
    "cos_configured": true,
    "dependencies": {
        "babeldoc": "✅ 已安装",
        "openai_api": "✅ 已配置",
        "cos_sdk": "✅ 已安装",
        "cos_config": "✅ 已配置"
    },
    "configuration": {
        "model": "deepseek-ai/DeepSeek-V3",
        "cos_region": "ap-nanjing",
        "cos_bucket": "my-bucket"
    },
    "ready": true,
    "cos_upload_ready": true
}
```

## MCP资源说明

### config://
获取服务器配置信息
```json
{
    "service_name": "PDFTranslate MCP Server",
    "version": "1.0.0",
    "babeldoc_available": true,
    "openai_model": "deepseek-ai/DeepSeek-V3",
    ...
}
```

### tasks://
获取任务状态统计
```json
{
    "total_tasks": 10,
    "tasks_by_status": {
        "completed": 7,
        "processing": 2,
        "failed": 1
    },
    "recent_tasks": [...]
}
```

## 客户端配置

### Cherry Studio

1. 打开Cherry Studio设置
2. 添加MCP服务器
3. 选择 **"SSE"** 传输方式
4. 输入服务器地址: `http://your-server:8003/sse`
   - 本地测试: `http://localhost:8003/sse`
   - 云服务器: `http://your-domain:8003/sse`
5. 保存配置

### Dify

在Dify工作流中添加MCP节点，配置SSE服务器地址:
- 本地: `http://localhost:8003/sse`
- 远程: `http://your-server:8003/sse`

### N8N

使用HTTP Request节点连接到MCP服务器的SSE端点:
- URL: `http://your-server:8003/sse`
- Method: POST
- Content-Type: application/json

**重要提示**: 
- SSE方式支持base64文件上传，推荐使用`input_type="base64"`
- 文件大小限制为100MB
- 支持URL下载方式 (`input_type="url"`)
- 本地文件路径方式仅在服务器本地可用

## 云存储功能 (COS集成)

### 功能说明

本服务集成了腾讯云对象存储(COS)，提供以下功能：

- ☁️ **自动上传**: 翻译完成后自动上传结果文件到COS
- 🔗 **直接访问**: 返回可直接下载的COS URL链接
- 📁 **文件管理**: 自动生成唯一文件名，避免冲突
- 🔒 **安全配置**: 支持多种配置方式，保护密钥安全

### 配置方式优先级

1. **环境变量** (最高优先级)
2. **config.ini文件**
3. **MCP动态配置**

### 使用流程

1. **配置COS参数** - 通过环境变量、config.ini或MCP工具配置
2. **翻译文件** - 正常使用`translate_pdf()`功能
3. **自动上传** - 翻译完成后自动上传到COS
4. **获取URL** - 使用`get_translation_result_cos_url()`获取下载链接
5. **直接下载** - 用户通过URL直接下载文件

### 文件命名规则

上传到COS的文件会自动添加时间戳前缀：
- 双语版本: `dual_原文件名_20250128_143022.pdf`
- 单语版本: `mono_原文件名_20250128_143022.pdf`

### 故障处理

如果COS上传失败，系统会：
- 记录详细错误日志
- 保留本地文件供其他方式获取
- 在任务状态中标明上传失败原因

## 支持的语言

- 中文 (zh)
- English (en)
- 日本語 (ja)
- 한국어 (ko)
- Français (fr)
- Deutsch (de)
- Español (es)
- Русский (ru)
- Italiano (it)
- Português (pt)
- العربية (ar)
- हिन्दी (hi)

## 部署

### 本地开发

```bash
uv run main.py
```

### 云服务器部署

1. 安装依赖和配置环境变量
2. 使用systemd或supervisor管理进程
3. 配置nginx反向代理 (可选)

示例systemd服务文件:
```ini
[Unit]
Description=PDFTranslate MCP Server
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/pdftranslate-mcp-server
Environment=PATH=/path/to/venv/bin
ExecStart=/path/to/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Docker部署

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install uv
RUN uv pip install .
RUN uv pip install babeldoc

EXPOSE 8003

CMD ["python", "main.py"]
```

## 故障排除

### 常见问题

1. **BabelDOC未安装**
   ```bash
   pip install babeldoc
   # 或
   uv pip install babeldoc
   ```

2. **COS SDK未安装**
   ```bash
   pip install cos-python-sdk-v5
   # 或
   uv pip install cos-python-sdk-v5
   ```

3. **API密钥错误**
   检查 `.env` 文件中的 `OPENAI_API_KEY` 配置

4. **COS配置错误**
   - 检查 `COS_REGION`、`COS_SECRET_ID`、`COS_SECRET_KEY`、`COS_BUCKET` 配置
   - 使用 `check_system_status()` 工具检查COS配置状态
   - 使用 `update_cos_config()` 工具动态更新配置

5. **COS上传失败**
   - 检查网络连接
   - 验证COS密钥权限
   - 确认存储桶名称和地域正确
   - 查看服务器日志获取详细错误信息

6. **端口占用**
   修改 `.env` 文件中的 `MCP_PORT` 配置

7. **内存不足**
   处理大型PDF文件时可能需要更多内存

8. **文件无法下载**
   - 如果COS上传失败，可使用 `get_translation_result_base64()` 获取文件
   - 检查COS存储桶的访问权限设置

### 日志查看

服务器日志包含详细的错误信息和调试信息，可以帮助定位问题。

## 许可证

MIT License

## 贡献

欢迎贡献代码和报告问题！请创建Issue或提交Pull Request。

## 更新日志

### v1.0.0 (2025-07-28)
- 初始版本发布
- 支持PDF翻译功能
- 支持MCP协议
- 支持多种客户端