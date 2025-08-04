# PDF翻译MCP服务器产品需求文档 (PRD)

## 1. 项目概述

### 1.1 项目名称
PDFTranslate MCP Server - PDF文档翻译模型上下文协议服务器

### 1.2 项目背景
基于现有的PDF翻译Web应用(`src/pdftranslate_web/api_server.py`)，开发一个MCP服务器，使AI助手能够通过模型上下文协议直接调用PDF翻译功能，提供标准化的PDF文档翻译服务接口。

### 1.3 项目目标
- 提供基于MCP协议的PDF翻译服务
- 支持多种语言间的PDF文档翻译
- 提供异步翻译任务管理
- 兼容Cherry Studio、Cursor、Cline、Dify、FastGPT、N8N等MCP客户端

## 2. 功能需求

### 2.1 核心功能
1. **PDF翻译工具 (translate_pdf)**
   - 上传PDF文件进行翻译
   - 支持指定源语言和目标语言
   - 支持自定义QPS(每秒查询数)
   - 支持双语对照和单语翻译模式选择
   - 支持水印输出模式配置

2. **翻译状态查询工具 (get_translation_status)**
   - 查询翻译任务状态
   - 获取翻译进度信息
   - 查看翻译结果文件列表

3. **翻译结果下载工具 (download_translation_result)**
   - 下载翻译完成的PDF文件
   - 支持下载双语对照版本
   - 支持下载单语翻译版本

### 2.2 资源提供
1. **配置信息资源 (config://)**
   - 当前服务器配置信息
   - 支持的语言列表
   - 默认翻译参数

2. **任务列表资源 (tasks://)**
   - 所有翻译任务列表
   - 任务状态概览

## 3. 技术规格

### 3.1 技术栈
- **MCP SDK**: 基于`mcp[cli]` Python SDK
- **翻译引擎**: BabelDOC翻译库
- **AI模型**: OpenAI兼容API (支持DeepSeek等)
- **异步处理**: 基于Python asyncio
- **文件处理**: 临时文件管理和清理

### 3.2 传输方式
- **主要**: SSE (Server-Sent Events) - 适用于云部署
- **备选**: STDIO - 适用于本地开发

### 3.3 配置管理
通过环境变量进行配置:
- `OPENAI_API_KEY`: AI模型API密钥
- `OPENAI_MODEL`: 使用的AI模型
- `OPENAI_BASE_URL`: API基础URL
- `DEFAULT_LANG_IN`: 默认源语言
- `DEFAULT_LANG_OUT`: 默认目标语言
- `QPS`: 默认查询每秒数
- `MCP_HOST`: MCP服务器监听地址
- `MCP_PORT`: MCP服务器监听端口

## 4. 接口设计

### 4.1 工具接口

#### translate_pdf
```python
@mcp.tool()
def translate_pdf(
    file_path: str,
    lang_in: str = "en",
    lang_out: str = "zh",
    qps: int = 4,
    no_dual: bool = False,
    no_mono: bool = False,
    watermark_output_mode: str = "no_watermark"
) -> dict:
    """
    翻译PDF文档
    
    Args:
        file_path: PDF文件路径
        lang_in: 源语言代码
        lang_out: 目标语言代码
        qps: 每秒查询数限制
        no_dual: 是否禁用双语对照版本
        no_mono: 是否禁用单语翻译版本
        watermark_output_mode: 水印模式 (no_watermark/watermarked/both)
    
    Returns:
        dict: {"task_id": str, "message": str}
    """
```

#### get_translation_status
```python
@mcp.tool()
def get_translation_status(task_id: str) -> dict:
    """
    查询翻译任务状态
    
    Args:
        task_id: 翻译任务ID
    
    Returns:
        dict: {
            "task_id": str,
            "status": str,  # pending/processing/completed/failed
            "progress": float,  # 0.0-100.0
            "message": str,
            "result_files": dict
        }
    """
```

#### download_translation_result
```python
@mcp.tool()
def download_translation_result(
    task_id: str,
    file_type: str = "dual"
) -> str:
    """
    下载翻译结果文件
    
    Args:
        task_id: 翻译任务ID
        file_type: 文件类型 (dual/mono)
    
    Returns:
        str: 下载链接或文件路径
    """
```

### 4.2 资源接口

#### config://
```python
@mcp.resource("config://")
def get_config() -> str:
    """返回当前配置信息"""
```

#### tasks://
```python
@mcp.resource("tasks://")
def get_all_tasks() -> str:
    """返回所有翻译任务状态"""
```

## 5. 部署要求

### 5.1 环境要求
- Python 3.12+
- UV包管理器
- 足够的磁盘空间存储临时文件
- 网络访问权限(调用AI API)

### 5.2 部署方式
1. **本地开发部署**
   - STDIO传输方式
   - 直接通过UV运行

2. **云服务器部署**
   - SSE传输方式
   - 配置外部访问端口
   - 建议使用反向代理

### 5.3 安全考虑
- API密钥安全存储
- 文件上传大小限制
- 临时文件定期清理
- 访问频率限制

## 6. 客户端兼容性

### 6.1 已测试兼容
- Cherry Studio
- Dify
- N8N

### 6.2 理论兼容
- Cursor
- Cline
- FastGPT
- 其他支持MCP协议的客户端

## 7. 性能指标

### 7.1 翻译性能
- 支持自定义QPS限制
- 异步处理避免阻塞
- 进度实时反馈

### 7.2 系统性能
- 内存使用: 根据PDF大小动态调整
- 磁盘使用: 临时文件自动清理
- 网络使用: 依赖AI API调用频率

## 8. 错误处理

### 8.1 常见错误
- 文件格式不支持
- API密钥无效
- 网络连接失败
- 磁盘空间不足

### 8.2 错误响应
所有错误都通过标准MCP错误格式返回，包含错误代码和详细信息。

## 9. 未来扩展

### 9.1 功能扩展
- 支持更多文档格式
- 批量翻译功能
- 翻译记忆库集成
- 自定义翻译模板

### 9.2 性能优化
- 缓存机制
- 分布式处理
- GPU加速支持

## 10. 验收标准

### 10.1 功能验收
- [ ] 成功翻译PDF文档
- [ ] 正确返回任务状态
- [ ] 文件下载功能正常
- [ ] 配置信息获取正确

### 10.2 兼容性验收
- [ ] Cherry Studio客户端调用成功
- [ ] Dify平台集成正常
- [ ] N8N工作流调用成功

### 10.3 性能验收
- [ ] 单个文档翻译时间在合理范围内
- [ ] 并发处理不影响系统稳定性
- [ ] 内存和磁盘使用控制在预期范围内

---

**文档版本**: v1.0  
**创建日期**: 2025-07-28  
**最后更新**: 2025-07-28