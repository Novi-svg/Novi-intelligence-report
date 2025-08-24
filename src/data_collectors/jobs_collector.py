import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)

class JobsCollector:
    def __init__(self):
        self.config = Config()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_jobs(self):
        """Collect SAP job opportunities"""
        jobs = []
        
        # Collect from multiple sources
        jobs.extend(self._search_linkedin_jobs())
        jobs.extend(self._search_naukri_jobs())
        jobs.extend(self._search_indeed_jobs())
        
        # Filter and sort by relevance
        relevant_jobs = self._filter_relevant_jobs(jobs)
        
        return relevant_jobs[:10]  # Top 10 most relevant
    
    def _search_linkedin_jobs(self):
        """Search LinkedIn for SAP jobs (simplified)"""
        jobs = []
        
        # This is a placeholder - LinkedIn requires API access or complex scraping
        # You can replace this with actual LinkedIn API calls if you have access
        
        sample_jobs = [
            {
                'title': 'SAP Finance Architect',
                'company': 'Tech Solutions Inc',
                'location': 'Bangalore, India',
                'package': '25-30 LPA',
                'experience': '8-12 years',
                'requirements': 'SAP FICO, S/4HANA, Finance transformation experience',
                'description': 'Lead SAP Finance implementations and transformations',
                'url': 'https://linkedin.com/jobs/sample',
                'source': 'LinkedIn',
                'posted_date': datetime.now().strftime('%Y-%m-%d')
            },
            {
                'title': 'SAP B2P Lead',
                'company': 'Global Consulting',
                'location': 'Hyderabad, India',
                'package': '22-28 LPA',
                'experience': '6-10 years',
                'requirements': 'SAP Ariba, B2P processes, procurement',
                'description': 'Lead Buy-to-Pay workstream in large SAP implementations',
                'url': 'https://linkedin.com/jobs/sample2',
                'source': 'LinkedIn',
                'posted_date': datetime.now().strftime('%Y-%m-%d')
            }
        ]
        
        jobs.extend(sample_jobs)
        return jobs
    
    def _search_naukri_jobs(self):
        """Search Naukri.com for SAP jobs"""
        jobs = []
        
        try:
            # Basic Naukri search (you may need to handle anti-scraping measures)
            search_terms = ['SAP Finance Architect', 'SAP Program Lead']
            
            for term in search_terms:
                # This is a simplified example - actual implementation would be more complex
                jobs.append({
                    'title': f'{term}',
                    'company': 'Sample Company',
                    'location': 'Mumbai, India',
                    'package': '20-25 LPA',
                    'experience': '5-8 years',
                    'requirements': 'SAP implementation, team leadership',
                    'description': f'Opportunity in {term} role',
                    'url': 'https://naukri.com/sample',
                    'source': 'Naukri',
                    'posted_date': datetime.now().strftime('%Y-%m-%d')
                })
                
        except Exception as e:
            logger.warning(f"Naukri search failed: {e}")
        
        return jobs
    
    def _search_indeed_jobs(self):
        """Search Indeed for SAP jobs"""
        jobs = []
        
        # Sample Indeed jobs (replace with actual scraping/API)
        sample_jobs = [
            {
                'title': 'Program Lead - SAP Finance',
                'company': 'Enterprise Solutions',
                'location': 'Chennai, India',
                'package': '30-35 LPA',
                'experience': '10+ years',
                'requirements': 'SAP S/4HANA, program management, finance domain',
                'description': 'Lead large-scale SAP finance transformation programs',
                'url': 'https://indeed.com/sample',
                'source': 'Indeed',
                'posted_date': datetime.now().strftime('%Y-%m-%d')
            }
        ]
        
        jobs.extend(sample_jobs)
        return jobs
    
    def _filter_relevant_jobs(self, jobs):
        """Filter jobs based on relevance to SAP Finance/Architecture roles"""
        relevant_jobs = []
        
        # Keywords that indicate high relevance
        high_priority_keywords = ['architect', 'lead', 'manager', 'director', 'finance', 's/4hana']
        
        for job in jobs:
            relevance_score = 0
            title_lower = job['title'].lower()
            desc_lower = job['description'].lower()
            
            # Score based on title keywords
            for keyword in high_priority_keywords:
                if keyword in title_lower:
                    relevance_score += 2
                if keyword in desc_lower:
                    relevance_score += 1
            
            # Score based on package (higher package = more relevant for senior roles)
            try:
                package_str = job.get('package', '0')
                if 'LPA' in package_str:
                    package_num = int(package_str.split('-')[0])
                    if package_num >= 25:
                        relevance_score += 3
                    elif package_num >= 20:
                        relevance_score += 2
                    elif package_num >= 15:
                        relevance_score += 1
            except:
                pass
            
            job['relevance_score'] = relevance_score
            if relevance_score > 0:
                relevant_jobs.append(job)
        
        # Sort by relevance score
        relevant_jobs.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return relevant_jobs
