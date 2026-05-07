#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== TenderEval AI - Render & Vercel Deployment Setup ===${NC}\n"

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}GitHub CLI not found. Please install it: https://cli.github.com/${NC}"
    exit 1
fi

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${RED}Git not found. Please install it.${NC}"
    exit 1
fi

# Get repository information
REPO=$(git remote get-url origin | sed 's/.*\///;s/.git$//')
OWNER=$(git remote get-url origin | sed 's/.*[:/]//;s/\/.*//')

echo -e "${GREEN}Repository: ${OWNER}/${REPO}${NC}\n"

# Create GitHub Actions secrets
echo -e "${BLUE}Setting up GitHub secrets for Render deployment...${NC}"

read -p "Enter your Render API Key: " RENDER_API_KEY
read -p "Enter your Render Backend Service ID (srv-xxxxx): " RENDER_BACKEND_SERVICE_ID
read -p "Enter your Render Frontend Service ID (srv-xxxxx): " RENDER_FRONTEND_SERVICE_ID
read -p "Enter your Vercel Token (optional, press Enter to skip): " VERCEL_TOKEN

# Set GitHub secrets
gh secret set RENDER_API_KEY --body "$RENDER_API_KEY" --repo "${OWNER}/${REPO}"
gh secret set RENDER_BACKEND_SERVICE_ID --body "$RENDER_BACKEND_SERVICE_ID" --repo "${OWNER}/${REPO}"
gh secret set RENDER_FRONTEND_SERVICE_ID --body "$RENDER_FRONTEND_SERVICE_ID" --repo "${OWNER}/${REPO}"

if [ -n "$VERCEL_TOKEN" ]; then
    gh secret set VERCEL_TOKEN --body "$VERCEL_TOKEN" --repo "${OWNER}/${REPO}"
    echo -e "${GREEN}✓ Vercel token set${NC}"
fi

echo -e "${GREEN}✓ All GitHub secrets configured${NC}\n"

# Display deployment URLs
echo -e "${BLUE}Deployment Guide:${NC}"
echo ""
echo "1. Push your code to GitHub:"
echo "   git push origin main"
echo ""
echo "2. Your services will be available at:"
echo "   - Backend API: https://tender-eval-backend.onrender.com"
echo "   - Frontend: https://tender-eval-frontend.onrender.com"
echo "   - Frontend (Vercel): https://tender-eval-frontend.vercel.app"
echo ""
echo "3. Monitor deployments:"
echo "   - Render: https://dashboard.render.com"
echo "   - Vercel: https://vercel.com/dashboard"
echo ""
echo -e "${GREEN}Setup complete! 🚀${NC}"
