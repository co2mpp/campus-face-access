"""断网缓存与重传上传线程"""
import json
import time
import threading
import logging
import requests
from client.config import get_db, SERVER_URL, DEVICE_SN

logger = logging.getLogger('client.uploader')

UPLOAD_INTERVAL = 30   # 上传扫描间隔
BATCH_SIZE = 50        # 单次上传最大条数


class RecordUploader:
    def __init__(self, network_monitor):
        self._monitor = network_monitor
        self._thread = None
        self._running = False

    def store_pending(self, record: dict):
        """缓存一条待传记录"""
        conn = get_db()
        conn.execute(
            "INSERT INTO pending_record (record_json) VALUES (?)",
            (json.dumps(record),)
        )
        conn.commit()
        conn.close()

    def _upload_pending(self):
        conn = get_db()
        rows = conn.execute(
            "SELECT id, record_json, retry_count FROM pending_record "
            "ORDER BY id LIMIT ?", (BATCH_SIZE,)
        ).fetchall()
        if not rows:
            conn.close()
            return

        records = []
        ids = []
        for r in rows:
            records.append(json.loads(r['record_json']))
            ids.append(r['id'])

        try:
            resp = requests.post(
                f"{SERVER_URL}/api/record/batch",
                json={'records': records},
                timeout=10
            )
            if resp.status_code == 200:
                placeholders = ','.join('?' * len(ids))
                conn.execute(
                    f"DELETE FROM pending_record WHERE id IN ({placeholders})",
                    ids
                )
                conn.commit()
                logger.info(f"上传成功: {len(ids)} 条记录")
            else:
                # 标记重试
                for rid in ids:
                    conn.execute(
                        "UPDATE pending_record SET retry_count = retry_count + 1 WHERE id = ?",
                        (rid,)
                    )
                conn.commit()
                logger.warning(f"上传失败: HTTP {resp.status_code}")
        except requests.RequestException as e:
            for rid in ids:
                conn.execute(
                    "UPDATE pending_record SET retry_count = retry_count + 1 WHERE id = ?",
                    (rid,)
                )
            conn.commit()
            logger.warning(f"上传异常: {e}")
        finally:
            conn.close()

    def upload_record(self, record: dict) -> bool:
        """尝试直接上传单条记录，失败则缓存"""
        try:
            resp = requests.post(
                f"{SERVER_URL}/api/record",
                json=record,
                timeout=5
            )
            if resp.status_code == 201:
                return True
        except requests.RequestException:
            pass
        self.store_pending(record)
        return False

    def _loop(self):
        while self._running:
            if self._monitor.is_online:
                self._upload_pending()
            time.sleep(UPLOAD_INTERVAL)

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name='uploader')
        self._thread.start()
        logger.info("上传线程已启动")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
