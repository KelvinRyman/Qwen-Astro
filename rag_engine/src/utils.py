import logging
import sys
import os
import re


def setup_logging(level: int = logging.INFO):
    """配置全局日志记录器"""
    logging.basicConfig(
        stream=sys.stdout,
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logging.info("日志系统已启动。")


def ensure_directory_exists(path: str):
    """确保指定路径的目录存在，如果不存在则创建它"""
    if not os.path.exists(path):
        os.makedirs(path)
        logging.info(f"已创建目录: {path}")
    else:
        logging.info(f"目录已存在: {path}")


# TODO: Deprecated
def sanitize_group_id(name: str) -> str:
    """
    将用户提供的组名转换为一个安全的、用作ID的字符串。
    - 转换为小写
    - 按空格和多个下划线替换单个下划线
    - 移除非法字符（只允许字母、数字、下划线）
    """
    if not name:
        return "default_group"
    # 转换为小写
    s = name.lower().strip().replace(" ", "_")
    # 移除非法字符
    s = re.sub(r"[^\w_]+", "", s)
    # 将多个下划线合并为一个
    s = re.sub(r"__+", "_", s)
    return s
