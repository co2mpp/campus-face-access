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
.btn-icon {
  width:32px;height:32px;padding:0;background:transparent;border:none;cursor:pointer;
  border-radius:6px;color:var(--text-muted);display:inline-flex;
  align-items:center;justify-content:center;transition:all .15s;
}
.btn-icon:hover { color:var(--primary); background:rgba(37,99,235,.08); }
.btn-icon.danger:hover { color:var(--danger); background:rgba(239,68,68,.08); }
.btn-icon svg { width:16px; height:16px; }

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
.pagination button:disabled { opacity:.3; cursor:default; pointer-events:none; }

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

/* ===== Login Page ===== */
.login-overlay {
  position:fixed; inset:0; background:var(--sidebar-bg); z-index:300;
  display:flex; align-items:center; justify-content:center;
}
.login-card {
  background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1);
  border-radius:16px; padding:40px 36px; width:90%; max-width:400px;
  text-align:center;
}
.login-card .login-icon {
  width:56px; height:56px; background:var(--primary); border-radius:14px;
  display:flex; align-items:center; justify-content:center;
  color:#fff; font-size:26px; margin:0 auto 16px;
}
.login-card h2 { color:#fff; font-size:20px; margin-bottom:6px; }
.login-card .login-sub { color:var(--text-muted); font-size:13px; margin-bottom:24px; }
.login-card input {
  width:100%; padding:10px 14px; margin-bottom:12px; border-radius:8px;
  background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.15);
  color:#fff; font-size:14px;
}
.login-card input::placeholder { color:var(--text-muted); }
.login-card input:focus { border-color:var(--primary); outline:none; }
.login-card .login-btn {
  width:100%; padding:10px; border:none; border-radius:8px;
  background:var(--primary); color:#fff; font-size:14px; font-weight:600;
  cursor:pointer; margin-top:8px; transition:background .15s;
}
.login-card .login-btn:hover { background:var(--primary-hover); }
.login-card .login-err { color:var(--danger); font-size:12px; margin-top:8px; min-height:18px; }

/* Logout button in sidebar */
.sidebar-footer { padding:8px; border-top:1px solid rgba(255,255,255,0.08); }
.sidebar-footer .logout-btn {
  display:flex; align-items:center; gap:8px; padding:10px 12px;
  border-radius:var(--radius); cursor:pointer; color:rgba(255,255,255,0.5);
  font-size:13px; transition:all .15s; border:none; background:none; width:100%;
}
.sidebar-footer .logout-btn:hover { color:var(--danger); background:rgba(239,68,68,0.1); }

/* ===== Refresh indicator ===== */
.refresh-indicator { font-size:11px; color:var(--text-muted); display:flex; align-items:center; gap:4px; }
.refresh-indicator .refresh-dot { width:6px; height:6px; border-radius:50%; background:var(--success); animation:pulse-dot 2s infinite; }
@keyframes pulse-dot { 0%,100%{opacity:1} 50%{opacity:0.3} }

/* ===== Stat number animation ===== */
.stat-value { transition:all .3s ease; }

/* ===== Canvas chart wrappers ===== */
.chart-canvas-wrap { width:100%; height:260px; position:relative; }
.chart-canvas-wrap canvas { width:100%!important; height:100%!important; }

/* ===== Batch import ===== */
.batch-tabs { display:flex; gap:0; margin-bottom:16px; border-bottom:2px solid var(--border); }
.batch-tab {
  padding:8px 20px; cursor:pointer; font-size:13px; font-weight:500;
  color:var(--text-secondary); background:none; border:none;
  border-bottom:2px solid transparent; margin-bottom:-2px; transition:all .15s;
}
.batch-tab.active { color:var(--primary); border-bottom-color:var(--primary); }
.batch-result { margin-top:12px; padding:10px 14px; border-radius:8px; font-size:13px; display:none; }
.batch-result.success { background:#ecfdf5; color:#166534; border:1px solid #bbf7d0; }
.batch-result.partial { background:#fffbeb; color:#92400e; border:1px solid #fde68a; }
.batch-result.error { background:#fef2f2; color:#991b1b; border:1px solid #fecaca; }
.textarea-field { width:100%; min-height:120px; font-family:monospace; font-size:12px; resize:vertical; }
</style>
</head>
<body>

<!-- ===== Login Overlay ===== -->
<div class="login-overlay" id="login-overlay">
  <div class="login-card">
    <div class="login-icon">&#x1f6e1;</div>
    <h2>校园门禁管理后台</h2>
    <p class="login-sub">请输入管理员账号登录</p>
    <input type="text" id="login-username" placeholder="用户名" autocomplete="username">
    <input type="password" id="login-password" placeholder="密码" autocomplete="current-password">
    <button class="login-btn" onclick="doLogin()">登 录</button>
    <div class="login-err" id="login-err"></div>
  </div>
</div>

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
  <div class="sidebar-footer">
    <button class="logout-btn" onclick="doLogout()">
      <span style="font-size:15px">&#x1f6aa;</span> <span>退出登录</span>
    </button>
  </div>
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
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:16px">
      <div class="refresh-indicator"><span class="refresh-dot"></span> 上次刷新: <span id="refresh-time">--:--:--</span></div>
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
          <div class="chart-canvas-wrap"><canvas id="trend-chart-canvas"></canvas></div>
          <div class="chart-legend" style="margin-top:8px">
            <div class="chart-legend-item"><span class="chart-legend-dot" style="background:#3b82f6"></span>进入</div>
            <div class="chart-legend-item"><span class="chart-legend-dot" style="background:#10b981"></span>离开</div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">&#x1f465; 院系分布</div>
        <div class="card-body">
          <div class="chart-canvas-wrap"><canvas id="dept-chart-canvas"></canvas></div>
          <div class="chart-legend" id="dept-legend" style="margin-top:8px">
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
      <div style="display:flex;gap:8px">
        <button class="btn btn-outline" onclick="showBatchImportModal()">&#x1f4e5; 批量导入</button>
        <button class="btn btn-primary" onclick="showStudentModal()">+ 添加学生</button>
      </div>
    </div>
    <div class="card">
      <div class="card-body">
        <div class="search-bar">
          <div class="search-input-wrap">
            <span class="search-icon">&#x1f50d;</span>
            <input type="text" id="stu-search" placeholder="搜索学号、姓名、院系..." onkeyup="loadStudents()" class="search-input">
          </div>
          <select id="stu-status-filter" class="filter-select" onchange="loadStudents()">
            <option value="">全部状态</option>
            <option value="in">在校</option>
            <option value="out">离校</option>
          </select>
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
            <input type="text" id="rec-stu" placeholder="搜索姓名、学号、设备..." class="search-input" oninput="onRecSearchInput()">
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
        <p class="subtitle">管理门禁终端设备，共 <span id="dev-total-count">0</span> 台</p>
      </div>
      <button class="btn btn-primary" onclick="showDeviceModal()">+ 添加设备</button>
    </div>
    <div class="card">
      <div class="card-body no-padding" style="overflow-x:auto">
        <table>
          <thead><tr><th>设备序列号</th><th>名称</th><th>状态</th><th>最后心跳</th><th>操作</th></tr></thead>
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

  <!-- ===== Batch Import Modal ===== -->
  <div class="modal-overlay" id="batch-import-modal-overlay">
    <div class="modal" style="max-width:600px">
      <h3>批量导入学生</h3>
      <div class="batch-tabs">
        <button class="batch-tab active" onclick="switchBatchTab('csv')">CSV 文件上传</button>
        <button class="batch-tab" onclick="switchBatchTab('json')">JSON 粘贴</button>
      </div>
      <div id="batch-tab-csv">
        <div class="form-group"><label>CSV 文件 (列: 学号,姓名,院系)</label></div>
        <input type="file" id="batch-csv-file" accept=".csv" style="width:100%">
        <p style="font-size:11px;color:var(--text-muted);margin-top:6px">第一行为列名，必须包含: stu_no(或学号), name(或姓名), department(或院系，可选)</p>
      </div>
      <div id="batch-tab-json" style="display:none">
        <div class="form-group"><label>JSON 数组</label></div>
        <textarea class="textarea-field" id="batch-json-text" placeholder='[{"stu_no":"20231113513","name":"张三","department":"计算机学院"}, ...]'></textarea>
      </div>
      <div class="batch-result" id="batch-result"></div>
      <div class="modal-actions" style="margin-top:16px">
        <button class="btn btn-ghost" onclick="closeBatchImportModal()">取消</button>
        <button class="btn btn-primary" onclick="doBatchImport()">开始导入</button>
      </div>
    </div>
  </div>

  <!-- ===== Device Modal ===== -->
  <div class="modal-overlay" id="device-modal-overlay">
    <div class="modal">
      <h3 id="device-modal-title">添加设备</h3>
      <input type="hidden" id="dev-edit-id">
      <div class="form-group"><label>设备序列号 *</label><input type="text" id="dev-sn" placeholder="如 GATE-002"></div>
      <div class="form-group"><label>设备名称</label><input type="text" id="dev-name" placeholder="如 南门闸机"></div>
      <div class="modal-actions">
        <button class="btn btn-ghost" onclick="closeDeviceModal()">取消</button>
        <button class="btn btn-primary" onclick="saveDevice()">保存</button>
      </div>
    </div>
  </div>

</main>

<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<script>
const API = '';
let studentPage = 1, recordPage = 1;
let selectedFaceStudentId = null;
let allFaceStudents = [];
let faceStudentMap = {}; // student_id -> {has_face, feature_version}
let dashboardTimer = null;
let trendChart = null;
let deptChart = null;

// ====== Auth ======
function showLogin() {
  document.querySelector('.sidebar').style.display = 'none';
  document.querySelector('.main').style.display = 'none';
  $('login-overlay').style.display = 'flex';
  if (dashboardTimer) { clearInterval(dashboardTimer); dashboardTimer = null; }
}
function hideLogin() {
  $('login-overlay').style.display = 'none';
  document.querySelector('.sidebar').style.display = 'flex';
  document.querySelector('.main').style.display = 'block';
}
async function checkAuth() {
  try {
    const resp = await fetch(API + '/api/auth/status', {credentials:'same-origin'});
    if (resp.status === 401) { showLogin(); return false; }
    const data = await resp.json();
    if (data.authenticated) { hideLogin(); return true; }
    else { showLogin(); return false; }
  } catch(e) { showLogin(); return false; }
}
async function doLogin() {
  const username = $('login-username').value.trim();
  const password = $('login-password').value.trim();
  if (!username || !password) { $('login-err').textContent = '请输入用户名和密码'; return; }
  $('login-err').textContent = '';
  try {
    const resp = await fetch(API + '/api/auth/login', {
      method:'POST', credentials:'same-origin',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({username:username, password:password})
    });
    const data = await resp.json();
    if (data.success) { hideLogin(); initApp(); }
    else { $('login-err').textContent = data.message || '登录失败'; }
  } catch(e) { $('login-err').textContent = '网络错误: ' + e.message; }
}
async function doLogout() {
  try { await fetch(API + '/api/auth/logout', {method:'POST', credentials:'same-origin'}); } catch(e) {}
  if (dashboardTimer) { clearInterval(dashboardTimer); dashboardTimer = null; }
  showLogin();
}
document.addEventListener('keydown', function(e) {
  if (e.key === 'Enter' && $('login-overlay').style.display === 'flex') { doLogin(); }
});

// ====== API Wrapper ======
async function apiFetch(url, options) {
  options = options || {};
  options.credentials = 'same-origin';
  const resp = await fetch(API + url, options);
  if (resp.status === 401) { showLogin(); throw new Error('需要登录'); }
  return resp;
}

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
function animateValue(el, target, duration) {
  const start = parseInt(el.textContent) || 0;
  if (start === target) return;
  const startTime = performance.now();
  function step(ts) {
    const elapsed = ts - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(start + (target - start) * eased);
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

function updateRefreshTime() {
  const now = new Date();
  $('refresh-time').textContent = now.toLocaleTimeString('zh-CN', {hour:'2-digit',minute:'2-digit',second:'2-digit'});
}

async function loadDashboard() {
  try {
    const resp = await apiFetch('/api/dashboard/stats');
    const d = await resp.json();

    // Stat cards with animation
    animateValue($('stat-students'), d.total_students || 0, 600);
    $('stat-registered').textContent = '已注册人脸 ' + (d.registered_faces || 0) + ' 人';
    animateValue($('stat-in'), d.in_school || 0, 600);
    $('stat-out').textContent = '离校 ' + (d.out_school || 0) + ' 人';
    animateValue($('stat-today'), d.today_total || 0, 600);
    $('stat-today-fail').textContent = '失败 ' + (d.today_fail || 0) + ' 次';
    animateValue($('stat-devices'), d.online_devices || 0, 600);
    $('stat-total-devices').textContent = '共 ' + (d.total_devices || 0) + ' 台设备';

    updateRefreshTime();

    // Recent records
    let recHtml = '';
    if (d.recent_records) d.recent_records.forEach(r => {
      const simDisplay = r.similarity != null ? (r.similarity * 100).toFixed(1) + '%' : '-';
      const simColor = r.similarity != null ? (r.similarity >= 0.5 ? 'var(--success)' : 'var(--danger)') : 'var(--text-muted)';
      const dirLabel = r.direction==='in'?'进入':(r.direction==='out'?'离开':'手动');
      const dirClass = r.direction==='in'?'in':(r.direction==='out'?'out':'manual');
      recHtml += `<tr>
        <td style="font-family:monospace;font-size:12px">${formatDateTime(r.record_time)}</td>
        <td>${r.name||'-'}</td>
        <td style="font-family:monospace">${r.stu_no||'-'}</td>
        <td><span class="badge badge-${dirClass}">${dirLabel}</span></td>
        <td><span class="badge badge-${r.result||'success'}">${r.result==='success'?'&#x2713; 成功':'&#x2717; 失败'}</span></td>
        <td style="font-weight:500;color:${simColor}">${simDisplay}</td></tr>`;
    });
    $('recent-records').innerHTML = recHtml || '<tr><td colspan="6" style="color:var(--text-muted);text-align:center;padding:24px">暂无记录</td></tr>';

    // Trend chart (Chart.js)
    if (d.trend_7days && d.trend_7days.length > 0) {
      const labels = d.trend_7days.map(function(t) { return t.date.slice(5); });
      const inData = d.trend_7days.map(function(t) { return t.in_count || 0; });
      const outData = d.trend_7days.map(function(t) { return t.out_count || 0; });
      const ctx = $('trend-chart-canvas').getContext('2d');
      if (trendChart) trendChart.destroy();
      trendChart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [
            { label: '进入', data: inData, borderColor: '#3b82f6', backgroundColor: 'rgba(59,130,246,0.08)', fill: true, tension: 0.3, pointRadius: 4, pointBackgroundColor: '#3b82f6' },
            { label: '离开', data: outData, borderColor: '#10b981', backgroundColor: 'rgba(16,185,129,0.08)', fill: true, tension: 0.3, pointRadius: 4, pointBackgroundColor: '#10b981' }
          ]
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            y: { beginAtZero: true, ticks: { stepSize: 1, font: { size: 11 } }, grid: { color: '#e2e8f0' } },
            x: { ticks: { font: { size: 11 } }, grid: { display: false } }
          }
        }
      });
    }

    // Department chart (Chart.js horizontal bar)
    if (d.department_distribution && d.department_distribution.length > 0) {
      var deptLabels = d.department_distribution.map(function(dd) { return dd.name; });
      var deptData = d.department_distribution.map(function(dd) { return dd.count; });
      var deptColors = d.department_distribution.map(function(_, i) {
        var colors = ['#10b981','#3b82f6','#f59e0b','#8b5cf6','#ef4444','#06b6d4','#ec4899','#84cc16'];
        return colors[i % colors.length];
      });
      var ctx2 = $('dept-chart-canvas').getContext('2d');
      if (deptChart) deptChart.destroy();
      deptChart = new Chart(ctx2, {
        type: 'bar',
        data: {
          labels: deptLabels,
          datasets: [{ label: '人数', data: deptData, backgroundColor: deptColors, borderRadius: 6 }]
        },
        options: {
          indexAxis: 'y',
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { beginAtZero: true, ticks: { stepSize: 1, font: { size: 11 } }, grid: { color: '#e2e8f0' } },
            y: { ticks: { font: { size: 11 } }, grid: { display: false } }
          }
        }
      });
      // Update legend
      var legendHtml = '';
      d.department_distribution.forEach(function(dd, i) {
        legendHtml += '<div class="chart-legend-item"><span class="chart-legend-dot" style="background:' + deptColors[i] + '"></span>' + dd.name + ' (' + dd.count + '人)</div>';
      });
      $('dept-legend').innerHTML = legendHtml;
    } else {
      $('dept-legend').innerHTML = '<div class="chart-legend-item"><span class="chart-legend-dot" style="background:var(--text-muted)"></span>暂无数据</div>';
    }
  } catch(e) { if (e.message !== '需要登录') console.error(e); }
}

// ====== Students ======
async function loadStudents() {
  const kw = $('stu-search').value;
  const statusFilter = $('stu-status-filter').value;
  try {
    var url = '/api/student?keyword=' + encodeURIComponent(kw) + '&page=' + studentPage;
    if (statusFilter) url += '&status=' + statusFilter;
    const resp = await apiFetch(url);
    const data = await resp.json();
    $('stu-total-count').textContent = data.total || 0;

    // Also get face data for registration status
    let faceMap = {};
    try {
      const fResp = await apiFetch('/api/sync/features?since_version=0');
      const fData = await fResp.json();
      if (fData.features) fData.features.forEach(function(f) { faceMap[f.student_id] = true; });
    } catch(e) {}

    let html = '';
    if (data.data) data.data.forEach(function(s) {
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
          <button class="btn-icon" onclick="editStudent(${s.id})" title="编辑"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg></button>
          <button class="btn-icon danger" onclick="deleteStudent(${s.id})" title="删除"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6h14"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg></button>
        </td></tr>`;
    });
    $('student-table').innerHTML = html || '<tr><td colspan="6" style="color:var(--text-muted);text-align:center;padding:24px">暂无学生</td></tr>';
    renderPagination('student-pages', data.total, studentPage, function(p) { studentPage = p; loadStudents(); });
  } catch(e) { if (e.message !== '需要登录') toast('加载失败: '+e.message, 'error'); }
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
      resp = await apiFetch('/api/student/' + id, {method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    } else {
      resp = await apiFetch('/api/student', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    }
    if (resp.ok) { toast(id?'更新成功':'添加成功', 'success'); closeStudentModal(); loadStudents(); loadFaces(); }
    else { const e = await resp.json(); toast(e.error||'操作失败', 'error'); }
  } catch(e) { if (e.message !== '需要登录') toast('请求失败: '+e.message, 'error'); }
}
async function editStudent(id) {
  try {
    const resp = await apiFetch('/api/student/' + id);
    const s = await resp.json();
    showStudentModal(s);
  } catch(e) { if (e.message !== '需要登录') toast('加载失败', 'error'); }
}
async function deleteStudent(id) {
  if (!confirm('确定删除该学生？关联的人脸特征也将被删除。')) return;
  try {
    const resp = await apiFetch('/api/student/' + id, {method:'DELETE'});
    if (resp.ok) { toast('删除成功', 'success'); loadStudents(); loadFaces(); }
    else toast('删除失败', 'error');
  } catch(e) { if (e.message !== '需要登录') toast('请求失败', 'error'); }
}

// ====== Batch Import ======
var batchTabName = 'csv';
function showBatchImportModal() { $('batch-import-modal-overlay').style.display = 'flex'; }
function closeBatchImportModal() { $('batch-import-modal-overlay').style.display = 'none'; $('batch-result').style.display = 'none'; }
function switchBatchTab(name) {
  batchTabName = name;
  document.querySelectorAll('.batch-tab').forEach(function(t) { t.classList.remove('active'); });
  document.querySelector('.batch-tab[onclick*="' + name + '"]').classList.add('active');
  $('batch-tab-csv').style.display = name === 'csv' ? 'block' : 'none';
  $('batch-tab-json').style.display = name === 'json' ? 'block' : 'none';
  $('batch-result').style.display = 'none';
}
async function doBatchImport() {
  $('batch-result').style.display = 'none';
  try {
    var resp;
    if (batchTabName === 'csv') {
      var file = $('batch-csv-file').files[0];
      if (!file) { toast('请选择CSV文件', 'error'); return; }
      var formData = new FormData();
      formData.append('file', file);
      resp = await apiFetch('/api/student/batch', {method:'POST', body:formData});
    } else {
      var text = $('batch-json-text').value.trim();
      if (!text) { toast('请粘贴JSON数据', 'error'); return; }
      resp = await apiFetch('/api/student/batch', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({students: JSON.parse(text)})
      });
    }
    var data = await resp.json();
    var resultClass = 'success';
    var errorCount = data.errors ? data.errors.length : 0;
    var successCount = data.success || 0;
    var skippedCount = data.skipped || 0;
    if (errorCount > 0 && successCount > 0) resultClass = 'partial';
    else if (errorCount > 0 && successCount === 0) resultClass = 'error';
    $('batch-result').className = 'batch-result ' + resultClass;
    $('batch-result').innerHTML = '导入完成: 成功 ' + successCount + ' 条, 跳过 ' + skippedCount + ' 条, 失败 ' + errorCount + ' 条';
    $('batch-result').style.display = 'block';
    if (successCount > 0) { loadStudents(); loadFaces(); }
  } catch(e) {
    if (e instanceof SyntaxError) { toast('JSON格式错误，请检查', 'error'); return; }
    if (e.message !== '需要登录') toast('导入失败: ' + e.message, 'error');
  }
}

// ====== Faces ======
async function loadFaces() {
  try {
    const stuResp = await apiFetch('/api/student?per_page=999');
    const stuData = await stuResp.json();
    allFaceStudents = stuData.data || [];

    const syncResp = await apiFetch('/api/sync/features?since_version=0');
    const syncData = await syncResp.json();
    faceStudentMap = {};
    let globalVersion = 0;
    if (syncData.features) syncData.features.forEach(function(f) {
      faceStudentMap[f.student_id] = { has_face: true, feature_version: f.feature_version };
      if (f.feature_version > globalVersion) globalVersion = f.feature_version;
    });

    $('face-global-version').textContent = 'v' + globalVersion;
    $('face-registered-count').textContent = Object.keys(faceStudentMap).length;

    renderFaceStudentList(allFaceStudents);
  } catch(e) { if (e.message !== '需要登录') console.error(e); }
}

function renderFaceStudentList(students) {
  const list = $('face-student-list');
  if (students.length === 0) {
    list.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:20px;font-size:13px">暂无学生</div>';
    return;
  }
  let html = '';
  students.forEach(function(s) {
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
  const filtered = allFaceStudents.filter(function(s) {
    return s.name.toLowerCase().includes(kw) || s.stu_no.toLowerCase().includes(kw);
  });
  renderFaceStudentList(filtered);
}

function selectFaceStudent(studentId) {
  selectedFaceStudentId = studentId;
  document.querySelectorAll('.face-student-item').forEach(function(el) { el.classList.remove('selected'); });
  const item = document.getElementById('face-item-' + studentId);
  if (item) item.classList.add('selected');

  const student = allFaceStudents.find(function(s) { return s.id === studentId; });
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
    const resp = await apiFetch('/api/face/register', {method:'POST', body:formData});
    const data = await resp.json();
    if (resp.ok) {
      toast('注册成功！版本号: ' + data.feature_version, 'success');
      loadFaces();
      selectFaceStudent(selectedFaceStudentId);
    } else {
      toast(data.error||'注册失败', 'error');
    }
  } catch(e) { if (e.message !== '需要登录') toast('请求失败: '+e.message, 'error'); }
}

async function deleteFaceForSelected() {
  if (!selectedFaceStudentId) return;
  if (!confirm('确定删除该学生的人脸特征？')) return;
  try {
    const resp = await apiFetch('/api/face/student/' + selectedFaceStudentId, {method:'DELETE'});
    if (resp.ok) { toast('特征已删除', 'success'); loadFaces(); selectFaceStudent(selectedFaceStudentId); }
    else toast('删除失败', 'error');
  } catch(e) { if (e.message !== '需要登录') toast('请求失败', 'error'); }
}

// ====== Records ======
var recSearchTimer = null;
function onRecSearchInput() {
  clearTimeout(recSearchTimer);
  recSearchTimer = setTimeout(function() { recordPage = 1; loadRecords(); }, 300);
}
async function loadRecords() {
  const params = new URLSearchParams();
  const stu = $('rec-stu').value.trim(); if (stu) params.set('stu_no', stu);
  const dir = $('rec-dir').value; if (dir) params.set('direction', dir);
  const res = $('rec-result').value; if (res) params.set('result', res);
  params.set('page', recordPage); params.set('per_page', 20);
  try {
    const resp = await apiFetch('/api/record?' + params.toString());
    const data = await resp.json();
    $('rec-total').textContent = data.total || 0;
    $('rec-filtered').textContent = data.total || 0;
    let html = '';
    if (data.data) data.data.forEach(function(r) {
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
        <td><button class="btn-icon danger" onclick="deleteRecord(${r.id})" title="删除"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6h14"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg></button></td></tr>`;
    });
    $('record-table').innerHTML = html || '<tr><td colspan="8" style="color:var(--text-muted);text-align:center;padding:24px">暂无记录</td></tr>';
    renderPagination('record-pages', data.total, recordPage, function(p) { recordPage = p; loadRecords(); });
  } catch(e) { if (e.message !== '需要登录') toast('查询失败', 'error'); }
}

async function deleteRecord(id) {
  if (!confirm('确定删除该记录？')) return;
  try {
    const resp = await apiFetch('/api/record/' + id, {method:'DELETE'});
    if (resp.ok) { toast('删除成功', 'success'); loadRecords(); }
    else toast('删除失败', 'error');
  } catch(e) { if (e.message !== '需要登录') toast('请求失败', 'error'); }
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
  apiFetch('/api/student?per_page=999').then(function(r) { return r.json(); }).then(function(data) {
    let opts = '<option value="">-- 选择学生 --</option>';
    if (data.data) data.data.forEach(function(s) {
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
    const resp = await apiFetch('/api/record', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({student_id:parseInt(studentId), device_sn:'MANUAL', direction:direction, result:'success', similarity:1.0})
    });
    if (resp.ok) { toast('记录已添加', 'success'); closeManualRecordModal(); loadRecords(); }
    else { const e = await resp.json(); toast(e.error||'添加失败', 'error'); }
  } catch(e) { if (e.message !== '需要登录') toast('请求失败', 'error'); }
}

// ====== Devices ======
async function loadDevices() {
  try {
    // Fetch both device registry and heartbeat status
    const [devResp, hbResp] = await Promise.all([
      apiFetch('/api/device').then(function(r) { return r.json(); }),
      apiFetch('/api/heartbeat/status').then(function(r) { return r.json(); })
    ]);
    // Build heartbeat map by device_sn
    var hbMap = {};
    if (hbResp.devices) hbResp.devices.forEach(function(d) { hbMap[d.device_sn] = d; });
    // Device list from registry (supports array or paginated response)
    var devices = devResp.data || devResp.devices || devResp || [];
    if (!Array.isArray(devices)) devices = [];
    let html = '';
    devices.forEach(function(d) {
      var hb = hbMap[d.device_sn] || {};
      var isOnline = hb.is_online || false;
      var lastHb = hb.last_heartbeat || '-';
      html += `<tr>
        <td style="font-family:monospace">${d.device_sn}</td>
        <td>${d.device_name||d.device_sn}</td>
        <td><span style="display:inline-flex;align-items:center;gap:6px">
          <span class="status-dot ${isOnline?'in':'out'}"></span>
          <span style="color:${isOnline?'var(--success)':'var(--text-muted)'}">${isOnline?'在线':'离线'}</span>
        </span></td>
        <td style="font-family:monospace;font-size:12px">${lastHb}</td>
        <td>
          <button class="btn-icon" onclick="editDevice(${d.id})" title="编辑"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg></button>
          <button class="btn-icon danger" onclick="deleteDevice(${d.id})" title="删除"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6h14"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg></button>
        </td></tr>`;
    });
    $('device-table').innerHTML = html || '<tr><td colspan="5" style="color:var(--text-muted);text-align:center;padding:24px">暂无设备</td></tr>';
    $('dev-total-count').textContent = devices.length;
  } catch(e) { if (e.message !== '需要登录') console.error(e); }
}

function showDeviceModal(editData) {
  if (editData) {
    $('device-modal-title').textContent = '编辑设备';
    $('dev-edit-id').value = editData.id;
    $('dev-sn').value = editData.device_sn;
    $('dev-sn').readOnly = true;
    $('dev-name').value = editData.device_name || '';
  } else {
    $('device-modal-title').textContent = '添加设备';
    $('dev-edit-id').value = '';
    $('dev-sn').value = '';
    $('dev-sn').readOnly = false;
    $('dev-name').value = '';
  }
  $('device-modal-overlay').style.display = 'flex';
}
function closeDeviceModal() { $('device-modal-overlay').style.display = 'none'; }
async function saveDevice() {
  const id = $('dev-edit-id').value;
  const deviceSn = $('dev-sn').value.trim();
  const deviceName = $('dev-name').value.trim();
  if (!deviceSn) { toast('设备序列号为必填项', 'error'); return; }
  try {
    let resp;
    if (id) {
      resp = await apiFetch('/api/device/' + id, {method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({device_name:deviceName})});
    } else {
      resp = await apiFetch('/api/device', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({device_sn:deviceSn, device_name:deviceName})});
    }
    if (resp.ok) { toast(id?'更新成功':'添加成功', 'success'); closeDeviceModal(); loadDevices(); }
    else { const e = await resp.json(); toast(e.error||'操作失败', 'error'); }
  } catch(e) { if (e.message !== '需要登录') toast('请求失败: '+e.message, 'error'); }
}
async function editDevice(id) {
  try {
    const resp = await apiFetch('/api/device/' + id);
    if (resp.ok) {
      const d = await resp.json();
      showDeviceModal(d);
    } else {
      toast('设备不存在', 'error');
    }
  } catch(e) { if (e.message !== '需要登录') toast('加载失败', 'error'); }
}
async function deleteDevice(id) {
  if (!confirm('确定删除该设备？')) return;
  try {
    const resp = await apiFetch('/api/device/' + id, {method:'DELETE'});
    if (resp.ok) { toast('删除成功', 'success'); loadDevices(); }
    else toast('删除失败', 'error');
  } catch(e) { if (e.message !== '需要登录') toast('请求失败', 'error'); }
}

// ====== Pagination ======
function renderPagination(containerId, total, page, cb) {
  const container = $(containerId);
  const totalPages = Math.ceil(total / 20) || 1;
  if (totalPages <= 1) { container.innerHTML = ''; return; }
  let html = '';
  // First + Prev
  html += `<button${page===1?' disabled':''} onclick="(${cb.toString()})(1)">&#xAB;</button>`;
  html += `<button${page===1?' disabled':''} onclick="(${cb.toString()})(${page-1})">&#x2039;</button>`;
  // Page numbers with ellipsis
  const range = 2;
  for (let i = 1; i <= totalPages; i++) {
    if (i === 1 || i === totalPages || (i >= page - range && i <= page + range)) {
      html += `<button class="${i===page?'active':''}" onclick="(${cb.toString()})(${i})">${i}</button>`;
    } else if (i === page - range - 1 || i === page + range + 1) {
      html += '<button disabled>...</button>';
    }
  }
  // Next + Last
  html += `<button${page===totalPages?' disabled':''} onclick="(${cb.toString()})(${page+1})">&#x203A;</button>`;
  html += `<button${page===totalPages?' disabled':''} onclick="(${cb.toString()})(${totalPages})">&#xBB;</button>`;
  container.innerHTML = html;
}

// ====== Init ======
async function initApp() {
  loadDashboard();
  if (!dashboardTimer) {
    dashboardTimer = setInterval(function() { loadDashboard(); }, 30000);
  }
}
// Start: check auth first
checkAuth().then(function(authed) {
  if (authed) { initApp(); }
});
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
