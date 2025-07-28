#!/usr/bin/env python3
"""
BabelDOC Gradio Client Launcher

启动BabelDOC Gradio客户端界面
"""

import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pdftranslate_web.gradio_client import main

if __name__ == "__main__":
    main()