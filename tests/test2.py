from dotenv import load_dotenv
load_dotenv()  # 自动加载同目录下的 .env 文件
import os
print(os.getenv("OPENAI_API_KEY"))  # 验证是否加载成功