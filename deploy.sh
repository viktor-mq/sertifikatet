#!/bin/bash

# =============================================================================
# Sertifikatet.no cPanel Deployment Script
# =============================================================================

echo "🚗 Deploying Sertifikatet.no to cPanel hosting..."
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're in the hosting environment
if [ -d "/home/zezevhwz" ]; then
    echo -e "${GREEN}✓ Running on cPanel hosting environment${NC}"
    HOSTING_ENV=true
else
    echo -e "${YELLOW}Running on local development environment${NC}"
    HOSTING_ENV=false
fi

# Step 1: Update code (if in hosting environment)
if [ "$HOSTING_ENV" = true ]; then
    echo -e "${YELLOW}Step 1: Updating code from Git...${NC}"
    git pull origin main
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Code updated successfully${NC}"
    else
        echo -e "${RED}✗ Failed to update code${NC}"
        exit 1
    fi
fi

# Step 2: Set up environment
echo -e "${YELLOW}Step 2: Setting up environment...${NC}"
if [ "$HOSTING_ENV" = true ]; then
    cp .env.cpanel .env
    echo -e "${GREEN}✓ cPanel environment activated${NC}"
else
    echo -e "${BLUE}For local testing, keeping current .env${NC}"
fi

# Step 3: Install/update dependencies
echo -e "${YELLOW}Step 3: Installing dependencies...${NC}"
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Dependencies installed successfully${NC}"
else
    echo -e "${RED}✗ Failed to install dependencies${NC}"
    exit 1
fi

# Step 4: Create necessary directories
echo -e "${YELLOW}Step 4: Creating necessary directories...${NC}"
mkdir -p logs
mkdir -p static/images/signs
mkdir -p static/images/quiz
mkdir -p static/images/custom
mkdir -p backups/database
echo -e "${GREEN}✓ Directories created${NC}"

# Step 5: Database setup
echo -e "${YELLOW}Step 5: Setting up database...${NC}"
python -c "
from app import create_app, db
try:
    app = create_app()
    with app.app_context():
        db.create_all()
    print('✓ Database tables created/updated successfully')
except Exception as e:
    print(f'✗ Database setup failed: {e}')
    exit(1)
"

# Step 6: Set file permissions (hosting environment)
if [ "$HOSTING_ENV" = true ]; then
    echo -e "${YELLOW}Step 6: Setting file permissions...${NC}"
    chmod 644 passenger_wsgi.py
    chmod -R 755 static/
    chmod -R 755 templates/
    chmod 755 *.py
    echo -e "${GREEN}✓ File permissions set${NC}"
fi

# Step 7: Restart application (hosting environment)
if [ "$HOSTING_ENV" = true ]; then
    echo -e "${YELLOW}Step 7: Restarting application...${NC}"
    touch passenger_wsgi.py
    echo -e "${GREEN}✓ Application restarted${NC}"
fi

# Display deployment information
echo ""
echo -e "${GREEN}🌟 Sertifikatet.no Deployment Complete!${NC}"
echo "=================================================="

if [ "$HOSTING_ENV" = true ]; then
    echo -e "Website URL:        ${GREEN}https://sertifikatet.no${NC}"
    echo -e "Admin Panel:        ${GREEN}https://sertifikatet.no/admin${NC}"
else
    echo -e "Local URL:          ${GREEN}http://localhost:8000${NC}"
    echo -e "Admin Panel:        ${GREEN}http://localhost:8000/admin${NC}"
fi

echo ""
echo -e "${YELLOW}🔐 Developer Authentication:${NC}"
echo -e "Username: ${GREEN}admin${NC}"
echo -e "Password: ${GREEN}test123${NC}"
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "1. Test website access and developer login"
echo "2. Test admin panel functionality"
echo "3. Share access credentials with your partner"
echo "4. Monitor logs for any issues"
echo ""

if [ "$HOSTING_ENV" = true ]; then
    echo -e "${BLUE}To view logs: tail -f ~/logs/sertifikatet.no.error.log${NC}"
    echo -e "${BLUE}To restart app: touch passenger_wsgi.py${NC}"
else
    echo -e "${BLUE}To start locally: python run.py${NC}"
fi
