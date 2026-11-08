# sidecar 协议层（PL006.1）：stdio JSON Lines 信封编解码 + 命令/事件/错误分类常量单源
# 信封：请求 {"id", "cmd", "params"} → 响应 {"id", "ok", "result" | "error"{category,message}}；事件 {"event", "data"} 单向
# 定案见 z.plan.md 附录 PL006；本模块只管编解码与常量，零业务（分发在 commands.py，进程在 app.py）

import json
from typing import Any

# 错误分类（与 AGENTS 错误策略主线对齐：generate/file_missing 等业务分类透传，框架级四类兜底）
CAT_BAD_REQUEST = "bad_request"  # 未知命令/参数缺失或类型非法
CAT_NOT_FOUND = "not_found"  # item_id 等引用不存在
CAT_GENERATE = "generate"  # GenerateError（选歌校验/容量/空文件）
CAT_IO = "io"  # 文件系统层失败
CAT_INTERNAL = "internal"  # 未分类异常兜底

# 事件名（协议 wire 名，event_bus 域事件在 app.py 事件泵映射到这些名字）
EV_READY = "ready"  # 握手：bootstrap 完成首发，{version, items_count}
EV_PROGRESS = "progress"  # ← event_bus PROGRESS
EV_PLAYBACK_STATE = "playback_state"  # ← PLAYBACK_STATE
EV_TRACK_CHANGED = "track_changed"  # ← TRACK_CHANGED
EV_SIDE_FLIPPED = "side_flipped"  # ← SIDE_FLIPPED
EV_ERROR = "error"  # ← ERROR
EV_LIBRARY_CHANGED = "library_changed"  # 库写命令成功后（sidecar 级，不经 event_bus）
EV_CONFIG_CHANGED = "config_changed"  # set_config 成功后（sidecar 级）


def encode_message(message: dict[str, Any]) -> str:
    # 信封 → 一行 JSON（ensure_ascii=False 保中文可读；换行由调用方追加——JSON Lines 帧定界符）
    return json.dumps(message, ensure_ascii=False)


def make_result(req_id: int, result: Any) -> dict[str, Any]:
    # 成功响应信封
    return {"id": req_id, "ok": True, "result": result}


def make_error(req_id: int, category: str, message: str) -> dict[str, Any]:
    # 失败响应信封（分类 + 中文消息；UI/前端只认分类不认细节）
    return {"id": req_id, "ok": False, "error": {"category": category, "message": message}}


def make_event(name: str, data: Any = None) -> dict[str, Any]:
    # 事件信封（无 id；data 可为 None）
    return {"event": name, "data": data}


def parse_line(line: str) -> dict[str, Any] | None:
    # 行 → 请求信封（非对象/坏 JSON 返回 None 由分发层报 bad_request）；容忍首尾空白
    try:
        data = json.loads(line)
    except (json.JSONDecodeError, ValueError):
        return None
    return data if isinstance(data, dict) else None


# ===== sidecar/protocol.py 函数/常量说明 =====
# CAT_*: 错误分类常量（bad_request/not_found/generate/io/internal；业务 GenerateError→generate）
# EV_*: 事件名常量（ready 握手/五个域事件映射/library_changed/config_changed；wire 名单源）
# encode_message(message) -> str: 信封序列化（ensure_ascii=False；调用方补 "\n" 定界）
# make_result(req_id, result) -> dict: 成功响应 {"id","ok":True,"result"}
# make_error(req_id, category, message) -> dict: 失败响应 {"id","ok":False,"error"{category,message}}
# make_event(name, data) -> dict: 事件 {"event","data"}
# parse_line(line) -> dict|None: 请求行解析（坏 JSON/非对象 → None，分发层报 bad_request）
#   设计理由：协议编解码单源（前端 mock 测试与本模块同契约）；常量显式声明防手写漂移
#   异常：parse_line 捕获 JSONDecodeError 返回 None（不抛出到线程）
#   关联配置：无（纯协议层）；消费方 sidecar/app.py、sidecar/commands.py
