"""
Resume Screening Agent
Uses Groq API to rank resumes based on job descriptions
Now with vector database retrieval for efficiency
"""
import os
import json
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from groq import Groq
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from vector_db import ResumeRetriever  # Import our new vector database

@dataclass
class Resume:
    """Resume data structure"""
    id: str
    name: str
    email: str
    phone: str
    skills: List[str]
    experience: List[Dict[str, str]]
    education: List[Dict[str, str]]
    summary: str

@dataclass
class JobDescription:
    """Job Description data structure"""
    title: str
    company: str
    required_skills: List[str]
    preferred_skills: List[str]
    experience_years: int
    responsibilities: List[str]
    qualifications: List[str]
    description: str

@dataclass
class ResumeScore:
    """Resume scoring result"""
    resume_id: str
    candidate_name: str
    overall_score: float
    skills_match_score: float
    experience_score: float
    education_score: float
    reasoning: str
    strengths: List[str]
    weaknesses: List[str]
    recommendation: str
    similarity_score: float = 0.0  # Add similarity score from vector DB

class ResumeScreeningAgent:
    """AI-powered Resume Screening Agent using Groq API with vector database retrieval"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.1-8b-instant"):
        """
        Initialize the Resume Screening Agent
        
        Args:
            api_key: Groq API key (if not provided, loads from environment)
            model: Groq model to use for screening
        """
        load_dotenv()
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found. Please set it in .env file or pass it directly.")
        
        self.client = Groq(api_key=self.api_key)
        self.model = model
        self.retriever = ResumeRetriever()  # Initialize our retriever
    
    def _create_screening_prompt(self, resume: Resume, job_desc: JobDescription) -> str:
        """Create a detailed prompt for resume screening"""
        
        resume_text = f"""
CANDIDATE INFORMATION:
Name: {resume.name}
Email: {resume.email}
Phone: {resume.phone}

SUMMARY:
{resume.summary}

SKILLS:
{', '.join(resume.skills)}

EXPERIENCE:
{self._format_experience(resume.experience)}

EDUCATION:
{self._format_education(resume.education)}
"""
        
        job_text = f"""
JOB TITLE: {job_desc.title}
COMPANY: {job_desc.company}

DESCRIPTION:
{job_desc.description}

REQUIRED SKILLS:
{', '.join(job_desc.required_skills)}

PREFERRED SKILLS:
{', '.join(job_desc.preferred_skills)}

MINIMUM EXPERIENCE: {job_desc.experience_years} years

RESPONSIBILITIES:
{self._format_list(job_desc.responsibilities)}

QUALIFICATIONS:
{self._format_list(job_desc.qualifications)}
"""
        
        prompt = f"""You are an expert recruiter and resume screening specialist. Analyze the following resume against the job description and provide a detailed evaluation.

{job_text}

---

{resume_text}

---

Please analyze this candidate and provide a JSON response with the following structure:
{{
    "overall_score": <float 0-100>,
    "skills_match_score": <float 0-100>,
    "experience_score": <float 0-100>,
    "education_score": <float 0-100>,
    "reasoning": "<detailed explanation of the scores>",
    "strengths": ["<strength 1>", "<strength 2>", ...],
    "weaknesses": ["<weakness 1>", "<weakness 2>", ...],
    "recommendation": "<HIGHLY_RECOMMENDED|RECOMMENDED|MAYBE|NOT_RECOMMENDED>"
}}

Evaluation Criteria:
1. Skills Match (0-100): How well do the candidate's skills align with required and preferred skills?
2. Experience Score (0-100): Does the candidate have relevant experience and meet the years requirement?
3. Education Score (0-100): Does the education background fit the role requirements?
4. Overall Score (0-100): Weighted average considering all factors
5. Provide specific strengths and weaknesses
6. Give a clear hiring recommendation

Be thorough, fair, and objective in your analysis. Return ONLY valid JSON."""
        
        return prompt
    
    def _format_experience(self, experience: List[Dict[str, str]]) -> str:
        """Format experience list for display"""
        formatted = []
        for exp in experience:
            formatted.append(
                f"• {exp.get('title', 'N/A')} at {exp.get('company', 'N/A')} "
                f"({exp.get('duration', 'N/A')})\n  {exp.get('description', '')}"
            )
        return '\n'.join(formatted)
    
    def _format_education(self, education: List[Dict[str, str]]) -> str:
        """Format education list for display"""
        formatted = []
        for edu in education:
            formatted.append(
                f"• {edu.get('degree', 'N/A')} in {edu.get('field', 'N/A')} "
                f"from {edu.get('institution', 'N/A')} ({edu.get('year', 'N/A')})"
            )
        return '\n'.join(formatted)
    
    def _format_list(self, items: List[str]) -> str:
        """Format list items with bullets"""
        return '\n'.join([f"• {item}" for item in items])
    
    def screen_resume(self, resume: Resume, job_desc: JobDescription) -> ResumeScore:
        """
        Screen a single resume against a job description
        
        Args:
            resume: Resume object to screen
            job_desc: Job description to match against
            
        Returns:
            ResumeScore object with detailed evaluation
        """
        prompt = self._create_screening_prompt(resume, job_desc)
        
        # Try up to 3 times with exponential backoff for rate limiting
        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert recruiter. Analyze resumes objectively and return valid JSON responses only."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,
                    max_tokens=2000
                )
                
                result_text = response.choices[0].message.content.strip()
                
                # Extract JSON from response (handle potential markdown code blocks)
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0].strip()
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0].strip()
                
                result = json.loads(result_text)
                
                return ResumeScore(
                    resume_id=resume.id,
                    candidate_name=resume.name,
                    overall_score=float(result.get("overall_score", 0)),
                    skills_match_score=float(result.get("skills_match_score", 0)),
                    experience_score=float(result.get("experience_score", 0)),
                    education_score=float(result.get("education_score", 0)),
                    reasoning=result.get("reasoning", ""),
                    strengths=result.get("strengths", []),
                    weaknesses=result.get("weaknesses", []),
                    recommendation=result.get("recommendation", "NOT_RECOMMENDED")
                )
                
            except Exception as e:
                # Check if it's a rate limit error
                if "rate_limit_exceeded" in str(e) and attempt < 2:
                    # Wait before retrying (exponential backoff)
                    import time
                    wait_time = (2 ** attempt) * 5  # 5s, 10s, 20s
                    print(f"Rate limit hit for {resume.name}. Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"Error screening resume {resume.id}: {str(e)}")
                    # Return a default low score on error
                    return ResumeScore(
                        resume_id=resume.id,
                        candidate_name=resume.name,
                        overall_score=0.0,
                        skills_match_score=0.0,
                        experience_score=0.0,
                        education_score=0.0,
                        reasoning=f"Error during screening: {str(e)}",
                        strengths=[],
                        weaknesses=["Error during automated screening"],
                        recommendation="NOT_RECOMMENDED"
                    )
        
        # This should never be reached, but just in case
        return ResumeScore(
            resume_id=resume.id,
            candidate_name=resume.name,
            overall_score=0.0,
            skills_match_score=0.0,
            experience_score=0.0,
            education_score=0.0,
            reasoning="Max retries exceeded",
            strengths=[],
            weaknesses=["Max retries exceeded"],
            recommendation="NOT_RECOMMENDED"
        )

    def rank_resumes(self, resumes: List[Resume], job_desc: JobDescription, max_workers: int = 2, use_retrieval: bool = True, retrieval_k: int = 100) -> List[ResumeScore]:
        """
        Screen and rank multiple resumes using parallel processing with optional hybrid search retrieval
        
        Args:
            resumes: List of Resume objects to screen
            job_desc: Job description to match against
            max_workers: Maximum number of parallel workers (default: 2 to avoid rate limits)
            use_retrieval: Whether to use hybrid search retrieval (default: True)
            retrieval_k: Number of top candidates to retrieve (default: 100)
            
        Returns:
            List of ResumeScore objects, sorted by overall_score (highest first)
        """
        print(f"Screening {len(resumes)} resumes for: {job_desc.title}")
        print("=" * 60)
        
        # Use hybrid search retrieval if enabled
        if use_retrieval:
            print(f"Using hybrid search to select top {retrieval_k} candidates from {len(resumes)}...")
            
            # Convert Resume objects to dictionaries for indexing
            resume_dicts = []
            resume_id_map = {}  # Map from indexed IDs to original Resume objects
            for i, resume in enumerate(resumes):
                resume_dict = {
                    'id': resume.id,  # Use original ID
                    'name': resume.name,
                    'email': resume.email,
                    'phone': resume.phone,
                    'skills': resume.skills,
                    'experience': resume.experience,
                    'education': resume.education,
                    'summary': resume.summary
                }
                resume_dicts.append(resume_dict)
                resume_id_map[resume.id] = resume  # Map ID to original object
            
            # Index all resumes and job description
            self.retriever.index_resumes(resume_dicts)
            job_id = self.retriever.index_job_description({
                'title': job_desc.title,
                'company': job_desc.company,
                'required_skills': job_desc.required_skills,
                'preferred_skills': job_desc.preferred_skills,
                'experience_years': job_desc.experience_years,
                'responsibilities': job_desc.responsibilities,
                'qualifications': job_desc.qualifications,
                'description': job_desc.description
            })
            
            # Retrieve top candidates using hybrid search
            top_candidates = self.retriever.retrieve_candidates({
                'title': job_desc.title,
                'company': job_desc.company,
                'required_skills': job_desc.required_skills,
                'preferred_skills': job_desc.preferred_skills,
                'experience_years': job_desc.experience_years,
                'responsibilities': job_desc.responsibilities,
                'qualifications': job_desc.qualifications,
                'description': job_desc.description
            }, retrieval_k)
            
            # Convert back to Resume objects using the ID map
            filtered_resumes = []
            for candidate in top_candidates:
                candidate_id = candidate['id']
                if candidate_id in resume_id_map:
                    filtered_resumes.append(resume_id_map[candidate_id])
                else:
                    # Fallback: try to find by name if ID doesn't match
                    for original_resume in resumes:
                        if original_resume.name == candidate.get('name'):
                            filtered_resumes.append(original_resume)
                            break
            
            print(f"Selected {len(filtered_resumes)} candidates for detailed LLM screening")
            resumes_to_process = filtered_resumes
        else:
            resumes_to_process = resumes
        
        scores = []
        
        # Use ThreadPoolExecutor for parallel processing with fewer workers to avoid rate limits
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_resume = {
                executor.submit(self.screen_resume, resume, job_desc): resume 
                for resume in resumes_to_process
            }
            
            # Collect results as they complete
            for i, future in enumerate(as_completed(future_to_resume), 1):
                resume = future_to_resume[future]
                try:
                    score = future.result()
                    # Add hybrid score if available
                    if hasattr(resume, 'hybrid_score'):
                        score.similarity_score = getattr(resume, 'hybrid_score', 0.0)
                    scores.append(score)
                    print(f"[{i}/{len(resumes_to_process)}] Completed screening for {resume.name} (Score: {score.overall_score:.1f})")
                except Exception as e:
                    print(f"[{i}/{len(resumes_to_process)}] Error screening {resume.name}: {str(e)}")
                    # Create a default low score for failed resumes
                    default_score = ResumeScore(
                        resume_id=resume.id,
                        candidate_name=resume.name,
                        overall_score=0.0,
                        skills_match_score=0.0,
                        experience_score=0.0,
                        education_score=0.0,
                        reasoning=f"Error during parallel screening: {str(e)}",
                        strengths=[],
                        weaknesses=["Error during automated screening"],
                        recommendation="NOT_RECOMMENDED"
                    )
                    scores.append(default_score)
        
        # Sort by overall score (descending)
        ranked_scores = sorted(scores, key=lambda x: x.overall_score, reverse=True)
        
        print("\n" + "=" * 60)
        print("SCREENING COMPLETE")
        print("=" * 60)
        
        return ranked_scores
    
    def display_results(self, ranked_scores: List[ResumeScore]) -> None:
        """
        Display screening results in a formatted manner
        
        Args:
            ranked_scores: List of ResumeScore objects (sorted)
        """
        print("\n" + "🏆 " + "=" * 58 + " 🏆")
        print(" " * 20 + "RANKING RESULTS")
        print("🏆 " + "=" * 58 + " 🏆\n")
        
        for rank, score in enumerate(ranked_scores, 1):
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
            
            print(f"{medal} RANK {rank}: {score.candidate_name}")
            print(f"   Overall Score: {score.overall_score:.1f}/100")
            print(f"   Skills Match: {score.skills_match_score:.1f}/100")
            print(f"   Experience: {score.experience_score:.1f}/100")
            print(f"   Education: {score.education_score:.1f}/100")
            print(f"   Recommendation: {score.recommendation}")
            print(f"\n   Reasoning: {score.reasoning}")
            print(f"\n   ✅ Strengths:")
            for strength in score.strengths:
                print(f"      • {strength}")
            print(f"\n   ⚠️  Weaknesses:")
            for weakness in score.weaknesses:
                print(f"      • {weakness}")
            print("\n" + "-" * 60 + "\n")
    
    def save_results(self, ranked_scores: List[ResumeScore], filename: str = "screening_results.json") -> None:
        """
        Save screening results to a JSON file
        
        Args:
            ranked_scores: List of ResumeScore objects
            filename: Output filename
        """
        results = [asdict(score) for score in ranked_scores]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Results saved to: {filename}")
