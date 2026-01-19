#!/bin/bash

# Xianyu monitoring system local startup script
# Feature: Clean up old builds、Install dependencies and build front-end、Start service

set -e  # Exit immediately if an error occurs

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Xianyu monitoring system - local startup script${NC}"
echo -e "${GREEN}========================================${NC}"

# 0. Environment and dependency checks
echo -e "\n${YELLOW}[1/6] Check environment and dependencies...${NC}"

OS_FAMILY="unknown"
LINUX_ID=""
LINUX_LIKE=""
PYTHON_CMD="python3"
PIP_CMD="python3 -m pip"

if [ -f /etc/os-release ]; then
    . /etc/os-release
    LINUX_ID="$ID"
    LINUX_LIKE="$ID_LIKE"
fi

case "$(uname -s 2>/dev/null || echo unknown)" in
    Darwin)
        OS_FAMILY="macos"
        ;;
    Linux)
        if grep -qi microsoft /proc/version 2>/dev/null; then
            OS_FAMILY="wsl"
        else
            OS_FAMILY="linux"
        fi
        ;;
    MINGW*|MSYS*|CYGWIN*)
        OS_FAMILY="windows"
        ;;
    *)
        OS_FAMILY="unknown"
        ;;
esac

MISSING_ITEMS=()

if ! command -v python3 >/dev/null 2>&1; then
    MISSING_ITEMS+=("python3(>=3.10)")
else
    if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
        MISSING_ITEMS+=("python3(>=3.10)")
    fi
fi

if ! python3 -m pip --version >/dev/null 2>&1; then
    MISSING_ITEMS+=("pip")
fi

if ! command -v node >/dev/null 2>&1; then
    MISSING_ITEMS+=("node")
fi

if ! command -v npm >/dev/null 2>&1; then
    MISSING_ITEMS+=("npm")
fi

if ! python3 -m playwright --version >/dev/null 2>&1; then
    MISSING_ITEMS+=("playwright")
fi

has_browser=false
case "$OS_FAMILY" in
    macos)
        if [ -d "/Applications/Google Chrome.app" ] || [ -d "/Applications/Microsoft Edge.app" ]; then
            has_browser=true
        fi
        ;;
    linux|wsl)
        if command -v google-chrome >/dev/null 2>&1 \
            || command -v google-chrome-stable >/dev/null 2>&1 \
            || command -v chromium >/dev/null 2>&1 \
            || command -v chromium-browser >/dev/null 2>&1 \
            || command -v microsoft-edge >/dev/null 2>&1 \
            || command -v microsoft-edge-stable >/dev/null 2>&1; then
            has_browser=true
        fi
        ;;
    windows)
        if [ -d "/c/Program Files/Google/Chrome/Application" ] \
            || [ -d "/c/Program Files (x86)/Google/Chrome/Application" ] \
            || [ -d "/c/Program Files (x86)/Microsoft/Edge/Application" ] \
            || [ -d "/c/Program Files/Microsoft/Edge/Application" ]; then
            has_browser=true
        fi
        ;;
esac

if [ "$has_browser" = false ]; then
    MISSING_ITEMS+=("Browser(Chrome or Edge)")
fi


print_solution_macos() {
    cat <<'EOF'
macOS Solution:
1) Install Homebrew:
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
2) Install Python and Node:
   brew install python@3.11 node
3) Install Playwright:
   python3 -m pip install playwright
   python3 -m playwright install chromium
4) Install browser:
   brew install --cask google-chrome
   # or
   brew install --cask microsoft-edge
5) Configuration file (optional）:
   cp .env.example .env
   cp config.json.example config.json
EOF
}

print_solution_linux_deb() {
    cat <<'EOF'
Linux (Debian/Ubuntu) Solution:
1) Install Python and pip:
   sudo apt-get update
   sudo apt-get install -y python3 python3-pip python3-venv
2) Install Node.js and npm (LTS):
   curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
   sudo apt-get install -y nodejs
3) Install Playwright:
   python3 -m pip install playwright
   python3 -m playwright install chromium
   python3 -m playwright install-deps chromium
4) Install browser:
   sudo apt-get install -y chromium-browser || sudo apt-get install -y chromium
   # or install Edge:
   sudo apt-get install -y microsoft-edge-stable
5) Configuration file (optional）:
   cp .env.example .env
   cp config.json.example config.json
EOF
}

print_solution_linux_rpm() {
    cat <<'EOF'
Linux (RHEL/CentOS/Fedora) Solution:
1) Install Python and pip:
   sudo dnf install -y python3 python3-pip
2) Install Node.js and npm (LTS):
   sudo dnf install -y nodejs
3) Install Playwright:
   python3 -m pip install playwright
   python3 -m playwright install chromium
   python3 -m playwright install-deps chromium
4) Install browser:
   sudo dnf install -y chromium
   # or install Edge:
   sudo dnf install -y microsoft-edge-stable
5) Configuration file (optional）:
   cp .env.example .env
   cp config.json.example config.json
EOF
}

print_solution_linux_arch() {
    cat <<'EOF'
Linux (Arch) Solution:
1) Install Python and pip:
   sudo pacman -S --noconfirm python python-pip
2) Install Node.js and npm:
   sudo pacman -S --noconfirm nodejs npm
3) Install Playwright:
   python3 -m pip install playwright
   python3 -m playwright install chromium
   python3 -m playwright install-deps chromium
4) Install browser:
   sudo pacman -S --noconfirm chromium
   # or install Edge:
   yay -S microsoft-edge-stable
5) Configuration file:
   cp .env.example .env
   cp config.json.example config.json
EOF
}

print_solution_wsl() {
    cat <<'EOF'
WSL Solution:
1) Install Python and pip:
   sudo apt-get update
   sudo apt-get install -y python3 python3-pip python3-venv
2) Install Node.js and npm (LTS):
   curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
   sudo apt-get install -y nodejs
3) Install Playwright:
   python3 -m pip install playwright
   python3 -m playwright install chromium
   python3 -m playwright install-deps chromium
4) Install browser:
   sudo apt-get install -y chromium-browser || sudo apt-get install -y chromium
   # or in Windows Install Chrome/Edge And in WSL use Linux version browser
5) Configuration file:
   cp .env.example .env
   cp config.json.example config.json
EOF
}

print_solution_windows() {
    cat <<'EOF'
Windows (PowerShell) Solution:
1) Install Python and Node:
   winget install Python.Python.3.11
   winget install OpenJS.NodeJS.LTS
2) Install Playwright:
   py -m pip install playwright
   py -m playwright install chromium
3) Install browser:
   winget install Google.Chrome
   # or
   winget install Microsoft.Edge
4) Configuration file (optional）:
   Copy-Item .env.example .env
   Copy-Item config.json.example config.json
EOF
}

print_solution_generic() {
    cat <<'EOF'
General solution:
1) Install Python 3.10+ and pip
2) Install Node.js and npm
3) Install Playwright:
   python3 -m pip install playwright
   python3 -m playwright install chromium
4) Install browser Chrome or Edge
5) Configuration file (optional）:
   cp .env.example .env
   cp config.json.example config.json
EOF
}

if [ "${#MISSING_ITEMS[@]}" -ne 0 ]; then
    echo -e "${RED}✗ Missing environment detected/rely:${NC}"
    for item in "${MISSING_ITEMS[@]}"; do
        echo "  - $item"
    done
    echo ""
    case "$OS_FAMILY" in
        macos)
            print_solution_macos
            ;;
        linux)
            if [ "$LINUX_ID" = "arch" ] || echo "$LINUX_LIKE" | grep -qi "arch"; then
                print_solution_linux_arch
            elif [ "$LINUX_ID" = "fedora" ] || [ "$LINUX_ID" = "rhel" ] || [ "$LINUX_ID" = "centos" ] || echo "$LINUX_LIKE" | grep -qi "rhel\|fedora"; then
                print_solution_linux_rpm
            else
                print_solution_linux_deb
            fi
            ;;
        wsl)
            print_solution_wsl
            ;;
        windows)
            print_solution_windows
            ;;
        *)
            print_solution_generic
            ;;
    esac
    exit 1
fi

echo -e "${GREEN}✓ Environment and dependency check passed${NC}"

# 1. Clean out the old ones dist Table of contents
echo -e "\n${YELLOW}[2/6] Clean up old build artifacts...${NC}"
if [ -d "dist" ]; then
    rm -rf dist
    echo -e "${GREEN}✓ Old one deleted dist Table of contents${NC}"
else
    echo -e "${GREEN}✓ dist Directory does not exist, skip cleaning${NC}"
fi

# 2. Check and install Python rely
echo -e "\n${YELLOW}[3/6] examine Python rely...${NC}"
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}✗ mistake: requirements.txt File does not exist${NC}"
    exit 1
fi

echo "Installing Python rely..."
python3 -m pip install -r requirements.txt --quiet
echo -e "${GREEN}✓ Python Dependency installation completed${NC}"

# 3. Build the front end
echo -e "\n${YELLOW}[4/6] Build front-end project...${NC}"
if [ ! -d "web-ui" ]; then
    echo -e "${RED}✗ mistake: web-ui Directory does not exist${NC}"
    exit 1
fi

cd web-ui

# examine node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Running for the first time, installing front-end dependencies..."
    npm install
fi

echo "Building frontend..."
npm run build

if [ ! -d "dist" ]; then
    echo -e "${RED}✗ mistake: Frontend build failed，dist Directory not generated${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Front-end build completed${NC}"

# 4. Copy the build product to the project root directory
echo -e "\n${YELLOW}[5/6] Copy the build product...${NC}"
cd "$SCRIPT_DIR"
cp -r web-ui/dist ./
echo -e "${GREEN}✓ The build products have been copied to the project root directory${NC}"

# 5. Start backend service
echo -e "\n${YELLOW}[6/6] Start backend service...${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Service starting...${NC}"
echo -e "${GREEN}Access address: http://localhost:8000${NC}"
echo -e "${GREEN}API document: http://localhost:8000/docs${NC}"
echo -e "${GREEN}========================================${NC}\n"

python3 -m src.app
