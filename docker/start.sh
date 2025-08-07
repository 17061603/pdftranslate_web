#!/bin/bash
set -e

# 检查必需的环境变量
if [ -z "$OPENAI_API_KEY" ]; then
    echo "错误: 必须设置 OPENAI_API_KEY 环境变量"
    exit 1
fi

echo "=== BabelDOC PDF翻译服务 ==="
echo "OpenAI模型: ${OPENAI_MODEL:-deepseek-ai/DeepSeek-V3}"
echo "API服务: http://localhost:8000"
echo "Web界面: http://localhost:7860"
echo "========================="

# 启动API服务器(后台)
echo "启动API服务器..."
python3 /app/scripts/run_server.py

# # 等待API服务器启动
# sleep 10

# # 启动Gradio客户端
# echo "启动Web界面..."
# python3 /app/scripts/run_gradio.py --server-url http://localhost:8000 --host 0.0.0.0 --port 7860