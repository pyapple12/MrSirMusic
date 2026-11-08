// MrSirMusic Tauri 壳（PL007）：窗口 + 侧车 IPC 桥——业务全部在 Python sidecar，本壳零业务
mod sidecar;

use sidecar::{start_sidecar, kill_child, SidecarState};

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .manage(SidecarState::default())
        .invoke_handler(tauri::generate_handler![sidecar::sidecar_cmd])
        .setup(move |app| {
            // 启动即拉起侧车（dev spawn venv python；崩溃重启×3 在 sidecar.rs 泵循环内）
            start_sidecar(app.handle().clone());
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("Tauri 应用构建失败")
        .run(|app_handle, event| {
            // 退出清理：杀侧车进程（engine.stop 由 sidecar 自己的 stdin EOF 收尾）
            if let tauri::RunEvent::Exit = event {
                kill_child(app_handle);
            }
        })
}
