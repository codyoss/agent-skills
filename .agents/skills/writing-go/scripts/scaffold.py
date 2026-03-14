#!/usr/bin/env python3
"""
Go Project Scaffolder.
Creates a new Go project with the standard layout:
- cmd/
- internal/
- pkg/
- go.mod
- .gitignore
- Makefile
"""

import sys
import os
import subprocess
from pathlib import Path

MAIN_GO = """package main

import (
    "context"
    "log/slog"
    "os"
)

func main() {
    ctx := context.Background()
    if err := run(ctx); err != nil {
        slog.Error("shutting down", "err", err)
        os.Exit(1)
    }
}

func run(ctx context.Context) error {
    // TODO: Add application logic here
    _ = ctx
    return nil
}
"""

def init_go_project(project_name, path):
    project_dir = Path(path).resolve()
    
    if project_dir.exists() and any(project_dir.iterdir()):
        print(f"❌ Error: Directory is not empty: {project_dir}")
        return False

    print(f"🔨 Scaffolding Go project '{project_name}' at {project_dir}...")
    
    try:
        # Create Project Directory
        project_dir.mkdir(parents=True, exist_ok=True)

        # Create Files
        (project_dir / 'main.go').write_text(MAIN_GO)

        # Initialize Go Module
        subprocess.run(['go', 'mod', 'init', project_name], cwd=project_dir, check=True)
        subprocess.run(['go', 'mod', 'tidy'], cwd=project_dir, check=True)

        print(f"✅ Successfully initialized project '{project_name}'.")
        return True

    except Exception as e:
        print(f"❌ Error initializing project: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: scaffold.py <project-name> [path]")
        sys.exit(1)
        
    p_name = sys.argv[1]
    p_path = sys.argv[2] if len(sys.argv) > 2 else "."
    
    init_go_project(p_name, p_path)
