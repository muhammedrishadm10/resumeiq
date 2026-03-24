from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re
import json
import tempfile
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = tempfile.mkdtemp()
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB max

resume_store = {}
analysis_history = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_txt(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def extract_text_from_pdf(filepath):
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"
        return text
    except ImportError:
        return extract_text_fallback(filepath)

def extract_text_from_docx(filepath):
    try:
        import docx
        doc = docx.Document(filepath)
        return "\n".join([para.text for para in doc.paragraphs])
    except ImportError:
        return extract_text_fallback(filepath)

def extract_text_fallback(filepath):
    try:
        with open(filepath, 'rb') as f:
            content = f.read()
        text = content.decode('utf-8', errors='ignore')
        text = re.sub(r'[^\x20-\x7E\n\r\t]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text[:5000]
    except:
        return ""

def extract_text(filepath, filename):
    ext = filename.rsplit('.', 1)[1].lower()
    if ext == 'txt':
        return extract_text_from_txt(filepath)
    elif ext == 'pdf':
        return extract_text_from_pdf(filepath)
    elif ext == 'docx':
        return extract_text_from_docx(filepath)
    return ""

def score_resume(text, criteria):
    text_lower = text.lower()
    criteria_lower = criteria.lower()
    
    score = 0
    matches = []
    gaps = []
    
    criteria_lines = [line.strip() for line in re.split(r'[,\n;]', criteria_lower) if line.strip()]
    
    skill_patterns = {
        'programming': r'\b(python|java|javascript|typescript|c\+\+|c#|ruby|go|rust|swift|kotlin|php|scala|r\b|matlab)\b',
        'frameworks': r'\b(react|angular|vue|django|flask|spring|node\.?js|express|fastapi|laravel|rails|tensorflow|pytorch|keras)\b',
        'databases': r'\b(sql|mysql|postgresql|mongodb|redis|elasticsearch|dynamodb|cassandra|oracle)\b',
        'cloud': r'\b(aws|azure|gcp|google cloud|docker|kubernetes|terraform|jenkins|ci/cd|devops)\b',
        'soft_skills': r'\b(leadership|communication|teamwork|problem.solving|analytical|management|agile|scrum)\b',
        'education': r'\b(bachelor|master|phd|degree|b\.?s\.?|m\.?s\.?|b\.?e\.?|mba|computer science|engineering|mathematics)\b',
    }
    
    total_criteria = len(criteria_lines)
    matched_criteria = 0
    
    for criterion in criteria_lines:
        criterion = criterion.strip('- \u2022*#').strip()
        if len(criterion) < 2:
            continue
        
        if criterion in text_lower:
            matched_criteria += 1
            matches.append(criterion.title())
        else:
            words = criterion.split()
            word_matches = sum(1 for w in words if len(w) > 3 and w in text_lower)
            if word_matches > len(words) * 0.6:
                matched_criteria += 0.7
                matches.append(f"{criterion.title()} (partial)")
            else:
                gaps.append(criterion.title())
    
    if total_criteria > 0:
        score = (matched_criteria / total_criteria) * 60
    
    exp_match = re.findall(r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)', text_lower)
    if exp_match:
        years = max(int(y) for y in exp_match)
        score += min(years * 2, 15)
    
    if re.search(r'\b(phd|doctorate)\b', text_lower):
        score += 10
    elif re.search(r'\b(master|m\.s\.|mba|m\.e\.)\b', text_lower):
        score += 7
    elif re.search(r'\b(bachelor|b\.s\.|b\.e\.|degree)\b', text_lower):
        score += 5
    
    cert_count = len(re.findall(r'\b(certified|certification|certificate|aws|pmp|cpa|cfa|ccna|cissp)\b', text_lower))
    score += min(cert_count * 1.5, 8)
    
    achievement_count = len(re.findall(r'\b\d+%|\$\d+|\d+x\b|\d+\s*(million|billion|thousand|users|customers)', text_lower))
    score += min(achievement_count * 1, 7)
    
    score = min(round(score, 1), 100)
    
    name = extract_name(text)
    email = extract_email(text)
    skills_found = extract_skills(text_lower, skill_patterns)
    
    return {
        'score': score,
        'matches': matches[:10],
        'gaps': gaps[:8],
        'name': name,
        'email': email,
        'skills': skills_found,
        'experience_years': max([int(y) for y in exp_match], default=0) if exp_match else 0,
    }

def extract_name(text):
    lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
    for line in lines[:5]:
        if len(line.split()) in [2, 3] and all(w[0].isupper() for w in line.split() if w):
            if not any(c.isdigit() for c in line) and '@' not in line:
                return line
    return "Candidate"

def extract_email(text):
    match = re.search(r'[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}', text)
    return match.group(0) if match else None

def extract_phone(text):
    patterns = [
        r'\b\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
        r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
        r'\b\+?\d{1,3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None

def extract_skills(text_lower, patterns):
    found = []
    for category, pattern in patterns.items():
        skills = re.findall(pattern, text_lower)
        found.extend([s.upper() if len(s) <= 4 else s.title() for s in set(skills)])
    return list(set(found))[:15]

def extract_job_titles(text):
    title_patterns = r'\b(software engineer|developer|manager|director|analyst|consultant|architect|lead|senior|junior|intern|specialist|coordinator|administrator|designer|product manager|project manager|data scientist|machine learning engineer)\b'
    titles = re.findall(title_patterns, text.lower())
    return list(set(titles))[:5]

def extract_companies(text):
    company_pattern = r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\s+(?:Inc\.?|LLC|Ltd\.?|Corp\.?|Corporation|Company|Co\.)'
    companies = re.findall(company_pattern, text)
    return list(set(companies))[:5]

@app.route('/api')
@app.route('/api/')
def index():
    return jsonify({'status': 'API is running', 'version': '1.1.0'})

@app.route('/api/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files')
    session_id = request.form.get('session_id', 'default')
    
    if session_id not in resume_store:
        resume_store[session_id] = []
    
    uploaded = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            text = extract_text(filepath, filename)
            
            resume_store[session_id].append({
                'filename': filename,
                'text': text,
                'char_count': len(text)
            })
            uploaded.append(filename)
    
    return jsonify({
        'uploaded': uploaded,
        'total': len(resume_store.get(session_id, [])),
        'session_id': session_id
    })

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    criteria = data.get('criteria', '')
    session_id = data.get('session_id', 'default')
    min_score = data.get('min_score', 0)

    if not criteria:
        return jsonify({'error': 'No criteria provided'}), 400

    resumes = resume_store.get(session_id, [])
    if not resumes:
        return jsonify({'error': 'No resumes uploaded'}), 400

    results = []
    for resume in resumes:
        analysis = score_resume(resume['text'], criteria)
        job_titles = extract_job_titles(resume['text'])
        companies = extract_companies(resume['text'])

        result = {
            'filename': resume['filename'],
            'name': analysis['name'],
            'email': analysis['email'],
            'phone': analysis.get('phone'),
            'score': analysis['score'],
            'matches': analysis['matches'],
            'gaps': analysis['gaps'],
            'skills': analysis['skills'],
            'experience_years': analysis['experience_years'],
            'education_level': analysis.get('education_level'),
            'job_titles': job_titles,
            'companies': companies,
            'text_preview': resume['text'][:400] + '...' if len(resume['text']) > 400 else resume['text']
        }

        if analysis['score'] >= min_score:
            results.append(result)

    results.sort(key=lambda x: x['score'], reverse=True)

    for i, r in enumerate(results):
        r['rank'] = i + 1

    analysis_history[session_id] = {
        'timestamp': datetime.now().isoformat(),
        'criteria': criteria,
        'total_resumes': len(resumes),
        'matched_resumes': len(results),
        'top_score': results[0]['score'] if results else 0
    }

    return jsonify({
        'results': results,
        'total_analyzed': len(resumes),
        'total_matched': len(results),
        'criteria_summary': {
            'criteria_text': criteria[:200] + '...' if len(criteria) > 200 else criteria,
            'min_score_applied': min_score
        }
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    session_id = request.args.get('session_id', 'default')
    history = analysis_history.get(session_id, {})
    resumes = resume_store.get(session_id, [])

    return jsonify({
        'session_id': session_id,
        'uploaded_resumes': len(resumes),
        'last_analysis': history,
        'supported_formats': list(ALLOWED_EXTENSIONS)
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'version': '1.1.0',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/clear', methods=['POST'])
def clear():
    data = request.get_json()
    session_id = data.get('session_id', 'default')
    if session_id in resume_store:
        del resume_store[session_id]
    return jsonify({'status': 'cleared'})
