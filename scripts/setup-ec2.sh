#!/bin/bash
# EC2 Setup Script for HKBU Buddy Bot Deployment
# Run this script on your EC2 instance to prepare for GitHub Actions deployment

set -e

echo "=========================================="
echo "  HKBU Buddy Bot - EC2 Setup Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    print_error "Cannot detect operating system"
    exit 1
fi

echo "📋 Detected OS: $OS"
echo ""

# Step 1: Install Docker
echo "🔧 Step 1: Installing Docker..."
if command -v docker &>/dev/null; then
    print_success "Docker is already installed"
    docker --version
else
    if [ "$OS" = "amzn" ]; then
        # Amazon Linux
        sudo yum update -y
        sudo yum install -y docker
        sudo service docker start
        sudo systemctl enable docker
    elif [ "$OS" = "ubuntu" ]; then
        # Ubuntu
        sudo apt update
        sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        sudo apt update
        sudo apt install -y docker-ce docker-ce-cli containerd.io
        sudo systemctl start docker
        sudo systemctl enable docker
    else
        print_error "Unsupported OS: $OS"
        exit 1
    fi
    print_success "Docker installed successfully"
fi

# Add current user to docker group
sudo usermod -aG docker $USER
print_success "Added user to docker group"
echo "   Note: You may need to log out and log back in for this to take effect"
echo ""

# Step 2: Create deployment directory
echo "📁 Step 2: Creating deployment directory..."
DEPLOY_DIR="$HOME/hkbu-bot"
mkdir -p $DEPLOY_DIR
print_success "Created directory: $DEPLOY_DIR"
echo ""

# Step 3: Create .env file
echo "🔐 Step 3: Creating .env file..."
ENV_FILE="$DEPLOY_DIR/.env"

if [ -f "$ENV_FILE" ]; then
    print_warning ".env file already exists"
    read -p "Do you want to overwrite it? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Skipping .env file creation"
    else
        cat > "$ENV_FILE" << 'EOF'
TELEGRAM_TOKEN=8793508154:AAEGsBz-RE-ellGm6WbNpFGU3DWT8wFCWfc
API_KEY=60ba81cf-1b79-47ba-a71f-4d0bc71ca099
API_BASE_URL=https://genai.hkbu.edu.hk/api/v0/rest
MODEL=gpt-5
API_VERSION=2024-12-01-preview
DB_HOST=hkbu-bot-db.cx22icumkbcu.ap-east-1.rds.amazonaws.com
DB_PORT=5432
DB_NAME=postgres
DB_USER=bot_user
DB_PASSWORD=comp7940project
EOF
        chmod 600 "$ENV_FILE"
        print_success ".env file created and secured"
    fi
else
    cat > "$ENV_FILE" << 'EOF'
TELEGRAM_TOKEN=8793508154:AAEGsBz-RE-ellGm6WbNpFGU3DWT8wFCWfc
API_KEY=60ba81cf-1b79-47ba-a71f-4d0bc71ca099
API_BASE_URL=https://genai.hkbu.edu.hk/api/v0/rest
MODEL=gpt-5
API_VERSION=2024-12-01-preview
DB_HOST=18.166.253.91
DB_PORT=5432
DB_NAME=postgres
DB_USER=bot_user
DB_PASSWORD=comp7940project
EOF
    chmod 600 "$ENV_FILE"
    print_success ".env file created and secured"
fi
echo ""

# Step 4: Test RDS connectivity
echo "🔍 Step 4: Testing RDS connectivity..."
DB_HOST="18.166.253.91"
DB_PORT=5432

if timeout 3 bash -c "echo > /dev/tcp/$DB_HOST/$DB_PORT" 2>/dev/null; then
    print_success "RDS PostgreSQL is accessible on port $DB_PORT"
else
    print_warning "Cannot connect to RDS on port $DB_PORT"
    echo "   Please check:"
    echo "   1. RDS security group allows connections from this EC2"
    echo "   2. RDS is in the same VPC or publicly accessible"
    echo "   3. Network ACL allows traffic on port 5432"
fi
echo ""

# Step 5: Verify Docker is working
echo "🐳 Step 5: Verifying Docker installation..."
if docker info &>/dev/null; then
    print_success "Docker is running properly"
else
    print_error "Docker is not running. Starting Docker..."
    sudo service docker start
    sleep 2
    if docker info &>/dev/null; then
        print_success "Docker started successfully"
    else
        print_error "Failed to start Docker"
        exit 1
    fi
fi
echo ""

# Step 6: Display setup summary
echo "=========================================="
echo "  ✅ Setup Complete!"
echo "=========================================="
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Configure GitHub Secrets:"
echo "   Go to: GitHub → Your Repo → Settings → Secrets and variables → Actions"
echo "   Add the following secrets:"
echo "   - EC2_HOST: $(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo 'Your EC2 Public IP')"
echo "   - EC2_USER: $USER"
echo "   - EC2_SSH_KEY: Your SSH private key content"
echo "   - GHCR_PAT: GitHub Personal Access Token (with read:packages scope)"
echo "   - GHCR_USERNAME: Your GitHub username"
echo ""
echo "2. Generate SSH Key for GitHub Actions:"
echo "   On your local machine, run:"
echo "   ssh-keygen -t rsa -b 4096 -C 'github-actions-deploy' -f ~/.ssh/github-actions-ec2 -N ''"
echo "   Then add the public key to ~/.ssh/authorized_keys on this EC2"
echo ""
echo "3. Deploy Directory: $DEPLOY_DIR"
echo "   Environment File: $ENV_FILE"
echo ""
echo "4. After pushing to main branch, GitHub Actions will:"
echo "   ✓ Build and test the application"
echo "   ✓ Push Docker image to GHCR"
echo "   ✓ SSH into this EC2 instance"
echo "   ✓ Pull the latest image"
echo "   ✓ Restart the container"
echo "   ✓ Verify deployment"
echo ""
echo "5. Monitor deployment:"
echo "   - GitHub Actions tab: View deployment logs"
echo "   - On EC2: docker logs -f hkbu-buddy-bot"
echo ""
echo "=========================================="
print_success "EC2 is ready for automated deployment!"
echo "=========================================="
