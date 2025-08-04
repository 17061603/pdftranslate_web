import asyncio
import logging
import uuid
import os
import tempfile
import shutil
import json
import base64
import aiohttp
import configparser
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# 尝试导入腾讯云COS相关模块
try:
    from qcloud_cos import CosConfig, CosS3Client
    COS_AVAILABLE = True
    print("✅ 腾讯云COS库已成功加载")
except ImportError as e:
    COS_AVAILABLE = False
    print("❌ 警告: 腾讯云COS库未安装")
    print("📦 请使用以下命令安装:")
    print("   pip install cos-python-sdk-v5")
    print("   或者")
    print("   uv pip install cos-python-sdk-v5")
    print(f"详细错误信息: {e}")

# 尝试导入BabelDOC相关模块
try:
    import babeldoc.format.pdf.high_level
    from babeldoc.format.pdf.translation_config import TranslationConfig, WatermarkOutputMode
    from babeldoc.translator.translator import OpenAITranslator, set_translate_rate_limiter
    from babeldoc.docvision.doclayout import DocLayoutModel
    BABELDOC_AVAILABLE = True
    print("✅ BabelDOC库已成功加载")
except ImportError as e:
    BABELDOC_AVAILABLE = False
    print("❌ 警告: BabelDOC库未安装")
    print("📦 请使用以下命令安装BabelDOC:")
    print("   pip install babeldoc")
    print("   或者")
    print("   uv pip install babeldoc")
    print(f"详细错误信息: {e}")

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

def load_cos_config():
    """从config.ini和环境变量加载COS配置"""
    cos_config = {}
    
    # 优先从环境变量加载
    cos_config["region"] = os.getenv("COS_REGION")
    cos_config["secret_id"] = os.getenv("COS_SECRET_ID") 
    cos_config["secret_key"] = os.getenv("COS_SECRET_KEY")
    cos_config["bucket"] = os.getenv("COS_BUCKET")
    
    # 如果环境变量没有设置，从config.ini加载
    config_file_path = os.getenv('CONFIG_INI_PATH', 'config.ini')
    if os.path.exists(config_file_path):
        config = configparser.ConfigParser()
        config.read(config_file_path, encoding='utf-8')
        
        if not cos_config["region"]:
            cos_config["region"] = config.get('common', 'cos_region', fallback=None)
        if not cos_config["secret_id"]:
            cos_config["secret_id"] = config.get('common', 'cos_secret_id', fallback=None)
        if not cos_config["secret_key"]:
            cos_config["secret_key"] = config.get('common', 'cos_secret_key', fallback=None)
        if not cos_config["bucket"]:
            cos_config["bucket"] = config.get('common', 'cos_bucket', fallback=None)
    
    return cos_config

# 全局配置
CONFIG = {
    "openai": {
        "api_key": os.getenv("OPENAI_API_KEY", ""),
        "model": os.getenv("OPENAI_MODEL", "DeepSeek-V3"),
        "base_url": os.getenv("OPENAI_BASE_URL", "https://ai.gitee.com/v1")
    },
    "translation": {
        "default_lang_in": os.getenv("DEFAULT_LANG_IN", "en"),
        "default_lang_out": os.getenv("DEFAULT_LANG_OUT", "zh"),
        "qps": int(os.getenv("QPS", "4")),
        "watermark_output_mode": os.getenv("WATERMARK_OUTPUT_MODE", "no_watermark"),
        "no_dual": os.getenv("NO_DUAL", "false").lower() == "true",
        "no_mono": os.getenv("NO_MONO", "false").lower() == "true"
    },
    "server": {
        "host": os.getenv("MCP_HOST", "0.0.0.0"),
        "port": int(os.getenv("MCP_PORT", "8003"))
    },
    "cos": load_cos_config()
}

# 验证配置
if not CONFIG["openai"]["api_key"]:
    logger.warning("未找到OpenAI API密钥！请通过环境变量OPENAI_API_KEY提供")

# 创建MCP服务器
mcp = FastMCP("PDFTranslate")

# 全局任务存储
translation_tasks: Dict[str, Dict[str, Any]] = {}
task_files: Dict[str, Dict[str, Path]] = {}

async def download_file_from_url(url: str, target_path: Path) -> bool:
    """
    从URL下载文件到本地路径
    
    Args:
        url: 文件URL
        target_path: 目标文件路径
        
    Returns:
        bool: 下载是否成功
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    with open(target_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                    return True
                else:
                    logger.error(f"下载失败，HTTP状态码: {response.status}")
                    return False
    except Exception as e:
        logger.error(f"下载文件时出错: {e}")
        return False

def save_base64_file(base64_content: str, target_path: Path) -> bool:
    """
    保存base64编码的文件内容到本地
    
    Args:
        base64_content: base64编码的文件内容
        target_path: 目标文件路径
        
    Returns:
        bool: 保存是否成功
    """
    try:
        # 如果包含data URL前缀，去掉它
        if ',' in base64_content and base64_content.startswith('data:'):
            base64_content = base64_content.split(',', 1)[1]
        
        file_data = base64.b64decode(base64_content)
        with open(target_path, 'wb') as f:
            f.write(file_data)
        return True
    except Exception as e:
        logger.error(f"保存base64文件时出错: {e}")
        return False

def validate_pdf_file(file_path: Path) -> bool:
    """
    验证文件是否为有效的PDF文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        bool: 是否为有效PDF
    """
    try:
        with open(file_path, 'rb') as f:
            header = f.read(8)
            return header.startswith(b'%PDF-')
    except Exception:
        return False

def upload_file_to_cos(file_path: Path, file_name: str = None) -> Dict[str, Any]:
    """
    上传文件到腾讯云COS
    
    Args:
        file_path: 本地文件路径
        file_name: COS中的文件名，如果为None则使用原文件名
        
    Returns:
        dict: 上传结果，包含success状态和url或error信息
    """
    if not COS_AVAILABLE:
        return {
            "success": False,
            "error": "腾讯云COS库未安装，无法上传文件",
            "message": "请先安装cos-python-sdk-v5库"
        }
    
    cos_config = CONFIG["cos"]
    if not all([cos_config.get("region"), cos_config.get("secret_id"), 
                cos_config.get("secret_key"), cos_config.get("bucket")]):
        return {
            "success": False,
            "error": "COS配置不完整",
            "message": "请检查config.ini或环境变量中的COS配置",
            "missing_config": {
                "region": not cos_config.get("region"),
                "secret_id": not cos_config.get("secret_id"),
                "secret_key": not cos_config.get("secret_key"),
                "bucket": not cos_config.get("bucket")
            }
        }
    
    try:
        # 创建COS客户端
        config = CosConfig(
            Region=cos_config["region"],
            SecretId=cos_config["secret_id"],
            SecretKey=cos_config["secret_key"]
        )
        client = CosS3Client(config)
        
        # 如果没有指定文件名，使用原文件名
        if not file_name:
            file_name = file_path.name
        
        # 添加时间戳避免文件名冲突
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        name_parts = file_name.rsplit('.', 1)
        if len(name_parts) == 2:
            file_name = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
        else:
            file_name = f"{file_name}_{timestamp}"
        
        # 上传文件
        with open(file_path, 'rb') as f:
            response = client.put_object(
                Bucket=cos_config["bucket"],
                Body=f,
                Key=file_name,
                EnableMD5=False
            )
        
        if response and response.get('ETag'):
            # 构造文件URL
            url = f"https://{cos_config['bucket']}.cos.{cos_config['region']}.myqcloud.com/{file_name}"
            return {
                "success": True,
                "url": url,
                "file_name": file_name,
                "etag": response['ETag'],
                "message": "文件上传成功"
            }
        else:
            return {
                "success": False,
                "error": "上传失败",
                "message": f"COS响应异常: {response}"
            }
            
    except Exception as e:
        logger.error(f"上传文件到COS时出错: {e}")
        return {
            "success": False,
            "error": f"上传过程出错: {str(e)}",
            "message": "请检查COS配置和网络连接"
        }

class TranslationTask:
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.status = "pending"  # pending, processing, completed, failed
        self.progress = 0.0
        self.message = "任务已创建，等待处理..."
        self.result_files = {}
        self.cos_urls = {}  # 添加COS URL存储
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self):
        return {
            "task_id": self.task_id,
            "status": self.status,
            "progress": self.progress,
            "message": self.message,
            "result_files": self.result_files,
            "cos_urls": self.cos_urls,  # 包含COS URL信息
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

async def translate_document_async(
    task_id: str,
    pdf_file: Path,
    lang_in: str,
    lang_out: str,
    qps: int,
    no_dual: bool,
    no_mono: bool,
    watermark_output_mode: str,
    output_dir: Path
):
    """异步翻译文档"""
    if not BABELDOC_AVAILABLE:
        translation_tasks[task_id].status = "failed"
        translation_tasks[task_id].message = "BabelDOC库未安装，无法进行翻译"
        return
    
    try:
        task = translation_tasks[task_id]
        task.status = "processing"
        task.message = "正在初始化翻译器..."
        task.updated_at = datetime.now().isoformat()
        
        # 初始化翻译器
        translator = OpenAITranslator(
            lang_in=lang_in,
            lang_out=lang_out,
            model=CONFIG["openai"]["model"],
            base_url=CONFIG["openai"]["base_url"],
            api_key=CONFIG["openai"]["api_key"],
            ignore_cache=False,
        )
        
        set_translate_rate_limiter(qps)
        
        # 加载文档布局模型
        doc_layout_model = DocLayoutModel.load_onnx()
        
        # 配置水印模式
        watermark_mode = WatermarkOutputMode.NoWatermark
        if watermark_output_mode == "watermarked":
            watermark_mode = WatermarkOutputMode.Watermarked
        elif watermark_output_mode == "both":
            watermark_mode = WatermarkOutputMode.Both
        
        # 创建翻译配置
        config_obj = TranslationConfig(
            input_file=str(pdf_file),
            output_dir=str(output_dir),
            translator=translator,
            lang_in=lang_in,
            lang_out=lang_out,
            no_dual=no_dual,
            no_mono=no_mono,
            qps=qps,
            doc_layout_model=doc_layout_model,
            watermark_output_mode=watermark_mode,
            debug=False,
            pages=None,
            font=None,
            formular_font_pattern=None,
            formular_char_pattern=None,
            split_short_lines=False,
            short_line_split_factor=0.8,
            skip_clean=False,
            dual_translate_first=False,
            disable_rich_text_translate=False,
            enhance_compatibility=False,
            use_alternating_pages_dual=False,
            report_interval=0.1,
            min_text_length=5,
            split_strategy=None,
            table_model=None,
            show_char_box=False,
            skip_scanned_detection=False,
            ocr_workaround=False,
            custom_system_prompt=None,
            working_dir=None,
            add_formula_placehold_hint=False,
            glossaries=[],
            pool_max_workers=None,
            auto_extract_glossary=True,
            auto_enable_ocr_workaround=False,
            primary_font_family=None,
            only_include_translated_page=False,
            save_auto_extracted_glossary=False,
        )
        
        task.message = "正在翻译文档..."
        
        # 执行翻译
        async for event in babeldoc.format.pdf.high_level.async_translate(config_obj):
            if event["type"] == "progress_update":
                task.progress = event.get("overall_progress", 0.0)
                task.message = f"{event.get('stage', '处理中')} ({event.get('stage_current', 0)}/{event.get('stage_total', 100)})"
                task.updated_at = datetime.now().isoformat()
            elif event["type"] == "error":
                task.status = "failed"
                task.message = f"翻译失败: {event.get('error', '未知错误')}"
                task.updated_at = datetime.now().isoformat()
                logger.error(f"Translation failed for task {task_id}: {event.get('error')}")
                return
            elif event["type"] == "finish":
                result = event["translate_result"]
                task.status = "completed"
                task.progress = 100.0
                task.message = "翻译完成"
                task.updated_at = datetime.now().isoformat()
                
                # 收集结果文件并上传到COS
                result_files = {}
                cos_urls = {}
                
                if result.dual_pdf_path and Path(result.dual_pdf_path).exists():
                    dual_path = Path(result.dual_pdf_path)
                    result_files["dual"] = str(dual_path)
                    
                    # 上传双语版本到COS
                    task.message = "正在上传双语版本到云存储..."
                    task.updated_at = datetime.now().isoformat()
                    upload_result = upload_file_to_cos(dual_path, f"dual_{dual_path.name}")
                    if upload_result.get("success"):
                        cos_urls["dual"] = upload_result["url"]
                        logger.info(f"双语版本已上传到COS: {upload_result['url']}")
                    else:
                        logger.warning(f"双语版本上传COS失败: {upload_result.get('error')}")
                
                if result.mono_pdf_path and Path(result.mono_pdf_path).exists():
                    mono_path = Path(result.mono_pdf_path)
                    result_files["mono"] = str(mono_path)
                    
                    # 上传单语版本到COS
                    task.message = "正在上传单语版本到云存储..."
                    task.updated_at = datetime.now().isoformat()
                    upload_result = upload_file_to_cos(mono_path, f"mono_{mono_path.name}")
                    if upload_result.get("success"):
                        cos_urls["mono"] = upload_result["url"]
                        logger.info(f"单语版本已上传到COS: {upload_result['url']}")
                    else:
                        logger.warning(f"单语版本上传COS失败: {upload_result.get('error')}")
                
                task.result_files = result_files
                task.cos_urls = cos_urls  # 添加COS URL信息
                task_files[task_id] = {k: Path(v) for k, v in result_files.items()}
                
                # 更新最终状态
                if cos_urls:
                    task.message = f"翻译完成，文件已上传到云存储。可用版本: {', '.join(cos_urls.keys())}"
                else:
                    task.message = "翻译完成，但文件上传到云存储失败，可通过其他方式获取文件"
                
                logger.info(f"Translation completed for task {task_id}")
                break
                
    except Exception as e:
        task = translation_tasks[task_id]
        task.status = "failed"
        task.message = f"翻译过程出错: {str(e)}"
        task.updated_at = datetime.now().isoformat()
        logger.error(f"Translation error for task {task_id}: {e}", exc_info=True)

@mcp.tool()
async def translate_pdf(
    file_input: str,
    input_type: str = "base64",
    filename: str = "document.pdf",
    lang_in: str = None,
    lang_out: str = None,
    qps: int = None,
    no_dual: bool = False,
    no_mono: bool = False,
    watermark_output_mode: str = None
) -> dict:
    """
    翻译PDF文档 - 支持多种文件输入方式
    
    Args:
        file_input: 文件输入内容
            - 当input_type="base64"时，为base64编码的文件内容
            - 当input_type="url"时，为文件下载URL
            - 当input_type="path"时，为本地文件路径（仅限本地开发）
        input_type: 输入类型 ("base64", "url", "path")
        filename: 文件名称（用于识别和存储）
        lang_in: 源语言代码 (默认: en)
        lang_out: 目标语言代码 (默认: zh)
        qps: 每秒查询数限制 (默认: 4)
        no_dual: 是否禁用双语对照版本 (默认: False)
        no_mono: 是否禁用单语翻译版本 (默认: False)
        watermark_output_mode: 水印模式 (no_watermark/watermarked/both，默认: no_watermark)
    
    Returns:
        dict: {"task_id": str, "message": str, "status": str} 或错误信息
    """
    # 检查BabelDOC是否可用
    if not BABELDOC_AVAILABLE:
        return {
            "error": "BabelDOC库未安装，无法进行翻译",
            "message": "请先安装BabelDOC库",
            "install_commands": [
                "pip install babeldoc",
                "uv pip install babeldoc"
            ],
            "status": "failed"
        }
    
    # 检查API密钥
    if not CONFIG["openai"]["api_key"]:
        return {
            "error": "未配置OpenAI API密钥",
            "message": "请在.env文件中设置OPENAI_API_KEY",
            "status": "failed"
        }
    
    # 验证输入类型
    if input_type not in ["base64", "url", "path"]:
        return {
            "error": "不支持的输入类型",
            "message": f"支持的输入类型: base64, url, path。当前: {input_type}",
            "status": "failed"
        }
    
    try:
        # 创建临时目录和文件
        temp_dir = Path(tempfile.mkdtemp())
        
        # 确保文件名以.pdf结尾
        if not filename.lower().endswith('.pdf'):
            filename += '.pdf'
        
        pdf_path = temp_dir / filename
        
        # 根据输入类型处理文件
        if input_type == "base64":
            logger.info(f"正在处理base64文件: {filename}")
            if not save_base64_file(file_input, pdf_path):
                return {
                    "error": "base64文件解码失败",
                    "message": "请检查base64编码格式是否正确",
                    "status": "failed"
                }
        
        elif input_type == "url":
            logger.info(f"正在从URL下载文件: {file_input}")
            if not await download_file_from_url(file_input, pdf_path):
                return {
                    "error": "文件下载失败",
                    "message": f"无法从URL下载文件: {file_input}",
                    "status": "failed"
                }
        
        elif input_type == "path":
            logger.info(f"正在处理本地文件: {file_input}")
            source_path = Path(file_input)
            if not source_path.exists():
                return {
                    "error": f"文件不存在: {file_input}",
                    "message": "请检查文件路径是否正确",
                    "status": "failed"
                }
            # 复制文件到临时目录
            shutil.copy2(source_path, pdf_path)
        
        # 验证是否为有效的PDF文件
        if not validate_pdf_file(pdf_path):
            return {
                "error": "文件格式验证失败",
                "message": "文件不是有效的PDF格式",
                "status": "failed"
            }
        
        # 检查文件大小（限制为100MB）
        file_size = pdf_path.stat().st_size
        max_size = 100 * 1024 * 1024  # 100MB
        if file_size > max_size:
            return {
                "error": "文件过大",
                "message": f"文件大小 {file_size/1024/1024:.1f}MB 超过限制 {max_size/1024/1024}MB",
                "status": "failed"
            }
        
        # 使用默认值
        lang_in = lang_in or CONFIG["translation"]["default_lang_in"]
        lang_out = lang_out or CONFIG["translation"]["default_lang_out"]
        qps = qps or CONFIG["translation"]["qps"]
        watermark_output_mode = watermark_output_mode or CONFIG["translation"]["watermark_output_mode"]
        
        # 创建任务
        task_id = str(uuid.uuid4())
        task = TranslationTask(task_id)
        translation_tasks[task_id] = task
        
        # 创建输出目录
        output_dir = temp_dir / "output"
        output_dir.mkdir(exist_ok=True)
        
        # 启动异步翻译任务
        asyncio.create_task(translate_document_async(
            task_id, pdf_path, lang_in, lang_out, qps, 
            no_dual, no_mono, watermark_output_mode, output_dir
        ))
        
        logger.info(f"翻译任务已创建: {task_id}, 文件: {filename}")
        
        return {
            "task_id": task_id,
            "message": f"翻译任务已创建，正在从{lang_in}翻译到{lang_out}",
            "status": "pending",
            "file_name": filename,
            "file_size_mb": round(file_size / 1024 / 1024, 2),
            "input_type": input_type,
            "settings": {
                "source_language": lang_in,
                "target_language": lang_out,
                "qps": qps,
                "dual_output": not no_dual,
                "mono_output": not no_mono,
                "watermark_mode": watermark_output_mode
            }
        }
        
    except Exception as e:
        logger.error(f"创建翻译任务时出错: {e}")
        return {
            "error": f"创建翻译任务失败: {str(e)}",
            "message": "请检查文件内容和参数设置",
            "status": "failed"
        }

@mcp.tool()
def get_translation_status(task_id: str) -> dict:
    """
    查询翻译任务状态
    
    Args:
        task_id: 翻译任务ID
    
    Returns:
        dict: 任务状态信息
    """
    if task_id not in translation_tasks:
        return {
            "error": "任务不存在",
            "message": f"找不到任务ID: {task_id}",
            "status": "not_found"
        }
    
    task = translation_tasks[task_id]
    return task.to_dict()

@mcp.tool()
def get_translation_result_base64(task_id: str, file_type: str = "dual") -> dict:
    """
    获取翻译结果文件的base64编码内容
    
    Args:
        task_id: 翻译任务ID
        file_type: 文件类型 (dual/mono)
    
    Returns:
        dict: 包含base64编码内容的文件信息
    """
    if task_id not in translation_tasks:
        return {
            "error": "任务不存在",
            "message": f"找不到任务ID: {task_id}",
            "status": "not_found"
        }
    
    task = translation_tasks[task_id]
    if task.status != "completed":
        return {
            "error": "翻译尚未完成",
            "message": f"当前任务状态: {task.status}，请等待翻译完成",
            "current_status": task.status,
            "progress": task.progress
        }
    
    if task_id not in task_files or file_type not in task_files[task_id]:
        available_types = list(task_files.get(task_id, {}).keys())
        return {
            "error": f"文件类型 '{file_type}' 不存在",
            "message": f"可用的文件类型: {available_types}",
            "available_types": available_types
        }
    
    file_path = task_files[task_id][file_type]
    if not file_path.exists():
        return {
            "error": "文件不存在",
            "message": f"翻译结果文件已被删除或移动: {file_path}",
            "status": "file_missing"
        }
    
    try:
        # 读取文件并转换为base64
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        base64_content = base64.b64encode(file_data).decode('utf-8')
        
        return {
            "success": True,
            "file_name": file_path.name,
            "file_size": len(file_data),
            "file_size_mb": round(len(file_data) / 1024 / 1024, 2),
            "file_type": file_type,
            "base64_content": base64_content,
            "data_url": f"data:application/pdf;base64,{base64_content}",
            "message": f"成功获取{file_type}类型的翻译结果文件base64编码"
        }
        
    except Exception as e:
        logger.error(f"读取文件时出错: {e}")
        return {
            "error": f"读取文件失败: {str(e)}",
            "message": "无法读取翻译结果文件",
            "status": "read_error"
        }

@mcp.tool()
def get_translation_result_cos_url(task_id: str, file_type: str = "dual") -> dict:
    """
    获取翻译结果文件的COS URL
    
    Args:
        task_id: 翻译任务ID
        file_type: 文件类型 (dual/mono)
    
    Returns:
        dict: 包含COS URL的文件信息
    """
    if task_id not in translation_tasks:
        return {
            "error": "任务不存在",
            "message": f"找不到任务ID: {task_id}",
            "status": "not_found"
        }
    
    task = translation_tasks[task_id]
    if task.status != "completed":
        return {
            "error": "翻译尚未完成",
            "message": f"当前任务状态: {task.status}，请等待翻译完成",
            "current_status": task.status,
            "progress": task.progress
        }
    
    if not hasattr(task, 'cos_urls') or not task.cos_urls:
        return {
            "error": "文件未上传到云存储",
            "message": "翻译完成但文件未成功上传到COS，请使用其他方式获取文件",
            "status": "no_cos_upload"
        }
    
    if file_type not in task.cos_urls:
        available_types = list(task.cos_urls.keys())
        return {
            "error": f"文件类型 '{file_type}' 的COS URL不存在",
            "message": f"可用的文件类型: {available_types}",
            "available_types": available_types
        }
    
    return {
        "success": True,
        "file_type": file_type,
        "cos_url": task.cos_urls[file_type],
        "message": f"成功获取{file_type}类型的翻译结果文件COS URL",
        "download_url": task.cos_urls[file_type]
    }

@mcp.tool()
def download_translation_result(task_id: str, file_type: str = "dual") -> dict:
    """
    获取翻译结果文件信息
    
    Args:
        task_id: 翻译任务ID
        file_type: 文件类型 (dual/mono)
    
    Returns:
        dict: 文件信息
    """
    if task_id not in translation_tasks:
        return {
            "error": "任务不存在",
            "message": f"找不到任务ID: {task_id}",
            "status": "not_found"
        }
    
    task = translation_tasks[task_id]
    if task.status != "completed":
        return {
            "error": "翻译尚未完成",
            "message": f"当前任务状态: {task.status}，请等待翻译完成",
            "current_status": task.status,
            "progress": task.progress
        }
    
    if task_id not in task_files or file_type not in task_files[task_id]:
        available_types = list(task_files.get(task_id, {}).keys())
        return {
            "error": f"文件类型 '{file_type}' 不存在",
            "message": f"可用的文件类型: {available_types}",
            "available_types": available_types
        }
    
    file_path = task_files[task_id][file_type]
    if not file_path.exists():
        return {
            "error": "文件不存在",
            "message": f"翻译结果文件已被删除或移动: {file_path}",
            "status": "file_missing"
        }
    
    return {
        "success": True,
        "file_path": str(file_path),
        "file_name": file_path.name,
        "file_size": file_path.stat().st_size,
        "file_type": file_type,
        "message": f"找到{file_type}类型的翻译结果文件"
    }

@mcp.tool()
def check_system_status() -> dict:
    """
    检查系统状态和依赖
    
    Returns:
        dict: 系统状态信息
    """
    cos_config = CONFIG["cos"]
    cos_configured = all([cos_config.get("region"), cos_config.get("secret_id"), 
                         cos_config.get("secret_key"), cos_config.get("bucket")])
    
    status = {
        "service_name": "PDFTranslate MCP Server",
        "version": "1.0.0",
        "babeldoc_available": BABELDOC_AVAILABLE,
        "cos_available": COS_AVAILABLE,
        "api_key_configured": bool(CONFIG["openai"]["api_key"]),
        "cos_configured": cos_configured,
        "dependencies": {
            "babeldoc": "✅ 已安装" if BABELDOC_AVAILABLE else "❌ 未安装",
            "openai_api": "✅ 已配置" if CONFIG["openai"]["api_key"] else "❌ 未配置",
            "cos_sdk": "✅ 已安装" if COS_AVAILABLE else "❌ 未安装",
            "cos_config": "✅ 已配置" if cos_configured else "❌ 未配置"
        },
        "configuration": {
            "model": CONFIG["openai"]["model"],
            "base_url": CONFIG["openai"]["base_url"],
            "default_languages": f"{CONFIG['translation']['default_lang_in']} -> {CONFIG['translation']['default_lang_out']}",
            "default_qps": CONFIG["translation"]["qps"],
            "cos_region": cos_config.get("region", "未配置"),
            "cos_bucket": cos_config.get("bucket", "未配置")
        },
        "active_tasks": len(translation_tasks),
        "ready": BABELDOC_AVAILABLE and bool(CONFIG["openai"]["api_key"]),
        "cos_upload_ready": COS_AVAILABLE and cos_configured
    }
    
    if not BABELDOC_AVAILABLE:
        status["install_instructions"] = {
            "message": "请安装BabelDOC库以启用PDF翻译功能",
            "commands": [
                "pip install babeldoc",
                "uv pip install babeldoc"
            ]
        }
    
    if not COS_AVAILABLE:
        status["cos_install_instructions"] = {
            "message": "请安装腾讯云COS SDK以启用文件上传功能",
            "commands": [
                "pip install cos-python-sdk-v5",
                "uv pip install cos-python-sdk-v5"
            ]
        }
    
    if not CONFIG["openai"]["api_key"]:
        status["api_key_instructions"] = {
            "message": "请配置OpenAI API密钥",
            "steps": [
                "1. 复制 .env.example 为 .env",
                "2. 在 .env 文件中设置 OPENAI_API_KEY=your_api_key",
                "3. 重启MCP服务器"
            ]
        }
    
    if not cos_configured:
        status["cos_config_instructions"] = {
            "message": "请配置腾讯云COS参数以启用文件上传功能",
            "config_methods": [
                {
                    "method": "环境变量配置",
                    "steps": [
                        "设置 COS_REGION=your_region",
                        "设置 COS_SECRET_ID=your_secret_id", 
                        "设置 COS_SECRET_KEY=your_secret_key",
                        "设置 COS_BUCKET=your_bucket"
                    ]
                },
                {
                    "method": "config.ini配置",
                    "steps": [
                        "在config.ini的[common]部分添加:",
                        "cos_region = your_region",
                        "cos_secret_id = your_secret_id",
                        "cos_secret_key = your_secret_key", 
                        "cos_bucket = your_bucket"
                    ]
                }
            ],
            "note": "环境变量优先级高于config.ini配置"
        }
    
    return status

@mcp.tool()
def list_all_tasks() -> dict:
    """
    列出所有翻译任务
    
    Returns:
        dict: 所有任务状态
    """
    return {
        "total_tasks": len(translation_tasks),
        "tasks": [task.to_dict() for task in translation_tasks.values()]
    }

@mcp.tool()
def update_cos_config(
    cos_region: str = None,
    cos_secret_id: str = None, 
    cos_secret_key: str = None,
    cos_bucket: str = None
) -> dict:
    """
    动态更新COS配置参数
    
    Args:
        cos_region: COS地域
        cos_secret_id: COS密钥ID
        cos_secret_key: COS密钥Key
        cos_bucket: COS存储桶名称
    
    Returns:
        dict: 更新结果
    """
    try:
        updated_fields = []
        
        if cos_region:
            CONFIG["cos"]["region"] = cos_region
            updated_fields.append("region")
        
        if cos_secret_id:
            CONFIG["cos"]["secret_id"] = cos_secret_id
            updated_fields.append("secret_id")
            
        if cos_secret_key:
            CONFIG["cos"]["secret_key"] = cos_secret_key
            updated_fields.append("secret_key")
            
        if cos_bucket:
            CONFIG["cos"]["bucket"] = cos_bucket
            updated_fields.append("bucket")
        
        if not updated_fields:
            return {
                "success": False,
                "message": "没有提供任何配置参数",
                "current_config": {
                    "region": CONFIG["cos"].get("region", "未配置"),
                    "secret_id": "已配置" if CONFIG["cos"].get("secret_id") else "未配置",
                    "secret_key": "已配置" if CONFIG["cos"].get("secret_key") else "未配置", 
                    "bucket": CONFIG["cos"].get("bucket", "未配置")
                }
            }
        
        # 检查配置完整性
        cos_config = CONFIG["cos"]
        is_complete = all([cos_config.get("region"), cos_config.get("secret_id"), 
                          cos_config.get("secret_key"), cos_config.get("bucket")])
        
        return {
            "success": True,
            "message": f"COS配置已更新: {', '.join(updated_fields)}",
            "updated_fields": updated_fields,
            "config_complete": is_complete,
            "cos_upload_ready": COS_AVAILABLE and is_complete,
            "current_config": {
                "region": CONFIG["cos"].get("region", "未配置"),
                "secret_id": "已配置" if CONFIG["cos"].get("secret_id") else "未配置",
                "secret_key": "已配置" if CONFIG["cos"].get("secret_key") else "未配置",
                "bucket": CONFIG["cos"].get("bucket", "未配置")
            }
        }
        
    except Exception as e:
        logger.error(f"更新COS配置时出错: {e}")
        return {
            "success": False,
            "error": f"更新配置失败: {str(e)}",
            "message": "请检查提供的配置参数"
        }

@mcp.tool()
def get_supported_languages() -> dict:
    """
    获取支持的语言列表
    
    Returns:
        dict: 支持的语言代码
    """
    return {
        "languages": {
            "zh": "中文",
            "en": "English",
            "ja": "日本語",
            "ko": "한국어",
            "fr": "Français",
            "de": "Deutsch",
            "es": "Español",
            "ru": "Русский",
            "it": "Italiano",
            "pt": "Português",
            "ar": "العربية",
            "hi": "हिन्दी"
        },
        "default_lang_in": CONFIG["translation"]["default_lang_in"],
        "default_lang_out": CONFIG["translation"]["default_lang_out"]
    }

@mcp.resource("config://")
def get_config() -> str:
    """返回当前配置信息"""
    config_info = {
        "service_name": "PDFTranslate MCP Server",
        "version": "1.0.0",
        "babeldoc_available": BABELDOC_AVAILABLE,
        "openai_model": CONFIG["openai"]["model"],
        "openai_base_url": CONFIG["openai"]["base_url"],
        "default_languages": {
            "input": CONFIG["translation"]["default_lang_in"],
            "output": CONFIG["translation"]["default_lang_out"]
        },
        "default_qps": CONFIG["translation"]["qps"],
        "watermark_mode": CONFIG["translation"]["watermark_output_mode"]
    }
    return json.dumps(config_info, indent=2, ensure_ascii=False)

@mcp.resource("tasks://")
def get_all_tasks() -> str:
    """返回所有翻译任务状态"""
    tasks_info = {
        "total_tasks": len(translation_tasks),
        "tasks_by_status": {},
        "recent_tasks": []
    }
    
    # 按状态分组
    status_counts = {}
    for task in translation_tasks.values():
        status = task.status
        if status not in status_counts:
            status_counts[status] = 0
        status_counts[status] += 1
    
    tasks_info["tasks_by_status"] = status_counts
    
    # 最近的任务
    recent_tasks = sorted(
        translation_tasks.values(),
        key=lambda x: x.updated_at,
        reverse=True
    )[:10]
    
    tasks_info["recent_tasks"] = [task.to_dict() for task in recent_tasks]
    
    return json.dumps(tasks_info, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    # 初始化BabelDOC（如果可用）
    if BABELDOC_AVAILABLE:
        try:
            babeldoc.format.pdf.high_level.init()
            logger.info("BabelDOC initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize BabelDOC: {e}")
    
    # 配置MCP服务器
    mcp.settings.host = CONFIG["server"]["host"]
    mcp.settings.port = CONFIG["server"]["port"]
    
    # 配置信息日志
    logger.info(f"Starting PDFTranslate MCP Server in SSE mode")
    logger.info(f"Server URL: http://{CONFIG['server']['host']}:{CONFIG['server']['port']}/sse")
    logger.info(f"OpenAI Model: {CONFIG['openai']['model']}")
    logger.info(f"Default Translation: {CONFIG['translation']['default_lang_in']} -> {CONFIG['translation']['default_lang_out']}")
    logger.info(f"BabelDOC Available: {BABELDOC_AVAILABLE}")
    
    # 启动MCP服务器 (SSE模式)
    mcp.run(transport="sse")