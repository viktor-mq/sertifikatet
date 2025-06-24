#!/bin/bash

# =============================================================================
# Sertifikatet.no Auto-Reload Development Server
# =============================================================================

echo "🚗 Starting Sertifikatet.no with Auto-Reload..."
echo "==============================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if we're in the right directory
if [ ! -f "run.py" ]; then
    echo "Error: run.py not found. Please run this script from the project root."
    exit 1
fi

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
else
    echo "Error: Virtual environment not found."
    exit 1
fi

# Check if MySQL is running
if brew services list | grep mysql | grep started >/dev/null 2>&1; then
    echo -e "${GREEN}✓ MySQL is running${NC}"
else
    echo -e "${YELLOW}Starting MySQL...${NC}"
    brew services start mysql
fi

# Get IP addresses for display
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -n1 | awk '{print $2}')

echo ""
echo -e "${BLUE}🌟 Sertifikatet.no Development Server${NC}"
echo "======================================"
echo -e "Local Access:    ${GREEN}http://localhost:8000${NC}"
echo -e "Network Access:  ${GREEN}http://$LOCAL_IP:8000${NC}"
echo -e "Domain Access:   ${GREEN}http://sertifikatet.no:8000${NC}"
echo ""
echo -e "${YELLOW}🔥 AUTO-RELOAD ENABLED${NC}"
echo "Changes to Python files will automatically reload the server"
echo ""
echo -e "${YELLOW}🔐 Developer Login: admin / test123${NC}"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start Flask with auto-reload
export FLASK_ENV=development
export FLASK_DEBUG=1
python run.py
