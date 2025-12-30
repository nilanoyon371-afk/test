# Render Deployment - Quick Reference

## Files Created

- ✅ `Procfile` - Start command
- ✅ `runtime.txt` - Python version
- ✅ `build.sh` - Build script
- ✅ `render.yaml` - Infrastructure as code

## Deploy Steps

1. Push to GitHub
2. Connect repo to Render
3. Configure service (Python 3, Free tier)
4. Set build command: `./build.sh`
5. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Deploy!

## Environment Variables (Render Dashboard)

```
PYTHON_VERSION=3.13.7
CORS_ORIGINS=*
```

## Test After Deploy

```bash
curl https://YOUR-APP.onrender.com/health
curl "https://YOUR-APP.onrender.com/list?base_url=https://xvideos.com/new/1&limit=3"
```

## Update Flutter App

```dart
apiBaseUrl = 'https://YOUR-APP.onrender.com'
```

See [render_deployment.md](file:///C:/Users/Google11/.gemini/antigravity/brain/1b983c56-0d41-4946-980f-8a1aafbed4cb/render_deployment.md) for full guide.
