"""
客户端 Flask 主应用 — 监听 5001 端口
- 深色主题 Web 终端控制台（实时视频画面）
- 支持双摄像头 / 单摄像头模式（单摄时共用）
- MJPEG 实时视频流推送
- 心跳监测 / 断网缓存上传
"""
import os
import sys
import time
import json
import logging
import threading
import queue
from datetime import datetime

import numpy as np
import cv2
from flask import Flask, jsonify, request, render_template, Response

from client.config import (
    CLIENT_PORT, SERVER_URL, DEVICE_SN,
    FRAME_SKIP, DEDUP_INTERVAL_SEC,
)
from client.models import init_db
from client.camera import enumerate_cameras, get_binding, save_binding, is_bound
from client.recognizer import RecognizerEngine
from client.sync import sync_features, set_aes_key, get_local_version
from client.network import NetworkMonitor
from client.uploader import RecordUploader

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger('client')

# ========== Web UI — 深色主题终端控制台 ==========


# ========== MJPEG 视频流生成器 ==========
def generate_mjpeg(direction, frame_buffers, frame_locks):
    """生成 MJPEG 流"""
    while True:
        lock = frame_locks.get(direction)
        buf = frame_buffers.get(direction)
        frame = None
        if lock and buf is not None:
            with lock:
                frame = buf.copy() if buf is not None else None
        if frame is None:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            msg = 'Waiting...' if lock else 'Camera disabled'
            cv2.putText(frame, msg, (140, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        if not ret:
            continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
        time.sleep(0.015)  # ~60fps 上限


# ========== 摄像头采集线程（独立运行，保证视频流不卡顿） ==========
class CameraThread(threading.Thread):
    def __init__(self, camera_index: int, direction: str,
                 frame_buffers: dict, frame_locks: dict,
                 secondary_direction: str = None):
        super().__init__(daemon=True, name=f'cam-{direction}')
        self.camera_index = camera_index
        self.direction = direction
        self._secondary = secondary_direction  # 单摄像头时同步写入另一方向
        self._frame_buffers = frame_buffers
        self._frame_locks = frame_locks
        self._latest_frame = None
        self._frame_lock = threading.Lock()
        self.running = False

    def run(self):
        self.running = True
        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        if not cap.isOpened():
            logger.error(f"无法打开摄像头 #{self.camera_index} ({self.direction})")
            return
        logger.info(f"摄像头采集启动: #{self.camera_index} -> {self.direction}" +
                    (f" + {self._secondary}" if self._secondary else ""))
        while self.running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.01)
                continue
            with self._frame_lock:
                self._latest_frame = frame.copy()
            with self._frame_locks[self.direction]:
                self._frame_buffers[self.direction] = frame.copy()
            if self._secondary:
                with self._frame_locks[self._secondary]:
                    self._frame_buffers[self._secondary] = frame.copy()
        cap.release()

    def get_frame(self):
        with self._frame_lock:
            return self._latest_frame  # 已在 run() 中 copy

    def stop(self):
        self.running = False


# ========== 识别线程 ==========
class RecognitionThread(threading.Thread):
    def __init__(self, camera_thread: CameraThread, direction: str,
                 engine: RecognizerEngine, uploader: RecordUploader,
                 frame_buffers: dict, frame_locks: dict):
        super().__init__(daemon=True, name=f'recog-{direction}')
        self._cam = camera_thread
        self.direction = direction
        self.engine = engine
        self.uploader = uploader
        self._frame_buffers = frame_buffers
        self._frame_locks = frame_locks
        self.running = False
        self.events = queue.Queue(maxsize=100)

    def run(self):
        self.running = True
        logger.info(f"识别线程启动: {self.direction}")
        frame_count = 0
        encrypted_db = self.engine.load_encrypted_db()

        while self.running:
            frame = self._cam.get_frame()
            if frame is None:
                time.sleep(0.05)
                continue

            frame_count += 1
            if frame_count % FRAME_SKIP != 0:
                continue

            if frame_count % (FRAME_SKIP * 50) == 0:
                encrypted_db = self.engine.load_encrypted_db()

            results = self.engine.recognize_frame(frame, encrypted_db)

            if results:
                annotated = frame.copy()
                self.engine.draw_results(annotated, results)
                with self._frame_locks[self.direction]:
                    self._frame_buffers[self.direction] = annotated

                for r in results:
                    record = {
                        'student_id': r['student_id'],
                        'device_sn': DEVICE_SN,
                        'direction': self.direction,
                        'result': r['result'],
                        'similarity': r['similarity'],
                        'record_time': datetime.utcnow().isoformat(),
                    }
                    self.uploader.upload_record(record)

                    event = {
                        'time': datetime.now().strftime('%H:%M:%S'),
                        'name': r['name'],
                        'stu_no': r['stu_no'],
                        'direction': self.direction,
                        'similarity': r['similarity'],
                        'result': r['result'],
                    }
                    try:
                        self.events.put_nowait(event)
                    except queue.Full:
                        pass

        logger.info(f"识别线程停止: {self.direction}")

    def stop(self):
        self.running = False


# ========== Flask 应用 ==========
def create_client_app():
    app = Flask(__name__, template_folder='templates')
    app.config['JSON_AS_ASCII'] = False

    app.config['engine'] = None
    app.config['uploader'] = None
    app.config['monitor'] = None
    app.config['recognition_threads'] = []
    app.config['frame_buffers'] = {}
    app.config['frame_locks'] = {}

    import numpy as np

    @app.route('/')
    def index():
        binding = get_binding()
        in_enabled = binding is not None and binding.get('in', -1) >= 0
        out_enabled = binding is not None and binding.get('out', -1) >= 0
        single_camera = binding is not None and in_enabled and out_enabled and binding['in'] == binding['out']
        return render_template(
            'terminal.html',
            device_sn=DEVICE_SN,
            binding=binding,
            binding_json=json.dumps(binding),
            in_enabled=in_enabled,
            out_enabled=out_enabled,
            single_camera=single_camera,
        )

    @app.route('/video_feed/<direction>')
    def video_feed(direction):
        if direction not in ('in', 'out'):
            return 'Invalid direction', 404
        return Response(
            generate_mjpeg(direction, app.config['frame_buffers'], app.config['frame_locks']),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )

    @app.route('/config')
    def config_page():
        cameras = enumerate_cameras()
        binding = get_binding()
        error = request.args.get('error', '')

        return render_template('config.html', cameras=cameras, binding=binding, error=error)

    @app.route('/config/save', methods=['POST'])
    def config_save():
        try:
            in_idx = int(request.form['in_index'])
            out_idx = int(request.form['out_index'])
            save_binding(in_idx, out_idx)
            restart_recognition(app)
            return '配置成功', 200
        except Exception as e:
            return str(e), 400

    @app.route('/api/events')
    def get_events():
        events = []
        for t in app.config.get('recognition_threads', []):
            while not t.events.empty():
                try:
                    events.append(t.events.get_nowait())
                except queue.Empty:
                    break
        return jsonify(events)

    @app.route('/api/status')
    def api_status():
        monitor = app.config.get('monitor')
        binding = get_binding()
        in_enabled = binding is not None and binding.get('in', -1) >= 0
        out_enabled = binding is not None and binding.get('out', -1) >= 0
        single_camera = binding is not None and in_enabled and out_enabled and binding['in'] == binding['out']
        return jsonify({
            'device_sn': DEVICE_SN,
            'online': monitor.is_online if monitor else False,
            'feature_version': get_local_version(),
            'binding': binding,
            'in_enabled': in_enabled,
            'out_enabled': out_enabled,
            'single_camera': single_camera,
        })

    @app.route('/api/pending_count')
    def pending_count():
        """返回待上传（离线缓存）记录数量"""
        from client.config import get_db
        conn = get_db()
        try:
            count = conn.execute("SELECT COUNT(*) FROM pending_record").fetchone()[0]
            return jsonify({'count': count})
        finally:
            conn.close()

    @app.route('/api/uptime')
    def uptime():
        """返回客户端启动时间戳，前端实时计算运行时长"""
        return jsonify({'start_time': app.config.get('start_time', time.time())})

    @app.route('/api/last_sync')
    def last_sync():
        """返回最近一次特征同步信息"""
        from client.config import get_db
        conn = get_db()
        try:
            version = conn.execute("SELECT value FROM config WHERE key='feature_version'").fetchone()
            sync_version = int(version['value']) if version else 0
            return jsonify({'feature_version': sync_version})
        finally:
            conn.close()

    @app.route('/api/manual_open', methods=['POST'])
    def manual_open():
        """手动开门 — 转发到服务端"""
        import requests as req
        try:
            data = request.get_json(silent=True) or {}
            resp = req.post(
                f'{SERVER_URL}/api/record/manual-open',
                json={'device_sn': data.get('device_sn', DEVICE_SN)},
                timeout=5
            )
            return jsonify(resp.json()), resp.status_code
        except Exception:
            return jsonify({'error': '服务端不可用'}), 503

    return app


def restart_recognition(app):
    for t in app.config.get('camera_threads', []):
        t.stop()
    for t in app.config.get('recognition_threads', []):
        t.stop()

    binding = get_binding()
    engine = app.config.get('engine')
    uploader = app.config.get('uploader')
    frame_buffers = app.config['frame_buffers']
    frame_locks = app.config['frame_locks']

    if not binding or not engine or not uploader:
        return

    in_enabled = binding.get('in', -1) >= 0
    out_enabled = binding.get('out', -1) >= 0
    single_camera = in_enabled and out_enabled and binding['in'] == binding['out']

    cam_threads = []
    recog_threads = []

    cam_in = None
    cam_out = None

    if in_enabled:
        cam_in = CameraThread(binding['in'], 'in', frame_buffers, frame_locks,
                              secondary_direction='out' if single_camera else None)
        cam_threads.append(cam_in)
        recog_threads.append(
            RecognitionThread(cam_in, 'in', engine, uploader, frame_buffers, frame_locks)
        )

    if out_enabled:
        if single_camera:
            cam_out_ref = cam_in
        else:
            cam_out = CameraThread(binding['out'], 'out', frame_buffers, frame_locks)
            cam_threads.append(cam_out)
            cam_out_ref = cam_out
        recog_threads.append(
            RecognitionThread(cam_out_ref, 'out', engine, uploader, frame_buffers, frame_locks)
        )

    for t in cam_threads:
        t.start()
    for t in recog_threads:
        t.start()
    app.config['camera_threads'] = cam_threads
    app.config['recognition_threads'] = recog_threads


def run_client():
    print("=" * 60)
    print("校园门禁系统 - 客户端")
    print("=" * 60)

    init_db()
    logger.info("SQLite 数据库已初始化")

    # 帧缓冲区与锁
    frame_buffers = {'in': None, 'out': None}
    frame_locks = {'in': threading.Lock(), 'out': threading.Lock()}

    engine = RecognizerEngine()
    print("正在加载 InsightFace 模型...")
    engine.init_model(ctx_id=0)
    print("模型加载完成！")

    # 同步 AES 密钥
    try:
        import requests
        import base64
        resp = requests.get(f"{SERVER_URL}/api/sync/version", timeout=5)
        if resp.status_code == 200:
            key_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 'server', 'aes_key.txt'
            )
            if os.path.exists(key_path):
                with open(key_path, 'rb') as f:
                    key_b64 = f.read().decode().strip()
                set_aes_key(key_b64)
                logger.info("AES密钥已同步")
    except Exception as e:
        logger.warning(f"AES密钥同步跳过: {e}")

    # 同步人脸库
    try:
        count = sync_features()
        logger.info(f"人脸库同步完成: {count} 条")
    except Exception as e:
        logger.warning(f"人脸库同步失败: {e}")

    # 启动网络监测
    monitor = NetworkMonitor()
    monitor.start()

    # 启动上传线程
    uploader = RecordUploader(monitor)

    def on_network_change(online):
        if online:
            uploader._upload_pending()

    monitor.on_status_change(on_network_change)
    uploader.start()

    # 检查摄像头
    binding = get_binding()
    if binding:
        in_enabled = binding.get('in', -1) >= 0
        out_enabled = binding.get('out', -1) >= 0
        parts = []
        if in_enabled: parts.append(f"进门=#{binding['in']}")
        if out_enabled: parts.append(f"出门=#{binding['out']}")
        if in_enabled and out_enabled and binding['in'] == binding['out']:
            parts.append("(单摄像头)")
        print(f"摄像头绑定: {', '.join(parts)}")
    else:
        print(f"摄像头未绑定，请通过 Web 控制台配置: http://127.0.0.1:{CLIENT_PORT}/config")

    # 启动摄像头采集 + 识别线程
    camera_threads = []
    recognition_threads = []
    if binding:
        in_enabled = binding.get('in', -1) >= 0
        out_enabled = binding.get('out', -1) >= 0
        single_camera = in_enabled and out_enabled and binding['in'] == binding['out']

        cam_in = None
        if in_enabled:
            cam_in = CameraThread(binding['in'], 'in', frame_buffers, frame_locks,
                                  secondary_direction='out' if single_camera else None)
            camera_threads.append(cam_in)
            recognition_threads.append(
                RecognitionThread(cam_in, 'in', engine, uploader, frame_buffers, frame_locks)
            )

        if out_enabled:
            if single_camera:
                cam_out_ref = cam_in
            else:
                cam_out = CameraThread(binding['out'], 'out', frame_buffers, frame_locks)
                camera_threads.append(cam_out)
                cam_out_ref = cam_out
            recognition_threads.append(
                RecognitionThread(cam_out_ref, 'out', engine, uploader, frame_buffers, frame_locks)
            )

        for t in camera_threads:
            t.start()
        for t in recognition_threads:
            t.start()

    # 启动 Web
    client_app = create_client_app()
    client_app.config['engine'] = engine
    client_app.config['uploader'] = uploader
    client_app.config['monitor'] = monitor
    client_app.config['camera_threads'] = camera_threads
    client_app.config['recognition_threads'] = recognition_threads
    client_app.config['frame_buffers'] = frame_buffers
    client_app.config['frame_locks'] = frame_locks

    print(f"客户端 Web 控制台: http://127.0.0.1:{CLIENT_PORT}")
    print("按 Ctrl+C 退出")
    client_app.config['start_time'] = time.time()
    client_app.run(host='0.0.0.0', port=CLIENT_PORT, debug=False)


if __name__ == '__main__':
    run_client()
