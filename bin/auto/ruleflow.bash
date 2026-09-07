#!/usr/bin/env bash
set -e

# 1. Check if uv is installed, download if missing
if ! command -v uv &> /dev/null; then
    echo "[INFO] uv not found. Downloading and installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Add default install paths to the active PATH for this session
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

    if ! command -v uv &> /dev/null; then
        echo "[ERROR] Failed to install or locate uv. Please restart your terminal."
        exit 1
    fi
fi

# 2. Check if ruleflow tool environment exists; install or check for updates
if ! uv tool list 2>/dev/null | grep -iE '^ruleflow\b' &> /dev/null; then
    echo "[INFO] ruleflow tool environment not found. Installing ruleflow..."
    if ! uv tool install --refresh ruleflow; then
        echo "[ERROR] Failed to install ruleflow."
        exit 1
    fi
else
    echo "[INFO] Checking for updates to ruleflow..."
    if ! uv tool upgrade ruleflow; then
        echo "[WARNING] Update check failed. Proceeding with existing version..."
    fi
fi

# 3. Run RuleFlow Studio
echo "[INFO] Launching RuleFlow Studio..."
uv tool run --from ruleflow studio
