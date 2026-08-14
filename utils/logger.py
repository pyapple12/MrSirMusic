# 统一日志模块（A2.1/B2.2）：控制台 + 文件双输出，中文 UTF-8，模块名级别；目录/级别走 base.json

import logging

from config.static.static_config import get_static_config
from utils.paths import project_root

# 静态配置一次解包（日志目录/级别外置，B2.2）
_SC = get_static_config()

# 日志目录与文件（base.json logs_dir 装配，gitignore 忽略 *.log）
LOG_DIR = project_root() / str(_SC.base.get("logs_dir", "logs"))
LOG_FILE = LOG_DIR / "mrsirmusic.log"
LOG_LEVEL = str(_SC.base.get("log_level", "INFO"))

# 统一日志格式（时间/级别/模块名/消息）
_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def get_logger(name: str = "app") -> logging.Logger:
    # 获取统一 logger：控制台 + 文件双输出；同名 logger 复用，handler 不重复添加
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(LOG_LEVEL)
        formatter = logging.Formatter(_LOG_FORMAT)
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        logger.addHandler(console)
        try:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception:
            pass
    return logger


# ===== utils/logger.py 函数/常量说明 =====
# LOG_DIR / LOG_FILE: 日志目录与文件路径（项目根 logs/，文件编码 UTF-8，*.log 已 gitignore）
# _LOG_FORMAT: 日志行格式（时间/级别/模块名/消息）
# get_logger(name) -> logging.Logger: 获取统一 logger
#   逻辑：logging.getLogger(name) → 无 handler 时装配控制台 + 文件双输出 → 返回
#   异常：文件 handler 装配失败静默跳过（控制台输出不中断，自愈策略）
#   设计理由：模块名作为 logger 名（任务要求）；UTF-8 编码保证中文日志不乱码
#   关联配置：无（路径固定项目根 logs/，可调参数后续可外置 base.json）
