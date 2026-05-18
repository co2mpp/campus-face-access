"""人脸库同步服务"""
import json
import logging
import requests
from client.config import get_db, SERVER_URL, get_aes_key

logger = logging.getLogger('client.sync')


def get_local_version() -> int:
    conn = get_db()
    row = conn.execute(
        "SELECT value FROM config WHERE key='feature_version'"
    ).fetchone()
    conn.close()
    if row:
        return int(row['value'])
    return 0


def set_local_version(version: int):
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO config (key, value) VALUES ('feature_version', ?)",
        (str(version),)
    )
    conn.commit()
    conn.close()


def set_aes_key(key_base64: str):
    """将服务端AES密钥同步到本地（首次使用时）"""
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO config (key, value) VALUES ('aes_key', ?)",
        (key_base64,)
    )
    conn.commit()
    conn.close()


def sync_features(server_url: str = None) -> int:
    """
    增量同步人脸特征库
    返回：本次同步的特征数量
    """
    if server_url is None:
        server_url = SERVER_URL

    since = get_local_version()
    url = f"{server_url}/api/sync/features?since_version={since}"

    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logger.error(f"同步失败: {e}")
        raise

    features = data.get('features', [])
    if not features:
        logger.info("人脸库已是最新版本，无需同步")
        return 0

    conn = get_db()
    try:
        for f in features:
            conn.execute(
                """INSERT OR REPLACE INTO cached_face
                   (student_id, stu_no, name, encrypted_feature, iv, feature_version)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    f['student_id'],
                    f['stu_no'],
                    f['name'],
                    bytes.fromhex(f['encrypted_feature']),
                    bytes.fromhex(f['iv']),
                    f['feature_version'],
                )
            )
        conn.commit()
        new_version = data['global_version']
        set_local_version(new_version)
        logger.info(f"同步完成: {len(features)} 条特征, 版本号 {since}→{new_version}")
    finally:
        conn.close()

    return len(features)
