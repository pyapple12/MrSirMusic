# 已知问题与增强备忘（y.problem.md）

> **文件职责**（2026-11-05 对齐 CapsulePulse 范本）：问题与远期改进的备忘录——**只增不删、编号递增**（解决后不删条目，在任务清单闭环时回改状态）；条目被任务清单以 `[problems#N]` 引用。
> 目的：记录已发现但不属于当前阶段范围的问题/增强项，供未来评估
> 记录格式：状态 [✅ 已完成 / 📌 待评估] / 来源（讨论日期/场景）；编号延续既有 P 前缀序列（P1、P2 → P3…）

---

## 已完成

### P1. Skill 体系补全：plan-task 与 prune-docs 设计（2026-08-14 讨论）

- **状态**：✅ 已完成（2026-08-15 创建落地）
- **来源**：2026-08-14 用户提出——"目前 skills 只涵盖审计到生成 plan 和 todolist 的，还没有根据讨论内容生成对应 plan 和 todolist 的 skill，以及精简 progress.md 和 plan.md 的 skill"
- **现状（已有三个 skill 的闭环）**：
  - `audit-project`：只读全量审计，输出 P0-P3 修复清单（不修改代码）
  - `audit-report`：审计归档——报告写入 z.plan.md 附录 A{NNN} + 修复 todo 写入 x.progress.md（字母系列延续，含简单修复方案）
  - `progress-task`：按 progress.md 章节执行任务（研究 → todo → 检验方案 → 执行 → 验证 → 勾选）
  - 覆盖范围：仅"审计驱动"的开发循环，日常功能讨论无法沉淀为方案/清单
- **缺口一：讨论 → plan/todolist 生成 skill（暂名 `plan-task`）**
  - 场景：日常讨论（版本规则、git 设定、功能设计等）→ 沉淀为 z.plan.md 方案章节 + x.progress.md 任务清单
  - 设计草案：询问环节（章节位置/清单系列字母/粒度）→ 写入 z.plan.md → 写入 x.progress.md（格式对齐 A 系列 `- [ ] X0.1 标题 —— 做法；验证：`）→ 汇报
- **缺口二：精简 progress.md / plan.md skill（暂名 `prune-docs`）**
  - 场景：z.plan.md 附录越积越多、x.progress.md 历史清单越来越长 → 归档压缩
  - 设计草案：分析现状 → 询问压缩方式（折叠一行摘要/移入历史归档区/删除）→ 执行（保留编号与结论，删除过程细节）→ 汇报 + 提醒 git commit
  - 依据：文档在 git 版本控制中，历史可回溯，可大胆压缩
- **编号协调问题（已解决，2026-08-14）**：
  - 用户定案：任务清单编号（x.progress.md 章节）为**全局单一递增序列，不分开发/审计**——每次新增清单（无论审计修复还是正常任务）都在**前一个清单基础上 +1**；开发任务 A 系列之后第一个审计清单从 B 起，后续 B→C→D…依次延续
  - 审计报告（z.plan.md 附录）独立递增：A001→A002→A003…
  - 落地：audit-report 取号规则维持"最后字母 +1"（无需改动）；当前已用 A001（第 1 轮审计报告）/ B（第 1 轮修复任务清单）
- **落地记录（2026-08-15）**：
  - `plan-task` / `prune-docs` 已创建（流程经 skillforge 质量审计 PASS；初版建于 .opencode/skills/，2026-11-07 随技能库收录迁入 `.agents/skills/`，.opencode 旧副本已删除）
  - 编号规则补充定案：z.plan 方案章节用 **PL001 起递增**（与审计附录 A{NNN}、核心机制 1/2/3 三轨并存）
  - prune-docs 执行标准：参照 z.plan.md"观察项豁免定案清单"压缩模板（汇总提炼/权威源声明/原始记录不保留/防重复记账）
  - 用户裁决：命名维持项目惯例（动词开头）、单文件结构（无 README/templates），与既有 3 个 skill 一致

---

## 待评估 / 待实施

3. **播放计数功能决策（✅ 已拍板：方案 A 接线，PATCH003 落地）**（2026-11-06 📌 → 2026-11-08 ✅）：

原问题：`Item.play_count` 字段与 `items.play_count` 列自 A6 建成起全链零写入点（播放计数恒 0）。FIX006.13（A006-P3-⑨）按默认决策移除了死写链（bump_play_count 方法 + update_item 的 play_count 写回）；字段与列保留读兼容（schema 不动）。

拍板与落地（2026-11-08）：用户裁决 **方案 A 补接线**——`sidecar/app.py` Session 以 TRACK_CHANGED 驱动回写（`repository.increment_play_count` SQL 单列原子自增 + 会话缓存同步；载入首曲/自动切曲/手动切曲/翻面各计一次，暂停恢复与 seek 不计），Web 详情面板加回"播放次数"行；口径与本章方案 A 草案字面（"ended 或手动切曲完成"计）的偏差如实注记于 z.plan 附录 PATCH003（改"曲目开始"计——单点判定、防恢复/seek 重复计数）。计数写库失败降级登记 AGENTS 容错登记制。方案 B（迁移 v2 删列）不再需要。

4. **Tauri 打包发布线（0.2 迁移完成后启动）**（2026-11-07 📌 待评估）[problems#4]：

范围：PyInstaller 打 sidecar exe（PySide6+mutagen 捆绑；已知坑：隐藏 DLL 导入、体积预期 60–100MB）→ Tauri externalBin 接线替换 dev spawn + NSIS 安装包 + 自动更新与代码签名评估。触发条件：PL010 迁移收官、parity 稳定后单独立项（发布线 PL）。来源：PL006-PL010 立项讨论（用户定案 0.2 不含打包）。

6. **Web Audio 直驱播放评估（0.3 优化线）**（2026-11-07 📌 待评估）[problems#6]：

0.2 定案播放留在 sidecar（QMediaPlayer 特许随进程）。0.3 评估移入 webview：HTML5 Audio（解码白嫖浏览器）+ Web Audio API（scratch/可视化潜力）——收益 = sidecar 摘除 PySide6（体积与打包复杂度大降）；风险 = 引擎七轮审计语义（pending_seek/缺失处理/seek_side）重写回归，需 parity 清单全套护航。
