#!/bin/bash

# SaaS Control Deck - DockerHub Secrets Setup Script
# This script helps set up the required secrets in GitHub for DockerHub CI/CD

set -e

echo "🔐 SaaS Control Deck - DockerHub Secrets Setup"
echo "=============================================="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    print_error "GitHub CLI (gh) is not installed. Please install it first."
    print_info "Visit: https://cli.github.com/"
    exit 1
fi

# Check if user is logged in to GitHub CLI
if ! gh auth status &> /dev/null; then
    print_error "You're not logged in to GitHub CLI."
    print_info "Please run: gh auth login"
    exit 1
fi

# Get repository information
REPO_OWNER=$(gh repo view --json owner --jq .owner.login)
REPO_NAME=$(gh repo view --json name --jq .name)
REPO_FULL="${REPO_OWNER}/${REPO_NAME}"

print_info "Setting up secrets for repository: ${REPO_FULL}"
echo

# Function to set a secret
set_secret() {
    local secret_name=$1
    local secret_description=$2
    local is_sensitive=${3:-true}

    echo "Setting up: ${secret_name}"
    print_info "${secret_description}"

    if [ "$is_sensitive" = true ]; then
        echo -n "Enter value (input will be hidden): "
        read -s secret_value
        echo
    else
        echo -n "Enter value: "
        read secret_value
    fi

    if [ -z "$secret_value" ]; then
        print_warning "Skipping ${secret_name} - no value provided"
        return
    fi

    if gh secret set "$secret_name" --body "$secret_value" --repo "$REPO_FULL"; then
        print_success "${secret_name} has been set successfully"
    else
        print_error "Failed to set ${secret_name}"
    fi
    echo
}

print_info "We need to set up the following secrets for DockerHub CI/CD:"
echo
echo "1. DOCKERHUB_USERNAME - Your DockerHub username"
echo "2. DOCKERHUB_TOKEN - DockerHub access token (recommended over password)"
echo

# Set DockerHub Username
set_secret "DOCKERHUB_USERNAME" "Your DockerHub username (this will be used in image names)" false

# Set DockerHub Token
echo "🔑 DockerHub Token Setup:"
print_info "It's recommended to use a DockerHub Access Token instead of your password."
print_info "To create an access token:"
print_info "1. Go to https://hub.docker.com/settings/security"
print_info "2. Click 'New Access Token'"
print_info "3. Give it a name like 'SaaS-Control-Deck-CI'"
print_info "4. Select permissions: Read, Write, Delete (for CI/CD)"
print_info "5. Copy the generated token"
echo

set_secret "DOCKERHUB_TOKEN" "Your DockerHub access token or password"

# Verify secrets are set
echo "🔍 Verifying secrets..."
echo

secrets_output=$(gh secret list --repo "$REPO_FULL" 2>/dev/null || echo "")

if echo "$secrets_output" | grep -q "DOCKERHUB_USERNAME"; then
    print_success "DOCKERHUB_USERNAME is set"
else
    print_error "DOCKERHUB_USERNAME is not set"
fi

if echo "$secrets_output" | grep -q "DOCKERHUB_TOKEN"; then
    print_success "DOCKERHUB_TOKEN is set"
else
    print_error "DOCKERHUB_TOKEN is not set"
fi

echo
print_info "DockerHub Repository Names that will be created:"
echo "• ${DOCKERHUB_USERNAME}/saascontrol-frontend"
echo "• ${DOCKERHUB_USERNAME}/saascontrol-backend-backend-pro1"
echo "• ${DOCKERHUB_USERNAME}/saascontrol-backend-backend-pro2"
echo

print_info "Make sure these repositories exist on DockerHub or set them to auto-create."
echo

# Show next steps
echo "🚀 Next Steps:"
echo "============="
print_info "1. Push your code to trigger the CI/CD pipeline:"
echo "   git add ."
echo "   git commit -m \"Add DockerHub CI/CD workflow\""
echo "   git push origin main"
echo

print_info "2. Check the Actions tab in your GitHub repository to see the build progress:"
echo "   https://github.com/${REPO_FULL}/actions"
echo

print_info "3. Once built, your images will be available at:"
echo "   • docker.io/${DOCKERHUB_USERNAME}/saascontrol-frontend:latest"
echo "   • docker.io/${DOCKERHUB_USERNAME}/saascontrol-backend-backend-pro1:latest"
echo "   • docker.io/${DOCKERHUB_USERNAME}/saascontrol-backend-backend-pro2:latest"
echo

print_info "4. To deploy using the built images, check the deployment configs generated in the workflow artifacts."
echo

print_success "DockerHub secrets setup complete! 🎉"
echo

# Optional: Test Docker login
echo "🧪 Testing DockerHub Authentication (Optional):"
echo "Would you like to test DockerHub login locally? (y/n)"
read -n 1 -r test_login
echo

if [[ $test_login =~ ^[Yy]$ ]]; then
    print_info "Testing DockerHub login..."
    echo "Enter your DockerHub username: "
    read dockerhub_username
    echo "Enter your DockerHub token/password: "
    read -s dockerhub_token

    if echo "$dockerhub_token" | docker login --username "$dockerhub_username" --password-stdin; then
        print_success "DockerHub authentication test successful!"
        docker logout
    else
        print_error "DockerHub authentication test failed. Please verify your credentials."
    fi
fi

echo
print_info "For troubleshooting, refer to the CI/CD documentation or GitHub Actions logs."
print_success "Setup completed successfully! 🎉"