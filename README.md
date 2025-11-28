# 🎯 Resume Screening Agent

An AI-powered resume screening and ranking system that uses **Groq API** to intelligently match resumes with job descriptions. This agent provides detailed analysis, scoring, and recommendations for each candidate.

## ✨ Features

- 🤖 **AI-Powered Screening**: Uses Groq's LLM to analyze resumes with human-like understanding
- 📊 **Comprehensive Scoring**: Evaluates skills match, experience, and education
- 🏆 **Intelligent Ranking**: Automatically ranks candidates from best to least fit
- 💡 **Detailed Analysis**: Provides strengths, weaknesses, and hiring recommendations
- 📁 **JSON Export**: Save results for further processing or integration
- 🎨 **Beautiful Output**: Formatted console output with rankings and medals
- 📧 **Email Notifications**: Send automated emails to candidates about their application status

## 🛠️ Installation

### Prerequisites

- Python 3.8 or higher
- Groq API key ([Get one here](https://console.groq.com))

### Setup Steps

1. **Clone or download this repository**

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure API Key**

Create a `.env` file in the project root:
```bash
cp .env.example .env
```

Edit `.env` and add your Groq API key:
```
GROQ_API_KEY=your_actual_groq_api_key_here
```

4. **Configure Email Notifications (Optional)**

To enable email notifications to candidates, configure your email settings in `.env`:
```
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

For Gmail, you'll need to use an App Password instead of your regular password. See [Google's documentation](https://support.google.com/accounts/answer/185833) for instructions on generating an App Password.

## ▶️ Running the Application

### Local Development
```bash
cd backend
python app.py
```

Visit: http://localhost:5000

### Production Deployment

This application is ready for deployment to various platforms:

#### Render.com (Recommended)
1. Push this code to a GitHub repository
2. Create a new Web Service on Render
3. Connect your GitHub repository
4. Set the following environment variables:
   - `GROQ_API_KEY` - Your Groq API key
5. Deploy!

The application will automatically use the PORT environment variable provided by Render.

## 📁 Project Structure
```
rooman13/
├── backend/              # Backend API
│   ├── app.py            # Main Flask application
│   ├── resume_screening_agent.py  # AI screening logic
│   ├── file_parser.py    # Resume and job description parsing
│   ├── database.py       # SQLite database management
│   ├── export_utils.py   # PDF and Excel export functionality
│   ├── email_utils.py    # Email notification system
│   ├── requirements.txt  # Python dependencies
│   ├── Dockerfile        # Docker configuration
│   ├── Procfile          # Heroku/Render deployment config
│   ├── runtime.txt       # Python version specification
│   └── .env              # Environment variables (not committed)
└── frontend/             # Frontend assets
    ├── templates/        # HTML templates
    └── static/           # CSS, JavaScript, images
```

## 🔧 Configuration

### Environment Variables
- `GROQ_API_KEY` (Required) - Your Groq API key
- `SENDER_EMAIL` (Optional) - Email address for sending notifications
- `SENDER_PASSWORD` (Optional) - App password for email account
- `SMTP_SERVER` (Optional) - SMTP server address (default: smtp.gmail.com)
- `SMTP_PORT` (Optional) - SMTP port (default: 587)

## 🚀 Deployment Ready

This application is configured for easy deployment to:
- Render.com (using render.yaml)
- Heroku (using Procfile)
- Docker (using Dockerfile)
- Any Python hosting platform

## 📝 License

This project is open source and available under the MIT License.
