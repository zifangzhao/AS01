#!/bin/bash
# =============================================================================
# Bootstrap Script for CereLoop / AS01 Sorting Server
# Installs git, clones the repo, and launches the full installer
# =============================================================================

REPO_URL="https://github.com/zifangzhao/AS01.git"
REPO_DIR="AS01"
INSTALLER="AutoInstall_full.sh"

echo "============================================="
echo "  CereLoop Bootstrap"
echo "============================================="
echo "Started: $(date)"
echo ""

# ---------------------------------------------------------------------------
# 1. Install git if not present
# ---------------------------------------------------------------------------
if ! command -v git &>/dev/null; then
    echo "[1/3] Installing git..."
    sudo apt update -qq
    if ! sudo apt install git -y; then
        echo "  [ERROR] Failed to install git. Aborting."
        exit 1
    fi
    echo "  [OK] git installed"
else
    echo "[1/3] git already installed ($(git --version))"
fi
echo ""

# ---------------------------------------------------------------------------
# 2. Clone the repository
# ---------------------------------------------------------------------------
echo "[2/3] Cloning repository from $REPO_URL ..."
if [ -d "$REPO_DIR" ]; then
    echo "  Directory '$REPO_DIR' already exists — pulling latest changes..."
    cd "$REPO_DIR"
    if ! git pull; then
        echo "  [ERROR] git pull failed. Aborting."
        exit 1
    fi
    cd ..
else
    if ! git clone "$REPO_URL" "$REPO_DIR"; then
        echo "  [ERROR] git clone failed. Aborting."
        exit 1
    fi
fi
echo "  [OK] Repository ready at ./$REPO_DIR"
echo ""

# ---------------------------------------------------------------------------
# 3. Run the full installer
# ---------------------------------------------------------------------------
echo "[3/3] Launching $INSTALLER ..."
INSTALLER_PATH="./$REPO_DIR/$INSTALLER"

if [ ! -f "$INSTALLER_PATH" ]; then
    echo "  [ERROR] $INSTALLER not found at $INSTALLER_PATH"
    echo "  Make sure the file exists in the root of the repository."
    exit 1
fi

chmod +x "$INSTALLER_PATH"
cd "$REPO_DIR"

if ! bash "$INSTALLER"; then
    echo ""
    echo "  [ERROR] $INSTALLER exited with errors. Check the log file above."
    exit 1
fi