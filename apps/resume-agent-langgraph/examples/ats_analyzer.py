"""
ATS (Applicant Tracking System) analyzer tool.

Analyzes resumes for ATS compatibility and keyword optimization.
"""

import re
from typing import List, Dict
from collections import Counter


class ATSAnalyzer:
    """Analyzer for ATS compatibility and keyword matching."""
    
    # Common ATS-unfriendly elements
    PROBLEMATIC_CHARS = {
        '•', '▪', '►', '★', '☆', '✓', '✔', '→', '←', '↑', '↓'
    }
    
    PROBLEMATIC_SECTIONS = {
        'tables', 'text boxes', 'headers/footers', 'images', 'graphs'
    }
    
    def __init__(self):
        self.stop_words = self._load_stop_words()
    
    def analyze_ats_compatibility(self, resume_text: str) -> Dict:
        """
        Analyze resume for ATS compatibility.
        
        Args:
            resume_text: The resume content
            
        Returns:
            Dictionary with compatibility score and issues
        """
        issues = []
        warnings = []
        score = 100  # Start with perfect score and deduct
        
        # Check for problematic characters
        problematic_found = [char for char in self.PROBLEMATIC_CHARS if char in resume_text]
        if problematic_found:
            issues.append(f"Contains ATS-unfriendly characters: {', '.join(problematic_found)}")
            score -= 10
        
        # Check for proper section headers
        required_sections = ['experience', 'education', 'skills']
        found_sections = []
        
        for section in required_sections:
            if re.search(rf'\b{section}\b', resume_text, re.IGNORECASE):
                found_sections.append(section)
        
        missing_sections = set(required_sections) - set(found_sections)
        if missing_sections:
            issues.append(f"Missing standard sections: {', '.join(missing_sections)}")
            score -= 15 * len(missing_sections)
        
        # Check for contact information
        has_email = bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', resume_text))
        has_phone = bool(re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', resume_text))
        
        if not has_email:
            issues.append("No email address found")
            score -= 20
        if not has_phone:
            warnings.append("No phone number detected")
            score -= 5
        
        # Check resume length (rough estimate)
        word_count = len(resume_text.split())
        if word_count < 200:
            warnings.append("Resume seems too short (< 200 words)")
            score -= 10
        elif word_count > 1000:
            warnings.append("Resume may be too long (> 1000 words)")
            score -= 5
        
        # Check for buzzwords without substance
        buzzword_ratio = self._calculate_buzzword_ratio(resume_text)
        if buzzword_ratio > 0.15:
            warnings.append("High ratio of buzzwords without concrete achievements")
            score -= 5
        
        return {
            "ats_score": max(0, min(100, score)),
            "issues": issues,
            "warnings": warnings,
            "found_sections": found_sections,
            "has_contact_info": has_email and has_phone,
            "word_count": word_count,
        }
    
    def calculate_keyword_match(
        self,
        resume_text: str,
        job_keywords: List[str]
    ) -> Dict:
        """
        Calculate keyword match between resume and job requirements.
        
        Args:
            resume_text: The resume content
            job_keywords: List of keywords from job posting
            
        Returns:
            Dictionary with match statistics
        """
        resume_lower = resume_text.lower()
        
        matched_keywords = []
        missing_keywords = []
        
        for keyword in job_keywords:
            keyword_lower = keyword.lower()
            # Check for exact match or variations
            if keyword_lower in resume_lower:
                matched_keywords.append(keyword)
            else:
                missing_keywords.append(keyword)
        
        match_percentage = (len(matched_keywords) / len(job_keywords) * 100) if job_keywords else 0
        
        return {
            "match_percentage": round(match_percentage, 1),
            "matched_keywords": matched_keywords,
            "missing_keywords": missing_keywords,
            "total_keywords": len(job_keywords),
            "matched_count": len(matched_keywords),
        }
    
    def extract_skills(self, text: str) -> List[str]:
        """
        Extract technical skills and keywords from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of identified skills
        """
        # Common skill patterns
        skills = []
        
        # Programming languages
        prog_langs = r'\b(Python|Java|JavaScript|TypeScript|C\+\+|C#|Ruby|Go|Rust|Swift|Kotlin|PHP|SQL)\b'
        skills.extend(re.findall(prog_langs, text, re.IGNORECASE))
        
        # Frameworks and libraries
        frameworks = r'\b(React|Angular|Vue|Django|Flask|FastAPI|Spring|Express|Node\.js|TensorFlow|PyTorch)\b'
        skills.extend(re.findall(frameworks, text, re.IGNORECASE))
        
        # Cloud and DevOps
        cloud = r'\b(AWS|Azure|GCP|Docker|Kubernetes|Jenkins|GitHub|GitLab|CI/CD|Terraform)\b'
        skills.extend(re.findall(cloud, text, re.IGNORECASE))
        
        # Databases
        databases = r'\b(PostgreSQL|MySQL|MongoDB|Redis|Elasticsearch|DynamoDB|Oracle)\b'
        skills.extend(re.findall(databases, text, re.IGNORECASE))
        
        # Remove duplicates and return
        return list(set(skills))
    
    def _calculate_buzzword_ratio(self, text: str) -> float:
        """Calculate ratio of buzzwords to total words."""
        buzzwords = [
            'synergy', 'leverage', 'innovative', 'cutting-edge', 'best-in-class',
            'world-class', 'dynamic', 'results-driven', 'team player', 'go-getter'
        ]
        
        words = text.lower().split()
        buzzword_count = sum(1 for word in words if any(bw in word for bw in buzzwords))
        
        return buzzword_count / len(words) if words else 0
    
    def _load_stop_words(self) -> set:
        """Load common stop words."""
        return {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }


# Module-level instance
ats_analyzer = ATSAnalyzer()


# Convenience functions
def analyze_resume_ats(resume_text: str) -> Dict:
    """Analyze resume for ATS compatibility."""
    return ats_analyzer.analyze_ats_compatibility(resume_text)


def calculate_keyword_match(resume_text: str, job_keywords: List[str]) -> Dict:
    """Calculate keyword match percentage."""
    return ats_analyzer.calculate_keyword_match(resume_text, job_keywords)


def extract_skills_from_text(text: str) -> List[str]:
    """Extract skills from text."""
    return ats_analyzer.extract_skills(text)
