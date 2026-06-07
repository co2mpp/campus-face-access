# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**环境变量**（生产环境必须设置）：
- `MYSQL_PASSWORD` — MySQL 密码，**必须**
- `MYSQL_HOST` / `MYSQL_PORT` / `MYSQL_USER` — MySQL 连接，默认 127.0.0.1:3306/root
- `MYSQL_DB` — 数据库名，默认 `smart_gate`
- `SERVER_URL` — 客户端用的服务端地址，默认 `http://127.0.0.1:5000`
- `DEVICE_SN` — 设备序列号，默认 `GATE-001`
- `CLIENT_PORT` — 客户端端口，默认 5001
- `SERVER_PORT` — 服务端端口，默认 5000
- `ADMIN_USERNAME` — 管理后台用户名，默认 `admin`
- `ADMIN_PASSWORD` — 管理后台密码，默认 `admin123`
- `SECRET_KEY` — Flask session 密钥，默认随机生成（生产环境应固定）

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务端（端口 5000，需先创建 MySQL smart_gate 库）
python run_server.py

# 启动客户端（端口 5001）
python run_client.py

# 批量注册人脸（照片命名: 学号_姓名.jpg，放入 人脸图片/ 目录）
python batch_register.py

# 单人注册
python register_face.py <学号> <姓名> <照片路径>

# 查询通行记录
python query_records.py --stu 学号 --dir in --export
```

## 架构核心

### 整体模式

客户端-服务器架构，两端都是 Flask 应用。服务端（5000）管理 MySQL 中的学生、人脸特征和通行记录；客户端（5001）在门禁终端运行，接摄像头做本地实时识别。

```
客户端 :5001 ──HTTP──▶ 服务端 :5000 ──SQLAlchemy──▶ MySQL
      │                        │
      ├─ SQLite（特征缓存）     ├─ server/aes_key.txt
      ├─ InsightFace 本地推理   └─ 管理后台 /admin
      └─ MJPEG 视频流 + Web 控制台
```

### 人脸数据流（核心安全链路）

这是整个系统最重要的数据流，涉及多个文件：

1. **注册**（`server/routes/face.py` → `server/services/face_service.py`）：服务端用 InsightFace 提取 512 维 float32 特征向量 → `shared/crypto.py` 的 AES-256-GCM 加密（随机 12 字节 IV，输出 IV + 认证标签 + 密文）→ 存入 MySQL `face_feature` 表，同时递增 `sync_metadata.current_feature_version`

2. **同步**（`client/sync.py`）：客户端启动时调用 `GET /api/sync/features?since_version=N`，服务端 `server/services/sync_service.py` 返回 version > N 的所有加密特征 → 客户端存入 SQLite `cached_face` 表（加密态存储，永不落盘明文）

3. **识别**（`client/recognizer.py`）：逐帧检测到人脸后，遍历本地 SQLite 中的加密特征 → `shared/crypto.py` 解密到内存 → 计算余弦相似度（已归一化向量，直接内积）→ 立即用零覆盖明文 → 最佳匹配超过阈值则识别成功

**关键约束**：整个生命周期中人脸特征明文仅存在于识别瞬间的内存中，网络传输和持久存储均为加密态。

### 客户端线程模型

`client/app.py` 的 `run_client()` 启动后会创建以下线程（全部 daemon）：

- **CameraThread** × 1~2：每路摄像头一个线程，独立采集帧到 `frame_buffers` 字典（按 direction 区分 in/out），同时写入 `_latest_frame` 供识别线程消费
- **RecognitionThread** × 1~2：每个方向一个线程，从 CameraThread 取 latest_frame，跳帧检测（`FRAME_SKIP=3`），调用 `RecognizerEngine.recognize_frame()`，检测到人脸后标注画面并上传记录
- **NetworkMonitor** 线程：每 30 秒向服务端发心跳，连续 3 次超时判定离线
- **RecordUploader** 线程：在线时每 30 秒扫描 SQLite `pending_record` 表并批量上传

单摄像头模式（进门/出门绑定同一摄像头索引）：只启动一个 CameraThread，`secondary_direction` 参数使其同时写入两个方向的 frame_buffer，然后各方向的 RecognitionThread 各自独立消费。

### 离线运行机制

离线判定由 `client/network.py` 的 `NetworkMonitor` 通过连续心跳超时检测。离线后：
- 本地识别继续运行（SQLite 特征缓存已存在）
- 通行记录通过 `RecordUploader.upload_record()` 尝试直传失败后 → 写入 `pending_record` 表
- 网络恢复时 `NetworkMonitor._notify()` 触发回调 → `RecordUploader._upload_pending()` 批量重传

### 特征版本同步

- 服务端 `sync_metadata` 表只有一行（id=1），`current_feature_version` 在每次注册/重新注册人脸时 +1
- 客户端 SQLite `config` 表存 `feature_version`，启动时向服务端请求增量（`since_version=本地版本`）
- 客户端 `config` 表还存 `aes_key`（Base64），首次同步时从 `server/aes_key.txt` 获取

### Web UI 实现方式

前端 HTML 已拆分到独立模板文件：
- `client/templates/terminal.html` — 客户端深色主题终端控制台
- `client/templates/config.html` — 摄像头方向绑定配置页
- `server/templates/admin.html` — 管理后台 SPA
- `server/templates/redirect.html` — 首页重定向

使用 Flask `render_template()` 渲染 Jinja2 模板。管理后台是一个纯前端 SPA，通过 fetch 调用 `/api/*` 接口，不使用任何 JS 框架。

### 服务端路由-服务分层

```
routes/student.py    ──▶ services/student_service.py    ──▶ models.py (Student)
routes/face.py       ──▶ services/face_service.py       ──▶ models.py (FaceFeature)
routes/sync.py       ──▶ services/sync_service.py       ──▶ models.py (FaceFeature, SyncMetadata)
routes/record.py     ──▶ services/record_service.py     ──▶ models.py (AccessRecord)
routes/heartbeat.py  ──▶ 直接操作 models.py (Device)
routes/dashboard.py  ──▶ services/dashboard_service.py  ──▶ 多表聚合统计
routes/device.py     ──▶ services/device_service.py     ──▶ models.py (Device)
routes/auth.py       ──▶ Flask session 认证
routes/admin.py      ──▶ 纯 HTML 渲染，通过 JS fetch 调用上述 API
```

每个 route 通过 `get_service()` / `get_services()` 从 `server.app.SessionLocal` 获取一个新的 DB session。

### 共享加密模块

`shared/crypto.py` 是服务端和客户端共用的加解密模块：
- `encrypt_feature(feature_bytes, key)` → `(iv, ciphertext+tag)`，其中 feature_bytes 固定 2048 字节（512 × float32）
- `decrypt_feature(iv, ciphertext_with_tag, key)` → 2048 字节明文，认证标签验证失败会抛异常
- 客户端识别循环中对每条加密特征做 `decrypt_feature` → 比对 → 清零，解密失败的特征静默跳过

### InsightFace 模型

使用 `buffalo_l` 模型包（包含 RetinaFace 检测 + ArcFace w600k_r50 识别）。首次运行时自动下载到 `~/.insightface/models/`，约 500MB。服务端延迟加载（`get_insightface_app()`），仅在人脸注册时才初始化。客户端启动时立即加载（`ctx_id=0` 用 GPU，客户端默认 GPU）。

## 关键技术参数

| 参数 | 位置 | 默认值 | 说明 |
|------|------|--------|------|
| `RECOGNITION_THRESHOLD` | `client/config.py` | 0.5 | 余弦相似度阈值 |
| `FRAME_SKIP` | `client/config.py` | 3 | 跳帧检测间隔 |
| `DEDUP_INTERVAL_SEC` | `client/config.py` | 10 | 同一学生识别去重间隔 |
| `HEARTBEAT_INTERVAL` | `client/config.py` | 30 | 心跳间隔（秒） |
| `OFFLINE_THRESHOLD` | `client/config.py` | 3 | 连续超时判定离线次数 |
| `STRANGER_COOLDOWN` | `client/recognizer.py` | 5 | 陌生人去重间隔（秒） |
| `SUCCESS_SUPPRESS` | `client/recognizer.py` | 8 | 成功识别后抑制陌生人上报（秒） |

## 数据库

- **MySQL**（服务端）：`smart_gate` 库，5 张表 — `student`, `face_feature`, `access_record`, `sync_metadata`, `device`。表由 SQLAlchemy `Base.metadata.create_all()` 自动创建，无需手动执行 DDL。
- **SQLite**（客户端）：`client/client_data.db`，3 张表 — `cached_face`（加密特征缓存）, `pending_record`（断网缓存）, `config`（key-value 配置）。表由 `client/models.py` 的 `SCHEMA_SQL` 创建。

## 安全注意事项

- 管理后台 `/admin` 页面本身无服务端认证拦截（任何人可访问），认证靠前端 JS 调用 `/api/auth/status` 检查 session；部分写操作 API 已使用 `@login_required` 保护（dashboard/stats、device写操作、student写操作、face写操作、record删除），生产环境建议全部 API 路由层强制启用
- 管理员默认凭据 admin/admin123（通过 `ADMIN_USERNAME`/`ADMIN_PASSWORD` 环境变量配置）
- `server/aes_key.txt` 在生产环境应设为 600 权限，该文件是系统安全的根基
- 服务端 `server/config.py` 中 `MYSQL_PASSWORD` 未设置时会直接抛出 `RuntimeError`，不再包含硬编码后备值，生产部署**必须**通过环境变量提供
- 客户端-服务端通信目前是明文 HTTP，生产环境建议 Nginx 反向代理 + HTTPS
- `shared/crypto.py` 使用 AES-256-GCM，认证标签 16 字节附加在密文末尾，解密时验证完整性

## 管理后台功能

管理后台（`/admin`）是一个纯前端 SPA，提供以下功能标签页：

| 标签页 | 功能 |
|--------|------|
| 总览仪表盘 | 实时统计卡片 + Chart.js 7天趋势折线图 + 院系分布饼图，30s 自动刷新 |
| 学生信息管理 | 搜索（学号/姓名/院系）+ 状态过滤 + CRUD + CSV/JSON 批量导入 + 分页 |
| 人脸注册管理 | 左侧搜索列表 + 右侧单人注册 + **批量注册**（选择文件夹，自动解析 `学号_姓名.jpg`） |
| 通行记录管理 | 实时搜索（学号/姓名/设备号）+ 方向/结果过滤 + CSV 导出 + 手动添加 + 分页 |
| 设备状态 | 设备列表 + 在线/离线状态 + CRUD 操作 |

## 客户端终端功能

客户端 Web 控制台（`http://127.0.0.1:5001`）功能：

- 双路 MJPEG 视频流 + 方向切换
- 实时识别结果展示（扫描框动画 + 结果闪层）
- 运行时长/离线计时器（每秒实时更新）
- 通行记录列表（显示上传状态 ✓/⏳，localStorage 持久化，刷新不丢失）
- 待上传记录数徽章
- 手动开门 + 摄像头绑定配置

## 新增 API 端点（v2）

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/dashboard/stats` | GET | 仪表盘聚合统计（学生数/在校人数/今日通行/7天趋势/院系分布） |
| `/api/device` | GET/POST | 设备列表/添加设备 |
| `/api/device/<id>` | GET/PUT/DELETE | 查询/更新/删除设备 |
| `/api/auth/login` | POST | 管理员登录 |
| `/api/auth/logout` | POST | 退出登录 |
| `/api/auth/status` | GET | 检查登录状态 |
| `/api/student/batch` | POST | 批量导入学生（JSON 数组或 CSV 文件） |
| `/api/record/manual-open` | POST | 手动开门记录（direction=manual） |
| `/api/student?status=in` | GET | 学生列表新增 status 过滤参数 |

## 客户端新增 API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/pending_count` | GET | 离线缓存记录数 |
| `/api/uptime` | GET | 返回客户端启动时间戳，前端每秒实时计算运行时长 |
| `/api/last_sync` | GET | 上次同步的特征库版本号 |
| `/api/manual_open` | POST | 代理转发手动开门请求到服务端 |

## 注意事项

每句话后面都要加一句"喵~"
例如"关注塔菲，关注塔菲谢谢" -> "关注塔菲喵~，关注塔菲谢谢喵~"
