"""Deterministic, privacy-friendly resume parsing for candidate onboarding.

This is intentionally a best-effort parser, not an AI decision maker. It only
prefills editable fields from text already present in a candidate's resume.
Candidates always review and may overwrite every extracted value.
"""
import re
from pathlib import Path


# Ordered from specific terms to broad ones to produce useful recruiter tags.
SKILLS = (
    'Amazon Web Services', 'Google Cloud Platform', 'Spring Boot', 'Machine Learning',
    'Data Analysis', 'Power BI', 'CI/CD', 'GitHub Actions', 'Azure DevOps',
    'Terraform', 'Kubernetes', 'Docker', 'Jenkins', 'Ansible', 'Linux', 'Nginx',
    'Python', 'JavaScript', 'TypeScript', 'Java', 'C++', 'C#', '.NET', 'Node.js',
    'React', 'Next.js', 'Angular', 'Vue.js', 'Vue', 'Flask', 'Django', 'FastAPI',
    'SQLAlchemy', 'SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'SQLite',
    'AWS', 'Azure', 'GCP', 'Git', 'GitHub', 'HTML', 'CSS', 'Sass', 'Bootstrap',
    'Tailwind CSS', 'Selenium', 'Playwright', 'Pytest', 'REST API', 'GraphQL',
    'Figma', 'Agile', 'Scrum', 'DevOps', 'Cybersecurity', 'Excel'
)


def extract_resume_text(path):
    """Return readable text from a PDF or DOCX, or an empty string otherwise."""
    suffix = Path(path).suffix.lower()
    if suffix == '.pdf':
        from pypdf import PdfReader
        return '\n'.join(page.extract_text() or '' for page in PdfReader(path).pages)
    if suffix == '.docx':
        from docx import Document
        document = Document(path)
        paragraphs = [paragraph.text for paragraph in document.paragraphs]
        # Many resume templates keep contact details in a table.
        table_cells = [cell.text for table in document.tables for row in table.rows for cell in row.cells]
        return '\n'.join(paragraphs + table_cells)
    # Legacy .doc is binary. It remains uploadable but cannot be reliably
    # parsed without a document converter.
    return ''


def _first_match(patterns, text, flags=re.I):
    for pattern in patterns:
        match = re.search(pattern, text, flags)
        if match:
            return match.group(1).strip(' \t:,-|')
    return ''


def _normalise_text(value):
    return re.sub(r'\s+', ' ', value or '').strip()


def _find_skills(text):
    found = []
    for skill in SKILLS:
        # Punctuation-bearing skills cannot use a conventional word boundary.
        match = re.search(r'(?<![\w+#])' + re.escape(skill) + r'(?![\w+#])', text, re.I)
        if match:
            display = {'Amazon Web Services': 'AWS', 'Google Cloud Platform': 'GCP'}.get(skill, skill)
            if display not in [item[1] for item in found]:
                found.append((match.start(), display))
    # Resume authors usually list related skills in a meaningful order.
    return ', '.join(skill for _position, skill in sorted(found))


def _find_experience(text):
    patterns = (
        r'\b(\d{1,2}(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)\b(?:\s+(?:of\s+)?)?(?:experience|exp\.?|professional)?',
        r'\bexperience\s*[:\-]?\s*(\d{1,2}(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)',
        r'\b(\d{1,2}(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)\s+in\b',
    )
    value = _first_match(patterns, text)
    try:
        return value if value and 0 <= float(value) <= 60 else ''
    except ValueError:
        return ''


def _find_education(lines):
    education_pattern = re.compile(
        r'\b(B\.?\s?(?:Tech|E|Sc|CA|Com)|M\.?\s?(?:Tech|E|Sc|CA|Com)|MBA|'
        r'Bachelor(?:\'s)?|Master(?:\'s)?|Diploma|Ph\.?D|University|College)\b',
        re.I,
    )
    return '\n'.join(line for line in lines if education_pattern.search(line))[:1200]


ROLE_PATTERN = re.compile(
    r'\b(?:engineer|developer|analyst|architect|consultant|administrator|manager|'
    r'intern|specialist|designer|recruiter|lead|tester|qa)\b',
    re.I,
)
DATE_PATTERN = re.compile(
    r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b|'
    r'\b(?:19|20)\d{2}\s*[-–]\s*(?:Present|(?:19|20)\d{2})\b',
    re.I,
)


def _clean_designation(value):
    value = value.strip(' |:-')
    value = re.sub(r'(?i)interninternship\b', 'Intern', value)
    value = re.sub(r'(?i)\binternship\b', 'Intern', value)
    value = re.sub(r'(?i)^(?:results[- ]driven|experienced|certified)\s+', '', value)
    return value[:100].strip()


def _find_current_employment(lines, compact):
    """Find the latest role/company from labels, summary text, or Experience."""
    designation = _first_match((
        r'\b(?:current\s+)?(?:designation|job\s*title|role|position)\s*[:\-]\s*([^|\n]{2,100})',
    ), compact)
    company = _first_match((
        r'\b(?:current\s+)?(?:company|employer|organisation|organization)\s*[:\-]\s*([^|\n]{2,100})',
        r'\b(?:working at|employed by)\s+([^|\n,.]{2,100})',
        r'\b(?:intern|engineer|developer|analyst|architect|consultant|administrator|manager|specialist|designer|recruiter)\s+at\s+([^,|.]{2,100})',
    ), compact)

    experience_index = next(
        (index for index, line in enumerate(lines) if re.fullmatch(r'(?:work\s+)?experiences?', line.strip(' |:-'), re.I)),
        None,
    )
    if experience_index is not None:
        section_lines = lines[experience_index + 1:experience_index + 10]
        role_index = next(
            (index for index, line in enumerate(section_lines)
             if ROLE_PATTERN.search(line) and not DATE_PATTERN.search(line) and len(line) <= 100),
            None,
        )
        if role_index is not None:
            designation = designation or _clean_designation(section_lines[role_index])
            for line in section_lines[role_index + 1:]:
                clean = line.strip(' |:-')
                if (clean and len(clean) <= 100 and not DATE_PATTERN.search(clean)
                        and not re.search(r'\b(?:India|Remote)\b', clean, re.I)
                        and not ROLE_PATTERN.search(clean)):
                    company = company or clean
                    break

    if not designation:
        title_line = next((line for line in lines[:10] if ROLE_PATTERN.search(line) and len(line) <= 100), '')
        designation = _clean_designation(title_line)
    return company[:100].strip(), designation


def _find_location(lines):
    city_pattern = re.compile(
        r'\b(Hyderabad|Bengaluru|Bangalore|Chennai|Mumbai|Pune|Delhi|Noida|Gurgaon|'
        r'Gurugram|Kolkata|Ahmedabad|Vijayawada|Visakhapatnam|Remote)\b',
        re.I,
    )
    for line in lines[:15]:
        explicit = re.search(r'\b(?:location|address|based in|city)\s*[:\-]\s*([^|,]{2,100})', line, re.I)
        if explicit:
            return explicit.group(1).strip()
        city = city_pattern.search(line)
        if city:
            india = re.search(r'\bIndia\b', line[city.start():], re.I)
            return f"{city.group(1)}, India" if india else city.group(1)
    return ''


def parse_resume(path):
    """Extract common candidate fields from text-based PDF and DOCX resumes."""
    text = extract_resume_text(path)
    lines = [_normalise_text(line) for line in text.splitlines() if _normalise_text(line)]
    compact = ' '.join(lines)

    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', compact)
    phone_match = re.search(
        r'(?<!\w)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?){2,4}\d{3,4}(?!\w)',
        compact,
    )
    linkedin_match = re.search(r'(https?://(?:www\.)?linkedin\.com/in/[^\s|,]+)', compact, re.I)
    portfolio_match = re.search(r'(https?://(?![^\s]+linkedin\.com)[^\s|,]+)', compact, re.I)

    likely_name = ''
    for line in lines[:5]:
        if len(line) < 80 and '@' not in line and not re.search(r'\b(resume|curriculum vitae|cv|phone|mobile)\b', line, re.I):
            likely_name = line
            break

    location = _find_location(lines)
    company, designation = _find_current_employment(lines, compact)

    return {
        'name': likely_name,
        'email': email_match.group(0) if email_match else '',
        'phone': phone_match.group(0) if phone_match else '',
        'location': location,
        'current_company': company,
        'designation': designation,
        'experience_years': _find_experience(compact),
        'skills': _find_skills(compact),
        'education': _find_education(lines),
        'linkedin_url': linkedin_match.group(1).rstrip(').,;') if linkedin_match else '',
        'portfolio_url': portfolio_match.group(1).rstrip(').,;') if portfolio_match else '',
        'has_extractable_text': bool(compact),
    }
