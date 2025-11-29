from PIL import Image, ImageDraw, ImageFont
import os

# Define the architecture diagram as text
architecture_text = """
Resume Screening System Architecture

┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   User Interface                         │   │
│  │  • Web Browser                                           │   │
│  │  • HTML Templates (Jinja2)                               │   │
│  │  • CSS Styling                                           │   │
│  │  • JavaScript Interactions                               │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND                                 │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                 Flask Web Application                    │   │
│  │  • Main App Controller (app.py)                          │   │
│  │  • Routing & Request Handling                            │   │
│  │  • Session Management                                    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │               Resume Screening Agent                      │   │
│  │  • LLM Integration (Groq API)                            │   │
│  │  • Resume Parsing & Analysis                             │   │
│  │  • Scoring Algorithm                                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   Hybrid Search Engine                   │   │
│  │  • Vector Database (FAISS)                               │   │
│  │  • Semantic Similarity Matching                          │   │
│  │  • Keyword Search                                        │   │
│  │  • Result Ranking                                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   Storage Components                     │   │
│  │  • SQLite Database (History & Results)                   │   │
│  │  • File Parser (PDF, DOCX, TXT)                          │   │
│  │  • Export Utilities (PDF, Excel)                         │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Groq API                              │   │
│  │  • Large Language Model Access                           │   │
│  │  • Resume Analysis & Scoring                             │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

Data Flow:
User Interface → Flask App → Resume Screening Agent → Groq API
                          ↘ Hybrid Search Engine → Vector DB
                          ↘ SQLite Database
                          ↘ File Parser
                          ↘ Export Utilities
"""

# Create image
width, height = 800, 1000
background_color = (255, 255, 255)
text_color = (0, 0, 0)

# Create image and drawing context
img = Image.new('RGB', (width, height), background_color)
draw = ImageDraw.Draw(img)

# Try to use a better font, fall back to default if not available
try:
    font = ImageFont.truetype("arial.ttf", 14)
except:
    font = ImageFont.load_default()

# Draw text
lines = architecture_text.strip().split('\n')
y_position = 20
for line in lines:
    draw.text((20, y_position), line, fill=text_color, font=font)
    y_position += 18

# Save image
img.save("updated_architecture.png")
print("Architecture diagram saved as updated_architecture.png")