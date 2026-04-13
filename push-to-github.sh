#!/bin/bash
# SWAP Report - Auto-push to GitHub Pages
# This script copies the latest index.html to the local git repo and pushes.
# Runs via launchd ~15 min after the scheduled SWAP Report task.

# --- CONFIGURATION (edit these) ---
GITHUB_USERNAME="stevennolanjr-dev"
REPO_NAME="swap-report"
GDRIVE_SOURCE="$HOME/Library/CloudStorage/GoogleDrive-steven.nolan.jr@gmail.com/My Drive/zz - Claude Working Stuff/SWAP-Report/index.html"
LOCAL_REPO="$HOME/Documents/swap-report"
# --- END CONFIGURATION ---

LOG="$LOCAL_REPO/push.log"

echo "$(date): SWAP Report push starting" >> "$LOG"

# Check if source file exists
if [ ! -f "$GDRIVE_SOURCE" ]; then
    echo "$(date): ERROR - Source file not found: $GDRIVE_SOURCE" >> "$LOG"
    exit 1
fi

# Check if source file was modified in the last 2 hours (i.e., fresh report)
if [ "$(uname)" = "Darwin" ]; then
    FILE_AGE=$(( $(date +%s) - $(stat -f %m "$GDRIVE_SOURCE") ))
else
    FILE_AGE=$(( $(date +%s) - $(stat -c %Y "$GDRIVE_SOURCE") ))
fi

if [ "$FILE_AGE" -gt 7200 ]; then
    echo "$(date): SKIP - Source file is $(($FILE_AGE / 60)) min old (>2hr). No fresh report." >> "$LOG"
    exit 0
fi

# Copy to local repo
cp "$GDRIVE_SOURCE" "$LOCAL_REPO/index.html"

# Push to GitHub
cd "$LOCAL_REPO" || exit 1

# Configure git if needed
git config user.email "steven.nolan.jr@gmail.com" 2>/dev/null
git config user.name "SWAP Report" 2>/dev/null

git add index.html
git commit -m "SWAP Report $(date '+%Y-%m-%d %H:%M CT')" >> "$LOG" 2>&1

if [ $? -eq 0 ]; then
    git push origin main >> "$LOG" 2>&1
    if [ $? -eq 0 ]; then
        echo "$(date): SUCCESS - Pushed to GitHub Pages" >> "$LOG"
    else
        echo "$(date): ERROR - git push failed" >> "$LOG"
    fi
else
    echo "$(date): SKIP - No changes to commit" >> "$LOG"
fi
