# Vercel Deployment Guide

## Important Note
Streamlit apps are designed for persistent server environments and may have limitations on Vercel's serverless platform. However, this configuration should work for basic deployments.

## Deployment Steps

### 1. Install Vercel CLI (if not already installed)
```bash
npm install -g vercel
```

### 2. Login to Vercel
```bash
vercel login
```

### 3. Deploy to Vercel
```bash
vercel
```

Or for production:
```bash
vercel --prod
```

### 4. Environment Variables
The following environment variables are set in `vercel.json`:
- `PLAYWRIGHT_BROWSERS_PATH`: Set to "0" to use system browsers
- `STREAMLIT_SERVER_PORT`: Port for Streamlit server
- `STREAMLIT_SERVER_ADDRESS`: Server address
- `STREAMLIT_BROWSER_GATHER_USAGE_STATS`: Disable usage stats
- `STREAMLIT_SERVER_HEADLESS`: Run in headless mode

### 5. Build Configuration
- **Build Command**: Installs dependencies and Playwright browsers
- **Function Timeout**: 300 seconds (5 minutes)
- **Memory**: 3008 MB
- **Region**: iad1 (US East)

## Alternative Deployment Options

If you encounter issues with Vercel, consider these alternatives:

1. **Streamlit Cloud** (Recommended for Streamlit apps)
   - Free tier available
   - Native Streamlit support
   - Easy deployment via GitHub

2. **Railway**
   - Good for Python apps
   - Easy deployment
   - Free tier available

3. **Render**
   - Free tier available
   - Good for web services
   - Easy GitHub integration

4. **Heroku**
   - Traditional platform
   - Good documentation
   - Paid plans available

## Troubleshooting

### Playwright Browser Issues
If Playwright browsers fail to install:
1. Check build logs in Vercel dashboard
2. Ensure `packages.txt` is properly configured
3. Verify system dependencies are installed

### Timeout Issues
If requests timeout:
1. Increase `maxDuration` in `vercel.json`
2. Optimize scraping logic
3. Consider caching strategies

### Memory Issues
If you encounter memory errors:
1. Increase memory allocation in `vercel.json`
2. Optimize data processing
3. Consider pagination for large datasets

## Support
For issues specific to Vercel deployment, check:
- [Vercel Documentation](https://vercel.com/docs)
- [Vercel Community](https://github.com/vercel/vercel/discussions)
