#!/bin/bash
# Vercel deployment script - Temporary fix for size limit

echo "🔄 Preparing for Vercel deployment..."

# Backup original requirements.txt
if [ -f "requirements.txt" ]; then
    cp requirements.txt requirements-full.txt
    echo "✅ Backed up original requirements.txt to requirements-full.txt"
fi

# Use minimal requirements for Vercel
if [ -f "requirements-vercel.txt" ]; then
    cp requirements-vercel.txt requirements.txt
    echo "✅ Using requirements-vercel.txt for Vercel"
else
    echo "❌ Error: requirements-vercel.txt not found!"
    exit 1
fi

# Deploy to Vercel
echo "🚀 Deploying to Vercel..."
vercel --prod

# Restore original requirements.txt
if [ -f "requirements-full.txt" ]; then
    cp requirements-full.txt requirements.txt
    echo "✅ Restored original requirements.txt"
fi

echo "✅ Done!"
