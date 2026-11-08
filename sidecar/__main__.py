# sidecar 进程入口（PL006.1）：argparse 测试钩子（--db/--config）→ 会话启动；`python -m sidecar` 运行
# 钩子必须在任何库访问前应用（repository/settings 首次连接延迟到 bootstrap）

import argparse
import sys


def main() -> None:
    # 入口：解析测试钩子 → 应用（先于 Session/任何库访问）→ 启动会话事件循环
    parser = argparse.ArgumentParser(description="MrSirMusic sidecar（stdio JSON Lines 协议）")
    parser.add_argument("--db", default=None, help="物品库路径覆盖（测试钩子，默认 music/items.db）")
    parser.add_argument("--config", default=None, help="用户配置路径覆盖（测试钩子，默认 config/user_config.json）")
    args = parser.parse_args()

    if args.db:
        import modules.library.repository as repository

        repository.set_db_path_for_tests(args.db)
    if args.config:
        from config import settings

        settings.set_config_path_for_tests(args.config)

    from sidecar.app import Session

    Session().run()


if __name__ == "__main__":
    main()


# ===== sidecar/__main__.py 函数/常量说明 =====
# main(): 进程入口
#   逻辑：argparse（--db/--config 测试钩子）→ 钩子先于任何库访问应用（set_db_path_for_tests /
#     set_config_path_for_tests，均带缓存/路径单点收敛）→ Session().run()（QCoreApplication 循环）
#   设计理由：钩子参数化隔离测试库与用户配置（a15 探针不污染真实数据，对称 B0.3 惯例）；
#     import 放钩子之后（库路径覆盖必须先于首次连接）
#   异常：无额外捕获（顶层异常直接崩溃——进程级错误由父进程 Tauri 壳的重启策略兜底，PL007.3）
#   关联配置：music/items.db（默认库）、config/user_config.json（默认配置）、base.json version（ready）
