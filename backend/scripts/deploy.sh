#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Revinteq v3 — Complete Production Deployment
# Django backend + Vue 3 frontend + MySQL + Redis + Celery + Nginx
# ═══════════════════════════════════════════════════════════════
set -e; set -o pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'
log()     { echo -e "${GREEN}[✓]${NC} $1"; }
warn()    { echo -e "${YELLOW}[!]${NC} $1"; }
err()     { echo -e "${RED}[✗]${NC} $1"; exit 1; }
section() { echo -e "\n${BLUE}${BOLD}══ $1 ══${NC}\n"; }

[ "$EUID" -ne 0 ] && err "Run as root: sudo bash deploy.sh"

section "Revinteq v3 — Configuration"
read -p "Domain (e.g. revinteq.co.ke — Enter for IP only): " DOMAIN
read -p "Server IP address: " SERVER_IP
read -s -p "MySQL password for revinteq_user: " DB_PASSWORD; echo
read -p "Django secret key (Enter to auto-generate): " DJANGO_SECRET
read -p "Meta App ID: " META_APP_ID
read -s -p "Meta App Secret: " META_APP_SECRET; echo
read -p "WhatsApp webhook verify token (any word): " WA_TOKEN
read -p "Admin email: " ADMIN_EMAIL

[ -z "$DJANGO_SECRET" ] && DJANGO_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
ENCRYPTION_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
[ -z "$DOMAIN" ] && DOMAIN=$SERVER_IP
SITE_URL="https://${DOMAIN}"
ALLOWED_HOSTS="${DOMAIN},www.${DOMAIN},${SERVER_IP},localhost"
META_REDIRECT="${SITE_URL}/api/v1/meta/callback/"
CORS_ORIGINS="${SITE_URL},http://localhost:5173"

log "Configuration ready"

section "Phase 1: System packages"
apt-get update -qq && apt-get upgrade -y -qq
apt-get install -y -qq \
    python3.12 python3.12-venv python3-pip \
    nginx mysql-server redis-server \
    git curl wget unzip supervisor \
    build-essential pkg-config \
    libssl-dev libffi-dev python3-dev \
    default-libmysqlclient-dev libmysqlclient-dev

# Install Node.js 20 LTS for Vue build
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs
log "System packages + Node.js $(node --version) installed"

section "Phase 2: MySQL"
systemctl start mysql && systemctl enable mysql
mysql -u root <<SQL
CREATE DATABASE IF NOT EXISTS revinteq CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'revinteq_user'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON revinteq.* TO 'revinteq_user'@'localhost';
FLUSH PRIVILEGES;
SQL
log "MySQL ready"

section "Phase 3: Redis"
systemctl start redis-server && systemctl enable redis-server
redis-cli ping | grep -q PONG && log "Redis running" || err "Redis failed"

section "Phase 4: Application files"
APP="/var/www/revinteq"
mkdir -p ${APP}/staticfiles ${APP}/media
mkdir -p /var/log/revinteq

SRC="/root/revinteq-v3"
VSRC="/root/revinteq-vue"

[ -d "$SRC" ]  || err "Backend not found at $SRC"
[ -d "$VSRC" ] || err "Frontend not found at $VSRC"

cp -r ${SRC}/* ${APP}/
log "Backend files copied"

section "Phase 5: Vue 3 frontend build"
cd ${VSRC}
npm install --silent
npm run build
log "Vue frontend built"

# Deploy Vue dist to Nginx serving location
mkdir -p ${APP}/dist
cp -r ${VSRC}/dist/* ${APP}/dist/
log "Vue frontend deployed to ${APP}/dist/"

section "Phase 6: Python virtualenv"
cd ${APP}
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
log "Python packages installed"

section "Phase 7: Environment (.env)"
cat > ${APP}/.env <<ENV
DJANGO_SECRET_KEY=${DJANGO_SECRET}
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=${ALLOWED_HOSTS}
DB_NAME=revinteq
DB_USER=revinteq_user
DB_PASSWORD=${DB_PASSWORD}
DB_HOST=localhost
DB_PORT=3306
REDIS_URL=redis://127.0.0.1:6379/0
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0
META_APP_ID=${META_APP_ID}
META_APP_SECRET=${META_APP_SECRET}
META_REDIRECT_URI=${META_REDIRECT}
META_SCOPES=ads_read,business_management,instagram_basic,instagram_manage_insights,whatsapp_business_management,whatsapp_business_messaging
WHATSAPP_WEBHOOK_VERIFY_TOKEN=${WA_TOKEN}
SITE_URL=${SITE_URL}
FIELD_ENCRYPTION_KEY=${ENCRYPTION_KEY}
CORS_ALLOWED_ORIGINS=${CORS_ORIGINS}
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=${ADMIN_EMAIL}
EMAIL_HOST_PASSWORD=
ENV
chmod 600 ${APP}/.env
log ".env created"

section "Phase 8: Django setup"
cd ${APP}
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python manage.py migrate --noinput
log "Migrations applied"

python manage.py collectstatic --noinput -v 0
log "Static files collected"

python manage.py shell <<PYSHELL
from django.contrib.auth.models import User
from apps.tenants.models import Tenant, TenantUser
from apps.accounts.models import UserProfile

u, created = User.objects.get_or_create(username='admin', defaults={
    'email': '${ADMIN_EMAIL}', 'is_staff': True, 'is_superuser': True,
    'first_name': 'Gimsc', 'last_name': 'Admin',
})
if created:
    u.set_password('${DB_PASSWORD}')
    u.save()
    UserProfile.objects.get_or_create(user=u, defaults={'full_name': 'Gimsc Admin'})

t, _ = Tenant.objects.get_or_create(slug='gimsc-admin', defaults={
    'name': 'Gimsc Solutions Ltd', 'status': 'active',
    'contact_email': '${ADMIN_EMAIL}',
})
TenantUser.objects.get_or_create(user=u, tenant=t, defaults={'role': 'SUPER_ADMIN'})
print("Superuser + admin tenant ready.")
PYSHELL
log "Superuser created"

chown -R www-data:www-data ${APP}
chmod -R 755 ${APP}
chmod 600 ${APP}/.env

section "Phase 9: Gunicorn"
cat > /etc/systemd/system/revinteq.service <<GUNICORN
[Unit]
Description=Revinteq v3 Django/Gunicorn
After=network.target mysql.service redis.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=${APP}
Environment="DJANGO_SETTINGS_MODULE=config.settings.production"
ExecStart=${APP}/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:${APP}/revinteq.sock \
    --log-file /var/log/revinteq/gunicorn.log \
    --access-logfile /var/log/revinteq/access.log \
    --timeout 120 \
    config.wsgi:application
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
GUNICORN

section "Phase 10: Celery (Supervisor)"
cat > /etc/supervisor/conf.d/revinteq.conf <<CELERY
[program:revinteq-worker]
command=${APP}/venv/bin/celery -A config worker -l info -Q celery,meta_sync,metrics,recommendations
directory=${APP}
user=www-data
autostart=true
autorestart=true
stopwaitsecs=600
stdout_logfile=/var/log/revinteq/celery-worker.log
stderr_logfile=/var/log/revinteq/celery-worker-err.log
environment=DJANGO_SETTINGS_MODULE="config.settings.production"

[program:revinteq-beat]
command=${APP}/venv/bin/celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
directory=${APP}
user=www-data
autostart=true
autorestart=true
stdout_logfile=/var/log/revinteq/celery-beat.log
stderr_logfile=/var/log/revinteq/celery-beat-err.log
environment=DJANGO_SETTINGS_MODULE="config.settings.production"
CELERY

section "Phase 11: Nginx"
cat > /etc/nginx/sites-available/revinteq <<NGINX
limit_req_zone \$binary_remote_addr zone=api:10m rate=200r/m;
limit_req_zone \$binary_remote_addr zone=mpesa:10m rate=600r/m;

server {
    listen 80;
    server_name ${DOMAIN} www.${DOMAIN} ${SERVER_IP};

    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";
    add_header X-XSS-Protection "1; mode=block";

    # Vue 3 SPA — serves the built frontend
    location / {
        root ${APP}/dist;
        try_files \$uri \$uri/ /index.html;
        expires 1h;
        add_header Cache-Control "public, must-revalidate";
    }

    # Vue JS/CSS assets — cache aggressively (Vite generates hashed filenames)
    location /assets/ {
        root ${APP}/dist;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Django static files
    location /static/ {
        alias ${APP}/staticfiles/;
        expires 30d;
        add_header Cache-Control "public";
    }

    location /media/ {
        alias ${APP}/media/;
    }

    # Django API (rate limited)
    location /api/ {
        limit_req zone=api burst=60 nodelay;
        proxy_pass http://unix:${APP}/revinteq.sock;
        proxy_set_header Host              \$host;
        proxy_set_header X-Real-IP         \$remote_addr;
        proxy_set_header X-Forwarded-For   \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;
    }

    # M-Pesa Daraja callbacks (higher burst — Safaricom sends fast)
    location /api/v1/mpesa/callback/ {
        limit_req zone=mpesa burst=200 nodelay;
        proxy_pass http://unix:${APP}/revinteq.sock;
        proxy_set_header Host              \$host;
        proxy_set_header X-Real-IP         \$remote_addr;
        proxy_set_header X-Forwarded-For   \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Django admin panel
    location /admin/ {
        proxy_pass http://unix:${APP}/revinteq.sock;
        proxy_set_header Host              \$host;
        proxy_set_header X-Real-IP         \$remote_addr;
        proxy_set_header X-Forwarded-For   \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Block sensitive files
    location ~ /\.(env|git|htaccess) { deny all; return 404; }

    gzip on;
    gzip_types text/plain application/json application/javascript
               text/css text/xml application/xml+rss;
    gzip_min_length 1000;
}
NGINX

rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/revinteq /etc/nginx/sites-enabled/revinteq
nginx -t && log "Nginx config valid"

section "Phase 12: Firewall"
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 'Nginx Full'
ufw --force enable
log "Firewall configured"

section "Phase 13: Start all services"
systemctl daemon-reload
systemctl enable revinteq && systemctl start revinteq && log "Gunicorn started"
supervisorctl reread && supervisorctl update
supervisorctl start revinteq-worker revinteq-beat && log "Celery started"
systemctl reload nginx && log "Nginx reloaded"

# HTTPS
if [ "$DOMAIN" != "$SERVER_IP" ]; then
    section "Phase 14: HTTPS (Let's Encrypt)"
    apt-get install -y -qq certbot python3-certbot-nginx
    certbot --nginx \
        -d "${DOMAIN}" \
        -d "www.${DOMAIN}" \
        --non-interactive --agree-tos \
        --email "${ADMIN_EMAIL}" --redirect
    log "HTTPS certificate installed"
fi

section "Deployment Complete!"
echo ""
echo -e "${GREEN}${BOLD}  Revinteq v3 is live!${NC}"
echo ""
echo -e "  App:           ${GREEN}${SITE_URL}${NC}"
echo -e "  Login:         ${GREEN}${SITE_URL}/login${NC}"
echo -e "  Admin Login:   ${GREEN}${SITE_URL}/admin/login${NC}"
echo -e "  Django Admin:  ${GREEN}${SITE_URL}/admin/${NC}"
echo -e "  API Docs:      ${GREEN}${SITE_URL}/api/docs/${NC}"
echo ""
echo -e "${BOLD}Admin credentials:${NC}"
echo -e "  Email:    ${ADMIN_EMAIL}"
echo -e "  Password: (same as DB password — change immediately!)"
echo ""
echo -e "${BOLD}Meta App Dashboard — configure these three things:${NC}"
echo -e "  OAuth redirect:         ${META_REDIRECT}"
echo -e "  WhatsApp webhook URL:   ${SITE_URL}/api/v1/whatsapp/webhook/"
echo -e "  Messenger webhook URL:  ${SITE_URL}/api/v1/messenger/webhook/"
echo -e "  Instagram webhook URL:  ${SITE_URL}/api/v1/instagram/webhook/"
echo -e "  Webhook verify token:   ${WA_TOKEN}"
echo -e "  Subscribe to:           messages, messaging_referrals"
echo ""
echo -e "${BOLD}Logs:${NC}"
echo -e "  tail -f /var/log/revinteq/gunicorn.log"
echo -e "  tail -f /var/log/revinteq/celery-worker.log"
echo -e "  supervisorctl status"
echo ""
