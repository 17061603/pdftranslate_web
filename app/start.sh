#!/bin/bash
set -e

# 检查必需的环境变量
if [ -z "$OPENAI_API_KEY" ]; then
    echo "错误: 必须设置 OPENAI_API_KEY 环境变量"
    exit 1
fi

echo "===  PDF翻译服务 ==="
echo "OpenAI模型: ${OPENAI_MODEL:-deepseek-ai/DeepSeek-V3}"
echo "API服务: http://localhost:8000"
echo "Web界面: http://localhost:7860"
echo "========================="

# 启动API服务器(后台)
echo "启动API服务器..."
python3 run_server.py
