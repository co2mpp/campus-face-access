"""网络状态监测（心跳线程）"""
import time
import threading
import logging
import requests
from client.config import SERVER_URL, DEVICE_SN, HEARTBEAT_INTERVAL, HEARTBEAT_TIMEOUT, OFFLINE_THRESHOLD

logger = logging.getLogger('client.network')


class NetworkMonitor:
    def __init__(self):
        self._online = True
        self._consecutive_failures = 0
        self._thread = None
        self._running = False
        self._callbacks = []  # 状态变更回调列表

    @property
    def is_online(self) -> bool:
        return self._online

    def on_status_change(self, callback):
        """注册状态变更回调 callback(is_online: bool)"""
        self._callbacks.append(callback)

    def _notify(self):
        for cb in self._callbacks:
            try:
                cb(self._online)
            except Exception:
                pass

    def _loop(self):
        while self._running:
            try:
                resp = requests.post(
                    f"{SERVER_URL}/api/heartbeat",
                    json={'device_sn': DEVICE_SN},
                    timeout=HEARTBEAT_TIMEOUT
                )
                success = resp.status_code == 200
            except requests.RequestException:
                success = False

            if success:
                was_offline = not self._online
                self._consecutive_failures = 0
                if not self._online:
                    self._online = True
                    logger.info("网络已恢复")
                    self._notify()
                elif was_offline:
                    self._notify()
            else:
                self._consecutive_failures += 1
                if self._consecutive_failures >= OFFLINE_THRESHOLD and self._online:
                    self._online = False
                    logger.warning(f"网络已断开（连续 {self._consecutive_failures} 次心跳超时）")
                    self._notify()

            time.sleep(HEARTBEAT_INTERVAL)

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name='heartbeat')
        self._thread.start()
        logger.info("心跳监测线程已启动")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
