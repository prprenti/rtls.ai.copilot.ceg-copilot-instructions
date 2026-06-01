#!/bin/bash

# Script to move home directories to alternate disk and create symlinks
# Usage: ./setup_home_symlinks.sh <disk_path>

set -e

# Directories to symlink
DIRS=(".code" ".config" ".cache" ".vscode" ".npm" ".mozilla" ".vscode-server" ".copilot")

# Function to show help
show_help() {
    cat << EOF
Setup Home Directory Symlinks
==============================

Usage: $0 <disk_path>
       $0 -help|--help|-h

Description:
    This script moves specified home directories to an alternate disk location
    and creates symbolic links in the home directory to save quota space.
    
    Directories handled: .code .config .cache .vscode .npm .mozilla

Arguments:
    <disk_path>    Path to the disk location where directories will be stored

Options:
    -help, --help, -h    Show this help message

Examples:
    $0 /nfs/site/disks/my_disk
    $0 /nfs/site/disks/ddg_store_jpkeller

Features:
    - Detects if directories are already symlinked
    - Asks for confirmation before moving existing directories
    - Handles merge conflicts if target already exists
    - Shows summary of all symlinks at completion

EOF
    exit 0
}

# Check for help flag
if [ $# -eq 1 ] && [[ "$1" =~ ^(-help|--help|-h)$ ]]; then
    show_help
fi

# Check if disk path is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <disk_path>"
    echo "Example: $0 /nfs/site/disks/my_disk"
    echo "Run '$0 -help' for more information"
    exit 1
fi

DISK_PATH="$1"

# Verify disk path exists
if [ ! -d "$DISK_PATH" ]; then
    echo "Error: Directory '$DISK_PATH' does not exist"
    exit 1
fi

# Verify disk path is writable
if [ ! -w "$DISK_PATH" ]; then
    echo "Error: Directory '$DISK_PATH' is not writable"
    exit 1
fi

echo "Setting up home directory symlinks to: $DISK_PATH"
echo "================================================"
echo ""

# Function to ask for confirmation
confirm() {
    local prompt="$1"
    local response
    read -p "$prompt [y/N]: " response
    case "$response" in
        [yY][eE][sS]|[yY]) 
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Process each directory
for dir in "${DIRS[@]}"; do
    home_path="$HOME/$dir"
    disk_dir="$DISK_PATH/$dir"
    
    echo "Processing: $dir"
    echo "  Home path: $home_path"
    echo "  Disk path: $disk_dir"
    
    # Check if path exists in home
    if [ -L "$home_path" ]; then
        # It's already a symlink
        current_target=$(readlink -f "$home_path")
        echo "  Status: Already a symlink -> $current_target"
        
        if [ "$current_target" = "$disk_dir" ]; then
            echo "  Action: Already points to correct location, skipping"
        else
            echo "  Warning: Symlink points to different location"
            old_size=$(du -sh "$current_target" 2>/dev/null | cut -f1 || echo "unknown")
            echo "  Current location size: $old_size"
            
            if confirm "  Do you want to move contents from $current_target to $disk_dir?"; then
                # Create target directory if needed
                if [ ! -d "$disk_dir" ]; then
                    mkdir -p "$disk_dir"
                    echo "  Created directory: $disk_dir"
                fi
                
                # Check if new location already has content
                if [ -d "$disk_dir" ] && [ "$(ls -A "$disk_dir" 2>/dev/null)" ]; then
                    echo "  Warning: $disk_dir already has content"
                    if confirm "  Merge contents? (existing files may be overwritten)"; then
                        cp -rf "$current_target/"* "$disk_dir/" 2>/dev/null || true
                        echo "  Merged contents from $current_target to $disk_dir"
                    else
                        echo "  Skipped content migration"
                    fi
                else
                    # Move all contents from old location to new location
                    if [ -d "$current_target" ] && [ "$(ls -A "$current_target" 2>/dev/null)" ]; then
                        mv "$current_target/"* "$disk_dir/" 2>/dev/null || true
                        mv "$current_target/".* "$disk_dir/" 2>/dev/null || true
                        echo "  Moved contents from $current_target to $disk_dir"
                    else
                        echo "  No contents to move (directory empty or inaccessible)"
                    fi
                fi
                
                # Update symlink
                rm "$home_path"
                ln -s "$disk_dir" "$home_path"
                echo "  Updated symlink: $home_path -> $disk_dir"
                
                # Optionally remove old directory
                if [ -d "$current_target" ] && [ ! "$(ls -A "$current_target" 2>/dev/null)" ]; then
                    if confirm "  Remove empty old directory $current_target?"; then
                        rmdir "$current_target" 2>/dev/null && echo "  Removed: $current_target" || echo "  Could not remove: $current_target"
                    fi
                fi
            else
                echo "  Skipped"
            fi
        fi
        
    elif [ -e "$home_path" ]; then
        # Path exists but is not a symlink (regular directory or file)
        size=$(du -sh "$home_path" 2>/dev/null | cut -f1)
        echo "  Status: Regular directory/file exists (size: $size)"
        
        if confirm "  Move contents to $disk_dir and create symlink?"; then
            # Create parent directory in disk path if needed
            mkdir -p "$DISK_PATH"
            
            # Move the directory
            if [ -d "$disk_dir" ]; then
                echo "  Warning: $disk_dir already exists"
                if ! confirm "  Merge contents? (existing files will be overwritten)"; then
                    echo "  Skipped"
                    continue
                fi
            fi

            echo "  Syncing contents to $disk_dir ..."
            mkdir -p "$disk_dir"
            rsync_errors=0
            rsync -a --ignore-errors "$home_path/" "$disk_dir/" 2>&1 \
                | grep -v '^$' | sed 's/^/    /' \
                || rsync_errors=1
            if [ $rsync_errors -ne 0 ]; then
                echo "  Warning: rsync reported errors; some files may not have copied"
            fi
            
            backup_path="${home_path}.migrate_bak_$$"
            if mv "$home_path" "$backup_path"; then
            # Create symlink
            ln -s "$disk_dir" "$home_path"
            echo "  Created symlink: $home_path -> $disk_dir"
                echo "  Cleaning up original (best-effort) ..."
                leftover=$(rm -rf "$backup_path" 2>&1) || true
                if [ -e "$backup_path" ]; then
                    echo "  Warning: Could not fully remove backup at $backup_path"
                    echo "  This is normal when files are in use (NFS locks, open apps)."
                    echo "  Re-run 'rm -rf $backup_path' after closing those applications."
                else
                    echo "  Cleanup complete"
                fi
            else
                echo "  Error: Could not rename $home_path; symlink not created."
                echo "  Contents were already copied to $disk_dir"
            fi
        else
            echo "  Skipped"
        fi
        
    else
        # Path doesn't exist in home
        echo "  Status: Does not exist in home directory"
        
        # Create directory on disk if it doesn't exist
        if [ ! -d "$disk_dir" ]; then
            mkdir -p "$disk_dir"
            echo "  Created directory: $disk_dir"
        fi
        
        # Create symlink
        ln -s "$disk_dir" "$home_path"
        echo "  Created symlink: $home_path -> $disk_dir"
    fi
    
    echo ""
done

echo "================================================"
echo "Setup complete!"
echo ""
echo "Summary of symlinks:"
for dir in "${DIRS[@]}"; do
    if [ -L "$HOME/$dir" ]; then
        target=$(readlink -f "$HOME/$dir")
        echo "  $dir -> $target"
    fi
done
