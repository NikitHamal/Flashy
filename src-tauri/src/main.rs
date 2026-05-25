#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use tauri::api::process::Command;
use tauri::Manager;

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            let _app_handle = app.handle();
            
            // Spawn backend sidecar
            tauri::async_runtime::spawn(async move {
                let (mut rx, _child) = Command::new_sidecar("flashy-backend")
                    .expect("failed to configure sidecar")
                    .spawn()
                    .expect("failed to spawn sidecar");

                // Stream backend stdout/stderr to terminal
                while let Some(event) = rx.recv().await {
                    match event {
                        tauri::api::process::CommandEvent::Stdout(line) => {
                            println!("[Backend]: {}", line);
                        }
                        tauri::api::process::CommandEvent::Stderr(line) => {
                            eprintln!("[Backend Error]: {}", line);
                        }
                        _ => {}
                    }
                }
            });

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
