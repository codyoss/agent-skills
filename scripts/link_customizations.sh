#!/usr/bin/env bash
set -euo pipefail

# Get repository root
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

AGENTS_SRC="$REPO_ROOT/.agents/agents"
SKILLS_SRC="$REPO_ROOT/.agents/skills"
PLUGINS_SRC="$REPO_ROOT/plugins"

CONFIG_DIR="$HOME/.gemini/config"
AGENTS_DST="$CONFIG_DIR/agents"
SKILLS_DST="$CONFIG_DIR/skills"
PLUGINS_DST="$CONFIG_DIR/plugins"

DRY_RUN=false
ACTION="link"

usage() {
    echo "Usage: $0 [link|unlink] [options]"
    echo ""
    echo "Actions:"
    echo "  link      Create symlinks for agents, skills, and plugins (default)"
    echo "  unlink    Remove symlinks for agents, skills, and plugins"
    echo ""
    echo "Options:"
    echo "  -d, --dry-run        Show what would be done without making changes"
    echo "  -h, --help           Show this help message"
    exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        link|unlink)
            ACTION="$1"
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

setup_link() {
    local src="$1"
    local dst="$2"

    echo "Linking $src -> $dst..."

    if [ "$DRY_RUN" = true ]; then
        echo "  [Dry Run] Would create symlink: $dst -> $src"
        return
    fi

    # Create destination parent directory if it doesn't exist
    local dst_parent
    dst_parent="$(dirname "$dst")"
    if [ ! -d "$dst_parent" ]; then
        echo "  Creating directory: $dst_parent"
        mkdir -p "$dst_parent"
    fi

    # Handle existing target
    if [ -L "$dst" ] || [ -e "$dst" ]; then
        if [ -L "$dst" ]; then
            local current_target
            current_target="$(readlink "$dst")"
            if [ "$current_target" = "$src" ]; then
                echo "  Link already exists and is correct."
                return
            else
                echo "  Removing incorrect symlink (pointed to $current_target)..."
                rm "$dst"
            fi
        else
            local bak_path="${dst}.bak"
            echo "  WARNING: $dst already exists and is not a symlink. Backing up to $bak_path..."
            if [ -e "$bak_path" ]; then
                rm -rf "$bak_path"
            fi
            mv "$dst" "$bak_path"
        fi
    fi

    # Create symlink
    ln -s "$src" "$dst"
    echo "  Created symlink successfully."
}

remove_link() {
    local dst="$1"

    if [ -L "$dst" ]; then
        echo "Removing symlink: $dst"
        if [ "$DRY_RUN" = false ]; then
            rm "$dst"
        fi
    elif [ -e "$dst" ]; then
        echo "Skipping non-symlink target: $dst"
    fi
}

process_dir() {
    local src_dir="$1"
    local dst_dir="$2"

    if [ ! -d "$src_dir" ]; then
        echo "Source directory $src_dir does not exist. Skipping."
        return
    fi

    # Find directories and files in the source, excluding dotfiles/folders
    find "$src_dir" -mindepth 1 -maxdepth 1 ! -name ".*" | while read -r item_src; do
        local item
        item="$(basename "$item_src")"
        local item_dst="$dst_dir/$item"

        if [ "$ACTION" = "link" ]; then
            setup_link "$item_src" "$item_dst"
        elif [ "$ACTION" = "unlink" ]; then
            remove_link "$item_dst"
        fi
    done
}

ACTION_CAP="$(echo "${ACTION:0:1}" | tr '[:lower:]' '[:upper:]')${ACTION:1}"
echo "=== ${ACTION_CAP}ing Antigravity Customizations ==="
if [ "$DRY_RUN" = true ]; then
    echo "*** DRY RUN MODE - No changes will be written ***"
fi

process_dir "$AGENTS_SRC" "$AGENTS_DST"
process_dir "$SKILLS_SRC" "$SKILLS_DST"
process_dir "$PLUGINS_SRC" "$PLUGINS_DST"

echo "Done!"
