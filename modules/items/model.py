# 领域模型模块（A3.1-A3.4）：ItemType/Track/Side/Item 纯数据 dataclass，零 GUI 依赖

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ItemType:
    # 载体类型（黑胶/磁带/CD）：注册表键 + 显示名 + 面集合 + 单面容量（分钟）+ 形态
    key: str
    name: str
    sides: tuple[str, ...]
    minutes_per_side: int
    shape: str

    @classmethod
    def from_config(cls, key: str, data: dict[str, Any]) -> "ItemType":
        # 从 item_types.json 单条记录构造；字段宽容解析（缺省回退默认，不崩溃）
        sides_raw = data.get("side") or []
        sides = tuple(str(s) for s in sides_raw if str(s) in ("A", "B"))
        return cls(
            key=key,
            name=str(data.get("name", key)),
            sides=sides or ("A",),
            minutes_per_side=int(data.get("minutes_per_side", 0)),
            shape=str(data.get("shape", "circle")),
        )


@dataclass
class Track:
    # 单曲模型：path 为唯一标识；title 等元数据可为空（标签解析失败降级）
    path: str
    title: str = ""
    artist: str = ""
    album: str = ""
    duration_seconds: float = 0.0
    format: str = ""

    @classmethod
    def from_tagging(cls, tag: Any, path: str) -> "Track":
        # 从标签解析结果构造（字段名对齐 TagData，duck typing 兼容缺字段）
        return cls(
            path=path,
            title=str(getattr(tag, "title", "") or ""),
            artist=str(getattr(tag, "artist", "") or ""),
            album=str(getattr(tag, "album", "") or ""),
            duration_seconds=float(getattr(tag, "duration_seconds", 0.0) or 0.0),
            format=str(getattr(tag, "format", "") or ""),
        )

    def is_missing(self) -> bool:
        # 路径失效检测：实体文件不存在（被移动/删除）视为缺失
        return not Path(self.path).is_file()


@dataclass
class Side:
    # 物品的某一面（A/B）：label + 曲目列表，容量由调用方校验（is_full 提供边界判断）
    label: str
    tracks: list[Track] = field(default_factory=list)

    def total_seconds(self) -> float:
        # 面内曲目总时长（秒）
        return sum(t.duration_seconds for t in self.tracks)

    def add_track(self, track: Track) -> None:
        # 追加曲目（容量校验由上层 add_track_to_side 负责，本方法仅追加）
        self.tracks.append(track)

    def remove_track(self, track_id: str) -> bool:
        # 按曲目 id（path）移除，找到并移除返回 True，未找到返回 False
        for i, t in enumerate(self.tracks):
            if t.path == track_id:
                del self.tracks[i]
                return True
        return False

    def is_full(self, max_seconds: int | float) -> bool:
        # 容量边界：总时长达到或超过上限视为满（恰好满与超出一秒均 True）
        return self.total_seconds() >= max_seconds


@dataclass
class Item:
    # 物品（拟物音乐载体）：id 为 uuid，sides 按面 label 索引；type 为 ItemType 实例
    name: str
    type: ItemType
    cover_source: str = "placeholder"
    cover_path: str = ""
    tag: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat(timespec="seconds")
    )
    play_count: int = 0
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sides: dict[str, Side] = field(default_factory=dict)
    missing_tracks: set[str] = field(default_factory=set)

    def all_tracks(self) -> list[Track]:
        # 全部面曲目按面顺序展平（A 面在前，B 面在后）
        return [t for side in self.sides.values() for t in side.tracks]

    def total_seconds(self) -> float:
        # 物品全部曲目总时长（秒）
        return sum(t.duration_seconds for t in self.all_tracks())

    def side_for(self, label: str) -> Side | None:
        # 按面 label 取 Side（不存在返回 None）
        return self.sides.get(label)

    def bump_play_count(self) -> None:
        # 播放次数 +1（拟物唱机播放时调用）
        self.play_count += 1


# ===== modules/items/model.py 类/方法说明 =====
# ItemType(frozen dataclass): 载体类型注册（key 为 item_types.json 键）
#   from_config(key, data): 宽容解析构造（side 白名单过滤 A/B、数值弹性转换）
# Track(dataclass): 单曲（path 唯一标识；title 等可空——标签解析失败降级 empty_record）
#   from_tagging(tag, path): duck typing 取 TagData 字段（A4.1 建成后天然兼容）
#   is_missing(): Path.is_file 检测（文件被移动 → 播放时提示，不崩溃）
# Side(dataclass): 面（label + tracks）
#   total_seconds(): 时长聚合；add_track(): 仅追加；remove_track(track_id): 按 path 移除
#   is_full(max_seconds): 边界判断（>= 视为满，恰好满/超出均 True）
# Item(dataclass): 物品（uuid id、sides dict、聚合方法 all_tracks/total_seconds/side_for/bump）
#   关联配置：ItemType 由 config/static/item_types.json 装配（经 static_config）
#   设计理由：纯数据层零依赖，持久化（A6）/规则（A5）/生成（A8）均在其上
