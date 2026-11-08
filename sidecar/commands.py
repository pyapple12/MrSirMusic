# sidecar 命令分发层（PL006.2/3/4）：命令注册表 + 统一执行与错误分类映射；业务全部委托 modules/（零复制）

from dataclasses import asdict
from typing import Any, Callable

from config.static.static_config import get_static_config
from modules.generator.delete import delete as delete_item_impl
from modules.generator.edit import change_tag as change_tag_impl
from modules.generator.edit import rename_item as rename_item_impl
from modules.generator.generator import GenerateError, generate as generate_impl
from modules.generator.regenerate import regenerate as regenerate_impl
from modules.items.model import Item, ItemType

from sidecar import protocol as _proto

# 静态配置一次解包（item_types 重建 ItemType / ping 版本）
_SC = get_static_config()


class CommandError(Exception):
    # 命令层业务异常（携带协议错误分类；分发器映射为 error 信封）

    def __init__(self, category: str, message: str) -> None:
        # 分类 + 中文消息（前端只认分类不认细节）
        super().__init__(message)
        self.category = category


def _item_to_dict(item: Item) -> dict[str, Any]:
    # Item → 协议 dict（前端渲染全量；is_missing 为方法调用结果显式带上；
    # PATCH003 增 play_count——详情面板播放次数行数据源）
    return {
        "id": item.id,
        "name": item.name,
        "type": {"key": item.type.key, "name": item.type.name, "shape": item.type.shape},
        "cover_source": item.cover_source,
        "cover_path": item.cover_path,
        "tag": item.tag,
        "play_count": item.play_count,
        "total_seconds": item.total_seconds(),
        "sides": [
            {
                "label": side.label,
                "tracks": [
                    {
                        **asdict(track),
                        "is_missing": track.is_missing(),
                    }
                    for track in side.tracks
                ],
            }
            for side in item.sides.values()
        ],
    }


def _payload_to_dict(payload: Any) -> Any:
    # 域事件 payload → 协议 dict（dataclass asdict 递归；非 dataclass 原样透传）
    try:
        return asdict(payload)
    except TypeError:
        return payload


def _require_str(params: dict[str, Any], key: str) -> str:
    # 参数必填字符串校验（缺失/非字符串 → bad_request）
    value = params.get(key)
    if not isinstance(value, str) or not value:
        raise CommandError(_proto.CAT_BAD_REQUEST, f"参数 {key} 必须为非空字符串")
    return value


def _find_item(session: Any, item_id: str) -> Item:
    # 按 id 在会话缓存中取物品（未命中 → not_found）
    for item in session.items:
        if item.id == item_id:
            return item
    raise CommandError(_proto.CAT_NOT_FOUND, f"物品不存在: {item_id}")


def _cmd_ping(session: Any, params: dict[str, Any]) -> dict[str, Any]:
    # 存活检查 + 版本回显（传输层隔离用）
    return {"pong": True, "version": str(_SC.base.get("version", "unknown"))}


def _cmd_get_bootstrap(session: Any, params: dict[str, Any]) -> dict[str, Any]:
    # 前端唯一配置源：静态四分类 + 用户配置 + 库全量（六合快照）
    return session.bootstrap_snapshot()


def _cmd_list_items(session: Any, params: dict[str, Any]) -> dict[str, Any]:
    # 库全量（刷新缺失标记后重读）
    session.refresh_items()
    return {"items": [_item_to_dict(item) for item in session.items]}


def _cmd_load_item(session: Any, params: dict[str, Any]) -> dict[str, Any]:
    # 载入物品到引擎（不自动播放；播放走 transport_play）；
    # 先记 current_item_id 再 load——load 内部即发 TRACK_CHANGED（PATCH003 计数依赖该锚点）
    item = _find_item(session, _require_str(params, "item_id"))
    session.current_item_id = item.id
    session.engine.load_item(item)
    return {"loaded": True}


def _cmd_transport_play(session: Any, params: dict[str, Any]) -> dict[str, Any]:
    # 播放（事件经事件泵推送 playback_state）
    session.engine.play()
    return {"ok": True}


def _cmd_transport_pause(session: Any, params: dict[str, Any]) -> dict[str, Any]:
    # 暂停
    session.engine.pause()
    return {"ok": True}


def _cmd_transport_stop(session: Any, params: dict[str, Any]) -> dict[str, Any]:
    # 停止
    session.engine.stop()
    return {"ok": True}


def _cmd_transport_next(session: Any, params: dict[str, Any]) -> dict[str, Any]:
    # 下一曲（引擎返回 bool；A 面末/序列末为 False——不视为错误）
    return {"applied": bool(session.engine.play_next())}


def _cmd_transport_prev(session: Any, params: dict[str, Any]) -> dict[str, Any]:
    # 上一曲
    return {"applied": bool(session.engine.play_prev())}


def _cmd_transport_flip(session: Any, params: dict[str, Any]) -> dict[str, Any]:
    # 翻面
    return {"applied": bool(session.engine.flip())}


def _cmd_seek(session: Any, params: dict[str, Any]) -> dict[str, Any]:
    # 曲内寻曲（秒）
    seconds = params.get("seconds")
    if not isinstance(seconds, (int, float)) or isinstance(seconds, bool):
        raise CommandError(_proto.CAT_BAD_REQUEST, "参数 seconds 必须为数字")
    session.engine.seek(float(seconds))
    return {"ok": True}


def _cmd_seek_side(session: Any, params: dict[str, Any]) -> dict[str, Any]:
    # 面内寻曲（比例 0-1；引擎定位跨曲）
    fraction = params.get("fraction")
    if not isinstance(fraction, (int, float)) or isinstance(fraction, bool):
        raise CommandError(_proto.CAT_BAD_REQUEST, "参数 fraction 必须为数字")
    return {"applied": bool(session.engine.seek_side(float(fraction)))}


def _cmd_generate(session: Any, params: dict[str, Any]) -> dict[str, Any]:
    # 生成物品：type_key → ItemType 重建（未知键 → bad_request）→ generate 委托 → 刷新 + library_changed
    files = params.get("files")
    if not isinstance(files, list) or not all(isinstance(f, str) for f in files):
        raise CommandError(_proto.CAT_BAD_REQUEST, "参数 files 必须为字符串数组")
    # 空列表放行——业务 generate 抛 GenerateError("未选择任何音频文件") → generate 分类（与 Qt UI 同语义）
    type_key = _require_str(params, "type_key")
    if type_key not in _SC.item_types:
        raise CommandError(_proto.CAT_BAD_REQUEST, f"未知载体类型: {type_key}")
    item_type = ItemType.from_config(type_key, _SC.item_types[type_key])
    item = generate_impl(
        files,
        item_type,
        _require_str(params, "name"),
        str(params.get("tag", "")),
        cover_source=str(params.get("cover_source", "placeholder")),
        cover_file=params.get("cover_file"),
    )
    session.refresh_items()
    session.emit_event(_proto.EV_LIBRARY_CHANGED, {"reason": "generate"})
    return {"id": item.id, "name": item.name}


def _cmd_regenerate(session: Any, params: dict[str, Any]) -> dict[str, Any]:
    # 重新刻录（原歌池重分配 → 新 id 物品；GenerateError 透传）
    item = _find_item(session, _require_str(params, "item_id"))
    new_item = regenerate_impl(item)
    session.refresh_items()
    session.emit_event(_proto.EV_LIBRARY_CHANGED, {"reason": "regenerate"})
    return {"id": new_item.id, "name": new_item.name}


def _cmd_rename_item(session: Any, params: dict[str, Any]) -> dict[str, Any]:
    # 改名
    item = _find_item(session, _require_str(params, "item_id"))
    rename_item_impl(item, _require_str(params, "name"))
    session.refresh_items()
    session.emit_event(_proto.EV_LIBRARY_CHANGED, {"reason": "rename"})
    return {"ok": True}


def _cmd_change_tag(session: Any, params: dict[str, Any]) -> dict[str, Any]:
    # 换 Tag（置物架分组依据）
    item = _find_item(session, _require_str(params, "item_id"))
    change_tag_impl(item, str(params.get("tag", "")))
    session.refresh_items()
    session.emit_event(_proto.EV_LIBRARY_CHANGED, {"reason": "change_tag"})
    return {"ok": True}


def _cmd_delete_item(session: Any, params: dict[str, Any]) -> dict[str, Any]:
    # 删除（级联 tracks + 封面引用检查）
    item = _find_item(session, _require_str(params, "item_id"))
    delete_item_impl(item)
    session.refresh_items()
    session.emit_event(_proto.EV_LIBRARY_CHANGED, {"reason": "delete"})
    return {"ok": True}


def _cmd_set_config(session: Any, params: dict[str, Any]) -> dict[str, Any]:
    # 用户配置更新（字段可选部分更新；save_config 内置档位白名单校验）→ config_changed
    from config.settings import load_config, save_config

    cfg = load_config()
    if "realism_level" in params:
        level = params.get("realism_level")
        if not isinstance(level, str):
            raise CommandError(_proto.CAT_BAD_REQUEST, "参数 realism_level 必须为字符串")
        cfg.realism_level = level
    if "auto_flip" in params:
        auto_flip = params.get("auto_flip")
        if not isinstance(auto_flip, bool):
            raise CommandError(_proto.CAT_BAD_REQUEST, "参数 auto_flip 必须为布尔")
        cfg.auto_flip = auto_flip
    save_config(cfg)
    fresh = load_config()
    data = {"realism_level": fresh.realism_level, "auto_flip": fresh.auto_flip}
    session.emit_event(_proto.EV_CONFIG_CHANGED, data)
    return data


# 命令注册表（wire 名 → 处理器；新增命令在此登记——前端契约同步点）
HANDLERS: dict[str, Callable[[Any, dict[str, Any]], Any]] = {
    "ping": _cmd_ping,
    "get_bootstrap": _cmd_get_bootstrap,
    "list_items": _cmd_list_items,
    "load_item": _cmd_load_item,
    "transport_play": _cmd_transport_play,
    "transport_pause": _cmd_transport_pause,
    "transport_stop": _cmd_transport_stop,
    "transport_next": _cmd_transport_next,
    "transport_prev": _cmd_transport_prev,
    "transport_flip": _cmd_transport_flip,
    "seek": _cmd_seek,
    "seek_side": _cmd_seek_side,
    "generate": _cmd_generate,
    "regenerate": _cmd_regenerate,
    "rename_item": _cmd_rename_item,
    "change_tag": _cmd_change_tag,
    "delete_item": _cmd_delete_item,
    "set_config": _cmd_set_config,
}


def execute(session: Any, cmd: str, params: dict[str, Any]) -> Any:
    # 统一执行入口：查表 → 调用 → 异常映射为 CommandError（分发器转 error 信封）
    handler = HANDLERS.get(cmd)
    if handler is None:
        raise CommandError(_proto.CAT_BAD_REQUEST, f"未知命令: {cmd}")
    try:
        return handler(session, params if isinstance(params, dict) else {})
    except GenerateError as exc:
        raise CommandError(_proto.CAT_GENERATE, str(exc)) from exc
    except FileNotFoundError as exc:
        raise CommandError(_proto.CAT_IO, f"文件不存在: {exc}") from exc
    except (ValueError, TypeError) as exc:
        raise CommandError(_proto.CAT_BAD_REQUEST, str(exc)) from exc


# ===== sidecar/commands.py 函数/常量说明 =====
# CommandError(category, message): 命令层业务异常（category ∈ protocol.CAT_*；分发器映射 error 信封）
# _item_to_dict(item) -> dict: 物品序列化（type.key/name/shape + sides/tracks 全字段 + is_missing 显式）
# _payload_to_dict(payload) -> Any: 域事件 payload 序列化（asdict 递归 dataclass；失败原样透传）
# _require_str(params, key) -> str: 必填字符串校验（缺失/空/非字符串 → bad_request）
# _find_item(session, item_id) -> Item: 会话缓存按 id 查找（未命中 → not_found）
# HANDLERS: 命令注册表（18 条 wire 名单源；ping/get_bootstrap/list_items/load_item/transport×6/
#   seek/seek_side/generate/regenerate/rename_item/change_tag/delete_item/set_config）
# execute(session, cmd, params) -> Any: 统一执行（查表 + 异常映射：GenerateError→generate、
#   FileNotFoundError→io、ValueError/TypeError→bad_request、其余上抛由分发器兜底 internal）
#   设计理由：业务全部委托 modules/（本层零复制零业务）；错误分类与 AGENTS 错误策略主线对齐；
#     库写命令统一 refresh_items + library_changed（前端三视图同步源）
#   异常：全部收敛为 CommandError（信封化；栈细节只进日志不进协议）
#   关联配置：item_types.json（generate 重建 ItemType）；config/user_config.json（set_config）
