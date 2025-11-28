"""
Main application to run the Resume Screening Agent
"""

from resume_screening_agent import ResumeScreeningAgent
from sample_data import get_sample_resumes, get_sample_job_description


def main():
    """Main function to run resume screening"""
    
    print("=" * 60)
    print(" " * 15 + "RESUME SCREENING AGENT")
    print(" " * 12 + "Powered by Groq API")
    print("=" * 60)
    print()
    
    # Initialize the agent
    try:
        agent = ResumeScreeningAgent()
        print("✅ Resume Screening Agent initialized successfully!")
        print(f"Using model: {agent.model}")
        print()
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("\nPlease follow these steps:")
        print("1. Copy .env.example to .env")
        print("2. Add your Groq API key to the .env file")
        print("3. Run the application again")
        return
    
    # Load sample data
    job_description = get_sample_job_description()
    resumes = get_sample_resumes()
    
    print(f"📋 Job Position: {job_description.title}")
    print(f"🏢 Company: {job_description.company}")
    print(f"📊 Number of Resumes: {len(resumes)}")
    print()
    
    # Screen and rank resumes
    ranked_results = agent.rank_resumes(resumes, job_description)
    
    # Display results
    agent.display_results(ranked_results)
    
    # Save results to file
    agent.save_results(ranked_results, "screening_results.json")
    
    print("\n✨ Resume screening completed successfully!")


if __name__ == "__main__":
    main()
