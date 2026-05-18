"""客户端配置"""
import os
import sqlite3
import base64
from Crypto.Random import get_random_bytes

# 客户端数据目录
CLIENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(CLIENT_DIR, 'client_data.db')

# 服务端地址
SERVER_URL = os.environ.get('SERVER_URL', 'http://127.0.0.1:5000')

# 客户端端口
CLIENT_PORT = int(os.environ.get('CLIENT_PORT', 5001))

# 设备序列号
DEVICE_SN = os.environ.get('DEVICE_SN', 'GATE-001')

# 识别参数
RECOGNITION_THRESHOLD = 0.6
DEDUP_INTERVAL_SEC = 10        # 同学生识别去重间隔
FRAME_SKIP = 3                 # 每3帧检测一次
HEARTBEAT_INTERVAL = 30        # 心跳间隔(秒)
HEARTBEAT_TIMEOUT = 5          # 单次心跳超时(秒)
OFFLINE_THRESHOLD = 3          # 连续超时判定离线


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def get_aes_key() -> bytes:
    """从配置表获取AES密钥，不存在则从服务端获取或生成"""
    conn = get_db()
    row = conn.execute("SELECT value FROM config WHERE key='aes_key'").fetchone()
    conn.close()
    if row:
        return base64.b64decode(row['value'])
    raise RuntimeError(
        "AES密钥未配置！请先执行首次同步或手动配置密钥。"
        "提示：密钥与服务端 server/aes_key.txt 中的一致"
    )
