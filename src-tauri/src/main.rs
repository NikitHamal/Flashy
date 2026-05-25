#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use tauri::api::process::{Command, CommandEvent};

fn main() {
    tauri::Builder::default()
        .setup(|_app| {
            let (mut rx, _child) = Command::new_sidecar("flashy-backend")
                .expect("failed to configure flashy-backend sidecar")
                .spawn()
                .expect("failed to spawn flashy-backend sidecar");

            tauri::async_runtime::spawn(async move {
                while let Some(event) = rx.recv().await {
                    match event {
                        CommandEvent::Stdout(line) => {
                            println!("[Backend]: {}", line);
                        }
                        CommandEvent::Stderr(line) => {
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
