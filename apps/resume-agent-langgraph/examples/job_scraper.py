"""
Job posting scraper tool.

Handles fetching and parsing job postings from various sources.
"""

import re
from typing import Optional
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup

from ..config import get_settings


class JobScraper:
    """Scraper for job postings."""
    
    def __init__(self):
        self.settings = get_settings()
        self.timeout = self.settings.scraping_timeout
        self.headers = {
            "User-Agent": self.settings.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
    
    async def fetch_job_posting(self, url: str) -> dict:
        """
        Fetch a job posting from a URL.
        
        Args:
            url: URL of the job posting
            
        Returns:
            Dictionary with raw_html, cleaned_text, and metadata
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, headers=self.headers, follow_redirects=True)
                response.raise_for_status()
                
                html_content = response.text
                parsed = self._parse_html(html_content, url)
                
                return {
                    "url": url,
                    "raw_html": html_content,
                    "cleaned_text": parsed["text"],
                    "title": parsed["title"],
                    "company": parsed["company"],
                    "source": self._identify_source(url),
                }
            except httpx.HTTPError as e:
                raise Exception(f"Failed to fetch job posting: {str(e)}")
    
    def _parse_html(self, html: str, url: str) -> dict:
        """Parse HTML and extract relevant information."""
        soup = BeautifulSoup(html, "html.parser")
        
        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
        
        # Extract title (try common patterns)
        title = None
        for selector in ["h1", ".job-title", "#job-title", '[data-testid="job-title"]']:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                break
        
        # Extract company (try common patterns)
        company = None
        for selector in [".company-name", "#company-name", '[data-testid="company-name"]']:
            element = soup.select_one(selector)
            if element:
                company = element.get_text(strip=True)
                break
        
        # Get main content
        text = soup.get_text(separator="\n", strip=True)
        # Clean up excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return {
            "text": text,
            "title": title or "Unknown Title",
            "company": company or self._extract_company_from_url(url),
        }
    
    def _identify_source(self, url: str) -> str:
        """Identify the job board source from URL."""
        domain = urlparse(url).netloc.lower()
        
        if "linkedin.com" in domain:
            return "LinkedIn"
        elif "indeed.com" in domain:
            return "Indeed"
        elif "glassdoor.com" in domain:
            return "Glassdoor"
        elif "greenhouse.io" in domain:
            return "Greenhouse"
        elif "lever.co" in domain:
            return "Lever"
        else:
            return "Unknown"
    
    def _extract_company_from_url(self, url: str) -> str:
        """Try to extract company name from URL."""
        domain = urlparse(url).netloc
        # Remove common prefixes and TLDs
        company = domain.replace("www.", "").replace("jobs.", "").replace("careers.", "")
        company = company.split(".")[0]
        return company.title()


# Synchronous wrapper for non-async contexts
def scrape_job_posting(url: str) -> dict:
    """
    Synchronous wrapper for job scraping.
    
    Args:
        url: Job posting URL
        
    Returns:
        Scraped job data
    """
    import asyncio
    
    scraper = JobScraper()
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(scraper.fetch_job_posting(url))
