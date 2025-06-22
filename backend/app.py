import os
import sys
import logging
from flask import Flask
from flask_cors import CORS

# 将 rag_engine 的父目录（即项目根目录）添加到 Python 路径中
# 这样可以确保可以导入 rag_engine 模块
# project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path.insert(0, project_root)

from rag_engine import RAGPipeline, config as engine_config
from .config import BackendConfig
from .routes import api


def create_app() -> Flask:
    """
    应用工厂函数
    """
    app = Flask(__name__)
    app.config.from_object(BackendConfig())
    
    # 启用CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # 设置日志记录
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # --- 依赖注入：创建并初始化 RAG 引擎单例 ---
    # 这个实例会在整个应用的生命周期中存在
    logging.info("正在初始化 RAG 管线...")
    try:
        rag_pipeline_instance = RAGPipeline(config=engine_config)
        rag_pipeline_instance.initialize()
        app.rag_pipeline = rag_pipeline_instance
        logging.info("RAG 管线初始化成功。")
    except Exception as e:
        logging.error(f"RAG 管线初始化失败: {e}", exc_info=True)
        sys.exit(1)

    # 注册 API 蓝图
    app.register_blueprint(api)

    @app.route("/")
    def index():
        return "RAG 引擎 API 正在运行中。使用 /api/groups 查看可用组。"

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=app.config["DEBUG"])
