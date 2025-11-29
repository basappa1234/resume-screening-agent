"""
Flask Web Application for Resume Screening Agent
Allows users to upload resumes and job descriptions via web interface
"""

import os
import json
# Load environment variables safely
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception as e:
    print(f"Warning: Could not load .env file: {e}")

from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify, session
from werkzeug.utils import secure_filename
from resume_screening_agent import ResumeScreeningAgent, Resume, JobDescription, ResumeScore
from file_parser import FileParser
from database import DatabaseManager
from export_utils import export_to_pdf, export_to_excel

from groq import Groq
from dataclasses import asdict
from datetime import datetime

# Set paths for templates and static files
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'templates')
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.secret_key = os.urandom(24)

# Configure upload folder - use /tmp for Vercel
if os.environ.get('VERCEL'):
    app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
else:
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'docx', 'doc', 'txt'}

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# For Vercel deployment, use in-memory database or disable persistence
if os.environ.get('VERCEL'):
    # Use a simple in-memory storage for sessions/results
    class InMemoryDatabase:
        def __init__(self):
            self.sessions = {}
            self.results = {}
            self.session_counter = 1
            self.result_counter = 1
        
        def get_all_sessions(self, include_hidden=False):
            return list(self.sessions.values())
        
        def save_session(self, job_title, company, results):
            session_id = self.session_counter
            self.sessions[session_id] = {
                'id': session_id,
                'job_title': job_title,
                'company': company,
                'timestamp': datetime.now().isoformat(),
                'is_hidden': False,
                'total_candidates': len(results)
            }
            
            # Save results
            for rank, result in enumerate(results, 1):
                result_id = self.result_counter
                self.results[result_id] = {
                    'id': result_id,
                    'session_id': session_id,
                    'resume_id': result.get('resume_id'),
                    'candidate_name': result.get('candidate_name'),
                    'overall_score': result.get('overall_score'),
                    'skills_match_score': result.get('skills_match_score'),
                    'experience_score': result.get('experience_score'),
                    'education_score': result.get('education_score'),
                    'reasoning': result.get('reasoning'),
                    'strengths': result.get('strengths', []),
                    'weaknesses': result.get('weaknesses', []),
                    'recommendation': result.get('recommendation'),
                    'rank': rank
                }
                self.result_counter += 1
            
            self.session_counter += 1
            return session_id
        
        def save_results(self, session_id, results):
            # Save results
            for rank, result in enumerate(results, 1):
                result_id = self.result_counter
                self.results[result_id] = {
                    'id': result_id,
                    'session_id': session_id,
                    'resume_id': result.get('resume_id'),
                    'candidate_name': result.get('candidate_name'),
                    'overall_score': result.get('overall_score'),
                    'skills_match_score': result.get('skills_match_score'),
                    'experience_score': result.get('experience_score'),
                    'education_score': result.get('education_score'),
                    'reasoning': result.get('reasoning'),
                    'strengths': result.get('strengths', []),
                    'weaknesses': result.get('weaknesses', []),
                    'recommendation': result.get('recommendation'),
                    'rank': rank
                }
                self.result_counter += 1
        
        def get_session_results(self, session_id):
            session = self.sessions.get(session_id, {})
            results = [r for r in self.results.values() if r['session_id'] == session_id]
            return session, results
        
        def hide_session(self, session_id):
            if session_id in self.sessions:
                self.sessions[session_id]['is_hidden'] = True
        
        def delete_session(self, session_id):
            if session_id in self.sessions:
                del self.sessions[session_id]
                # Remove associated results
                self.results = {k: v for k, v in self.results.items() if v['session_id'] != session_id}
        
        def clear_all_history(self):
            self.sessions = {}
            self.results = {}
    
    db_manager = InMemoryDatabase()
else:
    # Initialize database with absolute path for local development
    try:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'screening_history.db')
        db_manager = DatabaseManager(db_path=db_path)
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")
        # Create a mock database object
        class MockDatabase:
            def get_all_sessions(self, include_hidden=False):
                return []
            def save_session(self, job_title, company, results):
                return 1
            def save_results(self, session_id, results):
                pass
            def get_session_results(self, session_id):
                return {"job_title": "Sample Job", "company": "Sample Company", "timestamp": "2023-01-01"}, []
            def hide_session(self, session_id):
                pass
            def delete_session(self, session_id):
                pass
            def clear_all_history(self):
                pass
        db_manager = MockDatabase()

# Initialize the Resume Screening Agent
try:
    # Use a simpler initialization to avoid network issues
    agent = ResumeScreeningAgent(api_key=os.getenv("GROQ_API_KEY"))
except Exception as e:
    print(f"Warning: Could not initialize Resume Screening Agent: {e}")
    # Create a mock agent for basic functionality
    class MockAgent:
        def parse_job_description(self, text):
            from dataclasses import dataclass
            @dataclass
            class MockJobDescription:
                title: str = "Position"
                company: str = "Company"
                required_skills: list = None
                preferred_skills: list = None
                experience_years: int = 0
                responsibilities: list = None
                qualifications: list = None
                description: str = ""
                
                def __post_init__(self):
                    if self.required_skills is None:
                        self.required_skills = []
                    if self.preferred_skills is None:
                        self.preferred_skills = []
                    if self.responsibilities is None:
                        self.responsibilities = []
                    if self.qualifications is None:
                        self.qualifications = []
            
            return MockJobDescription(title="Position", description=text)
        
        def parse_resume(self, text):
            from dataclasses import dataclass
            @dataclass
            class MockResume:
                id: str = "resume"
                name: str = "Candidate"
                email: str = ""
                phone: str = ""
                skills: list = None
                experience: list = None
                education: list = None
                summary: str = ""
                
                def __post_init__(self):
                    if self.skills is None:
                        self.skills = []
                    if self.experience is None:
                        self.experience = []
                    if self.education is None:
                        self.education = []
            
            return MockResume(name="Candidate", summary=text[:300])
        
        def rank_resumes(self, resumes, job_desc, use_retrieval=True, retrieval_k=20):
            from dataclasses import dataclass
            @dataclass
            class MockResumeScore:
                resume_id: str = ""
                candidate_name: str = ""
                overall_score: float = 50.0
                skills_match_score: float = 50.0
                experience_score: float = 50.0
                education_score: float = 50.0
                reasoning: str = "Sample reasoning"
                strengths: list = None
                weaknesses: list = None
                recommendation: str = "Consider for interview"
                
                def __post_init__(self):
                    if self.strengths is None:
                        self.strengths = ["Strength 1", "Strength 2"]
                    if self.weaknesses is None:
                        self.weaknesses = ["Weakness 1", "Weakness 2"]
            
            return [MockResumeScore(resume_id=r.id, candidate_name=r.name) for r in resumes[:retrieval_k]]
    
    agent = MockAgent()


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def parse_file(file_obj):
    """
    Parse uploaded file object and extract text content
    
    Args:
        file_obj: Uploaded file object from Flask request
        
    Returns:
        Extracted text content
    """
    try:
        # Save file temporarily
        filename = secure_filename(file_obj.filename)
        if not filename:
            raise ValueError("Invalid filename")
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file_obj.save(file_path)
        
        # Parse based on extension
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        
        if ext == '.pdf':
            text = FileParser.parse_pdf(file_path)
        elif ext in ['.docx', '.doc']:
            text = FileParser.parse_docx(file_path)
        elif ext == '.txt':
            text = FileParser.parse_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
        
        # Clean up temporary file
        os.remove(file_path)
        
        return text
    except Exception as e:
        print(f"Error parsing file: {str(e)}")
        raise


def parse_resume_with_ai(text, filename, agent):
    """
    Use AI to extract structured information from resume text
    
    Args:
        text: Resume text content
        filename: Original filename
        agent: ResumeScreeningAgent instance
        
    Returns:
        Resume object with extracted information
    """
    prompt = f"""Extract the following information from this resume and return ONLY valid JSON:

RESUME TEXT:
{text}

Return JSON in this exact format:
{{
    "name": "Full Name",
    "email": "email@example.com",
    "phone": "+1-234-567-8900",
    "skills": ["skill1", "skill2", ...],
    "experience": [
        {{
            "title": "Job Title",
            "company": "Company Name",
            "duration": "2020-2023",
            "description": "Brief description"
        }}
    ],
    "education": [
        {{
            "degree": "Degree Name",
            "field": "Field of Study",
            "institution": "University Name",
            "year": "2020"
        }}
    ],
    "summary": "Brief professional summary"
}}

Extract what you can. Use "N/A" for missing information. Return ONLY valid JSON, no markdown."""

    try:
        response = agent.client.chat.completions.create(
            model=agent.model,
            messages=[
                {"role": "system", "content": "You are a resume parsing expert. Extract information and return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1500
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Extract JSON from response
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()
        
        data = json.loads(result_text)
        
        return Resume(
            id=filename.replace('.', '_'),
            name=data.get('name', 'Candidate'),
            email=data.get('email', ''),
            phone=data.get('phone', ''),
            skills=data.get('skills', []),
            experience=data.get('experience', []),
            education=data.get('education', []),
            summary=data.get('summary', text[:300])
        )
    except Exception as e:
        print(f"Error parsing resume with AI: {e}")
        # Fallback to basic parsing
        return Resume(
            id=filename.replace('.', '_'),
            name=filename.replace('_', ' ').replace('.pdf', '').replace('.docx', '').replace('.txt', ''),
            email='',
            phone='',
            skills=[],
            experience=[],
            education=[],
            summary=text[:300] if len(text) > 300 else text
        )


def parse_job_description_with_ai(text, agent):
    """
    Use AI to extract structured information from job description text
    
    Args:
        text: Job description text content
        agent: ResumeScreeningAgent instance
        
    Returns:
        JobDescription object with extracted information
    """
    prompt = f"""Extract the following information from this job description and return ONLY valid JSON:

JOB DESCRIPTION TEXT:
{text}

Return JSON in this exact format:
{{
    "title": "Job Title",
    "company": "Company Name",
    "required_skills": ["skill1", "skill2", ...],
    "preferred_skills": ["skill1", "skill2", ...],
    "experience_years": 5,
    "responsibilities": ["responsibility1", "responsibility2", ...],
    "qualifications": ["qualification1", "qualification2", ...],
    "description": "Full job description text"
}}

Extract what you can. Use reasonable defaults for missing information. Return ONLY valid JSON, no markdown."""

    try:
        response = agent.client.chat.completions.create(
            model=agent.model,
            messages=[
                {"role": "system", "content": "You are a job description parser. Extract information and return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=2000
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Extract JSON from response
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()
        
        data = json.loads(result_text)
        
        return JobDescription(
            title=data.get('title', 'Position'),
            company=data.get('company', 'Company'),
            required_skills=data.get('required_skills', []),
            preferred_skills=data.get('preferred_skills', []),
            experience_years=int(data.get('experience_years', 0)),
            responsibilities=data.get('responsibilities', []),
            qualifications=data.get('qualifications', []),
            description=data.get('description', text)
        )
    except Exception as e:
        print(f"Error parsing job description with AI: {e}")
        # Fallback to basic parsing
        return JobDescription(
            title='Position',
            company='Company',
            required_skills=[],
            preferred_skills=[],
            experience_years=0,
            responsibilities=[],
            qualifications=[],
            description=text
        )


@app.route('/')
def index():
    """Main landing page"""
    return render_template('landing.html')

@app.route('/upload')
def upload_page():
    """Upload page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle file uploads and initiate resume screening"""
    try:
        # Get job description (text or file)
        job_text = None
        job_description_text = request.form.get('job_description_text', '').strip()
        
        if job_description_text:
            # Use pasted text
            job_text = job_description_text
        elif 'job_description' in request.files:
            # Use uploaded file
            job_file = request.files['job_description']
            if job_file.filename != '':
                job_text = parse_file(job_file)
        
        if not job_text:
            return jsonify({'error': 'Please provide a job description (either paste text or upload a file)'}), 400
        
        # Get resume files
        resume_files = request.files.getlist('resumes')
        
        if not resume_files or resume_files[0].filename == '':
            return jsonify({'error': 'Please select at least one resume file'}), 400
        
        # Parse job description using the separate function
        job_desc = parse_job_description_with_ai(job_text, agent)
        
        # Parse resumes using the separate function
        parsed_resumes = []
        for resume_file in resume_files:
            try:
                resume_text = parse_file(resume_file)
                resume = parse_resume_with_ai(resume_text, resume_file.filename, agent)
                parsed_resumes.append(resume)
                
            except Exception as e:
                print(f"Error parsing resume {resume_file.filename}: {str(e)}")
                continue
        
        # Store in session for later use (temporary storage only)
        session['job_desc'] = {
            'title': job_desc.title,
            'company': job_desc.company,
            'required_skills': job_desc.required_skills,
            'preferred_skills': job_desc.preferred_skills,
            'experience_years': job_desc.experience_years,
            'responsibilities': job_desc.responsibilities,
            'qualifications': job_desc.qualifications,
            'description': job_desc.description
        }
        
        session['resumes'] = [
            {
                'id': resume.id,
                'name': resume.name,
                'email': resume.email,
                'phone': resume.phone,
                'skills': resume.skills,
                'experience': resume.experience,
                'education': resume.education,
                'summary': resume.summary
            }
            for resume in parsed_resumes
        ]
        
        # Get top_n parameter and validate it
        top_n = request.form.get('top_n', 3, type=int)
        # Ensure top_n is at least 1
        if top_n < 1:
            return jsonify({'error': 'Number of top candidates must be at least 1'}), 400
        # Ensure top_n doesn't exceed number of resumes
        elif top_n > len(parsed_resumes):
            return jsonify({'error': f'Number of top candidates ({top_n}) cannot be greater than the number of uploaded resumes ({len(parsed_resumes)})'}), 400
        
        session['top_n'] = top_n  # Store top_n in session
        
        return jsonify({
            'message': 'Files uploaded successfully',
            'job_title': job_desc.title,
            'num_resumes': len(parsed_resumes),
            'top_n': top_n
        })
        
    except Exception as e:
        print(f"Error in upload_files: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/screen', methods=['POST'])
def screen_resumes():
    """Screen resumes against job description using hybrid search"""
    try:
        # Get job description and resumes from session
        job_desc_data = session.get('job_desc')
        resumes_data = session.get('resumes')
        top_n = session.get('top_n', 3)  # Get top_n from session, default to 3
        
        if not job_desc_data or not resumes_data:
            return jsonify({'error': 'No job description or resumes found. Please upload files first.'}), 400
        
        # Validate top_n parameter
        if top_n < 1:
            return jsonify({'error': 'Number of top candidates must be at least 1'}), 400
        elif top_n > len(resumes_data):
            return jsonify({'error': f'Number of top candidates ({top_n}) cannot be greater than the number of uploaded resumes ({len(resumes_data)})'}), 400
        
        # Convert to data classes
        job_desc = JobDescription(**job_desc_data)
        
        resumes = []
        for resume_data in resumes_data:
            resume = Resume(**resume_data)
            resumes.append(resume)
        
        # Screen ONLY the top N candidates as specified by user
        print(f"Screening ONLY top {top_n} candidates as requested...")
        # We still use a reasonable pre-filter to ensure we have good candidates
        pre_filter_k = min(len(resumes), max(50, top_n * 2))  # At least 50 or 2x top_n
        ranked_results = agent.rank_resumes(resumes, job_desc, use_retrieval=True, retrieval_k=pre_filter_k)
        
        # Limit results to top_n as requested
        final_results = ranked_results[:top_n]
        
        # Save ONLY the screening results to database (not the raw resumes)
        results_data = [asdict(score) for score in final_results]
        session_id = db_manager.save_session(job_desc.title, len(resumes), {'job_desc': job_desc_data})
        db_manager.save_results(session_id, results_data)
        
        # Save parsed resumes to database for email retrieval
        for resume_data in resumes_data:
            try:
                db_manager.save_parsed_resume(resume_data)
            except Exception as e:
                print(f"Warning: Could not save parsed resume to database: {str(e)}")
        
        # Store results in session for display
        session['results'] = results_data
        session['job_title'] = job_desc.title
        session['session_id'] = session_id
        
        return jsonify({
            'message': 'Screening completed successfully',
            'num_candidates': len(final_results),
            'top_score': max([r.overall_score for r in final_results]) if final_results else 0
        })
        
    except Exception as e:
        print(f"Error in screen_resumes: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/results')
def show_results():
    """Display screening results"""
    try:
        results_data = session.get('results')
        job_title = session.get('job_title')
        session_id = session.get('session_id')
        
        if not results_data or not job_title:
            return redirect(url_for('index'))
        
        # Convert to ResumeScore objects for display
        results = [ResumeScore(**result_data) for result_data in results_data]
        
        return render_template('results.html', 
                             results=results,
                             job_title=job_title,
                             session_id=session_id)
        
    except Exception as e:
        print(f"Error in show_results: {str(e)}")
        return redirect(url_for('index'))

@app.route('/history')
def history():
    """Display screening history"""
    try:
        # Get all sessions from database
        sessions = db_manager.get_all_sessions()
        return render_template('history.html', sessions=sessions)
    except Exception as e:
        print(f"Error fetching history: {str(e)}")
        return render_template('history.html', sessions=[], error="Could not load history")

@app.route('/history/<int:session_id>')
def view_session(session_id):
    """View details of a specific screening session"""
    try:
        # Get session info and results from database
        session_info = db_manager.get_session_info(session_id)
        results_data = db_manager.get_session_results(session_id)
        
        if not session_info:
            flash('Session not found')
            return redirect(url_for('history'))
        
        # Convert results to ResumeScore objects
        results = []
        for result_data in results_data:
            # Convert JSON strings back to lists
            if isinstance(result_data.get('strengths'), str):
                result_data['strengths'] = json.loads(result_data['strengths'])
            if isinstance(result_data.get('weaknesses'), str):
                result_data['weaknesses'] = json.loads(result_data['weaknesses'])
            
            results.append(result_data)
        
        return render_template('results.html', 
                             results=results,
                             job_title=session_info.get('job_title', 'Unknown Position'),
                             session_id=session_id)
    except Exception as e:
        print(f"Error viewing session: {str(e)}")
        return redirect(url_for('history'))

@app.route('/hide-session/<int:session_id>', methods=['POST'])
def hide_session(session_id):
    """Hide a session from history"""
    try:
        db_manager.hide_session(session_id)
        flash('Session hidden successfully')
    except Exception as e:
        print(f"Error hiding session: {str(e)}")
        flash('Error hiding session')
    
    return redirect(url_for('history'))

@app.route('/delete-session/<int:session_id>', methods=['POST'])
def delete_session(session_id):
    """Delete a session from history"""
    try:
        db_manager.delete_session(session_id)
        flash('Session deleted successfully')
    except Exception as e:
        print(f"Error deleting session: {str(e)}")
        flash('Error deleting session')
    
    return redirect(url_for('history'))

@app.route('/clear-history')
def clear_history():
    """Clear all screening history"""
    try:
        db_manager.clear_all_history()
        flash('History cleared successfully')
    except Exception as e:
        print(f"Error clearing history: {str(e)}")
        flash('Error clearing history')
    
    return redirect(url_for('history'))

@app.route('/send-emails', methods=['POST'])
def send_emails():
    """Send email notifications to candidates"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        threshold = data.get('threshold', 70.0)
        job_title = data.get('job_title', 'Position')
        company_name = data.get('company_name', 'Company')
        
        if not session_id:
            return jsonify({'success': False, 'error': 'Session ID is required'}), 400
        
        # Get session info and results
        session_info = db_manager.get_session_info(session_id)
        results = db_manager.get_session_results(session_id)
        
        if not session_info:
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        
        # Email functionality has been disabled for security reasons
        # Return success response without sending emails
        stats = {"selected": 0, "not_selected": 0, "failed": 0, "emails_disabled": True}
        
        return jsonify({'success': True, 'stats': stats, 'message': 'Email functionality disabled for security reasons'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/export/<int:session_id>/<format>')
def export_session(session_id, format):
    """Export session to PDF or Excel"""
    # Get top_n from query params
    top_n = request.args.get('top_n', type=int)
    
    # Get session info and results
    session_info = db_manager.get_session_info(session_id)
    results = db_manager.get_session_results(session_id)
    
    if not session_info:
        return "Session not found", 404
    
    # Sanitize job title for filename
    job_title = session_info['job_title'].replace(' ', '_').replace('/', '_').replace('\\', '_')
    # Remove any non-alphanumeric characters except underscores and hyphens
    job_title = ''.join(c for c in job_title if c.isalnum() or c in ['_', '-'])
    
    if format == 'pdf':
        buffer = export_to_pdf(session_info, results, top_n)
        filename = f"screening_results_{job_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        response = send_file(buffer, download_name=filename, as_attachment=True, mimetype='application/pdf')
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Content-Security-Policy'] = "default-src 'self'"
        return response
    
    elif format == 'excel':
        buffer = export_to_excel(session_info, results, top_n)
        filename = f"screening_results_{job_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        response = send_file(buffer, download_name=filename, as_attachment=True, 
                           mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Content-Security-Policy'] = "default-src 'self'"
        return response
    
    else:
        return "Invalid format", 400


# Make sure the app is accessible for Vercel
application = app

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)

# Vercel requires this for serverless functions
app = app
