# 标签解析统一结构（A4.1）：TagData 纯数据 dataclass，embedded_cover 预留可选字段

from dataclasses import dataclass


@dataclass
class TagData:
    # 单曲标签解析结果（统一结构，跨格式归一）；embedded_cover 预留（A7 封面服务需要时提取）
    title: str = ""
    artist: str = ""
    album: str = ""
    duration_seconds: float = 0.0
    format: str = ""
    embedded_cover: bytes | None = None


# ===== modules/tagging/tag_data.py 类说明 =====
# TagData(dataclass): 标签解析统一输出结构
#   字段：title/artist/album（文本元数据，空串表示缺失）、duration_seconds（秒）、
#     format（扩展名，如 mp3/flac）、embedded_cover（可选封面 bytes，第一版不提取，预留）
#   设计理由：跨格式（ID3/FLAC/MP4/WAVE）字段归一，下游（Track.from_tagging）只认此结构
#   关联配置：无（纯数据层）
