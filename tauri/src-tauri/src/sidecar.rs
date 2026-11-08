// 侧车 IPC 桥（PL007.3）：dev spawn venv python -m sidecar + stdio JSON Lines 泵 + id 关联应答 + 崩溃重启×3
// 线程模型：泵循环跑在 tauri async_runtime（tokio）；命令经 mpsc 关联应答（60s 超时）；事件 emit 给前端
// 容错登记（AGENTS）：IPC 超时 60s 降级 / 侧车崩溃指数退避重启×3 / ready 前调用收敛超时错误

use serde_json::Value;
use std::collections::HashMap;
use std::path::PathBuf;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{mpsc, Mutex};
use std::time::Duration;
use tauri::{AppHandle, Emitter, Manager, State};
use tauri_plugin_shell::process::{CommandChild, CommandEvent};
use tauri_plugin_shell::ShellExt;

const EVENT_WIRE: &str = "sidecar://event"; // 侧车协议事件 → 前端 listen("sidecar://event")
const EVENT_DEAD: &str = "sidecar://dead"; // 重启耗尽 → 前端错误横幅
const MAX_RESTARTS: u32 = 3; // 崩溃后重启次数上限（第 4 次死亡发 dead）
const REQUEST_TIMEOUT: Duration = Duration::from_secs(60); // IPC 应答超时（generate 标签解析耗时较长）

pub struct SidecarState {
    next_id: AtomicU64,
    pending: Mutex<HashMap<u64, mpsc::Sender<Value>>>,
    child: Mutex<Option<CommandChild>>,
}

impl Default for SidecarState {
    fn default() -> Self {
        Self {
            next_id: AtomicU64::new(0),
            pending: Mutex::new(HashMap::new()),
            child: Mutex::new(None),
        }
    }
}

// 从当前 exe 向上找项目根（dev 模式 exe 在 src-tauri/target/debug——锚点 = .venv/Scripts/python.exe）
fn find_project_root() -> Option<PathBuf> {
    let mut dir = std::env::current_exe().ok()?.parent()?.to_path_buf();
    loop {
        if dir.join(".venv").join("Scripts").join("python.exe").is_file() {
            return Some(dir);
        }
        dir = dir.parent()?.to_path_buf();
    }
}

enum PumpOutcome {
    Crash(String), // 进程退出/管道错误（含 stdout 流意外关闭）
}

// 单轮泵：spawn 侧车 → 写入 child 引用 → 消费 stdout 行（事件转发/应答关联）直到进程终止
async fn pump_once(app: &AppHandle) -> PumpOutcome {
    let state = app.state::<SidecarState>();
    let root = match find_project_root() {
        Some(root) => root,
        None => return PumpOutcome::Crash("未找到项目根（缺 .venv/Scripts/python.exe）".into()),
    };
    let python = root.join(".venv").join("Scripts").join("python.exe");
    let (mut rx, child) = match app
        .shell()
        .command(python.to_string_lossy().to_string())
        .args(["-m", "sidecar"])
        .current_dir(root.clone())
        .spawn()
    {
        Ok(pair) => pair,
        Err(reason) => return PumpOutcome::Crash(format!("侧车 spawn 失败: {reason}")),
    };
    *state.child.lock().unwrap() = Some(child);
    _logger_info("侧车已拉起");

    while let Some(event) = rx.recv().await {
        match event {
            CommandEvent::Stdout(bytes) => {
                let line = String::from_utf8_lossy(&bytes).trim().to_string();
                if line.is_empty() {
                    continue;
                }
                let msg: Value = match serde_json::from_str(&line) {
                    Ok(value) => value,
                    Err(_) => continue, // 非 JSON 行（理论上不可能——协议流纪律）静默丢弃
                };
                if let Some(evt) = msg.get("event").cloned() {
                    // 侧车协议事件 → 前端
                    let _ = app.emit(EVENT_WIRE, serde_json::json!({"event": evt, "data": msg.get("data")}));
                } else if let Some(id) = msg.get("id").and_then(Value::as_u64) {
                    // 应答 → id 关联_sender 落空即丢弃（超时已清理）
                    let sender = state.pending.lock().unwrap().remove(&id);
                    if let Some(tx) = sender {
                        let _ = tx.send(msg);
                    }
                }
            }
            CommandEvent::Stderr(_) => {} // 日志/诊断走 stderr——协议流纪律，丢弃不转发
            CommandEvent::Terminated(payload) => {
                return PumpOutcome::Crash(format!("侧车进程退出（code={:?}）", payload.code))
            }
            CommandEvent::Error(reason) => return PumpOutcome::Crash(format!("管道错误: {reason}")),
            _ => {} // CommandEvent 标注 non_exhaustive（上游可增变体）——兜底忽略
        }
    }
    PumpOutcome::Crash("侧车 stdout 流关闭".into())
}

fn _logger_info(message: &str) {
    eprintln!("[sidecar.rs] {message}"); // 壳诊断走 stderr（窗口 debug 构建可见）
}

// 侧车生命周期：spawn → 崩溃即指数退避（1s/2s/4s）重启 → 超 MAX_RESTARTS 发 dead
pub fn start_sidecar(app: AppHandle) {
    let _join = tauri::async_runtime::spawn(async move {
        let mut attempt: u32 = 0;
        loop {
            attempt += 1;
            match pump_once(&app).await {
                PumpOutcome::Crash(reason) => {
                    let state = app.state::<SidecarState>();
                    // 清空未决请求（全部以 internal 落空——重启后前端可重试）
                    {
                        let mut pending = state.pending.lock().unwrap();
                        for (_, tx) in pending.drain() {
                            let _ = tx.send(serde_json::json!({
                                "ok": false,
                                "error": {"category": "internal", "message": "侧车进程退出，请求未完成"}
                            }));
                        }
                    }
                    *state.child.lock().unwrap() = None;
                    if attempt > MAX_RESTARTS {
                        _logger_info("侧车重启次数耗尽，发 dead 事件");
                        let _ = app.emit(EVENT_DEAD, serde_json::json!({"attempts": attempt, "reason": reason}));
                        break;
                    }
                    let backoff = Duration::from_millis(1000u64 << (attempt - 1)); // 1s/2s/4s
                    _logger_info(&format!(
                        "侧车崩溃（{reason}），{backoff:?} 后第 {attempt}/{MAX_RESTARTS} 次重启"
                    ));
                    tokio::time::sleep(backoff).await;
                }
            }
        }
    });
}

// 退出清理（lib.rs RunEvent::Exit 调用）：杀侧车进程——sidecar 检测 stdin EOF 自行优雅退出
pub fn kill_child(app: &AppHandle) {
    let state = app.state::<SidecarState>();
    let mut guard = state.child.lock().unwrap();
    if let Some(child) = guard.take() {
        let _ = child.kill();
    }
}

// 前端命令转发：自增 id → stdin 写行 → mpsc 等应答（60s 超时）→ ok 拆 result / 非 ok 抛错误串
#[tauri::command]
pub fn sidecar_cmd(
    state: State<'_, SidecarState>,
    cmd: String,
    params: Value,
) -> Result<Value, String> {
    let id = state.next_id.fetch_add(1, Ordering::SeqCst) + 1;
    let (tx, rx) = mpsc::channel();
    state.pending.lock().unwrap().insert(id, tx);
    let line = serde_json::json!({"id": id, "cmd": cmd, "params": params}).to_string() + "\n";
    let write_result = {
        let mut guard = state.child.lock().unwrap();
        match guard.as_mut() {
            Some(child) => child
                .write(line.as_bytes())
                .map_err(|reason| format!("侧车写入失败: {reason}")),
            None => Err("侧车未运行（启动中或已死亡）".to_string()),
        }
    };
    if let Err(reason) = write_result {
        state.pending.lock().unwrap().remove(&id);
        return Err(reason);
    }
    let response = match rx.recv_timeout(REQUEST_TIMEOUT) {
        Ok(message) => message,
        Err(_) => {
            state.pending.lock().unwrap().remove(&id);
            return Err("侧车响应超时（60s）".to_string());
        }
    };
    match response.get("ok") {
        Some(Value::Bool(true)) => Ok(response.get("result").cloned().unwrap_or(Value::Null)),
        _ => Err(response
            .get("error")
            .cloned()
            .map(|err| err.to_string())
            .unwrap_or_else(|| response.to_string())),
    }
}

// ===== sidecar.rs 模块说明 =====
// SidecarState: 原子请求 id + pending 应答表（mpsc Sender）+ child 写柄（Mutex）
// find_project_root(): exe 向上锚定 .venv/Scripts/python.exe（dev 模式 exe 在 src-tauri/target/debug）
// pump_once(): 单轮 spawn + 行消费（事件→emit / 应答→id 关联；stderr 丢弃=协议流纪律）
// start_sidecar(): 泵循环 + 指数退避重启×3（1s/2s/4s）+ 超限 dead 事件 + 未决请求 internal 落空
// kill_child(): 退出清理（RunEvent::Exit）——侧车 stdin EOF 自行优雅退出
// sidecar_cmd(): 前端 invoke 入口（60s 超时；ok 拆 result，错误串回传前端 toast）
//   设计理由：业务零进壳（全部转发 Python sidecar）；id 关联 + Mutex 避免竞态；
//     重启上限防无限循环；事件 wire 名 sidecar://event 与前端 ipc.ts 单源约定
//   关联配置：tauri.conf.json（devUrl/窗口）；.venv 路径锚点；PL006 协议信封
