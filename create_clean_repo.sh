#!/bin/bash

echo "🚗 Creating Clean Sertifikatet Repository..."
echo "============================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Step 1: Create clean copy
echo -e "${YELLOW}Step 1: Creating clean copy of project...${NC}"
cd /Users/viktorigesund/Documents/
cp -r teoritest sertifikatet-clean
cd sertifikatet-clean

# Step 2: Remove all sensitive files and git history
echo -e "${YELLOW}Step 2: Removing sensitive files and git history...${NC}"
rm -rf .git
rm -f .env
rm -f .env.production
rm -f .env.cpanel
rm -rf logs/
rm -rf backups/
rm -rf __pycache__/
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +

# Step 3: Initialize clean git repository
echo -e "${YELLOW}Step 3: Initializing clean git repository...${NC}"
git init
git add .
git commit -m "Initial commit: Clean Sertifikatet.no driving theory platform

Features:
- Flask web application for Norwegian driving theory test
- Quiz system with progress tracking
- User authentication and admin panel
- Video learning modules
- Gamification system
- Payment integration (Stripe)
- Machine learning personalization
- Responsive design with Tailwind CSS

All sensitive data (passwords, API keys) stored in environment variables.
Copy .env.example to .env and configure with your credentials."

echo -e "${GREEN}✓ Clean repository created successfully!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. cd /Users/viktorigesund/Documents/sertifikatet-clean"
echo "2. git remote add origin https://github.com/viktor-mq/sertifikatet.git"
echo "3. git push -u origin main --force"
echo ""
echo -e "${BLUE}This will completely replace the repository with clean code.${NC}"
