# Resume Screening Agent - Deployment Guide

## Project Structure
```
rooman13/
├── backend/              # Backend API
│   ├── app.py
│   ├── resume_screening_agent.py
│   ├── file_parser.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── Procfile
│   ├── runtime.txt
│   └── .env
└── frontend/            # Frontend assets
    ├── templates/
    └── static/
```

## Deployment Options

### 1. Render.com (Recommended - Free Tier Available)

**Steps:**
1. Create account at https://render.com
2. Connect your GitHub repository
3. Create new Web Service
4. Configure:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120`
   - Environment: Add `GROQ_API_KEY`
5. Deploy!

**Pros:** Free tier, auto-deploy, easy setup
**Cons:** Cold starts on free tier

---

### 2. Railway.app (Easy Deploy)

**Steps:**
1. Visit https://railway.app
2. Connect GitHub repo
3. Select `backend` folder
4. Add environment variable: `GROQ_API_KEY`
5. Deploy automatically

**Pros:** Simple, fast deploys
**Cons:** Paid after free trial

---

### 3. Heroku

**Steps:**
```bash
cd backend
heroku login
heroku create your-app-name
heroku config:set GROQ_API_KEY=your_key_here
git push heroku main
```

**Pros:** Mature platform, add-ons
**Cons:** No free tier anymore

---

### 4. Docker Deployment (Any Platform)

**Build:**
```bash
cd backend
docker build -t resume-screening-agent .
```

**Run locally:**
```bash
docker run -p 5000:5000 -e GROQ_API_KEY=your_key resume-screening-agent
```

**Deploy to:**
- AWS ECS
- Google Cloud Run
- Azure Container Instances
- DigitalOcean App Platform

---

### 5. PythonAnywhere (Simplest)

**Steps:**
1. Create account at https://www.pythonanywhere.com
2. Upload files
3. Create virtual environment
4. Install requirements
5. Configure WSGI file
6. Add environment variables

**Pros:** Very simple, free tier
**Cons:** Limited resources

---

### 6. Vercel (Serverless)

**Steps:**
1. Install Vercel CLI: `npm i -g vercel`
2. Create `vercel.json`:
```json
{
  "builds": [{
    "src": "backend/app.py",
    "use": "@vercel/python"
  }]
}
```
3. Deploy: `vercel`

**Pros:** Serverless, fast CDN
**Cons:** Serverless limitations

---

## Environment Variables

Required:
- `GROQ_API_KEY` - Your Groq API key

Optional:
- `PORT` - Port number (default: 5000)
- `FLASK_ENV` - production/development

---

## Quick Local Test

```bash
cd backend
pip install -r requirements.txt
python app.py
```

Visit: http://localhost:5000

---

## Production Checklist

- [ ] Set `GROQ_API_KEY` environment variable
- [ ] Use production WSGI server (gunicorn)
- [ ] Enable HTTPS
- [ ] Set up monitoring
- [ ] Configure file upload limits
- [ ] Add rate limiting
- [ ] Set up logging
- [ ] Database for results (optional)

---

## Recommended: Render.com Free Deployment

**Why Render?**
- Free tier available
- Auto-deploy from Git
- HTTPS included
- Easy environment variables
- Good performance

**Deploy in 5 minutes:**
1. Push code to GitHub
2. Connect to Render
3. Add GROQ_API_KEY
4. Click Deploy
5. Done! ✅
