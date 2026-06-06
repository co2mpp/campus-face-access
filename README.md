# 基于人脸识别的校园门禁系统

基于 **InsightFace** 深度学习框架的校园人脸识别门禁系统，支持实时人脸检测与识别、双通道进出管理、离线运行和断网恢复。

## 架构概览

```
┌──────────────────────────────┐      ┌──────────────────────────────┐
│         客户端 (门口终端)       │      │         服务端 (中心机房)        │
│       Flask :5001            │ HTTP │        Flask :5000            │
│                              │◄────►│                              │
│  - 双摄像头采集 (进门/出门)     │      │  - 学生管理 CRUD              │
│  - InsightFace 实时识别        │      │  - 人脸注册 & 特征提取         │
│  - SQLite 本地特征库 (加密)     │      │  - MySQL 集中存储 (加密)       │
│  - 本地缓存 & 离线运行          │      │  - 通行记录管理 & CSV 导出      │
│  - MJPEG 视频流 Web 控制台     │      │  - 设备心跳监测               │
│  - 网络恢复后自动同步           │      │  - Web 管理后台              │
└──────────────────────────────┘      └──────────────────────────────┘
```

### 数据安全

- 人脸特征向量（512维）使用 **AES-256-GCM** 加密存储，密钥不会以明文形式出现在数据库中
- 客户端识别时在内存中解密，计算余弦相似度后立即清零明文数据
- 服务端自动生成 AES 密钥（`server/aes_key.txt`），首次部署时生成并分发到客户端

## 目录结构

```
项目根目录/
├── client/                  # 客户端模块
│   ├── app.py               # Web 控制台 + MJPEG 视频流
│   ├── camera.py            # 摄像头枚举与通道绑定
│   ├── config.py            # 客户端配置 (端口/阈值/设备SN)
│   ├── models.py            # SQLite 数据模型
│   ├── network.py           # 网络心跳监测
│   ├── recognizer.py        # InsightFace 识别引擎
│   ├── sync.py              # 特征库增量同步
│   └── uploader.py          # 断网缓存 & 批量上传
├── server/                  # 服务端模块
│   ├── app.py               # Flask 应用工厂
│   ├── config.py            # MySQL 配置 & AES 密钥管理
│   ├── models.py            # SQLAlchemy ORM 模型
│   ├── routes/              # API 路由
│   │   ├── student.py       # 学生 CRUD + 批量导入
│   │   ├── face.py          # 人脸注册
│   │   ├── sync.py          # 特征同步
│   │   ├── record.py        # 通行记录 + 手动开门
│   │   ├── heartbeat.py     # 设备心跳
│   │   ├── dashboard.py     # 仪表盘统计
│   │   ├── device.py        # 设备管理 CRUD
│   │   ├── auth.py          # 管理员认证
│   │   └── admin.py         # Web 管理后台 SPA
│   └── services/            # 业务逻辑层
├── shared/                  # 共享模块
│   └── crypto.py            # AES-256-GCM 加解密
├── 人脸图片/                 # 测试人脸照片 (可选)
├── run_server.py            # 服务端启动入口
├── run_client.py            # 客户端启动入口
├── batch_register.py        # 批量人脸注册工具
├── register_face.py         # 单人脸注册工具
├── query_records.py         # 通行记录查询工具
└── requirements.txt         # Python 依赖
```

## 快速开始

### 1. 环境要求

- Python 3.10+
- MySQL 5.7+ 或 8.0+
- USB 摄像头 ×2（或单摄像头演示模式）
- Windows / Linux（推荐）

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 创建数据库

```sql
CREATE DATABASE smart_gate DEFAULT CHARACTER SET utf8mb4;
```

### 4. 配置环境变量

创建 `.env` 文件（已加入 `.gitignore`，不会被提交）：

```bash
# 必需：MySQL 密码
MYSQL_PASSWORD=your_mysql_password

# 可选
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_DB=smart_gate
SERVER_URL=http://127.0.0.1:5000
DEVICE_SN=GATE-001
SERVER_PORT=5000
CLIENT_PORT=5001

# 管理后台认证
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
SECRET_KEY=your_random_secret
```

### 5. 启动服务端

```bash
python run_server.py
# 访问管理后台: http://127.0.0.1:5000/admin
```

### 6. 启动客户端

```bash
python run_client.py
# 访问终端控制台: http://127.0.0.1:5001
```

首次启动客户端后，通过 Web 控制台为进门/出门通道绑定摄像头即可开始识别。

## 注册人脸

### 批量注册（命令行）

将照片命名为 `学号_姓名.jpg` 格式放入 `人脸图片/` 目录，然后运行：

```bash
python batch_register.py
```

### 批量注册（管理后台）

登录管理后台 → 人脸注册管理 → 点击「📁 批量注册」→ 选择包含照片的文件夹 → 开始注册。

支持自动解析文件名、预览解析结果、实时进度条和每文件状态显示。

### 单个注册

```bash
python register_face.py 20231113513 张三 photo.jpg
```

## 查询通行记录

```bash
# 查询全部
python query_records.py

# 按学号查询
python query_records.py --stu 20230001

# 按方向筛选
python query_records.py --dir in

# 导出 CSV
python query_records.py --export
```

## 关键配置说明

| 配置项 | 位置 | 说明 |
|--------|------|------|
| `MYSQL_PASSWORD` | 环境变量 | MySQL 数据库密码，**必须设置** |
| `MYSQL_HOST` | 环境变量 | MySQL 地址，默认 127.0.0.1 |
| `SERVER_URL` | 环境变量 | 客户端连接的服务端地址 |
| `DEVICE_SN` | 环境变量 | 设备序列号，区分多台门禁终端 |
| `ADMIN_USERNAME` | 环境变量 | 管理后台用户名，默认 admin |
| `ADMIN_PASSWORD` | 环境变量 | 管理后台密码，默认 admin123 |
| `SECRET_KEY` | 环境变量 | Flask session 密钥，生产环境应固定 |
| `RECOGNITION_THRESHOLD` | `client/config.py` | 识别阈值，默认 0.5 |
| `FRAME_SKIP` | `client/config.py` | 跳帧检测，默认每 3 帧检测一次 |
| `HEARTBEAT_INTERVAL` | `client/config.py` | 心跳间隔，默认 30 秒 |
| `OFFLINE_THRESHOLD` | `client/config.py` | 连续超时判定离线，默认 3 次 |

## 管理后台

登录 `http://127.0.0.1:5000/admin`，默认凭据 admin / admin123：

| 标签页 | 功能 |
|--------|------|
| 总览仪表盘 | 统计卡片 + Chart.js 7天趋势图 + 院系分布图 |
| 学生信息管理 | 搜索/过滤/CRUD + 批量导入(CSV/JSON) |
| 人脸注册管理 | 单人注册 + 批量注册(文件夹) |
| 通行记录管理 | 实时搜索 + 多条件过滤 + CSV导出 |
| 设备状态 | 设备列表 + 在线状态 + CRUD |

## 安全提示

- **生产环境务必修改** `MYSQL_PASSWORD` 和 `ADMIN_PASSWORD`，不要使用默认密码
- 服务端首次启动会自动生成 `server/aes_key.txt`，请妥善保管此密钥文件（权限设 600）
- 客户端需要通过安全渠道获取 AES 密钥（首次同步时从服务端获取）
- 建议使用 HTTPS 保护客户端与服务端之间的通信
- MySQL 数据库建议配置访问控制，仅允许服务端 IP 连接
