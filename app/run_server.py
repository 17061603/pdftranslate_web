#!/usr/bin/env python3


import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from api_server import start_server

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="启动pdf翻译API服务器")
    parser.add_argument("--host", default="0.0.0.0", help="服务器主机地址 (默认: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="服务器端口 (默认: 8000)")
    
    args = parser.parse_args()
    
    print(f"正在启动pdf翻译API服务器...")
    print(f"服务器地址: http://{args.host}:{args.port}")
    print(f"API文档: http://{args.host}:{args.port}/docs")
    
    start_server(host=args.host, port=args.port)