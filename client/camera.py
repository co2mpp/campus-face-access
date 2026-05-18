"""摄像头枚举与方向绑定管理"""
import json
import cv2
from client.config import get_db, DEVICE_SN


def enumerate_cameras(max_index: int = 10) -> list[dict]:
    """枚举所有可用摄像头"""
    available = []
    for idx in range(max_index):
        try:
            cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)  # Windows: 使用DirectShow避免MSMF错误
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    available.append({'index': idx, 'name': f'摄像头 #{idx}'})
                cap.release()
        except Exception:
            continue

    # 如果没找到摄像头，尝试更大的索引范围
    if not available:
        for idx in range(max_index, 20):
            try:
                cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
                if cap.isOpened():
                    ret, _ = cap.read()
                    if ret:
                        available.append({'index': idx, 'name': f'摄像头 #{idx}'})
                    cap.release()
            except Exception:
                continue

    return available


def get_binding() -> dict | None:
    """获取已保存的摄像头方向绑定"""
    conn = get_db()
    row = conn.execute(
        "SELECT value FROM config WHERE key='camera_binding'"
    ).fetchone()
    conn.close()
    if row:
        return json.loads(row['value'])
    return None


def save_binding(in_index: int, out_index: int) -> dict:
    """保存摄像头方向绑定（单摄像头时可共用）"""
    binding = {
        'in': in_index,
        'out': out_index,
        'device_sn': DEVICE_SN,
    }
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO config (key, value) VALUES ('camera_binding', ?)",
        (json.dumps(binding),)
    )
    conn.commit()
    conn.close()
    return binding


def is_bound() -> bool:
    return get_binding() is not None


def is_direction_enabled(direction: str) -> bool:
    """检查某个方向是否启用了摄像头"""
    binding = get_binding()
    if not binding:
        return False
    idx = binding.get(direction, -1)
    return isinstance(idx, int) and idx >= 0
