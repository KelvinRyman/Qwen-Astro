import os


class BackendConfig:
    """
    后端服务配置类。
    使用 dataclass 的 frozen=True 使配置对象不可变，防止在运行时意外修改。
    """

    HOST = os.getenv("FLASK_HOST", "0.0.0.0")
    PORT = int(os.getenv("FLASK_PORT", 5000))
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "yes")
    UPLOAD_FOLDER = os.path.join(os.getcwd(), "temp_uploads")   # 临时的上传目录
