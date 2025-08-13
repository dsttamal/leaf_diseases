# Leaf Disease Detection API - Ubuntu Deployment with PM2

A Node.js server that manages Python FastAPI applications for leaf disease detection using YOLO models, deployed with PM2 on Ubuntu.

## 🏗️ Architecture

- **Node.js Server** (`server.js`) - Main server that proxies requests and manages Python processes
- **Python FastAPI APIs** - Two separate APIs for different leaf disease detection:
  - `Friend/api.py` - Eggplant leaf disease detection (Port 8001)
  - `MAIN/api.py` - Malabar spinach leaf disease detection (Port 8002)
- **PM2** - Process manager for production deployment
- **Nginx** - Reverse proxy (optional)

## 📋 Prerequisites

### System Requirements
- Ubuntu 18.04+ or Ubuntu 20.04+
- Node.js 16+ and npm
- Python 3.8+
- At least 2GB RAM
- 10GB+ disk space

### Required Software
```bash
# Node.js, Python, Git
sudo apt update
sudo apt install -y nodejs npm python3 python3-pip python3-venv git

# System dependencies for OpenCV
sudo apt install -y libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1

# PM2 (install globally)
sudo npm install -g pm2
```

## 🚀 Quick Deployment

### Method 1: Automated Deployment Script

1. **Upload your project** to the Ubuntu server
2. **Make the deployment script executable:**
   ```bash
   chmod +x deploy.sh
   ```
3. **Run the deployment script:**
   ```bash
   ./deploy.sh
   ```

The script will automatically:
- Install all dependencies
- Set up Python virtual environment
- Configure PM2
- Start the application
- Set up Nginx (if available)

### Method 2: Manual Deployment

1. **Clone or upload your project:**
   ```bash
   cd /var/www
   sudo mkdir leaf-disease-api
   sudo chown $USER:$USER leaf-disease-api
   cd leaf-disease-api
   # Upload your files here
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

3. **Set up Python environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Create environment file:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Start with PM2:**
   ```bash
   pm2 start ecosystem.config.js --env production
   pm2 save
   pm2 startup
   ```

## 🔧 Configuration

### Environment Variables (.env)
```bash
NODE_ENV=production
PORT=3000
FRIEND_PORT=8001
MAIN_PORT=8002
API_TIMEOUT=60000
MAX_FILE_SIZE=50mb
```

### PM2 Configuration (ecosystem.config.js)
The PM2 configuration includes:
- Process management
- Auto-restart on failure
- Log management
- Memory limits
- Deployment settings

## 📡 API Endpoints

### Main Server (Port 3000)
- `GET /` - Server information
- `GET /health` - Health check
- `POST /friend/*` - Proxy to Friend API (Eggplant)
- `POST /main/*` - Proxy to Main API (Malabar Spinach)

### Friend API (Port 8001 - via /friend)
- `GET /friend/` - Frontend interface
- `GET /friend/health` - Health check
- `POST /friend/predict_with_image` - Disease detection with annotated image
- `POST /friend/diagnose` - Detailed disease diagnosis
- `GET /friend/diseases/info` - Disease information

### Main API (Port 8002 - via /main)
- `GET /main/` - Frontend interface
- `GET /main/health` - Health check
- `POST /main/predict_with_image` - Disease detection with annotated image
- `POST /main/diagnose` - Detailed disease diagnosis
- `GET /main/diseases/info` - Disease information

## 🔍 Monitoring and Management

### PM2 Commands
```bash
# View status
pm2 status

# View logs
pm2 logs
pm2 logs leaf-disease-api

# Monitor in real-time
pm2 monit

# Restart application
pm2 restart leaf-disease-api

# Stop application
pm2 stop leaf-disease-api

# Delete application
pm2 delete leaf-disease-api

# Reload with zero downtime
pm2 reload leaf-disease-api
```

### Application Logs
- PM2 logs: `pm2 logs`
- Application logs: `./logs/`
- System logs: `/var/log/syslog`

## 🌐 Nginx Configuration (Optional)

If you have Nginx installed, the deployment script will create a configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        
        client_max_body_size 50M;
    }
}
```

### Enable SSL with Let's Encrypt
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 🔒 Security Considerations

### Firewall Setup
```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### Additional Security
- Use environment variables for sensitive data
- Implement rate limiting
- Use HTTPS in production
- Regular security updates
- Monitor logs for suspicious activity

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   sudo lsof -i :3000
   sudo kill -9 <PID>
   ```

2. **Python dependencies not found:**
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **PM2 not starting:**
   ```bash
   pm2 kill
   pm2 start ecosystem.config.js
   ```

4. **Model file not found:**
   Ensure `best.pt` files are in the correct directories:
   - `Friend/best.pt`
   - `MAIN/best.pt`

### Debug Mode
```bash
# Run in development mode
pm2 start ecosystem.config.js --env development

# View detailed logs
pm2 logs --lines 100
```

## 📊 Performance Optimization

### For Production
1. **Enable cluster mode** in `ecosystem.config.js`:
   ```javascript
   instances: 'max',
   exec_mode: 'cluster'
   ```

2. **Optimize Python dependencies:**
   ```bash
   pip install --upgrade pip
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
   ```

3. **Configure Nginx caching:**
   ```nginx
   location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
       expires 1y;
       add_header Cache-Control "public, no-transform";
   }
   ```

## 🔄 Updates and Deployment

### Update Application
```bash
# Pull latest changes
git pull origin main

# Update dependencies
npm install
source venv/bin/activate
pip install -r requirements.txt

# Restart with PM2
pm2 restart leaf-disease-api
```

### Automated Deployment with PM2
```bash
# Setup deployment
pm2 deploy ecosystem.config.js production setup

# Deploy updates
pm2 deploy ecosystem.config.js production
```

## 📞 Support

If you encounter issues:
1. Check the logs: `pm2 logs`
2. Verify all dependencies are installed
3. Ensure ports are not blocked by firewall
4. Check system resources: `htop` or `free -h`

## 📝 License

This project is licensed under the MIT License.
