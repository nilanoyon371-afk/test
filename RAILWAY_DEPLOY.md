# Railway Deployment Guide

## 🚂 Deploy Your Scraper API to Railway (FREE)

Railway offers a generous free tier perfect for your API!

---

## Option 1: Deploy via GitHub (Recommended)

### Step 1: Push Code to GitHub

```bash
cd c:\Users\Google11\Desktop\apphub1\backend

# Initialize git if not already done
git init
git add .
git commit -m "Initial commit - Scraper API with streaming"
git branch -M main

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/scraper-api.git
git push -u origin main
```

### Step 2: Deploy on Railway

1. Go to https://railway.app
2. Click "Start a New Project"
3. Select "Deploy from GitHub repo"
4. Choose your `scraper-api` repository
5. Railway will auto-detect Python and deploy!

**That's it!** Railway will:

- ✅ Auto-install dependencies from `requirements.txt`
- ✅ Run your FastAPI app
- ✅ Generate a public URL (e.g., `your-app.up.railway.app`)

---

## Option 2: Manual Railway CLI (If you have it installed)

If you already have Railway CLI installed elsewhere or via npm:

```bash
# Install via npm (if you have Node.js)
npm install -g @railway/cli

# Or download binary manually from:
# https://github.com/railwayapp/cli/releases

# Then link and deploy
railway link -p fa73dd0f-fdae-4ce9-8902-71f863e491dd
railway up
```

---

## Option 3: Deploy via Railway Dashboard (Easiest)

1. **Go to**: https://railway.app
2. **Login** with GitHub
3. **Click**: "New Project"
4. **Select**: "Deploy from GitHub"
5. **Choose**: Your repository
6. **Configure**:
   - Build Command: (auto-detected)
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
7. **Deploy!**

---

## 📋 Pre-Deployment Checklist

### ✅ Files Needed

- [x] `main.py` - Your FastAPI app
- [x] `requirements.txt` - Python dependencies
- [ ] `Procfile` - Optional start command (create below)
- [x] `railway.json` - Railway config (already created!)

### Create Procfile (Optional)

```bash
echo "web: uvicorn main:app --host 0.0.0.0 --port \$PORT" > Procfile
```

### Update requirements.txt

Make sure all dependencies are listed:

```txt
fastapi
uvicorn[standard]
httpx
beautifulsoup4
lxml
pydantic
python-multipart
```

---

## 🔧 Environment Variables (Optional)

If you need API keys or secrets:

1. Go to Railway Dashboard
2. Select your project
3. Click "Variables"
4. Add:
   - `DATABASE_URL` (if using database)
   - `API_KEY` (if implementing authentication)
   - etc.

---

## 🌐 After Deployment

Railway will give you a public URL:

```
https://your-app-production.up.railway.app
```

### Test Your Deployed API:

```bash
# Test health endpoint
curl https://your-app.up.railway.app/health

# Test global search
curl "https://your-app.up.railway.app/api/v1/search/global?query=blonde&limit_per_site=5"

# Test video streaming
curl "https://your-app.up.railway.app/api/v1/video/info?url=https://www.xnxx.com/video-xxx/sample"
```

---

## 💰 Railway Free Tier

**FREE TIER INCLUDES**:

- ✅ 500 hours/month (enough for 24/7 uptime!)
- ✅ 100 GB bandwidth
- ✅ 512 MB RAM per service
- ✅ Auto SSL/HTTPS
- ✅ Custom domains

**Perfect for**:

- Development
- Testing
- Small-scale production (10k-50k requests/month)

---

## 🚀 Alternative FREE Hosting Options

If Railway doesn't work:

### 1. **Render.com** (Also FREE)

- Similar to Railway
- 750 hours/month free
- Auto-deploy from GitHub
- https://render.com

### 2. **Fly.io** (FREE tier)

- 3 shared VMs
- 160 GB bandwidth
- https://fly.io

### 3. **Vercel** (For API Routes)

- Serverless functions
- Unlimited bandwidth (fair use)
- https://vercel.com

---

## 📊 Current Project ID

Your Railway project ID: `fa73dd0f-fdae-4ce9-8902-71f863e491dd`

If you have access to this project already, you can deploy directly via GitHub integration!

---

## ❓ Troubleshooting

### Issue: "Port already in use"

Railway sets `$PORT` automatically. Make sure your code uses it:

```python
# In main.py
import os

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
```

### Issue: "Module not found"

Add missing module to `requirements.txt`:

```bash
pip freeze > requirements.txt
```

### Issue: "Build failed"

Check build logs in Railway dashboard for errors.

---

## ✅ Deployment Checklist

- [ ] Push code to GitHub
- [ ] Create Railway account
- [ ] Connect GitHub to Railway
- [ ] Deploy from repo
- [ ] Test public URL
- [ ] Update frontend/apps to use new URL
- [ ] Monitor logs in Railway dashboard

---

## 🎉 Success!

Once deployed, your API is live at:

```
https://your-scraper-api.up.railway.app
```

Share this URL with:

- Frontend developers
- Mobile app developers
- API consumers

**Your zero-cost, high-performance scraper API is now LIVE!** 🚀

---

## 📱 Next Steps

1. **Update Demo Player**: Change API URL from `localhost` to Railway URL
2. **Test Globally**: Share URL with testers
3. **Monitor**: Check Railway logs for errors
4. **Scale**: Upgrade to paid tier if you exceed free limits (~$5/mo)
5. **Custom Domain**: Add `api.yourdomain.com` in Railway settings
