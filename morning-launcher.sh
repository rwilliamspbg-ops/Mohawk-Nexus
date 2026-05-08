#!/bin/bash

# 🚀 HACKATHON MORNING LAUNCHER
# Run this tomorrow morning to prepare for the event

echo "════════════════════════════════════════════════════════════════"
echo "🚀 MOHAWK NEXUS HACKATHON - MORNING PREP"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}✓ Your Hackathon Strategy is Ready${NC}"
echo ""
echo "📚 DOCUMENTS YOU CREATED LAST NIGHT:"
echo "   1. README-HACKATHON.md       ← Start here"
echo "   2. HACKATHON-IDEAS.md        ← Three demo concepts"
echo "   3. PITCH.md                  ← Memorize this"
echo "   4. HACKATHON-TIMELINE.md     ← Minute-by-minute plan"
echo "   5. QUICK-REF.md              ← Print this card"
echo ""

echo "🎤 QUICK REMINDER: YOUR 30-SECOND PITCH"
echo "────────────────────────────────────────────────────────────────"
cat << 'EOF'
"Standard agentic systems route everything through central servers—
trust bottleneck, privacy nightmare, drinks 1000s of gallons water daily.

We aggregate across sovereign nodes with Byzantine consensus + zk-SNARK 
proofs guaranteeing correctness. O(d log n) scaling means 31x less RAM, 
zero-water edge inference, real sovereignty.

[Show demo]"
EOF
echo ""
echo "────────────────────────────────────────────────────────────────"
echo ""

# Environment check
echo -e "${CYAN}🔧 ENVIRONMENT CHECK${NC}"
if command -v go &> /dev/null; then
    echo -e "${GREEN}✓${NC} Go $(go version | awk '{print $3}')"
else
    echo -e "${YELLOW}⚠${NC} Go not found"
fi

if command -v node &> /dev/null; then
    echo -e "${GREEN}✓${NC} Node.js $(node --version)"
else
    echo -e "${YELLOW}⚠${NC} Node.js not found"
fi

if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker ready"
else
    echo -e "${YELLOW}⚠${NC} Docker not running"
fi

echo ""
echo "☕ YOUR MORNING CHECKLIST:"
echo "   [ ] Coffee ☕"
echo "   [ ] Say pitch out loud (1 min)"
echo "   [ ] Open README-HACKATHON.md (refresh memory)"
echo "   [ ] Verify laptop at 100% battery"
echo "   [ ] Test WiFi connection"
echo "   [ ] Keep QUICK-REF.md nearby (print if possible)"
echo "   [ ] Have GitHub links ready in browser bookmarks"
echo ""

echo "🎯 DEMO SELECTION REMINDER:"
echo "   • Pick Demo 1 (Agentic Sovereignty) if you want WOW factor ✨"
echo "   • Pick Demo 2 (Efficiency Dashboard) if you want safe win ⚡"
echo "   • Pick BOTH if you feel confident (split development time)"
echo ""

echo "⏰ TIMELINE: (~6 hours total)"
echo "   Hour 0 (30 min): Event start + your pitch"
echo "   Hour 1 (60 min): Scaffolding + setup"
echo "   Hour 2-4 (120 min): Build Demo 1 (or skip to Demo 2)"
echo "   Hour 3-4 (60 min): Build Demo 2"
echo "   Hour 4-5 (60 min): Polish + GitHub Pages deploy"
echo "   Hour 5-6 (60 min): Practice + backup planning"
echo ""

echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✨ You've got everything. Now go show judges the future. ✨${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo ""
