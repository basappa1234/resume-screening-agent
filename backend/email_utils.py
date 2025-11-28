"""
Email utility for sending notifications to candidates
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from typing import List, Dict

# Load environment variables safely
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception as e:
    print(f"Warning: Could not load .env file: {e}")

class EmailNotifier:
    """Handle email notifications for candidates"""
    
    def __init__(self):
        """Initialize email configuration"""
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
        
        # Email templates
        self.selected_template = """
Dear {candidate_name},

Congratulations! We are pleased to inform you that your resume has been shortlisted for the position of "{job_title}" at {company}.

Based on our comprehensive evaluation, your qualifications and experience align well with our requirements. We were particularly impressed with:
{strengths}

We would like to invite you to the next round of the selection process. Details of the next steps will be shared with you shortly.

Best regards,
{company} Recruitment Team
"""

        self.not_selected_template = """
Dear {candidate_name},

Thank you for your interest in the position of "{job_title}" at {company}.

After carefully reviewing your application, we regret to inform you that your resume was not selected to move forward in the hiring process at this time.

Feedback from our review:
{weaknesses}

We encourage you to continue improving your skills and experience. Consider focusing on:
{improvement_suggestions}

We wish you the best in your job search and future endeavors.

Best regards,
{company} Recruitment Team
"""
    
    def send_notification(self, recipient_email: str, candidate_name: str, job_title: str, 
                         company: str, is_selected: bool, strengths: List[str] = None, 
                         weaknesses: List[str] = None, improvement_suggestions: List[str] = None) -> bool:
        """
        Send email notification to candidate
        
        Args:
            recipient_email: Candidate's email address
            candidate_name: Candidate's name
            job_title: Job title
            company: Company name
            is_selected: Whether candidate was selected
            strengths: List of candidate's strengths (for selected candidates)
            weaknesses: List of candidate's weaknesses (for rejected candidates)
            improvement_suggestions: Suggestions for improvement (for rejected candidates)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"Application Status - {job_title} at {company}"
            msg["From"] = self.sender_email
            msg["To"] = recipient_email
            
            # Select template based on selection status
            if is_selected:
                # Format strengths as bullet points
                strengths_text = "\n".join([f"• {strength}" for strength in strengths]) if strengths else "Your relevant experience and qualifications"
                
                body = self.selected_template.format(
                    candidate_name=candidate_name,
                    job_title=job_title,
                    company=company,
                    strengths=strengths_text
                )
            else:
                # Format weaknesses and suggestions as bullet points
                weaknesses_text = "\n".join([f"• {weakness}" for weakness in weaknesses]) if weaknesses else "Aspects that didn't fully align with our current requirements"
                suggestions_text = "\n".join([f"• {suggestion}" for suggestion in improvement_suggestions]) if improvement_suggestions else "Enhancing your skills and gaining more relevant experience"
                
                body = self.not_selected_template.format(
                    candidate_name=candidate_name,
                    job_title=job_title,
                    company=company,
                    weaknesses=weaknesses_text,
                    improvement_suggestions=suggestions_text
                )
            
            # Add body to email
            msg.attach(MIMEText(body, "plain"))
            
            # Create secure connection and send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, recipient_email, msg.as_string())
            
            print(f"✅ Email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email to {recipient_email}: {str(e)}")
            return False
    
    def notify_candidates(self, results: List[Dict], job_title: str, company: str, 
                         threshold: float = 70.0) -> Dict[str, int]:
        """
        Notify all candidates based on their scores
        
        Args:
            results: List of screening results
            job_title: Job title
            company: Company name
            threshold: Score threshold for selection (default: 70.0)
            
        Returns:
            Dict with counts of sent emails
        """
        stats = {"selected": 0, "not_selected": 0, "failed": 0}
        
        if not self.sender_email or not self.sender_password:
            print("⚠️  Email configuration not found. Skipping email notifications.")
            return stats
        
        for result in results:
            try:
                # Extract candidate information
                candidate_name = result.get("candidate_name", "Candidate")
                candidate_email = result.get("email", "")
                
                # Skip if no email provided
                if not candidate_email:
                    print(f"⚠️  No email found for {candidate_name}. Skipping notification.")
                    stats["failed"] += 1
                    continue
                
                # Determine selection status
                overall_score = result.get("overall_score", 0)
                is_selected = overall_score >= threshold
                
                # Send notification
                success = self.send_notification(
                    recipient_email=candidate_email,
                    candidate_name=candidate_name,
                    job_title=job_title,
                    company=company,
                    is_selected=is_selected,
                    strengths=result.get("strengths", []),
                    weaknesses=result.get("weaknesses", []),
                    improvement_suggestions=result.get("weaknesses", [])  # Use weaknesses as improvement suggestions
                )
                
                if success:
                    if is_selected:
                        stats["selected"] += 1
                    else:
                        stats["not_selected"] += 1
                else:
                    stats["failed"] += 1
                    
            except Exception as e:
                print(f"❌ Error notifying candidate: {str(e)}")
                stats["failed"] += 1
        
        return stats