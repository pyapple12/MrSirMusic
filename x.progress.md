# MrSirMusic 开发任务清单

- 任务清单定稿：2026-08-14
- 依据：z.plan.md（MrSirMusic 项目方案 v1.0）
- 编号：A 系列（新项目首轮），组号 = 开发阶段，组内条目 `A{组}.{序号}`
- 约定：全部验证命令在项目根目录、`.venv` 解释器下执行；GUI 验证用 `QT_QPA_PLATFORM=offscreen` 免弹窗；正式文件注释禁止 `.reference/` 标注

> 文件职责（2026-11-05 对齐 CapsulePulse 范本）：任务清单与进度追踪，与 `z.plan.md` 配套——方案在 z.plan 附录展开，执行拆条在本文件勾选。结构：**`## 已完成 ✅` 区在前、`### FIX007: 第 7 轮审计修复 [audit#A007] ✅

> 结果：6 条 P 级全部落地；全量 14 探针 PASS + --version 0.1.4；反向验收（playbackState StoppedState 断言即原问题对照）。来源 z.plan.md 附录 A007。
> 编号备注：A007/FIX007 同号绑定对齐轮次（恰为 max+1，无例外）；A006 观察项未提升，float 截断维持"需定案"标记。

- [x] FIX007.1 [P2] load_item 缺失分支停声 —— `modules/playback/engine.py` `load_item` 缺失 elif 分支（file_missing 预检块内）补 `if self._player is not None: self._player.stop()`（与 FIX006.3 同构；player 已在 :157 ensure）；验证：a9 追加断言（真音频 playing → load_item 缺失首曲物品 → 旧媒体停声/stopped 保持，扬声器不再出声）（2026-11-05 已验证：缺失 elif 分支补 player.stop()（与 FIX006.3 同构）——a9 真音频 playing 载缺失物品 → stopped 且 playbackState StoppedState）
- [x] FIX007.2 [P3] pending_seek 跨换源竞态 —— `engine.py` `play_next`/`play_prev`/`flip` 三入口进入时补 `self._pending_seek = None`（勿在 `_play_current` 内清防误杀合法挂起）；`stop()` 维持不清并在 seek_side 说明区记录"续播点即用户意图"语义决策；验证：a9 追加断言（seek_side 跨曲挂起后立即 play_prev → pending 为 None）（2026-11-05 已验证：play_next/play_prev/flip 三入口补 _pending_seek = None（_play_current 内不清防误杀）——a9 置 pending 后 play_prev → None）
- [x] FIX007.3 [P3] cover/providers 断环残留清理 —— `_build_registry` 两条函数内 import 提升顶部（环已断无依据）；删 `COVERS_DIR` re-export（全仓零消费，CoverProvider 保留供注解）+ 说明区 :46 口径同步；a7 探针核查 re-export 断言（如有一并适配）；验证：冒烟 + a7/a8 回归 + grep 零消费（2026-11-05 已验证：_build_registry import 提升顶部 + 删 COVERS_DIR 零消费 re-export + 说明区口径同步；a7 探针改引 cover.base——a7/a8 回归过）
- [x] FIX007.4 [P3] deck_view 秒→毫秒收敛 —— `ui/views/deck_view.py:193-195` 改引 `utils.convert.ms_from_seconds`（删内联 int(...*1000)）；验证：a11 桥绑定回归 + 冒烟（2026-11-05 已验证：_on_track 改引 utils.convert.ms_from_seconds——a11 回归过）
- [x] FIX007.5 [P3] FIX006 残留文档组 —— ① `model.py:122` 说明区删 remove_track 条目；② `model.py:124` 删"bump"字样；③ `factory.py:1` 头注改"创建空物品"；④ `edit.py:53` 说明区改"内联移除 + check_item 拒绝回滚 + save_item"；⑤ `repository.py:227` 尾注去"播放次数"；⑥ `progress_widget.py:82` 说明区改"scrub 中滑条与时间均挂起"；验证：grep 五文件无残留 + 冒烟（2026-11-05 已验证：文档残留 5 处全部如实化（model×2/factory 头注/edit 幽灵符号/repository 尾注/progress_widget 说明区）——grep 无残留）
- [x] FIX007.6 [P3] 不可达分支清理 —— `static_config.py:179-180` 删非 dict continue 双保险分支（上游 values_must_be_dict 已保证）；验证：a1 shape 校验断言原样过 + 冒烟（2026-11-05 已验证：_sanitize_item_types 非 dict continue 删除——a1 shape 校验断言原样过）
- [x] FIX007.7 验证收尾 —— 全量 14 探针（offscreen）+ 冒烟 + `--version` 0.1.4 一致 + a9 重点核对（FIX007.1/2 断言）+ 反向验收（原问题"旧媒体不停声"→验收"缺失载入后停声"）；结论如实回写勾选注记（2026-11-05 已验证：全量 14 探针 PASS + 冒烟 + --version 0.1.4 + 反向验收（playbackState StoppedState 断言即原问题对照））

## 未完成

（暂无条目——FIX007 已收官，下一批方案走 plan-task 流程立项）
