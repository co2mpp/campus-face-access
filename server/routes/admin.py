"""服务端管理后台 Web UI"""
from flask import Blueprint, render_template

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/')
@bp.route('')
def admin_index():
    return render_template('admin.html')
