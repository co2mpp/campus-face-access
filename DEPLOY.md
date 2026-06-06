# 部署文档

## 系统要求

### 服务端

| 组件 | 最低要求 |
|------|---------|
| 操作系统 | Ubuntu 20.04+ / Windows Server 2019+ |
| Python | 3.10+ |
| MySQL | 5.7+ 或 8.0+ |
| 内存 | 4 GB+ |
| 磁盘 | 20 GB+ |
| 网络 | 与客户端局域网互通 |

### 客户端（门禁终端）

| 组件 | 最低要求 |
|------|---------|
| 操作系统 | Windows 10+ / Ubuntu 20.04+ |
| Python | 3.10+ |
| 摄像头 | USB 摄像头 ×2（支持单摄像头演示） |
| 内存 | 4 GB+（InsightFace 模型约 500MB） |
| 磁盘 | 5 GB+ |
| 网络 | 与服务端局域网互通 |

## 服务端部署

### 1. 安装 Python 依赖

```bash
# 创建虚拟环境 (推荐)
python -m venv venv
source venv/bin/activate  # Linux
# venv\Scripts\activate   # Windows

pip install -r requirements.txt
```

首次运行时 InsightFace 会自动下载模型文件 (`buffalo_l`)，约 500MB，请确保网络畅通。模型缓存路径为 `~/.insightface/models/`。

### 2. 安装并配置 MySQL

**Ubuntu:**
```bash
sudo apt install mysql-server
sudo mysql_secure_installation
```

**Windows:**
下载安装 [MySQL Community Server](https://dev.mysql.com/downloads/mysql/)。

创建数据库：

```sql
CREATE DATABASE smart_gate DEFAULT CHARACTER SET utf8mb4;
CREATE USER 'gate_admin'@'localhost' IDENTIFIED BY 'your_strong_password';
GRANT ALL PRIVILEGES ON smart_gate.* TO 'gate_admin'@'localhost';
FLUSH PRIVILEGES;
```

### 3. 配置环境变量

创建 `.env` 文件或直接设置系统环境变量：

```bash
export MYSQL_HOST=127.0.0.1
export MYSQL_PORT=3306
export MYSQL_USER=gate_admin
export MYSQL_PASSWORD=your_strong_password
export MYSQL_DB=smart_gate
export SERVER_PORT=5000
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=your_admin_password
export SECRET_KEY=your_random_secret_key
```

**重要**：`MYSQL_PASSWORD` 必须设置，程序不内置默认密码。

### 4. 启动服务端

```bash
python run_server.py
```

启动后：
- 服务端监听 `0.0.0.0:5000`
- 数据库表会自动创建
- AES 密钥文件 `server/aes_key.txt` 自动生成
- 管理后台：`http://<服务器IP>:5000/admin`

### 5. 配置服务端开机自启 (Linux systemd)

创建 `/etc/systemd/system/smartgate-server.service`：

```ini
[Unit]
Description=Smart Gate Access Control Server
After=network.target mysql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/smartgate
Environment="MYSQL_PASSWORD=your_password"
Environment="ADMIN_USERNAME=admin"
Environment="ADMIN_PASSWORD=your_admin_password"
Environment="SECRET_KEY=your_random_secret"
ExecStart=/opt/smartgate/venv/bin/python run_server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now smartgate-server
```

## 客户端部署

### 1. 安装依赖

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
export SERVER_URL=http://192.168.1.100:5000   # 替换为服务端实际 IP
export DEVICE_SN=GATE-001                       # 每台设备唯一标识
export CLIENT_PORT=5001
export MYSQL_PASSWORD=your_password             # 服务端数据库密码（客户端首次同步获取 AES 密钥用）
```

### 3. 连接摄像头

- 插入 2 个 USB 摄像头，系统会自动检测
- 支持单摄像头演示模式（进门/出门共用同一画面）

### 4. 启动客户端

```bash
python run_client.py
```

启动后通过浏览器访问 `http://127.0.0.1:5001/config` 绑定摄像头方向。

### 5. 配置客户端开机自启 (Windows)

创建 `start_client.bat`：

```bat
@echo off
cd /d C:\SmartGate
set MYSQL_PASSWORD=your_password
set SERVER_URL=http://192.168.1.100:5000
set DEVICE_SN=GATE-001
call venv\Scripts\activate
python run_client.py
```

将该批处理文件添加到 Windows 任务计划程序（触发条件：用户登录时）。

## 注册学生数据

### 准备照片

- 照片格式：JPG/JPEG/PNG
- 照片应包含清晰的人脸（单人正面照）
- 文件命名：`学号_姓名.jpg`（如 `20230001_张三.jpg`）
- 将照片放入 `人脸图片/` 目录

### 批量注册

```bash
python batch_register.py
```

该工具会：
1. 解析文件名获取学号和姓名
2. 自动创建学生记录（如已存在则跳过）
3. 上传照片，服务端提取人脸特征并加密存储
4. 已注册过人脸的学生会自动跳过

### 单个注册

```bash
python register_face.py <学号> <姓名> <照片路径>
```

管理后台 `http://<服务器IP>:5000/admin` 也支持 Web 界面的学生管理和人脸注册（含单人注册和批量文件夹注册）。

## 运维管理

### Web 管理后台

访问 `http://<服务器IP>:5000/admin`，默认凭据 admin / admin123（通过环境变量配置）。
功能包括：

- **总览仪表盘**：统计卡片 + Chart.js 7天通行趋势图 + 院系分布图，30s 自动刷新
- **学生管理**：增删改查 + 院系/学号/姓名搜索 + 在校状态过滤 + CSV/JSON 批量导入
- **人脸注册**：单人上传注册 + **批量文件夹注册**（自动解析 `学号_姓名.jpg` 格式）
- **通行记录**：实时搜索（学号/姓名/设备号）+ 方向/结果过滤 + 手动添加 + CSV 导出
- **设备状态**：查看/添加/编辑/删除设备，在线状态与最后心跳时间

### 命令行工具

```bash
# 查询记录
python query_records.py --stu 学号 --dir in --start 2024-01-01 --end 2024-12-31

# 导出 CSV
python query_records.py --export > records.csv
```

### 数据库维护

建议定期备份 MySQL 数据库：

```bash
mysqldump -u root -p smart_gate > smart_gate_backup_$(date +%Y%m%d).sql
```

## 离线运行机制

客户端在网络中断时：
1. 继续本地识别（使用已缓存的加密特征库）
2. 通行记录暂存于 SQLite 本地数据库 (`client/client_data.db`)
3. 心跳监测每 30 秒检测一次，连续 3 次超时判定离线
4. 网络恢复后自动批量上传缓存记录

## 安全加固建议

1. **数据库密码**：生产环境务必使用强密码，通过环境变量或密钥管理服务注入
2. **AES 密钥**：`server/aes_key.txt` 文件权限设为 600（仅所有者可读写）
3. **网络隔离**：服务端与客户端之间的通信建议通过 VLAN 隔离
4. **防火墙**：仅开放客户端需要的 5000 端口，不对外暴露管理后台
5. **HTTPS**：如需公网访问，请配置 Nginx 反向代理 + SSL
6. **日志审计**：定期检查通行记录，发现异常访问模式

## 故障排查

| 现象 | 可能原因 | 解决方案 |
|------|---------|---------|
| 服务端无法启动 | MySQL 未启动或密码错误 | 检查 MySQL 服务状态和 `MYSQL_PASSWORD` 环境变量 |
| 客户端无法连接服务端 | 网络不通或 IP 配置错误 | 检查 `SERVER_URL`，确认网络互通和防火墙设置 |
| 摄像头无画面 | 摄像头未连接或被占用 | 检查 USB 连接，确认摄像头索引正确 |
| 识别失败率高 | 光照不足 / 阈值过高 | 调整 `RECOGNITION_THRESHOLD`（降低阈值），改善光照 |
| 特征同步失败 | AES 密钥不一致 | 确保 `server/aes_key.txt` 内容与客户端配置表中的密钥一致 |
| 模型下载失败 | 网络问题 | 手动下载 InsightFace buffalo_l 模型到 `~/.insightface/models/` |
