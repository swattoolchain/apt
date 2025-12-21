// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::Command;
use tauri::Manager;

#[tauri::command]
fn run_pytest(test_file: String) -> Result<String, String> {
    let output = Command::new("pytest")
        .arg(&test_file)
        .arg("-v")
        .output()
        .map_err(|e| e.to_string())?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);

    Ok(format!("{}\n{}", stdout, stderr))
}

#[tauri::command]
fn run_aptcli(args: Vec<String>) -> Result<String, String> {
    let output = Command::new("aptcli")
        .args(&args)
        .output()
        .map_err(|e| e.to_string())?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);

    Ok(format!("{}\n{}", stdout, stderr))
}

#[tauri::command]
fn get_test_files(directory: String) -> Result<Vec<String>, String> {
    use std::fs;
    
    let paths = fs::read_dir(&directory)
        .map_err(|e| e.to_string())?;

    let mut files = Vec::new();
    for path in paths {
        let path = path.map_err(|e| e.to_string())?;
        let file_name = path.file_name().to_string_lossy().to_string();
        if file_name.ends_with(".yml") || file_name.ends_with(".yaml") {
            files.push(path.path().to_string_lossy().to_string());
        }
    }

    Ok(files)
}

#[tauri::command]
fn read_yaml_file(file_path: String) -> Result<String, String> {
    use std::fs;
    fs::read_to_string(&file_path).map_err(|e| e.to_string())
}

#[tauri::command]
fn write_yaml_file(file_path: String, content: String) -> Result<(), String> {
    use std::fs;
    fs::write(&file_path, content).map_err(|e| e.to_string())
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            run_pytest,
            run_aptcli,
            get_test_files,
            read_yaml_file,
            write_yaml_file
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
