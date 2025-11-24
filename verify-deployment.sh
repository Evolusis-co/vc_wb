#!/bin/bash
# Pre-Deployment Verification Script
# Run this before deploying to Render

echo "========================================"
echo "🔍 Pre-Deployment Verification"
echo "========================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
ERRORS=0
WARNINGS=0
SUCCESS=0

# Check 1: .env file exists
echo -n "Checking .env file exists (for local testing)... "
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC}"
    ((SUCCESS++))
else
    echo -e "${YELLOW}⚠ Not found (OK if deploying directly)${NC}"
    ((WARNINGS++))
fi

# Check 2: .env is in .gitignore
echo -n "Checking .env is in .gitignore... "
if grep -q "^\.env$" .gitignore 2>/dev/null; then
    echo -e "${GREEN}✓${NC}"
    ((SUCCESS++))
else
    echo -e "${RED}✗ CRITICAL: .env not in .gitignore!${NC}"
    ((ERRORS++))
fi

# Check 3: requirements.txt exists for both services
echo -n "Checking requirements.txt (VoiceCoach)... "
if [ -f "requirements.txt" ]; then
    echo -e "${GREEN}✓${NC}"
    ((SUCCESS++))
else
    echo -e "${RED}✗ Missing${NC}"
    ((ERRORS++))
fi

echo -n "Checking requirements.txt (Chatbot)... "
if [ -f "web_chatbot-main/requirements.txt" ]; then
    echo -e "${GREEN}✓${NC}"
    ((SUCCESS++))
else
    echo -e "${RED}✗ Missing${NC}"
    ((ERRORS++))
fi

# Check 4: render.yaml exists
echo -n "Checking render.yaml... "
if [ -f "render.yaml" ]; then
    echo -e "${GREEN}✓${NC}"
    ((SUCCESS++))
else
    echo -e "${RED}✗ Missing${NC}"
    ((ERRORS++))
fi

# Check 5: Critical Python files exist
echo -n "Checking server.py (VoiceCoach)... "
if [ -f "server.py" ]; then
    echo -e "${GREEN}✓${NC}"
    ((SUCCESS++))
else
    echo -e "${RED}✗ Missing${NC}"
    ((ERRORS++))
fi

echo -n "Checking app.py (Chatbot)... "
if [ -f "web_chatbot-main/app.py" ]; then
    echo -e "${GREEN}✓${NC}"
    ((SUCCESS++))
else
    echo -e "${RED}✗ Missing${NC}"
    ((ERRORS++))
fi

# Check 6: Database files exist
echo -n "Checking database.py files... "
DB_FILES=0
[ -f "core/database.py" ] && ((DB_FILES++))
[ -f "web_chatbot-main/database.py" ] && ((DB_FILES++))
if [ $DB_FILES -eq 2 ]; then
    echo -e "${GREEN}✓${NC}"
    ((SUCCESS++))
else
    echo -e "${RED}✗ Missing database configuration${NC}"
    ((ERRORS++))
fi

# Check 7: No .db files should be committed
echo -n "Checking for SQLite files in git... "
if git ls-files | grep -q "\.db$" 2>/dev/null; then
    echo -e "${RED}✗ Found .db files in git!${NC}"
    echo "  Run: git rm --cached *.db"
    ((ERRORS++))
else
    echo -e "${GREEN}✓${NC}"
    ((SUCCESS++))
fi

# Check 8: No .env files in git
echo -n "Checking for .env files in git... "
if git ls-files | grep -q "\.env$" 2>/dev/null; then
    echo -e "${RED}✗ CRITICAL: .env file committed!${NC}"
    echo "  Run: git rm --cached .env"
    ((ERRORS++))
else
    echo -e "${GREEN}✓${NC}"
    ((SUCCESS++))
fi

# Check 9: Gunicorn in chatbot requirements
echo -n "Checking gunicorn in chatbot requirements... "
if grep -q "gunicorn" web_chatbot-main/requirements.txt 2>/dev/null; then
    echo -e "${GREEN}✓${NC}"
    ((SUCCESS++))
else
    echo -e "${YELLOW}⚠ Gunicorn not found (needed for production)${NC}"
    ((WARNINGS++))
fi

# Check 10: Python version compatibility
echo -n "Checking Python syntax (server.py)... "
if python3 -m py_compile server.py 2>/dev/null; then
    echo -e "${GREEN}✓${NC}"
    ((SUCCESS++))
else
    echo -e "${YELLOW}⚠ Syntax check failed (might be OK)${NC}"
    ((WARNINGS++))
fi

echo ""
echo "========================================"
echo "📊 Summary"
echo "========================================"
echo -e "${GREEN}Passed: $SUCCESS${NC}"
echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
echo -e "${RED}Errors: $ERRORS${NC}"
echo ""

if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}❌ DEPLOYMENT BLOCKED - Fix errors above${NC}"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Ready with warnings - Review before deploying${NC}"
    exit 0
else
    echo -e "${GREEN}✅ READY FOR DEPLOYMENT!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. git add ."
    echo "2. git commit -m 'Ready for Render deployment'"
    echo "3. git push origin main"
    echo "4. Deploy via Render Blueprint"
    exit 0
fi
