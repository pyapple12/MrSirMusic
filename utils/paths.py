# 项目根路径工具（B1.2）：项目根派生单点收敛，供 logger/schema/static_config 等统一引用

from pathlib import Path


def project_root() -> Path:
    # 项目根目录（本文件所在目录的上一级：utils/paths.py → 项目根）
    return Path(__file__).resolve().parent.parent


# ===== utils/paths.py 函数说明 =====
# project_root() -> Path: 项目根目录
#   逻辑：__file__ 自定位（utils/paths.py 的父目录）
#   设计理由：收敛此前 main/logger/schema/static_config 四处独立"Path(__file__).resolve().parent..."
#     派生逻辑（审计 P2-2）；项目根迁移/打包只需改这一处
#   关联配置：无（utils 层最底层，零业务依赖）
