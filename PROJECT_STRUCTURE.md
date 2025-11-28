# Resume Screening Agent - Project Structure

## 📁 Restructured for Easy Deployment

```
rooman13/
│
├── backend/                        # 🔧 BACKEND (Deploy this folder)
│   ├── app.py                      # Flask application
│   ├── resume_screening_agent.py   # AI agent core logic
│   ├── file_parser.py              # PDF/DOCX parser
│   ├── requirements.txt            # Python dependencies
│   ├── Dockerfile                  # Docker configuration
│   ├── Procfile                    # Heroku/Render deployment
│   ├── runtime.txt                 # Python version
│   ├── .env                        # Environment variables (API keys)
│   ├── .env.example                # Environment template
│   ├── .gitignore                  # Git ignore rules
│   ├── DEPLOYMENT.md               # Deployment guide
│   └── uploads/                    # Temporary file storage
│
├── frontend/                       # 🎨 FRONTEND (Served by backend)
│   ├── templates/
│   │   ├── index.html              # Upload page
│   │   └── results.html            # Results page
│   └── static/
│       └── css/
│           └── style.css           # Styling
│
├── architecture.png                # System architecture diagram
├── main.py                         # CLI version (optional)
├── sample_data.py                  # Test data
└── README.md                       # Documentation
```

## 🚀 Quick Start

### Local Development:
```bash
cd backend
pip install -r requirements.txt
python app.py
```
Visit: http://localhost:5000

### Production Deployment:
See `backend/DEPLOYMENT.md` for detailed deployment guides

## 🎯 Key Changes

✅ **Separated Backend & Frontend**
- Backend in `/backend` folder
- Frontend assets in `/frontend` folder
- Backend serves frontend templates/static files

✅ **Added Deployment Files**
- `Dockerfile` - Docker containerization
- `Procfile` - Heroku/Render deployment
- `runtime.txt` - Python version specification
- `DEPLOYMENT.md` - Complete deployment guide

✅ **Production Ready**
- Gunicorn WSGI server
- Environment variable management
- Proper file paths
- Upload folder in backend

## 📦 Deployment Options

1. **Render.com** (Recommended) - Free tier
2. **Railway.app** - Simple deployment
3. **Docker** - Any platform
4. **Heroku** - Enterprise grade
5. **PythonAnywhere** - Easiest
6. **Vercel** - Serverless

See `backend/DEPLOYMENT.md` for detailed instructions.
