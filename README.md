# PDF翻译Web工具

🌍 基于AI的智能PDF文档翻译工具，支持Web界面和API接口，保持文档结构不变。

## 特性

- 🚀 **智能翻译**: 基于OpenAI/DeepSeek等大语言模型
- 📄 **保持格式**: 翻译后保持原始PDF文档结构和布局
- 🌐 **双重接口**: FastAPI REST API + Gradio Web界面
- ⚙️ **环境配置**: 通过环境变量灵活配置
- 🔧 **容器部署**: Docker一键部署
- 📊 **实时监控**: 翻译进度实时跟踪

## 项目结构

```
pdftranslate_web/
├── src/pdftranslate_web/       # 核心模块
│   ├── __init__.py
│   ├── api_server.py          # FastAPI API服务器
│   ├── api_client.py          # Python客户端SDK
│   └── gradio_client.py       # Gradio Web界面
├── scripts/                   # 启动脚本
│   ├── run_server.py         # 启动API服务器
│   └── run_gradio.py         # 启动Web界面
├── docker/                   # Docker配置
│   └── start.sh             # 容器启动脚本
├── docs/                     # 文档
│   ├── API_USAGE.md         # API使用说明
│   └── GRADIO_USAGE.md      # Web界面使用说明
├── tests/                    # 测试文件
├── .env.example             # 环境变量配置模板
├── docker-compose.yml       # Docker Compose配置
├── Dockerfile              # Docker镜像配置
├── pyproject.toml           # 项目配置和依赖
└── README.md               # 项目说明
```

## 快速开始

### 1. 环境准备

> **推荐使用 uv 包管理器**：uv 是一个超快的 Python 包安装器和解析器，比 pip 快 10-100 倍，支持自动依赖解析和虚拟环境管理。

```bash
# 克隆项目
git clone https://github.com/wwwzhouhui/pdftranslate_web
cd pdftranslate_web

# 方式一：使用 uv 包管理器 (推荐)
# 安装 uv (如果没有安装)
curl -LsSf https://astral.sh/uv/install.sh | sh
# 或者使用 pip 安装
pip install uv

# 使用 uv 安装依赖 (自动创建虚拟环境)
uv sync

# 方式二：使用传统 pip
# 安装依赖
pip install -e .
```

### 2. 配置设置

复制环境变量模板并编辑：

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置API密钥：

```bash
# OpenAI配置 (必填)
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=deepseek-ai/DeepSeek-V3
OPENAI_BASE_URL=https://api.siliconflow.cn/v1

# 翻译配置
QPS=4
DEFAULT_LANG_IN=en
DEFAULT_LANG_OUT=zh
WATERMARK_OUTPUT_MODE=no_watermark
```

### 3. 启动服务

#### 方式一：启动API服务器

```bash
# 使用 uv (推荐)
uv run python scripts/run_server.py --host 0.0.0.0 --port 8000

# 或使用传统方式
python scripts/run_server.py --host 0.0.0.0 --port 8000
```

API服务将在 `http://localhost:8000` 启动，文档地址：`http://localhost:8000/docs`

#### 方式二：启动Web界面

```bash
# 使用 uv (推荐)
uv run python scripts/run_gradio.py --server-url http://localhost:8000 --port 7860

# 或使用传统方式
python scripts/run_gradio.py --server-url http://localhost:8000 --port 7860
```

Web界面将在 `http://localhost:7860` 启动

## 使用方法

### API使用

```python
from pdftranslate_web.api_client import BabelDOCClient

# 创建客户端
client = BabelDOCClient("http://localhost:8000")

# 翻译PDF文件
downloaded_files = client.translate_and_download(
    pdf_path="document.pdf",
    output_dir="./output",
    lang_in="en",
    lang_out="zh"
)

print(f"翻译完成：{downloaded_files}")
```

### 命令行使用

```bash
# 使用API客户端
# uv方式 (推荐)
uv run python src/pdftranslate_web/api_client.py document.pdf --output-dir ./output --lang-out zh

# 传统方式
python src/pdftranslate_web/api_client.py document.pdf --output-dir ./output --lang-out zh

# 检查服务器状态
curl http://localhost:8000/health
```

### Web界面使用

1. 打开浏览器访问 `http://localhost:7860`
2. 上传PDF文件
3. 选择翻译选项（源语言、目标语言、输出类型）
4. 点击"开始翻译"
5. 等待翻译完成并下载结果

## API接口

### 核心接口

- `POST /translate` - 提交翻译任务
- `GET /status/{task_id}` - 查询翻译状态
- `GET /download/{task_id}/{file_type}` - 下载翻译结果
- `GET /health` - 健康检查

详细API文档请查看：`docs/API_USAGE.md`

## 配置说明

### 环境变量配置

所有配置通过环境变量进行设置。可以通过 `.env` 文件或直接设置环境变量：

```bash
# OpenAI配置 (必填)
OPENAI_API_KEY=your-api-key-here    # API密钥
OPENAI_MODEL=deepseek-ai/DeepSeek-V3  # 模型名称  
OPENAI_BASE_URL=https://api.siliconflow.cn/v1  # API基础URL

# 服务器配置
SERVER_HOST=0.0.0.0     # 绑定地址
SERVER_PORT=8000        # 端口号
QPS=4                   # 每秒请求数限制

# 翻译配置
DEFAULT_LANG_IN=en              # 默认源语言
DEFAULT_LANG_OUT=zh             # 默认目标语言
WATERMARK_OUTPUT_MODE=no_watermark  # 水印模式
NO_DUAL=false                   # 是否生成双语PDF
NO_MONO=false                   # 是否生成单语PDF
```

### 支持的环境变量

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `OPENAI_API_KEY` | - | OpenAI API密钥 (必填) |
| `OPENAI_MODEL` | `deepseek-ai/DeepSeek-V3` | 使用的模型 |
| `OPENAI_BASE_URL` | `https://api.siliconflow.cn/v1` | API端点 |
| `SERVER_HOST` | `0.0.0.0` | 服务器地址 |
| `SERVER_PORT` | `8000` | 服务器端口 |
| `QPS` | `4` | 请求频率限制 |
| `DEFAULT_LANG_IN` | `en` | 默认源语言 |
| `DEFAULT_LANG_OUT` | `zh` | 默认目标语言 |
| `WATERMARK_OUTPUT_MODE` | `no_watermark` | 水印模式 |

## 开发指南

### 开发环境设置

```bash
# 克隆项目
git clone https://github.com/wwwzhouhui/pdftranslate_web
cd pdftranslate_web

# 方式一：使用 uv (推荐)
# 安装 uv (如果没有安装)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装开发依赖
uv sync --dev

# 方式二：使用传统 pip + 虚拟环境
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装开发依赖
pip install -e ".[dev]"
```

### 运行测试

```bash
pytest tests/
```

### 代码格式化

```bash
black src/
isort src/
```

## Docker部署

### 快速开始

1. **准备环境变量文件**

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量 (必须设置API密钥)
nano .env
```

2. **启动服务**

```bash
# 构建并启动服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f pdftranslate
```

服务启动后访问：
- API服务：http://localhost:8000
- Web界面：http://localhost:7860
- API文档：http://localhost:8000/docs

### 环境变量配置

在 `.env` 文件中设置必需的配置：

```bash
# 必需配置
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=deepseek-ai/DeepSeek-V3
OPENAI_BASE_URL=https://api.siliconflow.cn/v1

# 可选配置
QPS=4
DEFAULT_LANG_IN=en
DEFAULT_LANG_OUT=zh
```

### Docker命令

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 查看日志
docker-compose logs pdftranslate

# 重启服务
docker-compose restart pdftranslate
```

### 直接使用Docker

```bash
# 构建镜像
docker build -t pdftranslate_web .

# 运行容器
docker run -d \
  --name pdftranslate \
  -p 8000:8000 \
  -p 7860:7860 \
  -e OPENAI_API_KEY="your-api-key" \
  pdftranslate_web
```

## 故障排除

### 常见问题

1. **API密钥错误**
   - 检查 `.env` 文件中的 `OPENAI_API_KEY` 设置
   - 确认API密钥有效且有足够配额

2. **模块导入错误**
   - 确保已正确安装项目依赖
   - 检查Python路径设置

3. **端口占用**
   - 修改 `.env` 文件中的端口号
   - 或使用环境变量指定其他端口

4. **翻译失败**
   - 检查网络连接
   - 确认API服务可用性
   - 查看日志文件获取详细错误信息

### 日志查看

```bash
# 查看API服务器日志
python scripts/run_server.py --log-level DEBUG

# 查看特定任务日志
curl http://localhost:8000/status/{task_id}
```

## 贡献指南

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 许可证

本项目采用 AGPL-3.0 许可证。详见 [LICENSE](LICENSE) 文件。

## 支持

- 📧 Email: 75271002@qq.com
- 🐛 问题反馈: [GitHub Issues](https://github.com/wwwzhouhui/pdftranslate_web/issues)

## 更新日志

### v0.0.1
- 重新整理项目目录结构
- 完善文档和配置文件
- 添加多种部署方式支持
- 优化API接口设计

---

⭐ 如果这个项目对您有帮助，请给我们一个star！