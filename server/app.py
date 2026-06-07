"""服务端 Flask 主应用 — 监听 5000 端口"""
import os
from flask import Flask
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from server.config import SQLALCHEMY_DATABASE_URI, SERVER_PORT
from server.models import Base

# 延迟初始化 InsightFace（仅在需要人脸注册时加载）
_insightface_app = None


def get_insightface_app():
    global _insightface_app
    if _insightface_app is None:
        from insightface.app import FaceAnalysis
        _insightface_app = FaceAnalysis(name='buffalo_l')
        _insightface_app.prepare(ctx_id=-1)
    return _insightface_app


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24).hex())
    CORS(app)

    engine = create_engine(SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    # 注入到模块级别
    import server.app as app_module
    app_module.SessionLocal = SessionLocal

    # 同步元数据初始化
    session = SessionLocal()
    try:
        from server.models import SyncMetadata
        if not session.query(SyncMetadata).filter(SyncMetadata.id == 1).first():
            session.add(SyncMetadata(id=1, current_feature_version=1))
            session.commit()
    finally:
        session.close()

    # 注册蓝图
    from server.routes.student import bp as student_bp
    from server.routes.face import bp as face_bp
    from server.routes.sync import bp as sync_bp
    from server.routes.record import bp as record_bp
    from server.routes.heartbeat import bp as heartbeat_bp
    from server.routes.admin import bp as admin_bp
    from server.routes.dashboard import bp as dashboard_bp
    from server.routes.device import bp as device_bp
    from server.routes.auth import bp as auth_bp
    app.register_blueprint(student_bp)
    app.register_blueprint(face_bp)
    app.register_blueprint(sync_bp)
    app.register_blueprint(record_bp)
    app.register_blueprint(heartbeat_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(device_bp)
    app.register_blueprint(auth_bp)

    # 根路径 → 管理后台
    from flask import render_template
    @app.route('/')
    def index():
        return render_template('redirect.html')

    app.config['JSON_AS_ASCII'] = False
    return app


if __name__ == '__main__':
    app = create_app()
    print(f"服务端启动: http://0.0.0.0:{SERVER_PORT}")
    app.run(host='0.0.0.0', port=SERVER_PORT, debug=False)
