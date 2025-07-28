"""
BabelDOC PDF Translation Package

一个基于AI的PDF文档翻译工具包，支持：
- FastAPI REST API服务
- Gradio Web界面
- Python客户端SDK
"""

__version__ = "0.0.1"
__author__ = "wwwzhouhui"

from .api_server import app, start_server
from .api_client import BabelDOCClient
from .gradio_client import create_gradio_interface, GradioClient

__all__ = [
    "app",
    "start_server", 
    "BabelDOCClient",
    "create_gradio_interface",
    "GradioClient"
]