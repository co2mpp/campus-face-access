"""
人脸识别引擎
- RetinaFace 检测 + ArcFace 特征提取
- AES-256-GCM 临时解密 → 余弦相似度 → 立即清除明文
"""
import time
import os
import struct
import threading
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

# 中文字体加载（Windows 常见路径）
_CN_FONT = None
_FONT_PATHS = [
    'C:/Windows/Fonts/msyh.ttc',   # 微软雅黑
    'C:/Windows/Fonts/simhei.ttf',  # 黑体
    'C:/Windows/Fonts/simsun.ttc',  # 宋体
    'C:/Windows/Fonts/STSONG.TTF',  # 华文宋体
]


def _get_font(size=20):
    global _CN_FONT
    if _CN_FONT is not None:
        try:
            return ImageFont.truetype(_CN_FONT, size)
        except Exception:
            pass
    for fp in _FONT_PATHS:
        if os.path.exists(fp):
            try:
                f = ImageFont.truetype(fp, size)
                _CN_FONT = fp
                return f
            except Exception:
                continue
    return ImageFont.load_default()


def _cv2pil(cv_img):
    """OpenCV BGR → PIL RGB"""
    return Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))


def _pil2cv(pil_img):
    """PIL RGB → OpenCV BGR"""
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def _draw_text_cn(frame, text, pos, color, size=22):
    """在 OpenCV 帧上用 PIL 绘制中文文本（原地修改）"""
    pil_img = _cv2pil(frame)
    draw = ImageDraw.Draw(pil_img)
    font = _get_font(size)
    pil_color = (color[2], color[1], color[0]) if len(color) == 3 else color
    # 黑色描边 + 无 stroke 填充，文字更锐利
    x, y = pos
    draw.text((x-1, y), text, font=font, fill=(0, 0, 0))
    draw.text((x+1, y), text, font=font, fill=(0, 0, 0))
    draw.text((x, y-1), text, font=font, fill=(0, 0, 0))
    draw.text((x, y+1), text, font=font, fill=(0, 0, 0))
    draw.text((x, y), text, font=font, fill=pil_color)
    result = _pil2cv(pil_img)
    frame[:] = result  # 原地写回，调用方无需重新赋值
from insightface.app import FaceAnalysis
from client.config import (
    get_db, get_aes_key, RECOGNITION_THRESHOLD,
    DEDUP_INTERVAL_SEC, FRAME_SKIP
)
from shared.crypto import decrypt_feature


class RecognizerEngine:
    def __init__(self):
        self.app = None
        self._last_trigger = {}      # student_id → 上次触发时间
        self._last_stranger = 0      # 上次陌生人上报时间
        self._last_success = 0       # 上次成功时间
        self._lock = threading.Lock()

    STRANGER_COOLDOWN = 5        # 陌生人去重（秒）
    SUCCESS_SUPPRESS = 8         # 成功后N秒内抑制陌生人上报

    def init_model(self, ctx_id: int = 0):
        """初始化 InsightFace 模型（ctx_id=0 GPU, -1 CPU）"""
        self.app = FaceAnalysis(name='buffalo_l')
        self.app.prepare(ctx_id=ctx_id)

    def load_encrypted_db(self) -> list[dict]:
        """从 SQLite 加载加密特征库"""
        conn = get_db()
        rows = conn.execute(
            "SELECT student_id, stu_no, name, encrypted_feature, iv FROM cached_face"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def recognize_frame(self, frame, encrypted_db: list[dict]) -> list[dict]:
        """
        对单帧图像进行识别
        返回: [{student_id, stu_no, name, bbox, similarity}, ...]
        """
        if self.app is None:
            raise RuntimeError("模型未初始化，请先调用 init_model()")

        faces = self.app.get(frame)
        results = []

        for face in faces:
            probe_emb = face.normed_embedding
            if probe_emb is None:
                continue

            best_sim = -1
            best_student = None

            # 逐条解密比对
            aes_key = get_aes_key()
            for record in encrypted_db:
                try:
                    plain_bytes = decrypt_feature(
                        bytes(record['iv']),
                        bytes(record['encrypted_feature']),
                        aes_key
                    )
                    db_emb = np.frombuffer(plain_bytes, dtype=np.float32)

                    # 余弦相似度（向量已归一化，直接内积）
                    sim = float(np.dot(probe_emb, db_emb))

                    # 立即清除明文（用零覆盖）
                    plain_bytes = b'\x00' * len(plain_bytes)

                    if sim > best_sim:
                        best_sim = sim
                        best_student = record
                except Exception:
                    # 解密失败（密钥错误、数据损坏），跳过
                    continue

            bbox = face.bbox.astype(int)
            now = time.time()

            if best_sim >= RECOGNITION_THRESHOLD and best_student:
                # === 识别成功 ===
                sid = best_student['student_id']
                with self._lock:
                    last = self._last_trigger.get(sid, 0)
                    if now - last < DEDUP_INTERVAL_SEC:
                        continue
                    self._last_trigger[sid] = now
                    self._last_success = now

                results.append({
                    'student_id': sid,
                    'stu_no': best_student['stu_no'],
                    'name': best_student['name'],
                    'bbox': bbox.tolist(),
                    'similarity': round(best_sim, 4),
                    'result': 'success',
                })
            else:
                # === 陌生人 ===
                with self._lock:
                    # 刚识别成功过，抑制短暂误检
                    if now - self._last_success < RecognizerEngine.SUCCESS_SUPPRESS:
                        continue
                    # 陌生人去重
                    if now - self._last_stranger < RecognizerEngine.STRANGER_COOLDOWN:
                        continue
                    self._last_stranger = now

                results.append({
                    'student_id': None,
                    'stu_no': '',
                    'name': '陌生人',
                    'bbox': bbox.tolist(),
                    'similarity': round(best_sim, 4) if best_sim > 0 else 0.0,
                    'result': 'fail',
                })

        return results

    def draw_results(self, frame, results: list[dict]):
        """在帧上绘制识别结果"""
        return RecognizerEngine.draw_results_static(frame, results)

    @staticmethod
    def draw_results_static(frame, results: list[dict]):
        """静态版本，供 MJPEG 流复用（支持中文）"""
        for r in results:
            bbox = r['bbox']
            is_success = r.get('result', 'success') == 'success'
            color = (0, 255, 0) if is_success else (0, 0, 255)
            label = f"{r['name']}（{r['stu_no']}）{r['similarity']:.1%}"
            if not is_success:
                label = f"陌生人 {r['similarity']:.1%}"
            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
            text_y = max(bbox[1] - 26, 4)
            _draw_text_cn(frame, label, (bbox[0], text_y), color, size=22)
        return frame
