"""客户端启动脚本（端口 5001）
前置条件：
  1. 安装依赖: pip install -r requirements.txt
  2. 确保服务端已启动
  3. 至少连接两个摄像头（或使用单摄像头测试模式）
用法:
  python run_client.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    from client.app import run_client
    run_client()
