# FeedJam Deployment Guide

## Architecture

```
GitHub (push to main)
    ↓
GitHub Actions (CI → Build → Deploy)
    ↓
DockerHub (image registry)
    ↓
EC2 Instance
    ├── Caddy (reverse proxy, SSL)
    ├── API (FastAPI + Gunicorn)
    ├── Web (static files)
    ├── PostgreSQL
    └── Redis
```

## Prerequisites

- AWS EC2 instance (t3.small or larger recommended)
- DockerHub account
- Domain name
- Cloudflare account (optional, for DNS)

## GitHub Secrets

Add these in your repo: Settings → Secrets and variables → Actions

| Secret | Description |
|--------|-------------|
| `DOCKERHUB_USERNAME` | Your DockerHub username |
| `DOCKERHUB_TOKEN` | DockerHub access token (not password) |
| `EC2_HOST` | EC2 public IP or hostname |
| `EC2_USER` | SSH user (`ubuntu`, `ec2-user`, etc.) |
| `EC2_SSH_KEY` | Full private SSH key content |

## EC2 Setup (One-time)

### 1. Launch EC2 Instance

- **AMI**: Ubuntu 22.04 LTS
- **Instance type**: t3.small (2 vCPU, 2GB RAM) minimum
- **Storage**: 20GB+ EBS
- **Security Group**:
  - SSH (22) - your IP only
  - HTTP (80) - anywhere
  - HTTPS (443) - anywhere

### 2. Install Docker

```bash
# Connect to EC2
ssh -i your-key.pem ubuntu@your-ec2-ip

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Log out and back in for group to take effect
exit
ssh -i your-key.pem ubuntu@your-ec2-ip

# Verify
docker --version
docker compose version
```

### 3. Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/feedjam.git ~/feedjam
cd ~/feedjam
```

### 4. Configure Environment

```bash
nano .env.prod
```

Create with these values:
```env
# Required
DOMAIN=feedjam.yourdomain.com
POSTGRES_USER=feedjam
POSTGRES_PASSWORD=<generate-strong-password>
POSTGRES_DB=feedjam
JWT_SECRET_KEY=<run: openssl rand -hex 32>
DOCKERHUB_USERNAME=your-dockerhub-username

# Optional
OPEN_AI_KEY=sk-...
WEBHOOK_SECRET=<random-string>
ENABLE_SUMMARIZATION=true
```

### 5. Initial Deploy

```bash
cd ~/feedjam
export $(cat .env.prod | xargs)

# Pull and start (first time may take a few minutes)
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

## DNS Setup (Cloudflare)

1. Go to Cloudflare DNS settings for your domain
2. Add an **A record**:
   - Name: `feedjam` (or `@` for root)
   - Content: Your EC2 public IP
   - Proxy: OFF (grey cloud) - let Caddy handle SSL
3. Wait for DNS propagation (usually minutes)

Caddy will automatically provision Let's Encrypt SSL certificates.

## Deploy Flow

```
1. Push code to main branch
2. CI workflow runs (lint + tests)
3. On CI success, Deploy workflow triggers:
   - Builds Docker images
   - Pushes to DockerHub
   - SSHs to EC2
   - Pulls new images
   - Restarts containers
4. Done! (~3-5 minutes total)
```

## Manual Deployment

If you need to deploy manually:

```bash
ssh ubuntu@your-ec2-ip
cd ~/feedjam
git pull origin main
export $(cat .env.prod | xargs)
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d --force-recreate
```

## Useful Commands

```bash
# View logs
docker compose -f docker-compose.prod.yml logs -f api
docker compose -f docker-compose.prod.yml logs -f caddy

# Restart specific service
docker compose -f docker-compose.prod.yml restart api

# Check status
docker compose -f docker-compose.prod.yml ps

# Run migrations manually
docker compose -f docker-compose.prod.yml exec api alembic upgrade head

# Access database
docker compose -f docker-compose.prod.yml exec db psql -U feedjam -d feedjam

# Cleanup unused images
docker image prune -f
```

## Troubleshooting

### SSL not working
- Ensure Cloudflare proxy is OFF (grey cloud)
- Check Caddy logs: `docker compose -f docker-compose.prod.yml logs caddy`
- Verify domain points to EC2 IP: `dig feedjam.yourdomain.com`

### API not responding
- Check API logs: `docker compose -f docker-compose.prod.yml logs api`
- Verify database is healthy: `docker compose -f docker-compose.prod.yml ps`

### Deploy fails
- Check GitHub Actions logs
- Verify SSH key is correct (no extra newlines)
- Test SSH manually: `ssh -i key.pem ubuntu@ec2-ip`

## Backups

### Database backup
```bash
docker compose -f docker-compose.prod.yml exec db pg_dump -U feedjam feedjam > backup.sql
```

### Restore
```bash
cat backup.sql | docker compose -f docker-compose.prod.yml exec -T db psql -U feedjam -d feedjam
```

## Scaling Considerations

For higher traffic:
- Increase EC2 instance size
- Add more Gunicorn workers in Dockerfile.prod (`-w 4` instead of `-w 2`)
- Consider managed PostgreSQL (RDS) for production
- Add CloudFront CDN for static assets
