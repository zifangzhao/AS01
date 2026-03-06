#!/bin/bash
# =============================================================================
# Unified Installation Script for CereLoop / AS01 Sorting Server
# Ubuntu - Single-file installer with full error reporting
# =============================================================================

# --- Logging setup -----------------------------------------------------------
LOG_FILE="./install_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1
echo "Log file: $LOG_FILE"
echo "Started: $(date)"
echo ""

# --- Error tracking ----------------------------------------------------------
ERRORS=()
WARNINGS=()

log_error() {
    local msg="$1"
    ERRORS+=("$msg")
    echo "  [ERROR] $msg" >&2
}

log_warning() {
    local msg="$1"
    WARNINGS+=("$msg")
    echo "  [WARNING] $msg"
}

log_ok() {
    echo "  [OK] $1"
}

# Run a command, log failure, but do NOT abort the whole script
run_or_error() {
    local description="$1"
    shift
    echo "  >> $description"
    if ! "$@" ; then
        log_error "$description FAILED (exit code $?)"
        return 1
    fi
    log_ok "$description"
    return 0
}

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
echo "============================================="
echo "  CereLoop / AS01 Sorting Server Installer  "
echo "============================================="
echo ""

# ---------------------------------------------------------------------------
# 1. System updates & base dependencies
# ---------------------------------------------------------------------------
echo "[1/7] Updating system packages..."
run_or_error "apt upgrade"      sudo apt -y upgrade -f -qq
run_or_error "apt fix-broken"   sudo apt -f install -y
echo ""

# ---------------------------------------------------------------------------
# 2. Install .deb packages in current directory (if any)
# ---------------------------------------------------------------------------
echo "[2/7] Installing local .deb packages..."
DEB_COUNT=0
for f in *.deb; do
    [ -e "$f" ] || continue
    [ "$f" = "teamviewer_15.5.3_amd64.deb" ] && continue  # handled in step 3
    DEB_COUNT=$((DEB_COUNT + 1))
    echo "  Installing $f ..."
    RETRIES=0
    rst=1
    while [ "$rst" -ne "0" ]; do
        RETRIES=$((RETRIES + 1))
        if [ "$RETRIES" -gt 5 ]; then
            log_error "dpkg install of $f failed after $RETRIES attempts"
            break
        fi
        sudo dpkg -i "$f"; rst=$?
        sudo apt upgrade -f -y
        sudo apt -f install -y
    done
    [ "$rst" -eq "0" ] && log_ok "$f installed"
done
[ "$DEB_COUNT" -eq "0" ] && echo "  No extra .deb packages found, skipping."
echo ""

# ---------------------------------------------------------------------------
# 3. Install TeamViewer
# ---------------------------------------------------------------------------
echo "[3/7] Installing TeamViewer..."
if [ -f "./teamviewer_15.5.3_amd64.deb" ]; then
    RETRIES=0
    rst=1
    while [ "$rst" -ne "0" ]; do
        RETRIES=$((RETRIES + 1))
        if [ "$RETRIES" -gt 5 ]; then
            log_error "TeamViewer install failed after $RETRIES attempts"
            break
        fi
        sudo dpkg -i ./teamviewer_15.5.3_amd64.deb; rst=$?
        sudo apt upgrade -f -y
        sudo apt -f install -y
    done
    if [ "$rst" -eq "0" ]; then
        run_or_error "TeamViewer daemon enable"  sudo teamviewer daemon enable
        run_or_error "TeamViewer set password"   sudo teamviewer passwd 12345678
    fi
else
    log_warning "teamviewer_15.5.3_amd64.deb not found — TeamViewer skipped"
fi
echo ""

# ---------------------------------------------------------------------------
# 4. Install system drivers
# ---------------------------------------------------------------------------
echo "[4/7] Installing system drivers..."
RETRIES=0
rst=1
while [ "$rst" -ne "0" ]; do
    RETRIES=$((RETRIES + 1))
    if [ "$RETRIES" -gt 5 ]; then
        log_error "ubuntu-drivers autoinstall failed after $RETRIES attempts"
        break
    fi
    sudo ubuntu-drivers autoinstall; rst=$?
    sudo apt upgrade -f -y
    sudo apt -f install -f -y
done
[ "$rst" -eq "0" ] && log_ok "Drivers installed"
echo ""

# ---------------------------------------------------------------------------
# 5. Install Miniconda
# ---------------------------------------------------------------------------
echo "[5/7] Installing Miniconda..."
MINICONDA_INSTALLER="Miniconda3-latest-Linux-x86_64.sh"
MINICONDA_URL="https://repo.anaconda.com/miniconda/$MINICONDA_INSTALLER"

if ! command -v conda &>/dev/null; then
    if [ ! -f "$MINICONDA_INSTALLER" ]; then
        echo "  Downloading Miniconda..."
        if ! wget -q "$MINICONDA_URL" -O "$MINICONDA_INSTALLER"; then
            log_error "Failed to download Miniconda from $MINICONDA_URL"
        fi
    fi

    if [ -f "$MINICONDA_INSTALLER" ]; then
        if run_or_error "Miniconda silent install" bash "$MINICONDA_INSTALLER" -b -p "$HOME/miniconda3"; then
            rm -f "$MINICONDA_INSTALLER"
            if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
                source "$HOME/miniconda3/etc/profile.d/conda.sh"
                run_or_error "conda init bash" conda init bash
                log_ok "Miniconda installed at $HOME/miniconda3"
            else
                log_error "Miniconda installed but conda.sh profile not found"
            fi
        else
            log_error "Miniconda installer script failed"
        fi
    else
        log_error "Miniconda installer not present — cannot continue conda setup"
    fi
else
    echo "  Conda already installed, skipping download."
    CONDA_BASE=$(conda info --base 2>/dev/null)
    if [ -n "$CONDA_BASE" ] && [ -f "$CONDA_BASE/etc/profile.d/conda.sh" ]; then
        source "$CONDA_BASE/etc/profile.d/conda.sh"
        log_ok "Existing conda sourced from $CONDA_BASE"
    else
        log_error "Could not source conda.sh from existing installation"
    fi
fi

# Configure conda mirrors (Tsinghua)
if command -v conda &>/dev/null; then
    run_or_error "conda mirror (free)"      conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
    run_or_error "conda mirror (main)"      conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
    run_or_error "conda show_channel_urls"  conda config --set show_channel_urls yes
else
    log_error "conda command not available — skipping channel configuration"
fi
echo ""

# ---------------------------------------------------------------------------
# 6. Create phy2 environment & install Python packages
# ---------------------------------------------------------------------------
echo "[6/7] Setting up phy2 conda environment..."

if ! command -v conda &>/dev/null; then
    log_error "conda not available — skipping phy2 environment setup entirely"
else
    if ! conda env list | grep -q "^phy2 "; then
        run_or_error "Create phy2 conda env" \
            conda create -n phy2 python=3.7 pip numpy matplotlib scipy \
            scikit-learn h5py cython pillow -y
    else
        log_ok "phy2 environment already exists"
    fi

    if conda activate phy2 2>/dev/null; then
        log_ok "Activated phy2 environment"
        run_or_error "pip mirror config"         pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
        run_or_error "pip self-upgrade"          pip install pip -U
        run_or_error "pip install phy"           pip install phy --pre --upgrade
        run_or_error "pip install klusta"        pip install klusta klustakwik2
        run_or_error "pip install phycontrib"    pip install klusta phy phycontrib --upgrade
        run_or_error "pip install psutil"        pip install psutil
        run_or_error "pip install tkfilebrowser" pip install tkfilebrowser
    else
        log_error "Could not activate phy2 conda environment"
    fi
fi
echo ""

# ---------------------------------------------------------------------------
# 7. Deploy CereLoop server files
# ---------------------------------------------------------------------------
echo "[7/7] Deploying CereLoop server files..."

# KlustaKwik binary
if [ -f "./KlustaKwik" ]; then
    run_or_error "Copy KlustaKwik binary" sudo cp "./KlustaKwik" "/bin/KlustaKwik"
    run_or_error "chmod KlustaKwik"       sudo chmod 777 /bin/KlustaKwik
else
    log_warning "KlustaKwik binary not found — skipping"
fi

# Create target directories
for dir in "/usr/local/bin/cereloop" \
           "/usr/local/bin/cereloop/map" \
           "/usr/local/bin/cereloop/AS01"; do
    run_or_error "mkdir $dir" sudo mkdir -p "$dir"
done

# Core config & launcher files
for f in data.prm AS01_start.sh run_resample.py nsx2dat; do
    if [ -f "./$f" ]; then
        run_or_error "Copy $f" sudo cp "./$f" "/usr/local/bin/cereloop/$f"
    else
        log_warning "$f not found — skipping"
    fi
done

if [ -f "./AS01-Sorting-Server-GUI.desktop" ]; then
    run_or_error "Copy desktop entry" sudo cp "./AS01-Sorting-Server-GUI.desktop" "/usr/share/applications/"
else
    log_warning "AS01-Sorting-Server-GUI.desktop not found — skipping"
fi

# Map files
if [ -d "./map" ]; then
    run_or_error "Copy map files" sudo cp -r ./map/. /usr/local/bin/cereloop/map/
else
    log_warning "./map directory not found — skipping map files"
fi

# NeuroSuite source files
if [ -d "./NeuroSuite" ]; then
    run_or_error "Copy NeuroSuite source" sudo cp -r ./NeuroSuite/. /usr/local/bin/cereloop/
else
    log_warning "./NeuroSuite not found — skipping NeuroSuite deployment"
fi

# AS01 source files
if [ -d "./AS01" ]; then
    run_or_error "Copy AS01 source" sudo cp -r ./AS01/. /usr/local/bin/cereloop/AS01/
else
    log_warning "./AS01 not found — skipping AS01 deployment"
fi

# Set permissions
run_or_error "chmod cereloop tree" sudo chmod 777 -R /usr/local/bin/cereloop

# Update electrode maps
if [ -d "./Update_Lotus_electrode_maps" ]; then
    cd "./Update_Lotus_electrode_maps"
    if ! bash ./Update_Electrode_maps.sh; then
        log_error "Update_Electrode_maps.sh failed"
    else
        log_ok "Electrode maps updated"
    fi
    cd ..
else
    log_warning "./Update_Lotus_electrode_maps not found — skipping electrode map update"
fi
echo ""

# ---------------------------------------------------------------------------
# Final summary
# ---------------------------------------------------------------------------
echo "============================================="
echo "  INSTALLATION SUMMARY"
echo "============================================="
echo "  Finished: $(date)"
echo "  Log file: $LOG_FILE"
echo ""

if [ ${#WARNINGS[@]} -gt 0 ]; then
    echo "  WARNINGS (${#WARNINGS[@]}):"
    for w in "${WARNINGS[@]}"; do
        echo "    ⚠  $w"
    done
    echo ""
fi

if [ ${#ERRORS[@]} -eq 0 ]; then
    echo "  ✔  All steps completed successfully."
    echo ""
    echo "  Next steps:"
    echo "    1. Reboot or run:  source ~/.bashrc"
    echo "    2. Activate env:   conda activate phy2"
    echo "============================================="
    exit 0
else
    echo "  ERRORS (${#ERRORS[@]}) — review and fix before use:"
    for e in "${ERRORS[@]}"; do
        echo "    ✘  $e"
    done
    echo ""
    echo "  Installation completed WITH ERRORS."
    echo "  Check the full log: $LOG_FILE"
    echo "============================================="
    exit 1
fi