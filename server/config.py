"""服务端配置"""
import os
import base64
from urllib.parse import quote_plus
from Crypto.Random import get_random_bytes

# MySQL 连接配置
MYSQL_HOST = os.environ.get('MYSQL_HOST', '127.0.0.1')
MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
MYSQL_PASSWORD_RAW = os.environ.get('MYSQL_PASSWORD', 'Xu31415926@qq.com')
MYSQL_PASSWORD = quote_plus(MYSQL_PASSWORD_RAW)
MYSQL_DB = os.environ.get('MYSQL_DB', 'smart_gate')

# SQLAlchemy 连接串
SQLALCHEMY_DATABASE_URI = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@"
    f"{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    f"?charset=utf8mb4"
)

# AES-256 密钥（32字节），Base64存储
# 生产环境应从HSM或安全配置中心获取
AES_KEY_FILE = os.path.join(os.path.dirname(__file__), 'aes_key.txt')


def get_or_create_key() -> bytes:
    if os.path.exists(AES_KEY_FILE):
        with open(AES_KEY_FILE, 'rb') as f:
            return base64.b64decode(f.read().strip())
    key = get_random_bytes(32)
    with open(AES_KEY_FILE, 'wb') as f:
        f.write(base64.b64encode(key))
    return key


AES_KEY = get_or_create_key()

# 服务配置
SERVER_PORT = int(os.environ.get('SERVER_PORT', 5000))
