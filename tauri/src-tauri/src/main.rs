// MrSirMusic Tauri 壳入口（PL007.2）：debug 构建带控制台（看诊断），release 隐藏控制台
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    mrsirmusic_lib::run()
}
