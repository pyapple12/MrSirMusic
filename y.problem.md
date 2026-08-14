# 已知问题与增强备忘（y.problem.md）

> 目的：记录已发现但不属于当前阶段范围的问题/增强项，供未来评估
> 记录格式：状态 [✅ 已完成 / 📌 待评估] / 来源（讨论日期/场景）

---

## 待评估 / 待实施

### P1. Skill 体系补全：plan-task 与 prune-docs 设计（2026-08-14 讨论）

- **状态**：📌 待处理（后续讨论设计）
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
- **编号协调问题（待拍板）**：
  - audit-report 取号规则为"x.progress.md 中 `^## [A-Z]\.` 最后字母 +1"，但本项目 A0-A9/B0-B4 为开发阶段编号（格式 `## A0.`），字母被占
  - 建议：开发任务固定用 A/B 系列（第一版），审计修复清单从 C 系列起（C=一轮审计、D=二轮…），audit-report 取号规则跳过已占用字母
- **触发条件**：后续处理（与 A 系列开发并行或完成后均可）
