"""服务端管理后台 Web UI"""
from flask import Blueprint, render_template_string

bp = Blueprint('admin', __name__, url_prefix='/admin')

# ========== 管理后台主页面 ==========
ADMIN_HTML = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>校园门禁管理后台</title>
<style>
:root {
  --primary: #3b82f6;
  --primary-hover: #2563eb;
  --success: #10b981;
  --warning: #f59e0b;
  --danger: #ef4444;
  --purple: #8b5cf6;
  --sidebar-bg: #1e293b;
  --page-bg: #f8fafc;
  --card-bg: #ffffff;
  --border: #e2e8f0;
  --text: #1e293b;
  --text-secondary: #64748b;
  --text-muted: #94a3b8;
  --shadow: 0 1px 3px rgba(0,0,0,0.1);
  --radius: 8px;
  --radius-sm: 6px;
}
* { margin:0; padding:0; box-sizing:border-box; }
body {
  font-family: "Inter","Microsoft YaHei","Segoe UI",sans-serif;
  background: var(--page-bg); color: var(--text); min-height:100vh;
  display:flex;
}

/* ===== Sidebar ===== */
.sidebar {
  width:200px; min-width:200px; background:var(--sidebar-bg);
  display:flex; flex-direction:column; position:fixed; top:0; left:0;
  bottom:0; z-index:100; overflow-y:auto;
}
.sidebar-logo {
  padding:20px 16px; display:flex; align-items:center; gap:10px;
  border-bottom:1px solid rgba(255,255,255,0.08);
}
.sidebar-logo .logo-icon {
  width:36px; height:36px; background:var(--primary); border-radius:10px;
  display:flex; align-items:center; justify-content:center;
  color:#fff; font-size:18px; flex-shrink:0;
}
.sidebar-logo .logo-text { color:#fff; font-size:15px; font-weight:600; white-space:nowrap; }
.sidebar-logo .logo-ver { color:var(--text-muted); font-size:10px; }
.sidebar-nav { padding:8px; flex:1; }
.nav-item {
  display:flex; align-items:center; gap:10px; padding:10px 12px;
  border-radius:var(--radius); cursor:pointer; color:rgba(255,255,255,0.65);
  font-size:14px; transition:all .15s; margin-bottom:2px; border:none;
  background:none; width:100%; text-align:left;
}
.nav-item:hover { color:#fff; background:rgba(255,255,255,0.08); }
.nav-item.active { background:var(--primary); color:#fff; }
.nav-item .nav-icon { font-size:16px; width:20px; text-align:center; flex-shrink:0; }

/* ===== Main Content ===== */
.main {
  margin-left:200px; flex:1; min-height:100vh; padding:24px;
  max-width:calc(100vw - 200px);
}
.page-header { margin-bottom:24px; display:flex; align-items:flex-start; justify-content:space-between; }
.page-header h2 { font-size:24px; font-weight:700; }
.page-header .subtitle { font-size:14px; color:var(--text-secondary); margin-top:4px; }
.page-header .header-badge {
  display:flex; align-items:center; gap:6px; font-size:12px;
  padding:6px 12px; border-radius:20px; white-space:nowrap;
}
.header-badge.online { color:var(--success); background:rgba(16,185,129,0.1); }

/* ===== Stat Cards ===== */
.stat-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin-bottom:24px; }
.stat-card {
  background:var(--card-bg); border-radius:var(--radius); padding:24px;
  box-shadow:var(--shadow); display:flex; align-items:center; gap:16px;
}
.stat-icon {
  width:48px; height:48px; border-radius:12px; display:flex;
  align-items:center; justify-content:center; font-size:22px; flex-shrink:0;
}
.stat-icon.blue { background:#eff6ff; color:var(--primary); }
.stat-icon.green { background:#ecfdf5; color:var(--success); }
.stat-icon.orange { background:#fffbeb; color:var(--warning); }
.stat-icon.purple { background:#f5f3ff; color:var(--purple); }
.stat-info .stat-value { font-size:28px; font-weight:700; line-height:1.2; }
.stat-info .stat-label { font-size:14px; color:var(--text-secondary); }

/* ===== Cards ===== */
.card {
  background:var(--card-bg); border-radius:var(--radius); box-shadow:var(--shadow);
  overflow:hidden;
}
.card-header {
  padding:16px 20px; border-bottom:1px solid var(--border);
  font-size:16px; font-weight:600; display:flex; align-items:center; gap:8px;
}
.card-body { padding:20px; }
.card-body.no-padding { padding:0; }

/* Chart containers */
.chart-container { width:100%; height:280px; display:flex; align-items:center; justify-content:center; }
.chart-row { display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:24px; }
.chart-legend { display:flex; gap:16px; flex-wrap:wrap; margin-top:12px; font-size:12px; }
.chart-legend-item { display:flex; align-items:center; gap:6px; }
.chart-legend-dot { width:10px; height:10px; border-radius:50%; flex-shrink:0; }

/* ===== Tables ===== */
table { width:100%; border-collapse:collapse; font-size:14px; }
th {
  text-align:left; padding:12px 16px; font-weight:500; color:var(--text-secondary);
  font-size:13px; background:#f8fafc; border-bottom:1px solid var(--border);
  white-space:nowrap;
}
td { padding:10px 16px; border-bottom:1px solid var(--border); }
tr:hover td { background:#f1f5f9; }

/* ===== Badges ===== */
.badge {
  display:inline-flex; align-items:center; gap:4px; padding:3px 10px;
  border-radius:4px; font-size:12px; font-weight:500; white-space:nowrap;
}
.badge-in { background:#eff6ff; color:var(--primary); }
.badge-out { background:#fff7ed; color:var(--warning); }
.badge-manual { background:#f8fafc; color:var(--text-secondary); }
.badge-success { background:#ecfdf5; color:var(--success); }
.badge-fail { background:#fef2f2; color:var(--danger); }
.badge-version {
  background:#eff6ff; color:var(--primary); border:1px solid #bfdbfe;
  font-size:11px; padding:4px 10px; border-radius:4px;
}

/* Status dot */
.status-dot { width:7px; height:7px; border-radius:50%; display:inline-block; margin-right:6px; flex-shrink:0; }
.status-dot.in { background:var(--success); }
.status-dot.out { background:var(--text-muted); }

/* ===== Buttons ===== */
.btn {
  padding:8px 16px; border:none; border-radius:var(--radius-sm); cursor:pointer;
  font-size:13px; font-weight:500; transition:all .15s; display:inline-flex;
  align-items:center; gap:6px; white-space:nowrap;
}
.btn-primary { background:var(--primary); color:#fff; }
.btn-primary:hover { background:var(--primary-hover); }
.btn-danger { background:transparent; color:var(--danger); border:1px solid var(--danger); }
.btn-danger:hover { background:var(--danger); color:#fff; }
.btn-outline { background:transparent; color:var(--primary); border:1px solid var(--primary); }
.btn-outline:hover { background:var(--primary); color:#fff; }
.btn-ghost { background:transparent; color:var(--text-secondary); border:1px solid var(--border); }
.btn-ghost:hover { border-color:var(--text-muted); color:var(--text); }
.btn-sm { padding:4px 10px; font-size:12px; }
.btn-icon { padding:6px; background:transparent; border:none; cursor:pointer; border-radius:4px; color:var(--text-secondary); }
.btn-icon:hover { color:var(--primary); background:#f1f5f9; }
.btn-icon.danger:hover { color:var(--danger); background:#fef2f2; }

/* ===== Forms ===== */
input, select, textarea {
  background:var(--card-bg); border:1px solid var(--border); border-radius:var(--radius-sm);
  padding:8px 12px; color:var(--text); font-size:13px; transition:border-color .15s;
}
input:focus, select:focus { outline:none; border-color:var(--primary); }
.form-group { margin-bottom:14px; }
.form-group label { display:block; font-size:12px; color:var(--text-secondary); margin-bottom:4px; font-weight:500; }
.form-row { display:grid; grid-template-columns:repeat(2,1fr); gap:12px; }
.search-bar { display:flex; gap:8px; margin-bottom:16px; flex-wrap:wrap; align-items:center; }
.search-input { width:100%; max-width:320px; }
.search-input-wrap { position:relative; display:inline-flex; align-items:center; }
.search-input-wrap .search-icon { position:absolute; left:10px; color:var(--text-muted); font-size:14px; pointer-events:none; }
.search-input-wrap input { padding-left:32px; }

/* ===== Section ===== */
.section { display:none; }
.section.active { display:block; }

/* ===== Face Registration Layout ===== */
.face-layout { display:grid; grid-template-columns:300px 1fr; gap:16px; }
.face-student-list { max-height:500px; overflow-y:auto; }
.face-student-item {
  display:flex; align-items:center; gap:10px; padding:10px 12px;
  cursor:pointer; border-bottom:1px solid var(--border); transition:background .15s;
}
.face-student-item:hover { background:#f1f5f9; }
.face-student-item.selected { background:#eff6ff; }
.face-student-avatar {
  width:36px; height:36px; border-radius:50%; background:var(--primary);
  color:#fff; display:flex; align-items:center; justify-content:center;
  font-size:14px; font-weight:600; flex-shrink:0;
}
.face-student-info { flex:1; min-width:0; }
.face-student-info .name { font-size:14px; font-weight:500; }
.face-student-info .stuno { font-size:12px; color:var(--text-secondary); }
.face-student-status { font-size:16px; flex-shrink:0; }
.face-student-status.registered { color:var(--success); }
.face-student-status.unregistered { color:var(--text-muted); }

.face-detail-card { text-align:center; padding:8px 0; }
.face-detail-avatar {
  width:64px; height:64px; border-radius:50%; background:var(--primary);
  color:#fff; display:flex; align-items:center; justify-content:center;
  font-size:24px; font-weight:600; margin:0 auto 12px;
}
.face-detail-name { font-size:20px; font-weight:600; }
.face-detail-meta { font-size:13px; color:var(--text-secondary); margin-top:4px; }
.face-detail-status { font-size:12px; color:var(--success); margin-top:8px; }

.upload-area {
  border:2px dashed var(--border); border-radius:var(--radius);
  padding:32px; text-align:center; margin-top:16px; cursor:pointer;
  transition:border-color .15s;
}
.upload-area:hover { border-color:var(--primary); }
.upload-area img { max-width:200px; max-height:200px; border-radius:var(--radius); }
.upload-area .upload-hint { font-size:13px; color:var(--text-secondary); margin-top:8px; }
.upload-area .upload-icon { font-size:40px; color:var(--text-muted); margin-bottom:8px; }

.security-notice {
  background:#eff6ff; border:1px solid #bfdbfe; border-radius:var(--radius-sm);
  padding:12px 16px; margin-top:16px; display:flex; align-items:flex-start; gap:10px;
  font-size:12px; color:var(--text-secondary); line-height:1.6;
}
.security-notice .lock-icon { color:var(--primary); font-size:16px; flex-shrink:0; margin-top:1px; }

.face-actions { display:flex; gap:10px; margin-top:16px; }

/* ===== Records filter ===== */
.filter-select { min-width:120px; }

/* ===== Pagination ===== */
.pagination { display:flex; justify-content:center; gap:4px; margin-top:16px; }
.pagination button {
  padding:6px 14px; border:1px solid var(--border); background:var(--card-bg);
  color:var(--text); border-radius:6px; cursor:pointer; font-size:12px;
}
.pagination button:hover { background:var(--primary); color:#fff; border-color:var(--primary); }
.pagination button.active { background:var(--primary); color:#fff; }

/* ===== Toast ===== */
.toast {
  position:fixed; top:20px; right:20px; z-index:9999;
  padding:12px 20px; border-radius:10px; font-size:13px; font-weight:500;
  animation:slideIn .3s ease; display:none;
}
.toast.success { background:#166534; color:#bbf7d0; border:1px solid #22c55e; }
.toast.error { background:#7f1d1d; color:#fecaca; border:1px solid #ef4444; }
@keyframes slideIn { from{transform:translateX(100%);opacity:0} to{transform:translateX(0);opacity:1} }

/* ===== Modal ===== */
.modal-overlay {
  position:fixed; inset:0; background:rgba(0,0,0,.7); z-index:200;
  display:flex; align-items:center; justify-content:center; display:none;
}
.modal {
  background:var(--card-bg); border:1px solid var(--border); border-radius:12px;
  padding:28px; width:90%; max-width:500px;
}
.modal h3 { font-size:16px; margin-bottom:16px; }
.modal-actions { display:flex; gap:8px; justify-content:flex-end; margin-top:20px; }

/* ===== Responsive ===== */
@media(max-width:768px){
  .stat-grid{grid-template-columns:repeat(2,1fr)}
  .chart-row{grid-template-columns:1fr}
  .face-layout{grid-template-columns:1fr}
  .sidebar{width:60px;min-width:60px}
  .sidebar .logo-text,.sidebar .logo-ver,.nav-item span:not(.nav-icon){display:none}
  .main{margin-left:60px;max-width:calc(100vw - 60px)}
}
</style>
</head>
<body>

<!-- ===== Sidebar ===== -->
<aside class="sidebar">
  <div class="sidebar-logo">
    <div class="logo-icon">&#x1f6e1;</div>
    <div><div class="logo-text">校园门禁</div><div class="logo-ver">管理后台 v1.0</div></div>
  </div>
  <nav class="sidebar-nav">
    <button class="nav-item active" onclick="switchTab('dashboard')">
      <span class="nav-icon">&#x1f4ca;</span> <span>总览仪表盘</span>
    </button>
    <button class="nav-item" onclick="switchTab('students')">
      <span class="nav-icon">&#x1f393;</span> <span>学生信息管理</span>
    </button>
    <button class="nav-item" onclick="switchTab('faces')">
      <span class="nav-icon">&#x1f9d1;</span> <span>人脸注册管理</span>
    </button>
    <button class="nav-item" onclick="switchTab('records')">
      <span class="nav-icon">&#x1f4cb;</span> <span>通行记录管理</span>
    </button>
    <button class="nav-item" onclick="switchTab('devices')">
      <span class="nav-icon">&#x1f4fb;</span> <span>设备状态</span>
    </button>
  </nav>
</aside>

<!-- ===== Main Content ===== -->
<main class="main">

  <!-- Toast -->
  <div id="toast" class="toast"></div>

  <!-- ===== Dashboard ===== -->
  <section id="sec-dashboard" class="section active">
    <div class="page-header">
      <div>
        <h2>总览仪表盘</h2>
        <p class="subtitle">实时掌握校园门禁运行状态</p>
      </div>
      <div class="header-badge online">&#x25cf; 系统运行中</div>
    </div>

    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-icon blue">&#x1f465;</div>
        <div class="stat-info">
          <div class="stat-value" id="stat-students">-</div>
          <div class="stat-label">学生总数 <span style="font-size:12px;color:var(--text-muted)" id="stat-registered">已注册人脸 0 人</span></div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon green">&#x2194;</div>
        <div class="stat-info">
          <div class="stat-value" id="stat-in">-</div>
          <div class="stat-label">当前在校 <span style="font-size:12px;color:var(--text-muted)" id="stat-out">离校 0 人</span></div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon blue">&#x2713;</div>
        <div class="stat-info">
          <div class="stat-value" id="stat-today">-</div>
          <div class="stat-label">今日通行 <span style="font-size:12px;color:var(--text-muted)" id="stat-today-fail">失败 0 次</span></div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon orange">&#x1f5b4;</div>
        <div class="stat-info">
          <div class="stat-value" id="stat-devices">-</div>
          <div class="stat-label">在线设备 <span style="font-size:12px;color:var(--text-muted)" id="stat-total-devices">共 0 台设备</span></div>
        </div>
      </div>
    </div>

    <div class="chart-row">
      <div class="card">
        <div class="card-header">&#x1f4c8; 近7日通行趋势</div>
        <div class="card-body">
          <div class="chart-container" id="trend-chart">
            <svg width="100%" height="240" viewBox="0 0 500 240">
              <line x1="50" y1="200" x2="480" y2="200" stroke="#e2e8f0" stroke-width="1"/>
              <line x1="50" y1="20" x2="50" y2="200" stroke="#e2e8f0" stroke-width="1"/>
              <text x="20" y="204" fill="#94a3b8" font-size="11" text-anchor="end">0</text>
              <text x="20" y="140" fill="#94a3b8" font-size="11" text-anchor="end">5</text>
              <text x="20" y="80" fill="#94a3b8" font-size="11" text-anchor="end">10</text>
              <line x1="50" y1="200" x2="480" y2="200" stroke="#3b82f6" stroke-width="2" stroke-dasharray="4,3"/>
              <line x1="245" y1="200" x2="245" y2="200" stroke="#10b981" stroke-width="2" stroke-dasharray="4,3"/>
              <text x="260" y="196" fill="#94a3b8" font-size="11">暂无通行数据</text>
            </svg>
          </div>
          <div class="chart-legend">
            <div class="chart-legend-item"><span class="chart-legend-dot" style="background:#3b82f6"></span>进入</div>
            <div class="chart-legend-item"><span class="chart-legend-dot" style="background:#10b981"></span>离开</div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">&#x1f465; 院系分布</div>
        <div class="card-body" style="display:flex;align-items:center;justify-content:center;flex-direction:column">
          <svg width="200" height="200" viewBox="0 0 42 42" id="dept-donut">
            <circle cx="21" cy="21" r="15.9" fill="none" stroke="#e2e8f0" stroke-width="8"/>
            <circle cx="21" cy="21" r="15.9" fill="none" stroke="#3b82f6" stroke-width="8"
              stroke-dasharray="0 100" stroke-dashoffset="25" transform="rotate(-90 21 21)" id="dept-seg"/>
            <text x="21" y="20" text-anchor="middle" fill="#1e293b" font-size="7" font-weight="700" id="dept-total">0</text>
            <text x="21" y="28" text-anchor="middle" fill="#94a3b8" font-size="4">总人数</text>
          </svg>
          <div class="chart-legend" id="dept-legend" style="margin-top:12px">
            <div class="chart-legend-item"><span class="chart-legend-dot" style="background:var(--text-muted)"></span>暂无数据</div>
          </div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">&#x1f4cb; 最近通行记录</div>
      <div class="card-body no-padding" style="overflow-x:auto">
        <table>
          <thead><tr><th>时间</th><th>姓名</th><th>学号</th><th>方向</th><th>结果</th><th>相似度</th></tr></thead>
          <tbody id="recent-records"></tbody>
        </table>
      </div>
    </div>
  </section>

  <!-- ===== Students ===== -->
  <section id="sec-students" class="section">
    <div class="page-header">
      <div>
        <h2>学生信息管理</h2>
        <p class="subtitle">管理学生基本信息，共 <span id="stu-total-count">0</span> 条记录</p>
      </div>
      <button class="btn btn-primary" onclick="showStudentModal()">+ 添加学生</button>
    </div>
    <div class="card">
      <div class="card-body">
        <div class="search-bar">
          <div class="search-input-wrap">
            <span class="search-icon">&#x1f50d;</span>
            <input type="text" id="stu-search" placeholder="搜索学号、姓名、院系..." onkeyup="loadStudents()" class="search-input">
          </div>
        </div>
        <div style="overflow-x:auto">
        <table>
          <thead><tr><th>学号</th><th>姓名</th><th>院系</th><th>在校状态</th><th>人脸注册</th><th>操作</th></tr></thead>
          <tbody id="student-table"></tbody>
        </table>
        </div>
        <div class="pagination" id="student-pages"></div>
      </div>
    </div>
  </section>

  <!-- ===== Faces ===== -->
  <section id="sec-faces" class="section">
    <div class="page-header">
      <div>
        <h2>人脸注册管理</h2>
        <p class="subtitle">为学生注册人脸特征，经 AES-256-GCM 加密后存储</p>
      </div>
      <div class="badge badge-version" style="display:flex;align-items:center;gap:6px">
        &#x1f512; 全局版本 <span id="face-global-version">v-</span> &middot; 已注册 <span id="face-registered-count">0</span> 人
      </div>
    </div>

    <div class="face-layout">
      <!-- Left: student list -->
      <div class="card">
        <div class="card-body" style="padding:12px">
          <div class="search-input-wrap" style="width:100%;margin-bottom:8px">
            <span class="search-icon">&#x1f50d;</span>
            <input type="text" id="face-search" placeholder="搜索学号或姓名..." onkeyup="filterFaceStudents()" style="width:100%">
          </div>
          <div class="face-student-list" id="face-student-list">
            <div style="text-align:center;color:var(--text-muted);padding:20px;font-size:13px">加载中...</div>
          </div>
        </div>
      </div>

      <!-- Right: registration detail -->
      <div class="card" id="face-detail-panel">
        <div class="card-body">
          <div style="text-align:center;color:var(--text-muted);padding:40px 0" id="face-detail-empty">
            <div style="font-size:48px;margin-bottom:12px">&#x1f464;</div>
            <p style="font-size:14px">请从左侧列表选择学生</p>
          </div>
          <div id="face-detail-content" style="display:none">
            <div class="face-detail-card">
              <div class="face-detail-avatar" id="face-detail-avatar">-</div>
              <div class="face-detail-name" id="face-detail-name">-</div>
              <div class="face-detail-meta" id="face-detail-meta">-</div>
              <div class="face-detail-status" id="face-detail-status">-</div>
            </div>
            <div class="upload-area" id="upload-area" onclick="document.getElementById('face-photo').click()">
              <div id="upload-preview">
                <div class="upload-icon">&#x1f4f7;</div>
                <p class="upload-hint">点击此处上传注册照片</p>
                <p style="font-size:11px;color:var(--text-muted)">支持 JPG、PNG 格式</p>
              </div>
              <img id="upload-preview-img" src="" style="display:none" alt="">
            </div>
            <input type="file" id="face-photo" accept="image/*" style="display:none" onchange="previewUploadPhoto()">
            <div class="security-notice">
              <span class="lock-icon">&#x1f512;</span>
              <span>人脸特征将经过 AES-256-GCM 加密，随机生成12字节IV，加密后存储。原始照片不持久保存。</span>
            </div>
            <div class="face-actions">
              <button class="btn btn-primary" onclick="registerFaceForSelected()" id="btn-register-face">&#x1f504; 重新注册</button>
              <button class="btn btn-danger" onclick="deleteFaceForSelected()" id="btn-delete-face" style="display:none">&#x2715; 清除注册</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- ===== Records ===== -->
  <section id="sec-records" class="section">
    <div class="page-header">
      <div>
        <h2>通行记录管理</h2>
        <p class="subtitle">共 <span id="rec-total">0</span> 条记录，当前筛选 <span id="rec-filtered">0</span> 条</p>
      </div>
      <div style="display:flex;gap:8px">
        <button class="btn btn-outline" onclick="showManualRecordModal()">+ 手动添加</button>
        <button class="btn btn-ghost" onclick="exportCSV()">&#x1f4e5; 导出CSV</button>
      </div>
    </div>
    <div class="card">
      <div class="card-body">
        <div class="search-bar">
          <div class="search-input-wrap">
            <span class="search-icon">&#x1f50d;</span>
            <input type="text" id="rec-stu" placeholder="搜索姓名、学号、设备..." class="search-input">
          </div>
          <select id="rec-dir" class="filter-select" onchange="loadRecords()">
            <option value="">全部方向</option>
            <option value="in">进入</option>
            <option value="out">离开</option>
            <option value="manual">手动</option>
          </select>
          <select id="rec-result" class="filter-select" onchange="loadRecords()">
            <option value="">全部结果</option>
            <option value="success">成功</option>
            <option value="fail">失败</option>
          </select>
          <button class="btn btn-primary btn-sm" onclick="loadRecords()">&#x1f50d; 查询</button>
        </div>
        <div style="overflow-x:auto">
        <table>
          <thead><tr><th>识别时间</th><th>姓名</th><th>学号</th><th>方向</th><th>结果</th><th>相似度</th><th>设备</th><th>操作</th></tr></thead>
          <tbody id="record-table"></tbody>
        </table>
        </div>
        <div class="pagination" id="record-pages"></div>
      </div>
    </div>
  </section>

  <!-- ===== Devices ===== -->
  <section id="sec-devices" class="section">
    <div class="page-header">
      <div>
        <h2>设备状态</h2>
        <p class="subtitle">查看所有门禁终端的在线状态</p>
      </div>
    </div>
    <div class="card">
      <div class="card-body no-padding" style="overflow-x:auto">
        <table>
          <thead><tr><th>设备序列号</th><th>名称</th><th>状态</th><th>最后心跳</th></tr></thead>
          <tbody id="device-table"></tbody>
        </table>
      </div>
    </div>
  </section>

  <!-- ===== Student Modal ===== -->
  <div class="modal-overlay" id="student-modal-overlay">
    <div class="modal">
      <h3 id="student-modal-title">添加学生</h3>
      <input type="hidden" id="stu-edit-id">
      <div class="form-group"><label>学号 *</label><input type="text" id="stu-no" placeholder="如 20231113513"></div>
      <div class="form-group"><label>姓名 *</label><input type="text" id="stu-name"></div>
      <div class="form-group"><label>院系</label><input type="text" id="stu-dept" placeholder="如 工学部计算机与信息工程学院"></div>
      <input type="hidden" id="stu-status" value="out">
      <div class="modal-actions">
        <button class="btn btn-ghost" onclick="closeStudentModal()">取消</button>
        <button class="btn btn-primary" onclick="saveStudent()">保存</button>
      </div>
    </div>
  </div>

  <!-- ===== Manual Record Modal ===== -->
  <div class="modal-overlay" id="manual-record-modal-overlay">
    <div class="modal">
      <h3>手动添加通行记录</h3>
      <div class="form-group"><label>学生</label><select id="manual-student-id"></select></div>
      <div class="form-group"><label>方向</label><select id="manual-direction"><option value="in">进门</option><option value="out">出门</option></select></div>
      <div class="modal-actions">
        <button class="btn btn-ghost" onclick="closeManualRecordModal()">取消</button>
        <button class="btn btn-primary" onclick="saveManualRecord()">保存</button>
      </div>
    </div>
  </div>

</main>

<script>
const API = '';
let studentPage = 1, recordPage = 1;
let selectedFaceStudentId = null;
let allFaceStudents = [];
let faceStudentMap = {}; // student_id -> {has_face, feature_version}

// ====== Utilities ======
function $(id) { return document.getElementById(id); }
function toast(msg, type) {
  const t = $('toast'); t.textContent = msg; t.className = 'toast ' + type; t.style.display = 'block';
  setTimeout(() => t.style.display = 'none', 3000);
}
function switchTab(name) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(t => t.classList.remove('active'));
  const sec = document.getElementById('sec-' + name);
  if (sec) { sec.classList.add('active'); loadTabData(name); }
  // Find and activate the corresponding nav item
  const navItem = document.querySelector('.nav-item[onclick*="' + name + '"]');
  if (navItem) navItem.classList.add('active');
}
function loadTabData(name) {
  if (name === 'dashboard') loadDashboard();
  if (name === 'students') loadStudents();
  if (name === 'faces') loadFaces();
  if (name === 'records') loadRecords();
  if (name === 'devices') loadDevices();
}
function formatTime(iso) {
  if (!iso) return '-';
  const d = new Date(iso.replace(' ','T') + (iso.includes('Z')?'':'Z'));
  return d.toLocaleString('zh-CN',{hour:'2-digit',minute:'2-digit',second:'2-digit'});
}
function formatDateTime(iso) {
  if (!iso) return '-';
  const d = new Date(iso.replace(' ','T') + (iso.includes('Z')?'':'Z'));
  return d.toLocaleString('zh-CN');
}

// ====== Dashboard ======
async function loadDashboard() {
  try {
    const [stuRes, recRes, devRes, facesRes] = await Promise.all([
      fetch(API + '/api/student').then(r=>r.json()),
      fetch(API + '/api/record?per_page=8').then(r=>r.json()),
      fetch(API + '/api/heartbeat/status').then(r=>r.json()),
      fetch(API + '/api/sync/features?since_version=0').then(r=>r.json()),
    ]);
    const totalStudents = stuRes.total || 0;
    const inCount = stuRes.data ? stuRes.data.filter(s=>s.status==='in').length : 0;
    const outCount = totalStudents - inCount;
    const todayTotal = recRes.total || 0;
    const devices = devRes.devices || [];
    const onlineDevices = devices.filter(d=>d.is_online).length;
    const faceCount = facesRes.features ? facesRes.features.length : 0;

    $('stat-students').textContent = totalStudents;
    $('stat-registered').textContent = '已注册人脸 ' + faceCount + ' 人';
    $('stat-in').textContent = inCount;
    $('stat-out').textContent = '离校 ' + outCount + ' 人';
    $('stat-today').textContent = todayTotal;
    $('stat-today-fail').textContent = '失败 0 次';
    $('stat-devices').textContent = onlineDevices;
    $('stat-total-devices').textContent = '共 ' + devices.length + ' 台设备';

    // Recent records
    let recHtml = '';
    if (recRes.data) recRes.data.slice(0,8).forEach(r => {
      const simDisplay = r.similarity != null ? (r.similarity * 100).toFixed(1) + '%' : '-';
      const dirLabel = r.direction==='in'?'进入':(r.direction==='out'?'离开':'手动');
      const dirClass = r.direction==='in'?'in':(r.direction==='out'?'out':'manual');
      recHtml += `<tr>
        <td style="font-family:monospace;font-size:12px">${formatDateTime(r.record_time)}</td>
        <td>${r.student_name||'-'}</td>
        <td style="font-family:monospace">${r.stu_no||'-'}</td>
        <td><span class="badge badge-${dirClass}">${dirLabel}</span></td>
        <td><span class="badge badge-${r.result||'success'}">${r.result==='success'?'&#x2713; 成功':'&#x2717; 失败'}</span></td>
        <td style="font-weight:500;color:var(--success)">${simDisplay}</td></tr>`;
    });
    $('recent-records').innerHTML = recHtml || '<tr><td colspan="6" style="color:var(--text-muted);text-align:center;padding:24px">暂无记录</td></tr>';

    // Update dept donut
    const depts = {};
    if (stuRes.data) stuRes.data.forEach(s => {
      const d = s.department || '未指定';
      depts[d] = (depts[d] || 0) + 1;
    });
    const deptNames = Object.keys(depts);
    const colors = ['#10b981','#3b82f6','#f59e0b','#8b5cf6','#ef4444','#06b6d4','#ec4899','#84cc16'];
    if (deptNames.length > 0) {
      const total = deptNames.reduce((s,k)=>s+depts[k],0);
      let legendHtml = '';
      let cumulative = 0;
      let segHtml = '';
      deptNames.forEach((d,i) => {
        const pct = depts[d] / total;
        const color = colors[i % colors.length];
        legendHtml += `<div class="chart-legend-item"><span class="chart-legend-dot" style="background:${color}"></span>${d} (${depts[d]}人)</div>`;
        segHtml += `<circle cx="21" cy="21" r="15.9" fill="none" stroke="${color}" stroke-width="8"
          stroke-dasharray="${(pct*100).toFixed(1)} ${(100-pct*100).toFixed(1)}" stroke-dashoffset="${(25-cumulative).toFixed(1)}" transform="rotate(-90 21 21)"/>`;
        cumulative += pct * 100;
      });
      $('dept-donut').innerHTML = segHtml + `<text x="21" y="20" text-anchor="middle" fill="#1e293b" font-size="7" font-weight="700">${total}</text><text x="21" y="28" text-anchor="middle" fill="#94a3b8" font-size="4">总人数</text>`;
      $('dept-legend').innerHTML = legendHtml;
    }
  } catch(e) { console.error(e); }
}

// ====== Students ======
async function loadStudents() {
  const kw = $('stu-search').value;
  try {
    const resp = await fetch(API + '/api/student?keyword=' + encodeURIComponent(kw) + '&page=' + studentPage);
    const data = await resp.json();
    $('stu-total-count').textContent = data.total || 0;

    // Also get face data for registration status
    let faceMap = {};
    try {
      const fResp = await fetch(API + '/api/sync/features?since_version=0');
      const fData = await fResp.json();
      if (fData.features) fData.features.forEach(f => { faceMap[f.student_id] = true; });
    } catch(e) {}

    let html = '';
    if (data.data) data.data.forEach(s => {
      const hasFace = faceMap[s.id];
      html += `<tr>
        <td style="font-family:monospace">${s.stu_no}</td>
        <td>${s.name}</td>
        <td>${s.department||'-'}</td>
        <td><span style="display:inline-flex;align-items:center;gap:6px">
          <span class="status-dot ${s.status==='in'?'in':'out'}"></span>
          <span style="color:${s.status==='in'?'var(--success)':'var(--text-muted)'}">${s.status==='in'?'在校':'离校'}</span>
        </span></td>
        <td><span style="color:${hasFace?'var(--success)':'var(--text-muted)'}">${hasFace?'&#x2713; 已注册':'&#x2717; 未注册'}</span></td>
        <td>
          <button class="btn-icon" onclick="editStudent(${s.id})" title="编辑">&#x270F;</button>
          <button class="btn-icon danger" onclick="deleteStudent(${s.id})" title="删除">&#x1f5d1;</button>
        </td></tr>`;
    });
    $('student-table').innerHTML = html || '<tr><td colspan="6" style="color:var(--text-muted);text-align:center;padding:24px">暂无学生</td></tr>';
    renderPagination('student-pages', data.total, studentPage, p => { studentPage = p; loadStudents(); });
  } catch(e) { toast('加载失败: '+e.message, 'error'); }
}

function showStudentModal(editData) {
  if (editData) {
    $('student-modal-title').textContent = '编辑学生';
    $('stu-edit-id').value = editData.id;
    $('stu-no').value = editData.stu_no;
    $('stu-name').value = editData.name;
    $('stu-dept').value = editData.department || '';
    $('stu-status').value = editData.status || 'out';
  } else {
    $('student-modal-title').textContent = '添加学生';
    $('stu-edit-id').value = '';
    $('stu-no').value = '';
    $('stu-name').value = '';
    $('stu-dept').value = '';
    $('stu-status').value = 'out';
  }
  $('student-modal-overlay').style.display = 'flex';
}
function closeStudentModal() { $('student-modal-overlay').style.display = 'none'; }
async function saveStudent() {
  const id = $('stu-edit-id').value;
  const body = {
    stu_no: $('stu-no').value.trim(),
    name: $('stu-name').value.trim(),
    department: $('stu-dept').value.trim() || null,
  };
  if (!body.stu_no || !body.name) { toast('学号和姓名为必填项', 'error'); return; }
  try {
    let resp;
    if (id) {
      resp = await fetch(API + '/api/student/' + id, {method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    } else {
      resp = await fetch(API + '/api/student', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    }
    if (resp.ok) { toast(id?'更新成功':'添加成功', 'success'); closeStudentModal(); loadStudents(); loadFaces(); }
    else { const e = await resp.json(); toast(e.error||'操作失败', 'error'); }
  } catch(e) { toast('请求失败: '+e.message, 'error'); }
}
async function editStudent(id) {
  try {
    const resp = await fetch(API + '/api/student/' + id);
    const s = await resp.json();
    showStudentModal(s);
  } catch(e) { toast('加载失败', 'error'); }
}
async function deleteStudent(id) {
  if (!confirm('确定删除该学生？关联的人脸特征也将被删除。')) return;
  try {
    const resp = await fetch(API + '/api/student/' + id, {method:'DELETE'});
    if (resp.ok) { toast('删除成功', 'success'); loadStudents(); loadFaces(); }
    else toast('删除失败', 'error');
  } catch(e) { toast('请求失败', 'error'); }
}

// ====== Faces ======
async function loadFaces() {
  try {
    // Load all students
    const stuResp = await fetch(API + '/api/student?per_page=999');
    const stuData = await stuResp.json();
    allFaceStudents = stuData.data || [];

    // Load face features
    const syncResp = await fetch(API + '/api/sync/features?since_version=0');
    const syncData = await syncResp.json();
    faceStudentMap = {};
    let globalVersion = 0;
    if (syncData.features) syncData.features.forEach(f => {
      faceStudentMap[f.student_id] = { has_face: true, feature_version: f.feature_version };
      if (f.feature_version > globalVersion) globalVersion = f.feature_version;
    });

    $('face-global-version').textContent = 'v' + globalVersion;
    $('face-registered-count').textContent = Object.keys(faceStudentMap).length;

    renderFaceStudentList(allFaceStudents);
  } catch(e) { console.error(e); }
}

function renderFaceStudentList(students) {
  const list = $('face-student-list');
  if (students.length === 0) {
    list.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:20px;font-size:13px">暂无学生</div>';
    return;
  }
  let html = '';
  students.forEach(s => {
    const face = faceStudentMap[s.id];
    const isRegistered = face && face.has_face;
    const selected = selectedFaceStudentId === s.id;
    html += `<div class="face-student-item${selected?' selected':''}" onclick="selectFaceStudent(${s.id})" id="face-item-${s.id}">
      <div class="face-student-avatar">${s.name.charAt(0)}</div>
      <div class="face-student-info">
        <div class="name">${s.name}</div>
        <div class="stuno">${s.stu_no}</div>
      </div>
      <span class="face-student-status ${isRegistered?'registered':'unregistered'}">${isRegistered?'&#x2713;':'&#x2717;'}</span>
    </div>`;
  });
  list.innerHTML = html;
}

function filterFaceStudents() {
  const kw = $('face-search').value.toLowerCase();
  const filtered = allFaceStudents.filter(s =>
    s.name.toLowerCase().includes(kw) || s.stu_no.toLowerCase().includes(kw)
  );
  renderFaceStudentList(filtered);
}

function selectFaceStudent(studentId) {
  selectedFaceStudentId = studentId;
  // Update list selection
  document.querySelectorAll('.face-student-item').forEach(el => el.classList.remove('selected'));
  const item = document.getElementById('face-item-' + studentId);
  if (item) item.classList.add('selected');

  const student = allFaceStudents.find(s => s.id === studentId);
  if (!student) return;

  const face = faceStudentMap[studentId];
  const isRegistered = face && face.has_face;

  $('face-detail-empty').style.display = 'none';
  $('face-detail-content').style.display = 'block';
  $('face-detail-avatar').textContent = student.name.charAt(0);
  $('face-detail-name').textContent = student.name;
  $('face-detail-meta').textContent = student.stu_no + ' · ' + (student.department || '未指定院系');
  $('face-detail-status').innerHTML = isRegistered
    ? '&#x2713; 人脸已注册 · 特征版本 v' + face.feature_version
    : '&#x2717; 未注册人脸';
  $('face-detail-status').style.color = isRegistered ? 'var(--success)' : 'var(--text-muted)';
  $('btn-delete-face').style.display = isRegistered ? 'inline-flex' : 'none';
  $('btn-register-face').innerHTML = isRegistered ? '&#x1f504; 重新注册' : '&#x1f4f7; 注册人脸';

  // Reset upload area
  $('upload-preview').style.display = 'block';
  $('upload-preview-img').style.display = 'none';
  $('face-photo').value = '';
}

function previewUploadPhoto() {
  const file = $('face-photo').files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = function(e) {
    $('upload-preview').style.display = 'none';
    $('upload-preview-img').src = e.target.result;
    $('upload-preview-img').style.display = 'block';
  };
  reader.readAsDataURL(file);
}

async function registerFaceForSelected() {
  if (!selectedFaceStudentId) { toast('请先从左侧列表选择学生', 'error'); return; }
  const photoFile = $('face-photo').files[0];
  if (!photoFile) { toast('请选择照片', 'error'); return; }
  const formData = new FormData();
  formData.append('student_id', selectedFaceStudentId);
  formData.append('photo', photoFile);
  try {
    const resp = await fetch(API + '/api/face/register', {method:'POST', body:formData});
    const data = await resp.json();
    if (resp.ok) {
      toast('注册成功！版本号: ' + data.feature_version, 'success');
      loadFaces();
      selectFaceStudent(selectedFaceStudentId);
    } else {
      toast(data.error||'注册失败', 'error');
    }
  } catch(e) { toast('请求失败: '+e.message, 'error'); }
}

async function deleteFaceForSelected() {
  if (!selectedFaceStudentId) return;
  if (!confirm('确定删除该学生的人脸特征？')) return;
  try {
    const resp = await fetch(API + '/api/face/student/' + selectedFaceStudentId, {method:'DELETE'});
    if (resp.ok) { toast('特征已删除', 'success'); loadFaces(); selectFaceStudent(selectedFaceStudentId); }
    else toast('删除失败', 'error');
  } catch(e) { toast('请求失败', 'error'); }
}

// ====== Records ======
async function loadRecords() {
  const params = new URLSearchParams();
  const stu = $('rec-stu').value.trim(); if (stu) params.set('stu_no', stu);
  const dir = $('rec-dir').value; if (dir) params.set('direction', dir);
  const res = $('rec-result').value; if (res) params.set('result', res);
  params.set('page', recordPage); params.set('per_page', 20);
  try {
    const resp = await fetch(API + '/api/record?' + params.toString());
    const data = await resp.json();
    $('rec-total').textContent = data.total || 0;
    $('rec-filtered').textContent = data.total || 0;
    let html = '';
    if (data.data) data.data.forEach(r => {
      const simDisplay = r.similarity != null ? (r.similarity * 100).toFixed(1) + '%' : '-';
      const simColor = r.similarity != null ? (r.similarity >= 0.5 ? 'var(--success)' : 'var(--danger)') : 'var(--text-muted)';
      const dirLabel = r.direction==='in'?'进入':(r.direction==='out'?'离开':'手动');
      const dirClass = r.direction==='in'?'in':(r.direction==='out'?'out':'manual');
      const isManual = r.direction === 'manual';
      html += `<tr>
        <td style="font-family:monospace;font-size:12px">${formatDateTime(r.record_time)}</td>
        <td>${isManual?'<span style="color:var(--text-muted)">手动开门</span>':(r.student_name||'-')}</td>
        <td style="font-family:monospace">${isManual?'-':(r.stu_no||'-')}</td>
        <td><span class="badge badge-${dirClass}">${dirLabel}</span></td>
        <td><span class="badge badge-${r.result||'success'}">${r.result==='success'?'&#x2713; 成功':'&#x2717; 失败'}</span></td>
        <td style="font-weight:500;color:${simColor}">${simDisplay}</td>
        <td style="font-family:monospace;font-size:12px">${r.device_sn||'-'}</td>
        <td><button class="btn-icon danger" onclick="deleteRecord(${r.id})" title="删除">&#x1f5d1;</button></td></tr>`;
    });
    $('record-table').innerHTML = html || '<tr><td colspan="8" style="color:var(--text-muted);text-align:center;padding:24px">暂无记录</td></tr>';
    renderPagination('record-pages', data.total, recordPage, p => { recordPage = p; loadRecords(); });
  } catch(e) { toast('查询失败', 'error'); }
}

async function deleteRecord(id) {
  if (!confirm('确定删除该记录？')) return;
  try {
    const resp = await fetch(API + '/api/record/' + id, {method:'DELETE'});
    if (resp.ok) { toast('删除成功', 'success'); loadRecords(); }
    else toast('删除失败', 'error');
  } catch(e) { toast('请求失败', 'error'); }
}

async function exportCSV() {
  const params = new URLSearchParams();
  const stu = $('rec-stu').value.trim(); if (stu) params.set('stu_no', stu);
  const dir = $('rec-dir').value; if (dir) params.set('direction', dir);
  window.open(API + '/api/record/export?' + params.toString(), '_blank');
}

// Manual record
function showManualRecordModal() {
  $('manual-record-modal-overlay').style.display = 'flex';
  // Load student options
  fetch(API + '/api/student?per_page=999').then(r=>r.json()).then(data => {
    let opts = '<option value="">-- 选择学生 --</option>';
    if (data.data) data.data.forEach(s => {
      opts += `<option value="${s.id}">${s.name} (${s.stu_no})</option>`;
    });
    $('manual-student-id').innerHTML = opts;
  });
}
function closeManualRecordModal() { $('manual-record-modal-overlay').style.display = 'none'; }
async function saveManualRecord() {
  const studentId = $('manual-student-id').value;
  if (!studentId) { toast('请选择学生', 'error'); return; }
  const direction = $('manual-direction').value;
  try {
    const resp = await fetch(API + '/api/record', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({student_id:parseInt(studentId), device_sn:'MANUAL', direction:direction, result:'success', similarity:1.0})
    });
    if (resp.ok) { toast('记录已添加', 'success'); closeManualRecordModal(); loadRecords(); }
    else { const e = await resp.json(); toast(e.error||'添加失败', 'error'); }
  } catch(e) { toast('请求失败', 'error'); }
}

// ====== Devices ======
async function loadDevices() {
  try {
    const resp = await fetch(API + '/api/heartbeat/status');
    const data = await resp.json();
    let html = '';
    if (data.devices) data.devices.forEach(d => {
      html += `<tr>
        <td style="font-family:monospace">${d.device_sn}</td>
        <td>${d.device_name||d.device_sn}</td>
        <td><span style="display:inline-flex;align-items:center;gap:6px">
          <span class="status-dot ${d.is_online?'in':'out'}"></span>
          <span style="color:${d.is_online?'var(--success)':'var(--text-muted)'}">${d.is_online?'在线':'离线'}</span>
        </span></td>
        <td style="font-family:monospace;font-size:12px">${d.last_heartbeat||'-'}</td></tr>`;
    });
    $('device-table').innerHTML = html || '<tr><td colspan="4" style="color:var(--text-muted);text-align:center;padding:24px">暂无设备</td></tr>';
  } catch(e) { console.error(e); }
}

// ====== Pagination ======
function renderPagination(containerId, total, page, cb) {
  const container = $(containerId);
  const totalPages = Math.ceil(total / 20) || 1;
  if (totalPages <= 1) { container.innerHTML = ''; return; }
  let html = '';
  for (let i = 1; i <= totalPages; i++) {
    html += `<button class="${i===page?'active':''}" onclick="(${cb.toString()})(${i})">${i}</button>`;
  }
  container.innerHTML = html;
}

// ====== Init ======
loadDashboard();
</script>
</body>
</html>'''

# ====== 首页重定向 ======
INDEX_REDIRECT = '''<!DOCTYPE html>
<html><head><meta http-equiv="refresh" content="0;url=/admin"></head>
<body><p>跳转至 <a href="/admin">管理后台</a>...</p></body></html>'''


@bp.route('/')
@bp.route('')
def admin_index():
    return render_template_string(ADMIN_HTML)
