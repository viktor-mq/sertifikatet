#!/bin/bash

# =============================================================================
# Sertifikatet.no Remote Access Setup Script
# =============================================================================

echo "🚗 Setting up Sertifikatet.no for Remote Access..."
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Step 1: Enable MySQL Remote Access
echo -e "${YELLOW}Step 1: Configuring MySQL for remote access...${NC}"
echo "Please run the following commands in MySQL:"
echo -e "${BLUE}mysql -u root -p${NC}"
echo -e "${BLUE}GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' IDENTIFIED BY 'creative';${NC}"
echo -e "${BLUE}FLUSH PRIVILEGES;${NC}"
echo -e "${BLUE}exit${NC}"
echo ""
read -p "Press Enter after you've run these MySQL commands..."

# Step 2: Restart MySQL
echo -e "${YELLOW}Step 2: Restarting MySQL service...${NC}"
brew services restart mysql
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ MySQL restarted successfully${NC}"
else
    echo -e "${RED}✗ Failed to restart MySQL${NC}"
fi

# Step 3: Switch to production environment
echo -e "${YELLOW}Step 3: Switching to production environment...${NC}"
cp .env.production .env
echo -e "${GREEN}✓ Production environment activated${NC}"

# Step 4: Test MySQL connection
echo -e "${YELLOW}Step 4: Testing MySQL remote connection...${NC}"
mysql -h 78.156.2.107 -u root -p sertifikatet -e "SELECT 'Remote connection successful!' as status;" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ MySQL remote connection working${NC}"
else
    echo -e "${RED}✗ MySQL remote connection failed${NC}"
    echo "This might be normal if port forwarding isn't configured yet."
fi

# Display connection information
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -n1 | awk '{print $2}')

echo ""
echo -e "${GREEN}🌟 Sertifikatet.no Remote Access Ready!${NC}"
echo "=================================================="
echo -e "Local Access:       ${GREEN}http://localhost:8000${NC}"
echo -e "Network Access:     ${GREEN}http://$LOCAL_IP:8000${NC}"
echo -e "Public IP Access:   ${GREEN}http://78.156.2.107:8000${NC}"
echo -e "Domain Access:      ${GREEN}http://sertifikatet.no:8000${NC}"
echo ""
echo -e "${YELLOW}🔐 Developer Authentication:${NC}"
echo -e "Username: ${GREEN}admin${NC}"
echo -e "Password: ${GREEN}test123${NC}"
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "1. Configure port forwarding for ports 3306 and 8000"
echo "2. Configure DNS A record: sertifikatet.no → 78.156.2.107"
echo "3. Start the Flask app: python run.py"
echo "4. Share access info with your partner"
echo ""
echo -e "${BLUE}To start the server: python run.py${NC}"
