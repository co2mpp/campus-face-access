"""服务端启动脚本（端口 5000）
前置条件：
  1. 安装依赖: pip install -r requirements.txt
  2. 启动 MySQL 服务，创建 smart_gate 数据库
  3. 修改 server/config.py 中的 MySQL 连接信息
用法:
  python run_server.py
"""
import sys
import os

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.app import create_app
from server.config import SERVER_PORT

if __name__ == '__main__':
    print("=" * 60)
    print("校园门禁系统 - 服务端")
    print(f"监听端口: {SERVER_PORT}")
    print("=" * 60)
    app = create_app()
    app.run(host='0.0.0.0', port=SERVER_PORT, debug=True)
