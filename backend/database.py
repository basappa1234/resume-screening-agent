"""
Database module for storing resume screening sessions and results
Also stores parsed resumes and job descriptions for persistent retrieval
"""
import sqlite3
import json
import os
from typing import List, Dict, Optional, Any
from datetime import datetime

class DatabaseManager:
    """Manages SQLite database for resume screening application"""
    
    def __init__(self, db_path: str = "screening_sessions.db"):
        """
        Initialize database manager
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create database tables if they don't exist"""
        try:
            import os
            # Ensure the directory exists for the database file
            db_dir = os.path.dirname(self.db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    job_title TEXT NOT NULL,
                    num_resumes INTEGER NOT NULL,
                    session_data TEXT NOT NULL
                )
            """)
            
            # Create results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    resume_id TEXT NOT NULL,
                    candidate_name TEXT NOT NULL,
                    overall_score REAL NOT NULL,
                    skills_match_score REAL NOT NULL,
                    experience_score REAL NOT NULL,
                    education_score REAL NOT NULL,
                    reasoning TEXT NOT NULL,
                    strengths TEXT NOT NULL,
                    weaknesses TEXT NOT NULL,
                    recommendation TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions (id)
                )
            """)
            
            # Create parsed resumes table for persistent storage
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS parsed_resumes (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    skills TEXT NOT NULL,
                    experience TEXT NOT NULL,
                    education TEXT NOT NULL,
                    summary TEXT,
                    raw_content TEXT NOT NULL,
                    parsed_timestamp TEXT NOT NULL
                )
            """)
            
            # Create job descriptions table for persistent storage
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS job_descriptions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    company TEXT,
                    required_skills TEXT NOT NULL,
                    preferred_skills TEXT NOT NULL,
                    experience_years INTEGER NOT NULL,
                    responsibilities TEXT NOT NULL,
                    qualifications TEXT NOT NULL,
                    description TEXT NOT NULL,
                    raw_content TEXT NOT NULL,
                    parsed_timestamp TEXT NOT NULL
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            # In Vercel environment, we'll use in-memory storage instead
            if not os.environ.get('VERCEL'):
                print(f"Error initializing database: {e}")
                raise e  # Re-raise for non-Vercel environments
    
    def save_session(self, job_title: str, num_resumes: int, session_data: Dict) -> int:
        """
        Save a screening session
        
        Args:
            job_title: Job title
            num_resumes: Number of resumes screened
            session_data: Session data
            
        Returns:
            Session ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        session_json = json.dumps(session_data, ensure_ascii=False)
        
        cursor.execute("""
            INSERT INTO sessions (timestamp, job_title, num_resumes, session_data)
            VALUES (?, ?, ?, ?)
        """, (timestamp, job_title, num_resumes, session_json))
        
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return session_id
    
    def save_results(self, session_id: int, results: List[Dict]) -> None:
        """
        Save screening results
        
        Args:
            session_id: Session ID
            results: List of result dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for result in results:
            strengths_json = json.dumps(result.get('strengths', []), ensure_ascii=False)
            weaknesses_json = json.dumps(result.get('weaknesses', []), ensure_ascii=False)
            
            cursor.execute("""
                INSERT INTO results (
                    session_id, resume_id, candidate_name, overall_score,
                    skills_match_score, experience_score, education_score,
                    reasoning, strengths, weaknesses, recommendation
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                result.get('resume_id', ''),
                result.get('candidate_name', ''),
                result.get('overall_score', 0.0),
                result.get('skills_match_score', 0.0),
                result.get('experience_score', 0.0),
                result.get('education_score', 0.0),
                result.get('reasoning', ''),
                strengths_json,
                weaknesses_json,
                result.get('recommendation', 'NOT_RECOMMENDED')
            ))
        
        conn.commit()
        conn.close()
    
    def save_parsed_resume(self, resume_data: Dict) -> None:
        """
        Save a parsed resume to the database
        
        Args:
            resume_data: Parsed resume data
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Convert lists to JSON strings for storage
        skills_json = json.dumps(resume_data.get('skills', []), ensure_ascii=False)
        experience_json = json.dumps(resume_data.get('experience', []), ensure_ascii=False)
        education_json = json.dumps(resume_data.get('education', []), ensure_ascii=False)
        
        cursor.execute("""
            INSERT OR REPLACE INTO parsed_resumes (
                id, name, email, phone, skills, experience, education, summary, raw_content, parsed_timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            resume_data.get('id', ''),
            resume_data.get('name', ''),
            resume_data.get('email', ''),
            resume_data.get('phone', ''),
            skills_json,
            experience_json,
            education_json,
            resume_data.get('summary', ''),
            resume_data.get('raw_content', ''),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def save_job_description(self, job_data: Dict) -> None:
        """
        Save a job description to the database
        
        Args:
            job_data: Parsed job description data
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Convert lists to JSON strings for storage
        required_skills_json = json.dumps(job_data.get('required_skills', []), ensure_ascii=False)
        preferred_skills_json = json.dumps(job_data.get('preferred_skills', []), ensure_ascii=False)
        responsibilities_json = json.dumps(job_data.get('responsibilities', []), ensure_ascii=False)
        qualifications_json = json.dumps(job_data.get('qualifications', []), ensure_ascii=False)
        
        cursor.execute("""
            INSERT OR REPLACE INTO job_descriptions (
                id, title, company, required_skills, preferred_skills,
                experience_years, responsibilities, qualifications, description, raw_content, parsed_timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job_data.get('id', ''),
            job_data.get('title', ''),
            job_data.get('company', ''),
            required_skills_json,
            preferred_skills_json,
            job_data.get('experience_years', 0),
            responsibilities_json,
            qualifications_json,
            job_data.get('description', ''),
            job_data.get('raw_content', ''),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def get_all_sessions(self) -> List[Dict]:
        """
        Get all screening sessions
        
        Returns:
            List of session dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM sessions ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        
        sessions = []
        for row in rows:
            # Parse session data to extract company information
            session_data = json.loads(row[4]) if row[4] else {}
            job_desc = session_data.get('job_desc', {})
            
            session = {
                'id': row[0],
                'timestamp': row[1],
                'job_title': row[2],
                'company': job_desc.get('company', 'Unknown Company'),
                'total_candidates': row[3],
                'num_resumes': row[3],
                'session_data': session_data
            }
            sessions.append(session)
        
        conn.close()
        return sessions
    
    def get_session_results(self, session_id: int) -> List[Dict]:
        """
        Get results for a specific session
        
        Args:
            session_id: Session ID
            
        Returns:
            List of result dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM results WHERE session_id = ? ORDER BY overall_score DESC", (session_id,))
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            result = {
                'id': row[0],
                'session_id': row[1],
                'resume_id': row[2],
                'candidate_name': row[3],
                'overall_score': row[4],
                'skills_match_score': row[5],
                'experience_score': row[6],
                'education_score': row[7],
                'reasoning': row[8],
                'strengths': json.loads(row[9]) if row[9] else [],
                'weaknesses': json.loads(row[10]) if row[10] else [],
                'recommendation': row[11]
            }
            results.append(result)
        
        conn.close()
        return results
    
    def get_session_info(self, session_id: int) -> Optional[Dict]:
        """
        Get session information by session ID
        
        Args:
            session_id: Session ID
            
        Returns:
            Session information dictionary or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        session_info = {
            'id': row[0],
            'timestamp': row[1],
            'job_title': row[2],
            'num_resumes': row[3],
            'session_data': json.loads(row[4]) if row[4] else {}
        }
        
        conn.close()
        return session_info

    def get_parsed_resume(self, resume_id: str) -> Optional[Dict]:
        """
        Get a parsed resume from the database
        
        Args:
            resume_id: Resume ID
            
        Returns:
            Parsed resume data or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM parsed_resumes WHERE id = ?", (resume_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        resume = {
            'id': row[0],
            'name': row[1],
            'email': row[2],
            'phone': row[3],
            'skills': json.loads(row[4]) if row[4] else [],
            'experience': json.loads(row[5]) if row[5] else [],
            'education': json.loads(row[6]) if row[6] else [],
            'summary': row[7],
            'raw_content': row[8],
            'parsed_timestamp': row[9]
        }
        
        conn.close()
        return resume
    
    def get_all_parsed_resumes(self) -> List[Dict]:
        """
        Get all parsed resumes from the database
        
        Returns:
            List of parsed resume dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM parsed_resumes")
        rows = cursor.fetchall()
        
        resumes = []
        for row in rows:
            resume = {
                'id': row[0],
                'name': row[1],
                'email': row[2],
                'phone': row[3],
                'skills': json.loads(row[4]) if row[4] else [],
                'experience': json.loads(row[5]) if row[5] else [],
                'education': json.loads(row[6]) if row[6] else [],
                'summary': row[7],
                'raw_content': row[8],
                'parsed_timestamp': row[9]
            }
            resumes.append(resume)
        
        conn.close()
        return resumes
    
    def get_job_description(self, job_id: str) -> Optional[Dict]:
        """
        Get a job description from the database
        
        Args:
            job_id: Job description ID
            
        Returns:
            Job description data or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM job_descriptions WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        job_desc = {
            'id': row[0],
            'title': row[1],
            'company': row[2],
            'required_skills': json.loads(row[3]) if row[3] else [],
            'preferred_skills': json.loads(row[4]) if row[4] else [],
            'experience_years': row[5],
            'responsibilities': json.loads(row[6]) if row[6] else [],
            'qualifications': json.loads(row[7]) if row[7] else [],
            'description': row[8],
            'raw_content': row[9],
            'parsed_timestamp': row[10]
        }
        
        conn.close()
        return job_desc
    
    def clear_history(self) -> None:
        """Clear all screening history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM results")
        cursor.execute("DELETE FROM sessions")
        cursor.execute("DELETE FROM parsed_resumes")
        cursor.execute("DELETE FROM job_descriptions")
        
        conn.commit()
        conn.close()