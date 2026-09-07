# Revinteq v3 — Complete Production Build

## Structure

```
revinteq-complete/
├── backend/     Django 5 + DRF — 116 Python files, 16 apps
├── frontend/    Vue 3 + Vite + Pinia + Tailwind — 35 Vue components
└── README.md
```

## Deployment (one command)

```bash
# 1. Upload both folders to your server
scp -r revinteq-complete root@YOUR_SERVER_IP:/root/

# 2. Rename to expected paths
ssh root@YOUR_SERVER_IP
mv /root/revinteq-complete/backend /root/revinteq-v3
mv /root/revinteq-complete/frontend /root/revinteq-vue

# 3. Run the deploy script
bash /root/revinteq-v3/scripts/deploy.sh
```

## What the deploy script does automatically

1. Installs all system packages (Python, MySQL, Redis, Nginx, Node.js)
2. Sets up the MySQL database
3. Creates a Python virtualenv and installs all dependencies
4. Writes your .env file with all secrets
5. Runs Django migrations (creates all 17 database tables)
6. Builds the Vue 3 frontend (npm run build)
7. Configures Gunicorn as a systemd service
8. Configures Celery workers via Supervisor
9. Configures Nginx to serve the Vue SPA + proxy API calls
10. Installs an HTTPS certificate via Let's Encrypt
11. Creates the admin superuser + Gimsc Solutions tenant

## After deployment

Login: https://yourdomain.co.ke/login
Admin: https://yourdomain.co.ke/admin/login

## Meta App Dashboard — three things to configure

1. OAuth redirect URI: https://yourdomain.co.ke/api/v1/meta/callback/
2. WhatsApp webhook:   https://yourdomain.co.ke/api/v1/whatsapp/webhook/
3. Messenger webhook:  https://yourdomain.co.ke/api/v1/whatsapp/messenger/webhook/
   Instagram webhook:  https://yourdomain.co.ke/api/v1/whatsapp/instagram/webhook/
4. Verify token:       (whatever you entered during deploy)
5. Subscribe to:       messages, messaging_referrals
