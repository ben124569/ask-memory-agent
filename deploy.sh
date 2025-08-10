#!/bin/bash

echo "🌩️ Deploying Ask Memory Agent to Cloudflare Workers..."
echo ""

# Check if logged in
if ! wrangler whoami > /dev/null 2>&1; then
    echo "🔓 First, login to Cloudflare:"
    echo "   wrangler login"
    echo ""
    echo "⚠️  This will open your browser to authenticate"
    wrangler login
fi

echo ""
echo "📦 Creating KV namespaces for memory storage..."

# Create KV namespaces
echo "Creating production KV namespace..."
PROD_KV_ID=$(wrangler kv namespace create "MEMORY_KV" --json | jq -r '.id')

echo "Creating preview KV namespace..."
PREVIEW_KV_ID=$(wrangler kv namespace create "MEMORY_KV" --preview --json | jq -r '.id')

echo ""
echo "📝 Updating wrangler.toml with KV namespace IDs..."

# Update wrangler.toml with actual IDs
sed -i.bak "s/your_kv_namespace_id/$PROD_KV_ID/" wrangler.toml
sed -i.bak "s/your_preview_kv_namespace_id/$PREVIEW_KV_ID/" wrangler.toml

echo ""
echo "🔑 Setting up OpenAI API key..."
echo "You'll be prompted to paste your OpenAI API key:"
wrangler secret put OPENAI_API_KEY

echo ""
echo "🚀 Deploying to Cloudflare Workers..."
wrangler deploy

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📱 Your MCP endpoint is ready:"
WORKER_URL=$(wrangler dev --no-local --json | jq -r '.url' | head -1)
echo "   ${WORKER_URL}/mcp"
echo ""
echo "Add this URL to your Claude app!"