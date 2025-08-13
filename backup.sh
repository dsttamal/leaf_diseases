#!/bin/bash

# Backup script for Leaf Disease Detection API

set -e

BACKUP_DIR="/var/backups/leaf-disease-api"
APP_DIR="/var/www/leaf-disease-api"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="leaf-disease-api_backup_$TIMESTAMP.tar.gz"

echo "📦 Starting backup process..."

# Create backup directory if it doesn't exist
sudo mkdir -p $BACKUP_DIR

# Create backup excluding unnecessary files
echo "🗂️ Creating backup archive..."
tar -czf "/tmp/$BACKUP_FILE" \
    --exclude="node_modules" \
    --exclude="venv" \
    --exclude="logs" \
    --exclude=".git" \
    --exclude="*.log" \
    -C "$(dirname $APP_DIR)" \
    "$(basename $APP_DIR)"

# Move backup to backup directory
sudo mv "/tmp/$BACKUP_FILE" "$BACKUP_DIR/"

# Set permissions
sudo chown $USER:$USER "$BACKUP_DIR/$BACKUP_FILE"

echo "✅ Backup completed: $BACKUP_DIR/$BACKUP_FILE"

# Remove backups older than 7 days
echo "🧹 Cleaning old backups (older than 7 days)..."
find $BACKUP_DIR -name "leaf-disease-api_backup_*.tar.gz" -mtime +7 -delete

echo "📊 Current backups:"
ls -lh $BACKUP_DIR/leaf-disease-api_backup_*.tar.gz 2>/dev/null || echo "No backups found"

echo "✅ Backup process completed successfully!"
