module.exports = {
  apps: [
    {
      name: 'leaf-disease-api',
      script: 'server.js',
      instances: 1, // or 'max' for cluster mode
      exec_mode: 'fork', // or 'cluster'
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production',
        PORT: 3000
      },
      env_production: {
        NODE_ENV: 'production',
        PORT: 3000
      },
      env_development: {
        NODE_ENV: 'development',
        PORT: 3000
      },
      // Logging
      log_file: './logs/combined.log',
      out_file: './logs/out.log',
      error_file: './logs/error.log',
      log_date_format: 'YYYY-MM-DD HH:mm Z',
      
      // Auto restart settings
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      
      // Graceful shutdown
      kill_timeout: 5000,
      wait_ready: true,
      listen_timeout: 3000,
      
      // Advanced PM2 features
      merge_logs: true,
      
      // Health monitoring
      health_check_grace_period: 3000,
      
      // Cron restart (optional - restart every day at 3 AM)
      // cron_restart: '0 3 * * *',
      
      // Source map support
      source_map_support: true,
      
      // Ignore watch on these folders
      ignore_watch: [
        'node_modules',
        'logs',
        '.git',
        '*.log',
        'Friend/best.pt',
        'MAIN/best.pt'
      ]
    }
  ],

  // Deployment configuration
  deploy: {
    production: {
      user: 'ubuntu',
      host: 'your-server-ip', // Replace with your server IP
      ref: 'origin/main',
      repo: 'https://github.com/dsttamal/leaf_diseases.git',
      path: '/var/www/leaf-disease-api',
      'pre-deploy-local': '',
      'post-deploy': 'npm install && pm2 reload ecosystem.config.js --env production',
      'pre-setup': '',
      env: {
        NODE_ENV: 'production'
      }
    },
    staging: {
      user: 'ubuntu',
      host: 'your-staging-server-ip', // Replace with your staging server IP
      ref: 'origin/develop',
      repo: 'https://github.com/dsttamal/leaf_diseases.git',
      path: '/var/www/leaf-disease-api-staging',
      'pre-deploy-local': '',
      'post-deploy': 'npm install && pm2 reload ecosystem.config.js --env staging',
      'pre-setup': '',
      env: {
        NODE_ENV: 'staging'
      }
    }
  }
};
