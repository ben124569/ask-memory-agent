# 🌩️ Cloudflare Workers Deployment

## Why Cloudflare Workers?
- ✅ **100,000 requests/day FREE**
- ✅ **No credit card required**
- ✅ **Global edge network** (super fast)
- ✅ **Built-in KV storage** for memories

## 🚀 Quick Setup (5 minutes)

### Step 1: Install Wrangler CLI
```bash
npm install -g wrangler
```

### Step 2: Login to Cloudflare
```bash
wrangler login
```

### Step 3: Create KV Namespace
```bash
wrangler kv:namespace create "MEMORY_KV"
wrangler kv:namespace create "MEMORY_KV" --preview
```

### Step 4: Update wrangler.toml
Replace the KV namespace IDs in `wrangler.toml` with the ones from step 3.

### Step 5: Set Secrets
```bash
wrangler secret put OPENAI_API_KEY
# Paste your OpenAI API key when prompted
```

### Step 6: Deploy
```bash
wrangler deploy
```

## 🎯 Your MCP Endpoint
After deployment, you'll get a URL like:
`https://ask-memory-agent.your-subdomain.workers.dev/mcp`

## 📱 Add to Claude App
1. Open Claude app
2. Settings → Developer → MCP Servers
3. Add New Server:
   - **Name:** Ask Memory Agent
   - **URL:** `https://ask-memory-agent.your-subdomain.workers.dev/mcp`

## 🧠 Available Tools
- **ask_memory** - Ask questions about stored memories
- **store_memory** - Store new information  
- **search_memory** - Search your memories

## 💰 Cost
- **Cloudflare Workers:** FREE (100k requests/day)
- **OpenAI API:** ~$0.01-0.10/day
- **Total:** Under $3/month even with heavy usage!