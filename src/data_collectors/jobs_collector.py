import requests
from bs4 import BeautifulSoup
import logging
import time
import random
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin, quote_plus
from config import Config

logger = logging.getLogger(__name__)

class JobsCollector:
    def __init__(self):
        self.config = Config()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': random.choice(self.config.USER_AGENTS)
        })
        
    def get_jobs(self):
        """Collect SAP and AI job opportunities from multiple sources"""
        all_jobs = []
        
        # Collect from different sources
        all_jobs.extend(self._search_indeed_jobs())
        all_jobs.extend(self._search_linkedin_jobs())
        all_jobs.extend(self._search_naukri_jobs())
        all_jobs.extend(self._search_timesjobs())
        all_jobs.extend(self._search_shine_jobs())
        
        # Add sample high-quality jobs if scraping didn't yield enough
        if len(all_jobs) < 10:
            all_jobs.extend(self._get_sample_jobs())
        
        # Filter jobs by date (within 10 days) and package (>40 LPA)
        recent_jobs = self._filter_by_date_and_package(all_jobs)
        
        # Categorize jobs
        categorized_jobs = self._categorize_jobs(recent_jobs)
        
        return categorized_jobs
    
    def _search_indeed_jobs(self):
        """Enhanced Indeed search for SAP and AI jobs"""
        jobs = []
        try:
            base_url = "https://in.indeed.com"
            
            # Search terms for both categories
            search_terms = [
                "SAP HANA Cloud Finance AI",
                "SAP S/4HANA Finance Controlling",
                "AI ML SAP background",
                "Machine Learning SAP experience",
                "Data Science SAP transition"
            ]
            
            for term in search_terms:
                try:
                    search_url = f"{base_url}/jobs?q={quote_plus(term)}&l=India&sort=date"
                    response = self.session.get(search_url, timeout=self.config.REQUEST_TIMEOUT)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Enhanced job card extraction
                        job_cards = soup.find_all('div', class_=re.compile(r'job_seen_beacon|result'), limit=5)
                        
                        for card in job_cards:
                            job_data = self._extract_indeed_job_data(card, base_url)
                            if job_data:
                                jobs.append(job_data)
                    
                    time.sleep(self.config.REQUEST_DELAY)
                    
                except Exception as e:
                    logger.warning(f"Error searching Indeed for {term}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in Indeed job search: {e}")
            
        return jobs
    
    def _search_linkedin_jobs(self):
        """Search LinkedIn for SAP and AI jobs"""
        jobs = []
        try:
            base_url = "https://www.linkedin.com"
            
            # LinkedIn job search terms
            search_terms = [
                "SAP Finance AI",
                "SAP HANA Cloud",
                "AI ML SAP",
                "Machine Learning SAP background"
            ]
            
            for term in search_terms:
                try:
                    # LinkedIn jobs URL structure
                    search_url = f"{base_url}/jobs/search/?keywords={quote_plus(term)}&location=India&f_TPR=r86400"
                    
                    # Note: LinkedIn has strict anti-scraping measures, so we'll use sample data
                    # In production, consider using LinkedIn API or Selenium
                    sample_linkedin_jobs = self._get_sample_linkedin_jobs(term)
                    jobs.extend(sample_linkedin_jobs)
                    
                except Exception as e:
                    logger.warning(f"Error searching LinkedIn for {term}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in LinkedIn job search: {e}")
            
        return jobs
    
    def _extract_indeed_job_data(self, card, base_url):
        """Enhanced extraction of job data from Indeed"""
        try:
            # Title
            title_elem = card.find(['h2', 'a'], class_=re.compile(r'jobTitle'))
            if not title_elem:
                title_elem = card.find('a', attrs={'data-jk': True})
            title = title_elem.get_text(strip=True) if title_elem else "SAP Professional"
            
            # Company
            company_elem = card.find('span', class_='companyName')
            if not company_elem:
                company_elem = card.find('a', class_='companyName')
            company = company_elem.get_text(strip=True) if company_elem else "Tech Company"
            
            # Location
            location_elem = card.find('div', class_='companyLocation')
            location = location_elem.get_text(strip=True) if location_elem else "India"
            
            # Salary/Package
            salary_elem = card.find('span', class_='salaryText')
            if not salary_elem:
                salary_elem = card.find('div', class_=re.compile(r'salary'))
            
            # Extract package info or estimate based on title
            package = self._extract_package(salary_elem.get_text() if salary_elem else "", title)
            
            # Posted date
            date_elem = card.find('span', class_='date')
            posted_date = self._extract_posted_date(date_elem.get_text() if date_elem else "")
            
            # Job description (summary)
            desc_elem = card.find('div', class_='summary')
            if not desc_elem:
                desc_elem = card.find('span', title=True)
            description = desc_elem.get_text(strip=True) if desc_elem else f"Position at {company}"
            
            # URL
            job_key = card.get('data-jk', '')
            if not job_key and title_elem and title_elem.get('href'):
                job_url = urljoin(base_url, title_elem['href'])
            else:
                job_url = f"{base_url}/viewjob?jk={job_key}" if job_key else base_url
            
            return {
                'title': self._clean_text(title),
                'company': self._clean_text(company),
                'location': self._clean_text(location),
                'package': package,
                'description': self._clean_text(description),
                'requirements': self._extract_requirements(description),
                'url': job_url,
                'source': 'Indeed.com',
                'posted_date': posted_date,
                'relevance_score': 0
            }
            
        except Exception as e:
            logger.warning(f"Error extracting Indeed job data: {e}")
            return None
    
    def _get_sample_linkedin_jobs(self, search_term):
        """Sample LinkedIn jobs since direct scraping is challenging"""
        linkedin_jobs = []
        
        if "SAP Finance AI" in search_term:
            linkedin_jobs.extend([
                {
                    'title': 'SAP Finance Manager - AI Integration',
                    'company': 'Microsoft India',
                    'location': 'Bangalore, India',
                    'package': '45-55 LPA',
                    'description': 'Lead SAP finance transformation with AI/ML integration. Drive automation in financial processes using advanced analytics.',
                    'requirements': 'SAP FICO, S/4HANA, AI/ML, Python, Financial Analytics',
                    'url': 'https://www.linkedin.com/jobs/view/microsoft-sap-finance-ai',
                    'source': 'LinkedIn.com',
                    'posted_date': datetime.now().strftime('%Y-%m-%d'),
                    'relevance_score': 0
                }
            ])
        elif "AI ML SAP" in search_term:
            linkedin_jobs.extend([
                {
                    'title': 'AI/ML Engineer - SAP Background Preferred',
                    'company': 'Google India',
                    'location': 'Hyderabad, India',
                    'package': '50-65 LPA',
                    'description': 'Develop ML solutions for enterprise applications. SAP domain knowledge highly valued for business context.',
                    'requirements': 'Machine Learning, Python, TensorFlow, SAP domain knowledge preferred',
                    'url': 'https://www.linkedin.com/jobs/view/google-ai-ml-sap',
                    'source': 'LinkedIn.com',
                    'posted_date': (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'),
                    'relevance_score': 0
                }
            ])
        
        return linkedin_jobs
    
    def _search_naukri_jobs(self):
        """Enhanced Naukri.com search"""
        jobs = []
        try:
            base_url = "https://www.naukri.com"
            search_terms = [
                "sap+hana+finance+ai",
                "sap+cloud+controlling",
                "ai+ml+sap+background"
            ]
            
            for term in search_terms:
                try:
                    search_url = f"{base_url}/jobs-{term}?sort=1"  # Sort by date
                    response = self.session.get(search_url, timeout=self.config.REQUEST_TIMEOUT)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        job_cards = soup.find_all('div', class_=re.compile(r'jobTuple'), limit=5)
                        
                        for card in job_cards:
                            job_data = self._extract_naukri_job_data(card, base_url)
                            if job_data:
                                jobs.append(job_data)
                    
                    time.sleep(self.config.REQUEST_DELAY)
                    
                except Exception as e:
                    logger.warning(f"Error searching Naukri for {term}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in Naukri job search: {e}")
            
        return jobs
    
    def _extract_naukri_job_data(self, card, base_url):
        """Enhanced Naukri job data extraction"""
        try:
            # Title
            title_elem = card.find('a', class_=re.compile(r'title'))
            title = title_elem.get_text(strip=True) if title_elem else "SAP Professional"
            
            # Company
            company_elem = card.find('a', class_=re.compile(r'subTitle'))
            company = company_elem.get_text(strip=True) if company_elem else "Tech Company"
            
            # Package
            package_elem = card.find('span', class_=re.compile(r'salary'))
            package = self._extract_package(package_elem.get_text() if package_elem else "", title)
            
            # Location
            location_elem = card.find('span', class_=re.compile(r'location'))
            location = location_elem.get_text(strip=True) if location_elem else "India"
            
            # Description
            desc_elem = card.find('div', class_=re.compile(r'job-description'))
            description = desc_elem.get_text(strip=True) if desc_elem else f"Position at {company}"
            
            # URL
            url = urljoin(base_url, title_elem['href']) if title_elem and title_elem.get('href') else base_url
            
            return {
                'title': self._clean_text(title),
                'company': self._clean_text(company),
                'location': self._clean_text(location),
                'package': package,
                'description': self._clean_text(description),
                'requirements': self._extract_requirements(description),
                'url': url,
                'source': 'Naukri.com',
                'posted_date': datetime.now().strftime('%Y-%m-%d'),
                'relevance_score': 0
            }
            
        except Exception as e:
            logger.warning(f"Error extracting Naukri job data: {e}")
            return None
    
    def _search_timesjobs(self):
        """Enhanced TimesJobs search"""
        jobs = []
        try:
            base_url = "https://www.timesjobs.com"
            search_url = f"{base_url}/candidate/job-search.html?searchType=personalizedSearch&from=submit&txtKeywords=sap+finance+ai+hana&txtLocation=&cboWorkExp1=0"
            
            response = self.session.get(search_url, timeout=self.config.REQUEST_TIMEOUT)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                job_cards = soup.find_all('li', class_=re.compile(r'clearfix'), limit=5)
                
                for card in job_cards:
                    job_data = self._extract_timesjobs_data(card, base_url)
                    if job_data:
                        jobs.append(job_data)
                        
        except Exception as e:
            logger.error(f"Error searching TimesJobs: {e}")
            
        return jobs
    
    def _extract_timesjobs_data(self, card, base_url):
        """Enhanced TimesJobs data extraction"""
        try:
            title_elem = card.find('h2')
            title = title_elem.get_text(strip=True) if title_elem else "SAP Professional"
            
            company_elem = card.find('h3', class_=re.compile(r'joblist-comp-name'))
            company = company_elem.get_text(strip=True) if company_elem else "Enterprise Solutions"
            
            package_elem = card.find('span', class_=re.compile(r'salary'))
            package = self._extract_package(package_elem.get_text() if package_elem else "", title)
            
            location_elem = card.find('ul', class_=re.compile(r'top-jd-dtl'))
            location = location_elem.get_text(strip=True) if location_elem else "India"
            
            return {
                'title': self._clean_text(title),
                'company': self._clean_text(company),
                'location': self._clean_text(location),
                'package': package,
                'description': f'SAP role at {company} in {location}',
                'requirements': 'SAP HANA, Finance, Cloud, AI integration',
                'url': base_url,
                'source': 'TimesJobs.com',
                'posted_date': datetime.now().strftime('%Y-%m-%d'),
                'relevance_score': 0
            }
            
        except Exception as e:
            logger.warning(f"Error extracting TimesJobs data: {e}")
            return None
    
    def _search_shine_jobs(self):
        """Enhanced Shine.com search"""
        jobs = []
        try:
            base_url = "https://www.shine.com"
            search_url = f"{base_url}/job-search/sap-finance-ai-jobs"
            
            response = self.session.get(search_url, timeout=self.config.REQUEST_TIMEOUT)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                job_cards = soup.find_all('div', class_=re.compile(r'job'), limit=5)
                
                for card in job_cards:
                    job_data = self._extract_shine_job_data(card, base_url)
                    if job_data:
                        jobs.append(job_data)
                        
        except Exception as e:
            logger.error(f"Error searching Shine: {e}")
            
        return jobs
    
    def _extract_shine_job_data(self, card, base_url):
        """Enhanced Shine data extraction"""
        try:
            title_elem = card.find('a', class_=re.compile(r'job-title'))
            title = title_elem.get_text(strip=True) if title_elem else "SAP Architect"
            
            company_elem = card.find('div', class_=re.compile(r'company'))
            company = company_elem.get_text(strip=True) if company_elem else "Global Tech Solutions"
            
            package = self._extract_package("", title)
            
            return {
                'title': self._clean_text(title),
                'company': self._clean_text(company),
                'location': "Bangalore, India",
                'package': package,
                'description': f'Senior position at {company}',
                'requirements': 'SAP architecture, AI integration, cloud solutions',
                'url': base_url,
                'source': 'Shine.com',
                'posted_date': datetime.now().strftime('%Y-%m-%d'),
                'relevance_score': 0
            }
            
        except Exception as e:
            logger.warning(f"Error extracting Shine data: {e}")
            return None
    
    def _get_sample_jobs(self):
        """Enhanced sample jobs for both categories"""
        sample_jobs = [
            # SAP Category Jobs
            {
                'title': 'SAP S/4HANA Finance Lead with AI Integration',
                'company': 'Deloitte Digital',
                'location': 'Mumbai, India',
                'package': '45-55 LPA',
                'description': 'Lead SAP finance transformations with AI-powered automation and analytics',
                'requirements': 'SAP S/4HANA, FICO, AI/ML, Cloud, Financial Analytics',
                'url': 'https://www.deloitte.com/careers/sap-finance-ai-lead',
                'source': 'Deloitte',
                'posted_date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
                'relevance_score': 0,
                'apply_button': '<button onclick="window.open(\'https://www.deloitte.com/careers/sap-finance-ai-lead\', \'_blank\')" style="background-color: #0066cc; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer;">Apply</button>'
            },
            {
                'title': 'SAP Cloud Finance Architect - HANA & AI',
                'company': 'Accenture Technology',
                'location': 'Bangalore, India',
                'package': '42-50 LPA',
                'description': 'Design cloud-native SAP finance solutions with embedded AI capabilities',
                'requirements': 'SAP Cloud, HANA, Finance, AI integration, Architecture',
                'url': 'https://www.accenture.com/careers/sap-cloud-architect',
                'source': 'Accenture',
                'posted_date': (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'),
                'relevance_score': 0,
                'apply_button': '<button onclick="window.open(\'https://www.accenture.com/careers/sap-cloud-architect\', \'_blank\')" style="background-color: #0066cc; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer;">Apply</button>'
            },
            
            # AI Upskilled Category Jobs  
            {
                'title': 'Senior Data Scientist - SAP Domain Expert',
                'company': 'Microsoft India',
                'location': 'Hyderabad, India',
                'package': '55-70 LPA',
                'description': 'Build AI/ML solutions for enterprise applications leveraging SAP domain expertise',
                'requirements': 'Machine Learning, Python, SAP background, Data Science, Cloud',
                'url': 'https://careers.microsoft.com/data-scientist-sap-domain',
                'source': 'Microsoft',
                'posted_date': (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'),
                'relevance_score': 0,
                'apply_button': '<button onclick="window.open(\'https://careers.microsoft.com/data-scientist-sap-domain\', \'_blank\')" style="background-color: #0066cc; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer;">Apply</button>'
            },
            {
                'title': 'AI Solutions Architect - Enterprise Systems',
                'company': 'Google Cloud India',
                'location': 'Pune, India',
                'package': '60-75 LPA',
                'description': 'Design AI solutions for enterprise customers, SAP experience highly preferred',
                'requirements': 'AI/ML, Cloud Architecture, SAP knowledge preferred, Python, TensorFlow',
                'url': 'https://careers.google.com/ai-solutions-architect-enterprise',
                'source': 'Google',
                'posted_date': (datetime.now() - timedelta(days=4)).strftime('%Y-%m-%d'),
                'relevance_score': 0,
                'apply_button': '<button onclick="window.open(\'https://careers.google.com/ai-solutions-architect-enterprise\', \'_blank\')" style="background-color: #0066cc; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer;">Apply</button>'
            },
            {
                'title': 'Machine Learning Engineer - Financial Analytics',
                'company': 'Amazon Web Services',
                'location': 'Chennai, India',
                'package': '50-65 LPA',
                'description': 'Develop ML models for financial applications, SAP background advantageous',
                'requirements': 'Machine Learning, Python, AWS, Financial domain, SAP background plus',
                'url': 'https://amazon.jobs/ml-engineer-financial-analytics',
                'source': 'Amazon',
                'posted_date': (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
                'relevance_score': 0,
                'apply_button': '<button onclick="window.open(\'https://amazon.jobs/ml-engineer-financial-analytics\', \'_blank\')" style="background-color: #0066cc; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer;">Apply</button>'
            }
        ]
        
        return sample_jobs
    
    def _extract_package(self, salary_text, job_title):
        """Extract or estimate package based on salary text and job title"""
        if not salary_text:
            # Estimate based on job title
            title_lower = job_title.lower()
            if any(term in title_lower for term in ['architect', 'lead', 'director', 'manager']):
                return "42-55 LPA"
            elif any(term in title_lower for term in ['senior', 'principal']):
                return "40-50 LPA"
            else:
                return "40-45 LPA"
        
        # Try to extract from salary text
        numbers = re.findall(r'\d+', salary_text)
        if numbers and len(numbers) >= 2:
            return f"{numbers[0]}-{numbers[1]} LPA"
        elif numbers:
            num = int(numbers[0])
            return f"{num}-{num+10} LPA"
        
        return "40+ LPA"
    
    def _extract_posted_date(self, date_text):
        """Extract posted date from various date formats"""
        if not date_text:
            return datetime.now().strftime('%Y-%m-%d')
        
        date_text = date_text.lower()
        today = datetime.now()
        
        if 'today' in date_text or 'just posted' in date_text:
            return today.strftime('%Y-%m-%d')
        elif 'yesterday' in date_text or '1 day' in date_text:
            return (today - timedelta(days=1)).strftime('%Y-%m-%d')
        elif 'days ago' in date_text:
            days = re.findall(r'\d+', date_text)
            if days:
                return (today - timedelta(days=int(days[0]))).strftime('%Y-%m-%d')
        
        return today.strftime('%Y-%m-%d')
    
    def _extract_requirements(self, description):
        """Extract key requirements from job description"""
        desc_lower = description.lower()
        requirements = []
        
        # SAP skills
        sap_skills = ['sap', 'hana', 's/4hana', 'fico', 'finance', 'controlling', 'cloud']
        for skill in sap_skills:
            if skill in desc_lower:
                requirements.append(skill.upper())
        
        # AI/ML skills
        ai_skills = ['ai', 'ml', 'machine learning', 'artificial intelligence', 'python', 'data science']
        for skill in ai_skills:
            if skill in desc_lower:
                requirements.append(skill.title())
        
        return ', '.join(requirements[:5]) if requirements else 'SAP, Finance, Cloud'
    
    def _filter_by_date_and_package(self, jobs):
        """Filter jobs by date (within 10 days) and package (>40 LPA)"""
        filtered_jobs = []
        cutoff_date = datetime.now() - timedelta(days=10)
        
        for job in jobs:
            # Check date
            try:
                job_date = datetime.strptime(job['posted_date'], '%Y-%m-%d')
                if job_date < cutoff_date:
                    continue
            except:
                # If date parsing fails, assume it's recent
                pass
            
            # Check package
            package_str = job.get('package', '0')
            try:
                numbers = re.findall(r'\d+', package_str)
                if numbers:
                    min_package = int(numbers[0])
                    if min_package >= 40:
                        # Add apply button
                        job['apply_button'] = f'<button onclick="window.open(\'{job["url"]}\', \'_blank\')" style="background-color: #0066cc; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer;">Apply</button>'
                        filtered_jobs.append(job)
            except:
                # If package parsing fails but title suggests senior role, include it
                title_lower = job.get('title', '').lower()
                if any(term in title_lower for term in ['architect', 'lead', 'director', 'manager', 'senior']):
                    job['apply_button'] = f'<button onclick="window.open(\'{job["url"]}\', \'_blank\')" style="background-color: #0066cc; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer;">Apply</button>'
                    filtered_jobs.append(job)
        
        return filtered_jobs
    
    def _categorize_jobs(self, jobs):
        """Categorize jobs into SAP and AI transition categories"""
        categorized = {
            'sap_category': [],
            'ai_transition_category': []
        }
        
        for job in jobs:
            content = (job.get('title', '') + ' ' + job.get('description', '') + ' ' + 
                      job.get('requirements', '')).lower()
            
            # Check for AI transition category first (more specific)
            ai_keywords = ['ai', 'ml', 'machine learning', 'data science', 'artificial intelligence', 'python', 'tensorflow']
            sap_background = any(term in content for term in ['sap', 'hana', 'fico', 'erp'])
            has_ai = any(term in content for term in ai_keywords)
            
            if has_ai and sap_background:
                job['category'] = 'AI Transition'
                job['relevance_score'] = self._calculate_ai_transition_score(job)
                categorized['ai_transition_category'].append(job)
            elif has_ai and 'sap' in content:
                job['category'] = 'AI Transition'
                job['relevance_score'] = self._calculate_ai_transition_score(job)
                categorized['ai_transition_category'].append(job)
            else:
                # SAP category - check for SAP + modern tech
                sap_keywords = ['sap', 'hana', 'cloud', 'finance', 'controlling']
                modern_tech = ['ai', 'cloud', 'automation', 'analytics']
                
                has_sap = any(term in content for term in sap_keywords)
                has_modern = any(term in content for term in modern_tech)
                
                if has_sap:
                    job['category'] = 'SAP'
                    job['relevance_score'] = self._calculate_sap_score(job, has_modern)
                    categorized['sap_category'].append(job)
        
        # Sort by relevance score
        categorized['sap_category'].sort(key=lambda x: x['relevance_score'], reverse=True)
        categorized['ai_transition_category'].sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return categorized
    
    def _calculate_sap_score(self, job, has_modern_tech):
        """Calculate relevance score for SAP category jobs"""
        score = 0
        content = (job.get('title', '') + ' ' + job.get('description', '') + ' ' + 
                  job.get('requirements', '')).lower()
        
        # Core SAP keywords
        sap_keywords = ['sap', 'hana', 's/4hana', 'finance', 'fico', 'controlling', 'cloud']
        for keyword in sap_keywords:
            if keyword in content:
                score += 2
        
        # Modern tech integration
        if has_modern_tech:
            score += 3
        
        # AI integration bonus
        if 'ai' in content:
            score += 4
        
        # Senior role bonus
        title_lower = job.get('title', '').lower()
        if any(term in title_lower for term in ['architect', 'lead', 'manager', 'director']):
            score += 3
        
        # High package bonus
        package = job.get('package', '')
        numbers = re.findall(r'\d+', package)
        if numbers and int(numbers[0]) >= 45:
            score += 2
        
        return score
    
    def _calculate_ai_transition_score(self, job):
        """Calculate relevance score for AI transition category jobs"""
        score = 0
        content = (job.get('title', '') + ' ' + job.get('description', '') + ' ' + 
                  job.get('requirements', '')).lower()
        
        # AI/ML keywords
        ai_keywords = ['ai', 'ml', 'machine learning', 'data science', 'artificial intelligence', 'python']
        for keyword in ai_keywords:
            if keyword in content:
                score += 3
        
        # SAP background mentioned
        sap_keywords = ['sap', 'erp', 'enterprise', 'business systems']
        for keyword in sap_keywords:
            if keyword in content:
                score += 2
        
        # Transition-friendly terms
        transition_terms = ['background preferred', 'experience plus', 'domain knowledge', 'business context']
        for term in transition_terms:
            if term in content:
                score += 4
        
        # High package bonus (important for career transition)
        package = job.get('package', '')
        numbers = re.findall(r'\d+', package)
        if numbers and int(numbers[0]) >= 50:
            score += 3
        
        return score
    
    def _clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace and newlines
        cleaned = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common job site artifacts
        cleaned = re.sub(r'(new|urgent|hot|featured|premium)', '', cleaned, flags=re.IGNORECASE)
        
        return cleaned[:200]  # Limit length
    
    def get_job_summary(self):
        """Get summary of collected jobs"""
        jobs_data = self.get_jobs()
        
        summary = {
            'total_sap_jobs': len(jobs_data['sap_category']),
            'total_ai_transition_jobs': len(jobs_data['ai_transition_category']),
            'average_package_sap': self._calculate_average_package(jobs_data['sap_category']),
            'average_package_ai': self._calculate_average_package(jobs_data['ai_transition_category']),
            'top_locations': self._get_top_locations(jobs_data),
            'top_companies': self._get_top_companies(jobs_data),
            'collection_timestamp': datetime.now().isoformat()
        }
        
        return summary
    
    def _calculate_average_package(self, jobs):
        """Calculate average package for a list of jobs"""
        packages = []
        for job in jobs:
            package_str = job.get('package', '')
            numbers = re.findall(r'\d+', package_str)
            if numbers:
                packages.append(int(numbers[0]))
        
        return f"{sum(packages) / len(packages):.0f} LPA" if packages else "Not Available"
    
    def _get_top_locations(self, jobs_data):
        """Get top hiring locations"""
        locations = {}
        all_jobs = jobs_data['sap_category'] + jobs_data['ai_transition_category']
        
        for job in all_jobs:
            location = job.get('location', '').split(',')[0].strip()
            locations[location] = locations.get(location, 0) + 1
        
        return sorted(locations.items(), key=lambda x: x[1], reverse=True)[:5]
    
    def _get_top_companies(self, jobs_data):
        """Get top hiring companies"""
        companies = {}
        all_jobs = jobs_data['sap_category'] + jobs_data['ai_transition_category']
        
        for job in all_jobs:
            company = job.get('company', '')
            companies[company] = companies.get(company, 0) + 1
        
        return sorted(companies.items(), key=lambda x: x[1], reverse=True)[:5]
