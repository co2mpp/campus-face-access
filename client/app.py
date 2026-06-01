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
from flask import Flask, jsonify, request, render_template_string, Response

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
CLIENT_HTML = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>校园门禁终端 — {{device_sn}}</title>
<style>
:root {
  --bg:#0f172a; --card:#1e293b; --border:#334155;
  --text:#f1f5f9; --text-secondary:#94a3b8; --text-muted:#64748b;
  --accent:#3b82f6; --accent-hover:#2563eb;
  --green:#10b981; --red:#ef4444; --orange:#f59e0b;
  --purple:#8b5cf6;
  --radius:8px; --radius-sm:6px;
}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:"Inter","Microsoft YaHei","Segoe UI",sans-serif;background:var(--bg);color:var(--text);min-height:100vh;overflow:hidden}

/* ===== Top Status Bar ===== */
.topbar{
  background:var(--card); border-bottom:1px solid var(--border);
  padding:0 20px; height:56px; display:flex; align-items:center; gap:16px;
  z-index:100; position:relative;
}
.topbar-brand{display:flex;align-items:center;gap:10px}
.topbar-logo{
  width:34px;height:34px;background:var(--accent);border-radius:10px;
  display:flex;align-items:center;justify-content:center;color:#fff;font-size:16px;font-weight:700;
}
.topbar-title{font-size:16px;font-weight:600;white-space:nowrap}
.topbar-select{
  background:var(--bg);border:1px solid var(--border);border-radius:var(--radius-sm);
  padding:6px 12px;color:var(--text);font-size:13px;cursor:pointer;outline:none;
}
.topbar-select:focus{border-color:var(--accent)}
.topbar-center{
  position:absolute;left:50%;transform:translateX(-50%);display:flex;
  align-items:center;gap:12px;
}
.topbar-clock{font-family:"SF Mono","Cascadia Code",monospace;font-size:20px;font-weight:600;color:#fff}
.topbar-date{font-family:"SF Mono","Cascadia Code",monospace;font-size:13px;color:var(--text-secondary)}

.topbar-actions{display:flex;align-items:center;gap:8px;margin-left:auto}
.dir-btn{
  padding:8px 18px;border:1px solid var(--border);background:transparent;
  color:var(--text-secondary);border-radius:var(--radius-sm);cursor:pointer;
  font-size:13px;font-weight:500;transition:all .15s;
}
.dir-btn:hover{color:#fff;border-color:var(--text-secondary)}
.dir-btn.active{background:var(--accent);color:#fff;border-color:var(--accent)}
.dir-btn.manual-btn{color:var(--green);border-color:var(--green);background:transparent}
.dir-btn.manual-btn:hover{background:var(--green);color:#fff}
.online-badge{
  display:flex;align-items:center;gap:6px;padding:6px 14px;
  border-radius:20px;font-size:12px;font-weight:600;white-space:nowrap;
}
.online-badge.online{color:var(--green);background:rgba(16,185,129,0.1)}
.online-badge.offline{color:var(--red);background:rgba(239,68,68,0.1)}

/* ===== Main Layout ===== */
.main-layout{display:grid;grid-template-columns:1fr 360px;height:calc(100vh - 56px);gap:0}
.camera-section{
  display:flex;flex-direction:column;padding:16px;
  border-right:1px solid var(--border);
}
.info-section{display:flex;flex-direction:column;padding:16px;gap:16px;overflow-y:auto}

/* ===== Camera Area ===== */
.camera-header{
  display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;
}
.camera-dir-tag{
  display:inline-flex;align-items:center;gap:6px;padding:6px 14px;
  border-radius:20px;font-size:13px;font-weight:600;
}
.camera-dir-tag.in{background:rgba(59,130,246,.2);color:var(--accent)}
.camera-dir-tag.out{background:rgba(249,115,22,.2);color:var(--orange)}
.camera-id{font-size:12px;color:var(--text-muted)}

.camera-viewport{
  flex:1;background:#000;border-radius:var(--radius);position:relative;
  overflow:hidden;display:flex;align-items:center;justify-content:center;
  border:1px solid var(--border);min-height:0;
}
.camera-viewport img{width:100%;height:100%;object-fit:cover;display:block}
.camera-placeholder{
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  color:var(--text-muted);text-align:center;
}
.camera-placeholder .cam-icon{font-size:56px;margin-bottom:12px;opacity:.4}
.camera-placeholder p{font-size:15px;color:var(--text-secondary);margin-bottom:4px}
.camera-placeholder .hint{font-size:12px;color:var(--text-muted)}

/* Scan overlay */
.scan-overlay{
  position:absolute;inset:0;display:flex;align-items:center;
  justify-content:center;pointer-events:none;z-index:2;
}
.scan-frame{
  width:200px;height:200px;border:2px solid rgba(59,130,246,.6);border-radius:20px;position:relative;
}
.scan-frame::before,.scan-frame::after{content:'';position:absolute;width:24px;height:24px;border-radius:6px}
.scan-frame::before{top:-2px;left:-2px;border-top:3px solid #60a5fa;border-left:3px solid #60a5fa}
.scan-frame::after{top:-2px;right:-2px;border-top:3px solid #60a5fa;border-right:3px solid #60a5fa}
.scan-frame .corner-bl{position:absolute;bottom:-2px;left:-2px;width:24px;height:24px;border-bottom:3px solid #60a5fa;border-left:3px solid #60a5fa;border-radius:6px}
.scan-frame .corner-br{position:absolute;bottom:-2px;right:-2px;width:24px;height:24px;border-bottom:3px solid #60a5fa;border-right:3px solid #60a5fa;border-radius:6px}
.scan-line{
  position:absolute;left:8%;right:8%;height:2px;
  background:linear-gradient(90deg,transparent,rgba(96,165,250,.8),transparent);
  box-shadow:0 0 16px 4px rgba(96,165,250,.5);
  animation:scanLine 1.5s ease-in-out infinite;
}
@keyframes scanLine{0%{top:8%}50%{top:88%}100%{top:8%}}

/* Result flash */
.result-flash{
  position:absolute;inset:0;pointer-events:none;z-index:4;
  transition:opacity .4s;opacity:0;
}
.result-flash.show{opacity:1}
.result-flash.success{background:rgba(16,185,129,.12);border:3px solid var(--green)}
.result-flash.fail{background:rgba(239,68,68,.12);border:3px solid var(--red)}

/* Camera action buttons */
.camera-actions{display:flex;gap:12px;margin-top:12px}
.camera-actions .btn-action{
  flex:1;padding:14px;border:none;border-radius:var(--radius-sm);cursor:pointer;
  font-size:15px;font-weight:600;transition:all .15s;display:flex;
  align-items:center;justify-content:center;gap:8px;
}
.btn-capture{background:var(--accent);color:#fff}
.btn-capture:hover{background:var(--accent-hover)}
.btn-simulate{background:var(--purple);color:#fff}
.btn-simulate:hover{background:#7c3aed}

/* ===== Recognition Area ===== */
.recognition-panel{
  background:var(--card);border:1px solid var(--border);border-radius:var(--radius);
  padding:24px;text-align:center;min-height:220px;display:flex;
  flex-direction:column;align-items:center;justify-content:center;
}
.recognition-waiting .waiting-icon{font-size:52px;color:var(--text-muted);margin-bottom:12px;opacity:.5}
.recognition-waiting p{font-size:15px;color:var(--text-secondary)}
.recognition-waiting .sub{font-size:12px;color:var(--text-muted);margin-top:4px}
/* Recognition result */
.recognition-result{display:none;text-align:center;width:100%}
.recognition-result .result-header-icon{font-size:44px;margin-bottom:6px}
.recognition-result .result-title{font-size:22px;font-weight:700;margin-bottom:12px}
.recognition-result .result-info-card{
  background:rgba(255,255,255,.04);border-radius:var(--radius-sm);
  padding:14px;margin-bottom:12px;text-align:left;
}
.recognition-result .result-name{font-size:20px;font-weight:700}
.recognition-result .result-stuno{font-family:monospace;font-size:12px;color:var(--text-secondary);margin-top:2px}
.recognition-result .sim-row{display:flex;align-items:center;gap:10px;margin-top:10px;font-size:13px}
.recognition-result .sim-value{font-weight:700;font-size:18px}
.recognition-result .sim-bar-track{flex:1;height:6px;background:rgba(255,255,255,.1);border-radius:3px;overflow:hidden}
.recognition-result .sim-bar-fill{height:100%;border-radius:3px;transition:width .3s}
.recognition-result .result-meta{display:flex;align-items:center;gap:10px;margin-top:8px;font-size:12px;color:var(--text-secondary)}
.recognition-result .dir-tag{
  padding:3px 12px;border-radius:20px;font-size:11px;font-weight:600;
}
.recognition-result .dir-tag.in{background:rgba(59,130,246,.2);color:var(--accent)}
.recognition-result .dir-tag.out{background:rgba(249,115,22,.2);color:var(--orange)}
.recognition-result .door-status-msg{
  padding:10px;border-radius:var(--radius-sm);font-size:14px;font-weight:700;margin-top:10px;
}
.recognition-result .door-open{background:var(--green);color:#fff}
.recognition-result .door-closed{background:rgba(255,255,255,.06);color:var(--text-muted)}

/* ===== Local Records ===== */
.records-panel{
  background:var(--card);border:1px solid var(--border);border-radius:var(--radius);
  display:flex;flex-direction:column;flex:1;min-height:0;overflow:hidden;
}
.records-header{
  padding:14px 16px;border-bottom:1px solid var(--border);
  display:flex;align-items:center;justify-content:space-between;
  font-size:14px;font-weight:600;
}
.records-header .device-id{font-size:11px;color:var(--text-muted);font-family:monospace}
.records-list{flex:1;overflow-y:auto}
.record-item{
  display:flex;align-items:center;gap:10px;padding:10px 16px;
  border-bottom:1px solid rgba(255,255,255,.04);font-size:13px;
}
.record-item:hover{background:rgba(255,255,255,.03)}
.record-item .rec-dot{width:7px;height:7px;border-radius:50%;flex-shrink:0}
.record-item .rec-dot.success{background:var(--green)}
.record-item .rec-dot.fail{background:var(--red)}
.record-item .rec-name{font-weight:500;min-width:55px}
.record-item .rec-stuno{font-family:monospace;font-size:12px;color:var(--text-secondary);min-width:90px}
.record-item .rec-dir{font-size:12px;min-width:28px}
.record-item .rec-dir.in{color:var(--accent)}
.record-item .rec-dir.out{color:var(--orange)}
.record-item .rec-time{font-family:monospace;font-size:11px;color:var(--text-muted);margin-left:auto}
.record-item .rec-sim{font-family:monospace;font-size:11px;color:var(--green)}

/* ===== Config Overlay ===== */
.config-overlay{
  position:fixed;inset:0;background:rgba(0,0,0,.85);z-index:300;
  display:flex;align-items:center;justify-content:center;
}
.config-card{
  background:var(--card);border:1px solid var(--border);border-radius:12px;
  padding:32px;width:90%;max-width:460px;text-align:center;
}
.config-card h3{font-size:18px;margin-bottom:20px}
.config-card select{
  background:var(--bg);border:1px solid var(--border);border-radius:8px;
  padding:10px 14px;color:var(--text);font-size:14px;width:200px;margin:6px;
}
.config-card .hint{font-size:11px;color:var(--text-muted);margin:12px 0}

.btn{
  padding:10px 22px;border:none;border-radius:var(--radius-sm);cursor:pointer;
  font-size:13px;font-weight:600;transition:all .15s;margin:3px;
}
.btn-primary{background:var(--accent);color:#fff}
.btn-primary:hover{background:var(--accent-hover)}
.btn-ghost{background:transparent;color:var(--text-secondary);border:1px solid var(--border)}
.btn-ghost:hover{border-color:var(--text-muted);color:var(--text)}
.btn-config{
  background:transparent;color:var(--text-muted);border:1px solid var(--border);
  padding:6px 12px;border-radius:var(--radius-sm);cursor:pointer;font-size:12px;
  transition:all .15s;
}
.btn-config:hover{color:var(--text);border-color:var(--text-secondary)}

/* Pending record badge */
.pending-badge{
  display:inline-flex;align-items:center;gap:4px;
  background:rgba(245,158,11,.15);color:var(--orange);
  font-size:11px;font-weight:600;padding:2px 8px;border-radius:12px;
  border:1px solid rgba(245,158,11,.3);white-space:nowrap;
}
.pending-badge.hidden{display:none}

/* Uptime display */
.uptime-display{
  font-family:"SF Mono","Cascadia Code",monospace;
  font-size:12px;color:var(--text-secondary);
  display:flex;align-items:center;gap:6px;
}
.uptime-dot{width:6px;height:6px;border-radius:50%;background:var(--green);flex-shrink:0}

/* Sync info */
.sync-info{
  font-family:"SF Mono","Cascadia Code",monospace;
  font-size:11px;color:var(--text-muted);
  display:flex;align-items:center;gap:6px;
}
.sync-info .sync-ver{color:var(--accent);font-weight:600}

/* Pulse animation for similarity bar */
@keyframes pulseBar{
  0%{filter:brightness(1);box-shadow:0 0 4px rgba(59,130,246,.3)}
  50%{filter:brightness(1.4);box-shadow:0 0 12px rgba(59,130,246,.6)}
  100%{filter:brightness(1);box-shadow:0 0 4px rgba(59,130,246,.3)}
}
.sim-bar-fill.pulse{animation:pulseBar .6s ease-in-out 2}

/* Recognition panel height transition */
.recognition-panel{
  transition:min-height .4s ease;
}
.recognition-waiting,.recognition-result{
  transition:opacity .35s ease;
}

/* Manual open accent */
.manual-accent{color:var(--green)}
.manual-icon-circle{
  width:60px;height:60px;border-radius:50%;
  background:rgba(16,185,129,.12);border:2px solid var(--green);
  display:inline-flex;align-items:center;justify-content:center;
  font-size:28px;margin-bottom:8px;
}

/* Offline banner enhanced */
.offline-banner{
  background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3);
  border-radius:8px;padding:10px 16px;margin:0 16px;
  font-size:12px;color:var(--red);display:flex;align-items:center;gap:10px;
  flex-wrap:wrap;
}
.offline-banner .offline-timer{font-weight:600;white-space:nowrap}
.offline-banner .offline-queued{
  background:rgba(239,68,68,.15);padding:2px 8px;border-radius:10px;
  font-size:11px;white-space:nowrap;
}
.offline-banner .offline-sep{color:rgba(239,68,68,.4)}

/* Config card enhanced */
.config-card{
  background:var(--card);border:1px solid var(--border);border-radius:16px;
  padding:36px;width:90%;max-width:500px;text-align:center;
  box-shadow:0 20px 60px rgba(0,0,0,.5);
}
.config-card h3{font-size:20px;margin-bottom:8px}
.config-card .cfg-subtitle{font-size:13px;color:var(--text-secondary);margin-bottom:24px}
.config-card .cfg-row{
  display:flex;align-items:center;gap:12px;margin-bottom:16px;
  padding:12px 16px;background:rgba(255,255,255,.03);border-radius:var(--radius-sm);
  text-align:left;
}
.config-card .cfg-row .cfg-label{
  font-size:13px;font-weight:600;color:var(--text);min-width:70px;
}
.config-card .cfg-row .cfg-arrow{color:var(--text-muted);font-size:18px}
.config-card select{
  background:var(--bg);border:1px solid var(--border);border-radius:8px;
  padding:10px 14px;color:var(--text);font-size:14px;width:160px;
}
.config-card select:focus{border-color:var(--accent);outline:none}
.config-card .hint{font-size:12px;color:var(--text-muted);margin:16px 0;line-height:1.5}
.config-card .cfg-actions{display:flex;gap:10px;justify-content:center;margin-top:8px}
.config-card .cfg-current{
  font-size:11px;color:var(--text-muted);margin-top:12px;
  padding:8px 14px;background:rgba(255,255,255,.02);border-radius:var(--radius-sm);
  display:inline-block;
}
.config-card .cfg-current span{color:var(--accent);font-weight:600}
.config-card .cfg-loading{
  display:inline-flex;align-items:center;gap:6px;color:var(--accent);font-size:13px;margin-top:8px;
}
.config-card .cfg-success{
  color:var(--green);font-size:13px;font-weight:600;margin-top:8px;
}
.config-card .cfg-error{
  color:var(--red);font-size:12px;margin-top:8px;
}

@media(max-width:1000px){
  .main-layout{grid-template-columns:1fr}
  .camera-section{border-right:none;border-bottom:1px solid var(--border)}
  .topbar-center{display:none}
}
</style>
</head>
<body>

<!-- ===== Top Status Bar ===== -->
<div class="topbar">
  <div class="topbar-brand">
    <div class="topbar-logo">&#x1f6e1;</div>
    <span class="topbar-title">门禁终端</span>
    <select class="topbar-select" id="terminal-select">
      <option value="{{device_sn}}">{{device_sn}}</option>
    </select>
  </div>

  <div class="topbar-center">
    <span class="topbar-clock" id="header-clock">--:--:--</span>
    <span class="topbar-date" id="header-date"></span>
  </div>

  <div class="topbar-actions">
    <span class="uptime-display" id="uptime-display"><span class="uptime-dot"></span>运行: --</span>
    <button class="dir-btn active" id="btn-dir-in" onclick="switchDirection('in')">&#x2b06; 进门</button>
    <button class="dir-btn" id="btn-dir-out" onclick="switchDirection('out')" {% if not out_enabled %}style="display:none"{% endif %}>&#x2b07; 出门</button>
    <button class="dir-btn manual-btn" onclick="manualOpen()">&#x1f513; 手动开门</button>
    <span class="online-badge offline" id="header-status">&#x26a0; 离线</span>
    {% if not binding %}
    <button class="btn-config" onclick="showConfig()">&#x2699;</button>
    {% endif %}
  </div>
</div>

<!-- Offline banner -->
<div id="offline-banner" class="offline-banner" style="display:none">
  <span>&#x26a0; 网络已断开</span>
  <span class="offline-timer" id="offline-timer"></span>
  <span class="offline-sep">|</span>
  <span class="offline-queued" id="offline-queued">排队: 0 条</span>
</div>

<!-- ===== Main Layout ===== -->
<div class="main-layout">
  <!-- Left: Camera Section -->
  <div class="camera-section">
    <div class="camera-header">
      <span class="camera-dir-tag in" id="camera-dir-label">&#x2b06; 进门通道</span>
      <span class="camera-id" id="camera-idx-label">摄像头 #<span id="cam-idx">-</span></span>
    </div>

    <div class="camera-viewport" id="camera-viewport">
      {% if in_enabled %}
      <img id="video-in" src="/video_feed/in" alt="进门摄像头">
      {% endif %}
      {% if out_enabled %}
      <img id="video-out" src="/video_feed/out" alt="出门摄像头" style="display:none">
      {% endif %}
      <div class="camera-placeholder" id="camera-placeholder" style="display:{% if in_enabled or out_enabled %}none{% else %}flex{% endif %}">
        <span class="cam-icon">&#x1f4f7;</span>
        <p>摄像头未启动</p>
        <span class="hint">点击下方按钮启动摄像头</span>
      </div>
      <div class="scan-overlay" id="scan-overlay" style="display:{% if in_enabled or out_enabled %}flex{% else %}none{% endif %}">
        <div class="scan-frame">
          <div class="corner-bl"></div><div class="corner-br"></div>
          <div class="scan-line"></div>
        </div>
      </div>
      <div class="result-flash" id="flash"></div>
    </div>

    <div class="camera-actions">
      <button class="btn-action btn-capture" onclick="triggerCapture()">&#x1f4f7; 拍照识别</button>
      <button class="btn-action btn-simulate" onclick="triggerSimulate()">&#x1f9d1; 模拟识别</button>
    </div>
  </div>

  <!-- Right: Info Section -->
  <div class="info-section">
    <!-- Recognition panel -->
    <div class="recognition-panel" id="recognition-panel">
      <div class="recognition-waiting" id="recognition-waiting">
        <div class="waiting-icon">&#x1f464;</div>
        <p>等待识别...</p>
        <p class="sub">请点击识别按钮或模拟</p>
      </div>
      <div class="recognition-result" id="recognition-result"></div>
    </div>

    <!-- Local records -->
    <div class="records-panel">
      <div class="records-header">
        <span style="display:flex;align-items:center;gap:8px">&#x1f4cb; 本机最近记录 <span class="pending-badge hidden" id="pending-badge" title="等待上传">0条待上传</span></span>
        <span class="sync-info" id="sync-info">特征库 v<span class="sync-ver" id="sync-ver">-</span></span>
        <span class="device-id">{{device_sn}}</span>
      </div>
      <div class="records-list" id="records-list">
        <div class="record-item" style="justify-content:center;color:var(--text-muted);font-size:13px;padding:24px">暂无记录</div>
      </div>
    </div>
  </div>
</div>

<!-- ===== Config Overlay ===== -->
<div class="config-overlay" id="config-overlay" style="display:{% if binding %}none{% else %}flex{% endif %}">
  <div class="config-card">
    <h3>&#x2699; 摄像头方向绑定</h3>
    <p class="cfg-subtitle">请为进门和出门分别选择摄像头设备</p>
    <div class="cfg-row">
      <span class="cfg-label">&#x2b06; 进门</span>
      <span class="cfg-arrow">&#x27a1;</span>
      <select id="cfg-in"></select>
    </div>
    <div class="cfg-row">
      <span class="cfg-label">&#x2b07; 出门</span>
      <span class="cfg-arrow">&#x27a1;</span>
      <select id="cfg-out"></select>
    </div>
    <p class="hint" id="cfg-msg">提示：选择"不使用"可关闭对应方向，单摄像头时可两个方向选同一个</p>
    <div id="cfg-status"></div>
    <div class="cfg-actions">
      <button class="btn btn-primary" onclick="saveConfig()" id="cfg-save-btn">&#x1f4be; 保存并启动</button>
      <button class="btn btn-ghost" onclick="skipConfig()" style="display:{% if binding %}inline-block{% else %}none{% endif %}">稍后配置</button>
    </div>
  </div>
</div>

<script>
const DEVICE_SN = '{{device_sn}}';
const BINDING = {{binding_json|safe}};
const IN_ENABLED = {{in_enabled|tojson}};
const OUT_ENABLED = {{out_enabled|tojson}};
let currentDirection = 'in';
let events = [];
let isOnline = false;
let doorTimer = null;
let cameraActive = IN_ENABLED || OUT_ENABLED;
let offlineSince = null;
let offlineTimerInterval = null;

// Header clock
function updateClock() {
  const now = new Date();
  document.getElementById('header-clock').textContent = now.toLocaleTimeString('zh-CN');
  document.getElementById('header-date').textContent = now.toLocaleDateString('zh-CN',{year:'numeric',month:'2-digit',day:'2-digit'}).replace(/\//g,'-');
}
setInterval(updateClock, 1000);
updateClock();

// Switch direction
function switchDirection(dir) {
  currentDirection = dir;
  document.getElementById('btn-dir-in').classList.toggle('active', dir === 'in');
  document.getElementById('btn-dir-out').classList.toggle('active', dir === 'out');
  const label = document.getElementById('camera-dir-label');
  if (dir === 'in') {
    label.innerHTML = '&#x2b06; 进门通道';
    label.className = 'camera-dir-tag in';
  } else {
    label.innerHTML = '&#x2b07; 出门通道';
    label.className = 'camera-dir-tag out';
  }
  // Switch video feed
  if (document.getElementById('video-in')) document.getElementById('video-in').style.display = dir === 'in' ? 'block' : 'none';
  if (document.getElementById('video-out')) document.getElementById('video-out').style.display = dir === 'out' ? 'block' : 'none';
  if (BINDING) {
    document.getElementById('cam-idx').textContent = dir === 'in' ? BINDING.in : BINDING.out;
  }
}

// Manual open
function manualOpen() {
  const now = new Date();
  const event = {
    time: now.toLocaleTimeString('zh-CN'),
    name: '手动开门',
    stu_no: '',
    direction: currentDirection,
    similarity: 1.0,
    result: 'success',
    manual: true
  };
  addEvent(event);
  // Also send to server
  fetch('/api/manual_open', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({device_sn:DEVICE_SN, direction:currentDirection})
  }).catch(()=>{});
}

// Trigger capture - flash the camera and show a prompt
function triggerCapture() {
  if (!cameraActive) {
    alert('摄像头未启动，请先配置摄像头。');
    return;
  }
  const flash = document.getElementById('flash');
  flash.className = 'result-flash show success';
  setTimeout(() => { flash.className = 'result-flash'; }, 800);
}

// Simulate recognition
function triggerSimulate() {
  const names = ['张三', '李四', '王五', '赵六', '陈七', '周八'];
  const stunos = ['20231113513', '20231113514', '20231113515', '20231113516', '20231113517', '20231113518'];
  const idx = Math.floor(Math.random() * names.length);
  const sim = 0.75 + Math.random() * 0.24;
  const now = new Date();
  const event = {
    time: now.toLocaleTimeString('zh-CN'),
    name: names[idx],
    stu_no: stunos[idx],
    direction: currentDirection,
    similarity: sim,
    result: 'success',
  };
  addEvent(event);
}

// Poll status + events
async function pollStatus() {
  try {
    const resp = await fetch('/api/status');
    const data = await resp.json();
    const wasOffline = !isOnline;
    isOnline = data.online;
    const statusEl = document.getElementById('header-status');
    statusEl.className = 'online-badge ' + (data.online ? 'online' : 'offline');
    statusEl.innerHTML = data.online ? '&#x2714; 在线' : '&#x26a0; 离线';

    // Offline banner with timer
    const banner = document.getElementById('offline-banner');
    if (data.online) {
      banner.style.display = 'none';
      offlineSince = null;
      if (offlineTimerInterval) { clearInterval(offlineTimerInterval); offlineTimerInterval = null; }
      document.getElementById('offline-timer').textContent = '';
    } else {
      banner.style.display = 'flex';
      if (!offlineSince) {
        offlineSince = Date.now();
        updateOfflineTimer();
        offlineTimerInterval = setInterval(updateOfflineTimer, 30000);
      }
    }

    if (data.binding) {
      cameraActive = data.in_enabled || data.out_enabled;
      document.getElementById('cam-idx').textContent = currentDirection === 'in' ? (data.in_enabled ? data.binding.in : '-') : (data.out_enabled ? data.binding.out : '-');
      document.getElementById('scan-overlay').style.display = cameraActive ? 'flex' : 'none';
      document.getElementById('camera-placeholder').style.display = cameraActive ? 'none' : 'flex';
      if (document.getElementById('video-in')) document.getElementById('video-in').style.display = (currentDirection === 'in' && data.in_enabled) ? 'block' : 'none';
      if (document.getElementById('video-out')) document.getElementById('video-out').style.display = (currentDirection === 'out' && data.out_enabled) ? 'block' : 'none';
    }
    // Update sync version
    document.getElementById('sync-ver').textContent = data.feature_version || '-';
  } catch(e) {}

  // Poll events
  try {
    const evResp = await fetch('/api/events');
    const newEvents = await evResp.json();
    if (newEvents.length > 0) {
      newEvents.forEach(e => addEvent(e));
    }
  } catch(e) {}

}
setInterval(pollStatus, 2000);
pollStatus();

// Update offline timer display
function updateOfflineTimer() {
  if (!offlineSince) return;
  const elapsed = Math.floor((Date.now() - offlineSince) / 1000);
  const min = Math.floor(elapsed / 60);
  const sec = elapsed % 60;
  document.getElementById('offline-timer').textContent = '已离线 ' + min + '分' + sec + '秒';
}

// Poll pending record count
async function pollPendingCount() {
  try {
    const resp = await fetch('/api/pending_count');
    const data = await resp.json();
    const badge = document.getElementById('pending-badge');
    if (data.count > 0) {
      badge.textContent = data.count + '条待上传';
      badge.classList.remove('hidden');
    } else {
      badge.classList.add('hidden');
    }
    // Also update offline banner queued count
    const queued = document.getElementById('offline-queued');
    if (queued) queued.textContent = '排队: ' + data.count + ' 条';
  } catch(e) {}
}
setInterval(pollPendingCount, 10000);
pollPendingCount();

// Poll uptime
async function pollUptime() {
  try {
    const resp = await fetch('/api/uptime');
    const data = await resp.json();
    const sec = data.uptime;
    const h = Math.floor(sec / 3600);
    const m = Math.floor((sec % 3600) / 60);
    const s = sec % 60;
    let text = '运行: ';
    if (h > 0) text += h + 'h ' + m + 'm';
    else if (m > 0) text += m + 'm ' + s + 's';
    else text += s + 's';
    document.getElementById('uptime-display').innerHTML = '<span class="uptime-dot"></span>' + text;
  } catch(e) {}
}
setInterval(pollUptime, 30000);
pollUptime();

// Poll last sync info
async function pollLastSync() {
  try {
    const resp = await fetch('/api/last_sync');
    const data = await resp.json();
    document.getElementById('sync-ver').textContent = 'v' + (data.feature_version || 0);
  } catch(e) {}
}
setInterval(pollLastSync, 60000);
pollLastSync();

function addEvent(e) {
  events.unshift(e);
  if (events.length > 50) events.pop();
  updateRecordsList();
  showRecognitionResult(e);
}

function showRecognitionResult(e) {
  const waiting = document.getElementById('recognition-waiting');
  const result = document.getElementById('recognition-result');
  waiting.style.opacity = '0';
  setTimeout(() => {
    waiting.style.display = 'none';
    result.style.display = 'block';
    result.style.opacity = '0';
    requestAnimationFrame(() => {
      result.style.opacity = '1';
    });
  }, 200);

  const success = e.result === 'success';
  const simPercent = (e.similarity * 100).toFixed(1);
  const simColor = e.similarity >= 0.8 ? 'var(--green)' : 'var(--orange)';

  if (e.manual) {
    result.innerHTML = `
      <div style="text-align:center">
        <div class="manual-icon-circle">&#x1f513;</div>
        <div class="result-title manual-accent">手动开门</div>
      </div>
      <div class="result-info-card" style="border:1px solid rgba(16,185,129,.2);background:rgba(16,185,129,.06)">
        <div style="display:flex;align-items:center;gap:10px;justify-content:center">
          <span class="dir-tag ${e.direction==='in'?'in':'out'}">${e.direction==='in'?'&#x2b06; 进门':'&#x2b07; 出门'}</span>
          <span style="font-family:monospace;font-size:12px;color:var(--text-secondary)">${e.time}</span>
        </div>
        <div style="font-size:13px;font-weight:600;color:var(--green);margin-top:8px">&#x1f513; 管理员手动放行</div>
      </div>
      <div class="door-status-msg door-open">&#x1f513; 门已开启，请通行</div>
    `;
  } else if (success) {
    result.innerHTML = `
      <div style="text-align:center">
        <div class="result-header-icon">&#x2705;</div>
        <div class="result-title" style="color:var(--green)">识别成功</div>
      </div>
      <div class="result-info-card">
        <div class="result-name">${e.name}</div>
        <div class="result-stuno">${e.stu_no}</div>
        <div class="sim-row">
          <span style="color:var(--text-secondary)">相似度</span>
          <span class="sim-value" style="color:${simColor}">${simPercent}%</span>
          <div class="sim-bar-track">
            <div class="sim-bar-fill pulse" style="width:${Math.min(100,e.similarity*100)}%;background:${simColor}"></div>
          </div>
        </div>
      </div>
      <div class="result-meta">
        <span class="dir-tag ${e.direction==='in'?'in':'out'}">${e.direction==='in'?'&#x2b06; 进门':'&#x2b07; 出门'}</span>
        <span style="font-family:monospace;font-size:11px">${e.time}</span>
      </div>
      <div class="door-status-msg door-open">&#x1f513; 门已开启，请通行</div>
    `;
    // Remove pulse class after animation completes
    setTimeout(() => {
      const bar = result.querySelector('.sim-bar-fill.pulse');
      if (bar) bar.classList.remove('pulse');
    }, 1500);
  } else {
    result.innerHTML = `
      <div style="text-align:center">
        <div class="result-header-icon">&#x274c;</div>
        <div class="result-title" style="color:var(--red)">陌生人</div>
      </div>
      <div class="result-info-card" style="border:1px solid rgba(239,68,68,.2);background:rgba(239,68,68,.06)">
        <div style="font-size:15px;font-weight:700;color:var(--red);margin-bottom:4px">该人员不在系统人脸库中</div>
        <div style="font-size:12px;color:var(--text-secondary)">未通过身份验证，禁止通行</div>
        <div class="sim-row" style="margin-top:8px">
          <span style="color:var(--text-secondary)">相似度</span>
          <span class="sim-value" style="color:var(--red)">${simPercent}%</span>
          <div class="sim-bar-track">
            <div class="sim-bar-fill pulse" style="width:${Math.min(100,e.similarity*100)}%;background:var(--red)"></div>
          </div>
          <span style="font-size:11px;color:var(--text-muted)">阈值 50%</span>
        </div>
      </div>
      <div class="result-meta">
        <span class="dir-tag ${e.direction==='in'?'in':'out'}">${e.direction==='in'?'&#x2b06; 进门':'&#x2b07; 出门'}</span>
        <span style="font-family:monospace;font-size:11px">${e.time}</span>
      </div>
      <div class="door-status-msg door-closed">&#x1f512; 门已关闭</div>
    `;
    setTimeout(() => {
      const bar = result.querySelector('.sim-bar-fill.pulse');
      if (bar) bar.classList.remove('pulse');
    }, 1500);
  }

  // Flash camera
  const flash = document.getElementById('flash');
  if (flash) {
    flash.className = 'result-flash show ' + (success ? 'success' : 'fail');
    setTimeout(() => { flash.className = 'result-flash'; }, 1500);
  }

  // Reset after 6s
  if (doorTimer) clearTimeout(doorTimer);
  doorTimer = setTimeout(() => {
    result.style.opacity = '0';
    setTimeout(() => {
      result.style.display = 'none';
      waiting.style.display = 'flex';
      waiting.style.opacity = '1';
    }, 350);
  }, 6000);
}

function updateRecordsList() {
  const list = document.getElementById('records-list');
  let html = '';
  events.slice(0, 20).forEach(e => {
    const success = e.result === 'success';
    html += `<div class="record-item">
      <span class="rec-dot ${success?'success':'fail'}"></span>
      <span class="rec-name">${e.name}</span>
      <span class="rec-stuno">${e.stu_no}</span>
      <span class="rec-dir ${e.direction==='in'?'in':'out'}">${e.direction==='in'?'&#x2b06;进':'&#x2b07;出'}</span>
      <span class="rec-time">${e.time}</span>
    </div>`;
  });
  list.innerHTML = html || '<div class="record-item" style="justify-content:center;color:var(--text-muted);font-size:13px;padding:24px">暂无记录</div>';
}

// Config
async function loadCameras() {
  try {
    const resp = await fetch('/api/status');
    const data = await resp.json();
    const binding = data.binding;
    const selIn = document.getElementById('cfg-in');
    const selOut = document.getElementById('cfg-out');
    selIn.innerHTML = '<option value="-1">不使用</option>';
    selOut.innerHTML = '<option value="-1">不使用</option>';
    for (let i = 0; i < 10; i++) {
      selIn.innerHTML += `<option value="${i}">摄像头 #${i}</option>`;
      selOut.innerHTML += `<option value="${i}">摄像头 #${i}</option>`;
    }
    if (binding) {
      selIn.value = binding.in >= 0 ? binding.in : -1;
      selOut.value = binding.out >= 0 ? binding.out : -1;
      // Show current binding status
      const statusEl = document.getElementById('cfg-status');
      const inLabel = binding.in >= 0 ? ('#' + binding.in) : '未绑定';
      const outLabel = binding.out >= 0 ? ('#' + binding.out) : '未绑定';
      const singleNote = (binding.in >= 0 && binding.out >= 0 && binding.in === binding.out) ? ' (单摄像头共用)' : '';
      statusEl.innerHTML = '<div class="cfg-current">当前绑定: 进门=<span>' + inLabel + '</span> | 出门=<span>' + outLabel + '</span>' + singleNote + '</div>';
    }
  } catch(e) { console.error(e); }
}

function showConfig() {
  document.getElementById('config-overlay').style.display = 'flex';
  loadCameras();
}
function skipConfig() {
  document.getElementById('config-overlay').style.display = 'none';
}

async function saveConfig() {
  const inIdx = document.getElementById('cfg-in').value;
  const outIdx = document.getElementById('cfg-out').value;
  const saveBtn = document.getElementById('cfg-save-btn');
  const statusEl = document.getElementById('cfg-status');
  saveBtn.disabled = true;
  saveBtn.textContent = '保存中...';
  statusEl.innerHTML = '<div class="cfg-loading">&#x23f3; 正在保存配置...</div>';
  try {
    const formData = new FormData();
    formData.append('in_index', inIdx);
    formData.append('out_index', outIdx);
    const resp = await fetch('/config/save', {method:'POST', body:formData});
    if (resp.ok) {
      statusEl.innerHTML = '<div class="cfg-success">&#x2705; 配置保存成功，正在重启识别线程...</div>';
      setTimeout(() => {
        document.getElementById('config-overlay').style.display = 'none';
        location.reload();
      }, 1200);
    } else {
      const text = await resp.text();
      statusEl.innerHTML = '<div class="cfg-error">&#x274c; 保存失败: ' + text + '</div>';
      saveBtn.disabled = false;
      saveBtn.textContent = '&#x1f4be; 保存并启动';
    }
  } catch(e) {
    statusEl.innerHTML = '<div class="cfg-error">&#x274c; 配置失败: ' + e.message + '</div>';
    saveBtn.disabled = false;
    saveBtn.textContent = '&#x1f4be; 保存并启动';
  }
}

// Init
if (BINDING) {
  document.getElementById('cam-idx').textContent = currentDirection === 'in' ? BINDING.in : BINDING.out;
}
loadCameras();
</script>
</body>
</html>'''


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
    app = Flask(__name__)
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
        return render_template_string(
            CLIENT_HTML,
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

        CONFIG_HTML = '''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>摄像头配置 — 校园门禁系统</title>
<style>
:root{--bg:#0f172a;--card:#1e293b;--border:#334155;--text:#f1f5f9;--text-secondary:#94a3b8;--text-muted:#64748b;--accent:#3b82f6;--green:#10b981;--red:#ef4444;--orange:#f59e0b;--radius:12px}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:"Inter","Microsoft YaHei","Segoe UI",sans-serif;background:var(--bg);color:var(--text);display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0}
.card{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:36px;width:90%;max-width:500px;text-align:center;box-shadow:0 20px 60px rgba(0,0,0,.5)}
.card h3{font-size:20px;margin-bottom:6px}
.card .subtitle{font-size:13px;color:var(--text-secondary);margin-bottom:24px}
.row{display:flex;align-items:center;gap:12px;margin-bottom:16px;padding:12px 16px;background:rgba(255,255,255,.03);border-radius:10px;text-align:left}
.row .label{font-size:13px;font-weight:600;color:var(--text);min-width:60px}
.row .arrow{color:var(--text-muted);font-size:16px;flex-shrink:0}
select{background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:10px 14px;color:var(--text);font-size:14px;width:170px;outline:none}
select:focus{border-color:var(--accent)}
.btn{padding:10px 24px;border:none;border-radius:10px;cursor:pointer;font-size:13px;font-weight:600;margin:4px;transition:all .15s}
.btn-blue{background:var(--accent);color:#fff}.btn-blue:hover{background:#2563eb}
.btn-ghost{background:transparent;color:var(--text-secondary);border:1px solid var(--border)}
.btn-ghost:hover{border-color:var(--text-muted);color:var(--text)}
.error{color:var(--red);font-size:12px;margin-top:12px;padding:8px 14px;background:rgba(239,68,68,.1);border-radius:8px;display:inline-block}
.hint{font-size:12px;color:var(--text-muted);margin-top:16px;line-height:1.5}
.current{font-size:11px;color:var(--text-muted);margin-top:12px;padding:8px 14px;background:rgba(255,255,255,.02);border-radius:10px;display:inline-block}
.current span{color:var(--accent);font-weight:600}
.actions{display:flex;gap:10px;justify-content:center;margin-top:8px}
</style></head>
<body>
<div class="card">
<h3>&#x2699; 摄像头方向绑定</h3>
<p class="subtitle">请为进门和出门分别选择摄像头设备</p>
<form method="post" action="/config/save">
<div class="row">
  <span class="label">&#x2b06; 进门</span>
  <span class="arrow">&#x27a1;</span>
  <select name="in_index">
    <option value="-1" {% if not binding or binding['in'] < 0 %}selected{% endif %}>不使用</option>
    {% for cam in cameras %}<option value="{{cam.index}}" {% if binding and binding['in']==cam.index %}selected{% endif %}>{{cam.name}}</option>{% endfor %}
  </select>
</div>
<div class="row">
  <span class="label">&#x2b07; 出门</span>
  <span class="arrow">&#x27a1;</span>
  <select name="out_index">
    <option value="-1" {% if not binding or binding['out'] < 0 %}selected{% endif %}>不使用</option>
    {% for cam in cameras %}<option value="{{cam.index}}" {% if binding and binding['out']==cam.index %}selected{% endif %}>{{cam.name}}</option>{% endfor %}
  </select>
</div>
{% if binding %}
<div class="current">
  当前绑定: 进门=<span>{% if binding['in'] >= 0 %}#{{binding['in']}}{% else %}未绑定{% endif %}</span> | 出门=<span>{% if binding['out'] >= 0 %}#{{binding['out']}}{% else %}未绑定{% endif %}</span>
  {% if binding['in'] >= 0 and binding['out'] >= 0 and binding['in'] == binding['out'] %}(单摄像头共用){% endif %}
</div>
{% endif %}
{% if error %}<p class="error">&#x274c; {{error}}</p>{% endif %}
<p class="hint">提示：选择"不使用"可关闭对应方向；单摄像头时可两个方向选同一个</p>
<div class="actions">
  <button type="submit" class="btn btn-blue">&#x1f4be; 保存并启动</button>
  <a href="/"><button type="button" class="btn btn-ghost">取消</button></a>
</div>
</form>
</div>
</body></html>'''
        return render_template_string(CONFIG_HTML, cameras=cameras, binding=binding, error=error)

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
        """返回客户端运行时长（秒）"""
        uptime_seconds = time.time() - app.config.get('start_time', time.time())
        return jsonify({'uptime': int(uptime_seconds)})

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
