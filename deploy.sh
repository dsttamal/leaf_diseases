#!/bin/bash

# Ubuntu Deployment Script for Leaf Disease Detection API
# This script sets up the environment and deploys the application

set -e

echo "🚀 Starting Ubuntu deployment for Leaf Disease Detection API..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="leaf-disease-api"
APP_DIR="/var/www/$APP_NAME"
SERVICE_USER="ubuntu"
NODE_VERSION="18"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root. Please run as ubuntu user with sudo privileges."
   exit 1
fi

# Update system packages
print_status "Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install essential packages
print_status "Installing essential packages..."
sudo apt install -y curl wget gnupg2 software-properties-common apt-transport-https ca-certificates lsb-release

# Install Node.js
print_status "Installing Node.js $NODE_VERSION..."
curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | sudo -E bash -
sudo apt install -y nodejs

# Verify Node.js installation
node_version=$(node --version)
npm_version=$(npm --version)
print_status "Node.js version: $node_version"
print_status "NPM version: $npm_version"

# Install PM2 globally
print_status "Installing PM2..."
sudo npm install -g pm2

# Install Python 3 and pip
print_status "Installing Python 3 and pip..."
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Install system dependencies for OpenCV and other packages
print_status "Installing system dependencies..."
sudo apt install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    libgtk-3-dev \
    pkg-config \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev

# Install Git if not present
if ! command -v git &> /dev/null; then
    print_status "Installing Git..."
    sudo apt install -y git
fi

# Create application directory
print_status "Creating application directory..."
sudo mkdir -p $APP_DIR
sudo chown $SERVICE_USER:$SERVICE_USER $APP_DIR

# Clone or copy application files
if [ -d ".git" ]; then
    print_status "Copying application files..."
    cp -r * $APP_DIR/
else
    print_warning "No git repository found. Please manually copy your files to $APP_DIR"
fi

# Change to application directory
cd $APP_DIR

# Create logs directory
print_status "Creating logs directory..."
mkdir -p logs

# Install Node.js dependencies
print_status "Installing Node.js dependencies..."
npm install --production

# Create Python virtual environment
print_status "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_status "Creating environment file..."
    cat > .env << EOF
NODE_ENV=production
PORT=3000
FRIEND_PORT=8001
MAIN_PORT=8002
EOF
fi

# Setup PM2 startup script
print_status "Setting up PM2 startup script..."
pm2 startup | tail -1 | sudo bash || true

# Start the application with PM2
print_status "Starting application with PM2..."
pm2 start ecosystem.config.js --env production

# Save PM2 configuration
print_status "Saving PM2 configuration..."
pm2 save

# Setup Nginx (optional)
if command -v nginx &> /dev/null; then
    print_status "Nginx detected. Setting up reverse proxy configuration..."
    
    sudo tee /etc/nginx/sites-available/$APP_NAME > /dev/null << EOF
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # Increase timeout for ML processing
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Increase max body size for image uploads
        client_max_body_size 50M;
    }
}
EOF

    # Enable the site
    sudo ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
    
    # Test nginx configuration
    sudo nginx -t && sudo systemctl reload nginx
    
    print_status "Nginx configuration created and reloaded."
else
    print_warning "Nginx not found. You may want to install it for production deployment."
fi

# Setup UFW firewall (optional)
if command -v ufw &> /dev/null; then
    print_status "Setting up firewall rules..."
    sudo ufw allow 22/tcp   # SSH
    sudo ufw allow 80/tcp   # HTTP
    sudo ufw allow 443/tcp  # HTTPS
    sudo ufw allow 3000/tcp # Node.js app (if direct access needed)
    # sudo ufw --force enable  # Uncomment to enable firewall
    print_warning "Firewall rules added but not enabled. Run 'sudo ufw enable' to activate."
fi

# Create systemd service as backup (optional)
print_status "Creating systemd service as backup..."
sudo tee /etc/systemd/system/$APP_NAME.service > /dev/null << EOF
[Unit]
Description=Leaf Disease Detection API
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$APP_DIR
Environment=NODE_ENV=production
ExecStart=/usr/bin/node server.js
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=$APP_NAME

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable $APP_NAME

print_status "✅ Deployment completed successfully!"
print_status ""
print_status "🔍 Useful commands:"
print_status "  View PM2 status:     pm2 status"
print_status "  View PM2 logs:       pm2 logs"
print_status "  View PM2 monitoring: pm2 monit"
print_status "  Restart app:         pm2 restart $APP_NAME"
print_status "  Stop app:            pm2 stop $APP_NAME"
print_status ""
print_status "🌐 Your application should be running on:"
print_status "  Local:  http://localhost:3000"
print_status "  Health: http://localhost:3000/health"
print_status ""
print_warning "Don't forget to:"
print_warning "  1. Update your domain name in Nginx config if using Nginx"
print_warning "  2. Configure SSL certificate for production"
print_warning "  3. Set up proper environment variables"
print_warning "  4. Configure your firewall settings"
