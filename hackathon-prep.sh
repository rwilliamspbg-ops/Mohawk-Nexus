#!/bin/bash

# Hackathon Rapid Environment Check for Mohawk Nexus
# Run this script tonight to verify your toolchain is ready for tomorrow

set -e

echo "🔧 Mohawk Nexus Hackathon Environment Check"
echo "============================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_tool() {
    local tool=$1
    local cmd=$2
    if command -v $cmd &> /dev/null; then
        version=$($cmd --version 2>&1 | head -n1)
        echo -e "${GREEN}✓${NC} $tool: $version"
        return 0
    else
        echo -e "${RED}✗${NC} $tool: NOT FOUND"
        return 1
    fi
}

echo "📋 CORE TOOLS"
echo "-------------"
check_tool "Git" "git" || echo "  Install: apt-get install git"
check_tool "Go" "go" || echo "  Install: https://golang.org/doc/install"
check_tool "Node.js" "node" || echo "  Install: nvm install 20"
check_tool "Python" "python3" || echo "  Install: apt-get install python3.11"
check_tool "Docker" "docker" || echo "  Install: https://docs.docker.com/install/"

echo ""
echo "🎨 FRONTEND TOOLS (for Demos 1 & 2)"
echo "------------------------------------"
if command -v npm &> /dev/null; then
    npm_ver=$(npm --version)
    echo -e "${GREEN}✓${NC} npm: v$npm_ver"
else
    echo -e "${RED}✗${NC} npm: NOT FOUND"
    echo "  Run: npm install -g npm"
fi

if command -v yarn &> /dev/null; then
    yarn_ver=$(yarn --version)
    echo -e "${GREEN}✓${NC} yarn: v$yarn_ver"
else
    echo -e "${YELLOW}◐${NC} yarn: optional (npm is enough)"
fi

echo ""
echo "🔐 CRYPTOGRAPHY & VERIFICATION (Core Features)"
echo "----------------------------------------------"
check_tool "Lean4" "lean" || echo "  Optional for demo, but good to verify: elan toolup"

echo ""
echo "⚙️  WASM TOOLS (for Demo 3: Edge PowerHouse)"
echo "--------------------------------------------"
check_tool "TinyGo" "tinygo" || echo "  Install: https://tinygo.org/getting-started/install/"
check_tool "Wasm-Pack" "wasm-pack" || echo "  Install: curl https://rustwasm.org/wasm-pack/installer/init.sh -sSf | sh"

echo ""
echo "📦 PROJECT SETUP"
echo "----------------"

# Check if Mohawk repo is cloned
if [ -d "/workspaces/Mohawk-Nexus/.git" ]; then
    echo -e "${GREEN}✓${NC} Mohawk-Nexus repository found"
    cd /workspaces/Mohawk-Nexus
    
    # Check if we can build
    if [ -f "go.mod" ]; then
        echo -e "${GREEN}✓${NC} Go module file found (go.mod)"
    else
        echo -e "${YELLOW}◐${NC} No go.mod found (may need initialization)"
    fi
else
    echo -e "${RED}✗${NC} Mohawk-Nexus not found at /workspaces/Mohawk-Nexus"
    echo "  Clone: git clone https://github.com/rwilliamspbg-ops/Mohawk-Nexus.git"
fi

echo ""
echo "🚀 QUICK START COMMANDS"
echo "----------------------"
echo ""
echo "Demo 1 (Agentic Sovereignty Viz):"
echo "  1. npm install (in frontend dir)"
echo "  2. npm start"
echo ""
echo "Demo 2 (Efficiency Dashboard):"
echo "  1. pip install -r requirements.txt"
echo "  2. npm install (dashboard)"
echo "  3. npm run dev"
echo ""
echo "Demo 3 (Edge Powerhouse):"
echo "  1. cd agent-wasm/"
echo "  2. tinygo build -target wasm -o agent.wasm agent.go"
echo "  3. ./demo-script.sh"
echo ""
echo "Deploy to GitHub Pages:"
echo "  git push origin main  # Triggers .github/workflows/deploy-pages.yml"
echo ""
echo "============================================="
echo "✅ Environment check complete!"
echo ""
echo "If any tools are missing, install them now BEFORE the hackathon."
echo "You don't want to waste the first hour on setup."
echo ""

