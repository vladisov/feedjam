# FeedJam Email Worker

Cloudflare Worker that receives emails via Email Routing and forwards them to the FeedJam API.

## Setup

### 1. Prerequisites

- Cloudflare account with Email Routing enabled
- Domain configured in Cloudflare (e.g., `feedjam.app`)
- Wrangler CLI installed: `npm install -g wrangler`

### 2. Configure Subdomain

Add MX records for `in.feedjam.app` to route to Cloudflare:
- Go to Cloudflare Dashboard > DNS
- Add subdomain `in` if needed
- Go to Email > Email Routing > Enable Email Routing for `in.feedjam.app`

### 3. Deploy Worker

```bash
cd cloudflare-worker

# Login to Cloudflare
wrangler login

# Set the webhook secret
wrangler secret put WEBHOOK_SECRET

# Update wrangler.toml with production WEBHOOK_URL
# WEBHOOK_URL = "https://api.feedjam.app/webhooks/inbound-email"

# Deploy
wrangler deploy
```

### 4. Configure Email Routing

In Cloudflare Dashboard:
1. Go to Email > Email Routing
2. Click "Routing Rules"
3. Add a catch-all rule: `*@in.feedjam.app` -> Worker: `feedjam-email-worker`

## Testing

Send a test email to `{your-email-token}@in.feedjam.app` and check:
1. Worker logs in Cloudflare Dashboard > Workers > feedjam-email-worker > Logs
2. Feed items in FeedJam

## Environment Variables

| Variable | Description |
|----------|-------------|
| `WEBHOOK_URL` | FeedJam API webhook endpoint |
| `WEBHOOK_SECRET` | Secret key for webhook authentication |
