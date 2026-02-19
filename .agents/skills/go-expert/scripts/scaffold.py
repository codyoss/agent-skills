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

STANDARD_GITIGNORE = """# Binaries for programs and plugins
*.exe
*.exe~
*.dll
*.so
*.dylib

# Test binary, built with `go test -c`
*.test

# Output of the go coverage tool, specifically when used with LiteIDE
*.out

# Dependency directories (remove the comment below to include it)
# vendor/
"""

STANDARD_MAKEFILE = """.PHONY: all build test clean

APP_NAME := {app_name}

all: build test

build:
	go build -o bin/$(APP_NAME) ./cmd/$(APP_NAME)

test:
	go test ./...

clean:
	rm -rf bin/
"""

MAIN_GO = """package main

import "fmt"

func main() {
	fmt.Println("Hello, World!")
}
"""

def init_go_project(project_name, path):
    project_dir = Path(path).resolve()
    
    if project_dir.exists() and any(project_dir.iterdir()):
        print(f"❌ Error: Directory is not empty: {project_dir}")
        return False

    print(f"🔨 Scaffolding Go project '{project_name}' at {project_dir}...")
    
    try:
        # Create Directories
        (project_dir / 'cmd' / project_name).mkdir(parents=True, exist_ok=True)
        (project_dir / 'internal').mkdir(exist_ok=True)
        (project_dir / 'pkg').mkdir(exist_ok=True)
        
        # Create Files
        (project_dir / '.gitignore').write_text(STANDARD_GITIGNORE)
        (project_dir / 'Makefile').write_text(STANDARD_MAKEFILE.format(app_name=project_name))
        (project_dir / 'cmd' / project_name / 'main.go').write_text(MAIN_GO)

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
