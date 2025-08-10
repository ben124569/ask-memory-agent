#!/bin/bash

echo "🌩️ Simple Cloudflare Workers Deployment"
echo ""

# Check if already logged in
if wrangler whoami > /dev/null 2>&1; then
    echo "✅ Already logged in to Cloudflare"
else
    echo "🔓 Please login to Cloudflare first:"
    echo "   wrangler login"
    echo ""
    exit 1
fi

echo "🔑 Setting up OpenAI API key..."
echo "Paste your OpenAI API key when prompted:"
wrangler secret put OPENAI_API_KEY

echo ""
echo "🚀 Deploying to Cloudflare Workers..."
wrangler deploy

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Your worker should be available at:"
echo "https://ask-memory-agent.[your-subdomain].workers.dev"
echo ""
echo "📱 Add this URL to Claude app:"
echo "https://ask-memory-agent.[your-subdomain].workers.dev/mcp"