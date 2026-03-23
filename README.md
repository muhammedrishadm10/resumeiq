# ResumeIQ — Intelligent Resume Screening App

A production-ready web application for screening and ranking multiple resumes against custom job criteria using AI-powered text analysis.

## Features

### Core Features
- **Multi-format Support** — Upload PDF, DOCX, and TXT resume files
- **Batch Processing** — Analyze up to 20 resumes simultaneously
- **Custom Criteria** — Define job requirements with flexible text input
- **Smart Scoring** — AI-powered scoring algorithm (0-100 scale)
- **Minimum Score Filter** — Filter candidates by score threshold
- **Detailed Analysis** — View matches, gaps, skills, and experience

### Analysis Capabilities
- **Criteria Matching** — Exact and partial keyword matching
- **Experience Detection** — Automatically extracts years of experience
- **Education Recognition** — Identifies degree levels (Bachelor, Masters, PhD)
- **Skill Extraction** — Detects programming languages, frameworks, tools
- **Contact Parsing** — Extracts email and phone numbers
- **Job Title Detection** — Identifies relevant roles from resume

### Export & Reporting
- **JSON Export** — Structured data for integration
- **CSV Export** — Spreadsheet-friendly format with all metrics
- **Visual Rankings** — Color-coded score indicators
- **Detailed Breakdown** — Per-candidate match/gap analysis

## Setup Instructions

### 1. Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### 2. Install Dependencies
```bash
cd resume_app
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python app.py
```

The server will start on `http://localhost:5000`

### 4. Open in Browser
Visit: http://localhost:5000

## How to Use

### Step 1: Upload Resumes
- Drag & drop resume files into the upload zone
- Or click to browse and select files
- Supports PDF, DOCX, and TXT formats
- Maximum file size: 32MB per file

### Step 2: Define Criteria
- Enter job requirements in the criteria textarea
- Use bullet points or comma-separated values
- Click quick-add chips for common requirements
- Adjust minimum score filter (optional)

**Example Criteria:**
```
- 5+ years of Python experience
- Strong knowledge of machine learning
- Experience with AWS or Azure cloud platforms
- Bachelor's degree in Computer Science
- Excellent communication skills
- Team leadership experience
```

### Step 3: Analyze & Review
- Click "Analyze Resumes" to start processing
- View ranked candidates with scores
- Click any candidate card to expand details
- Review matches, gaps, and detected skills

### Step 4: Export Results
- Download as JSON for system integration
- Download as CSV for spreadsheet analysis
- Re-run analysis with different criteria anytime

## Scoring Algorithm

Candidates are scored out of 100 based on:

| Category | Points | Description |
|----------|--------|-------------|
| Criteria Match | 60 | Direct and partial matches against your criteria |
| Experience | 15 | Years of professional experience (2 pts/year, max 15) |
| Education | 10 | PhD (10), Masters (7), Bachelors (5) |
| Certifications | 8 | Professional certifications detected |
| Achievements | 7 | Quantifiable results (%, $, growth metrics) |

### Score Categories
- **Excellent (80-100)** — Strong match, highly recommended
- **Good (60-79)** — Solid candidate, meets most requirements
- **Fair (40-59)** — Partial match, may need development
- **Low (0-39)** — Weak match, unlikely fit

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serve the web interface |
| `/upload` | POST | Upload resume files |
| `/analyze` | POST | Analyze resumes against criteria |
| `/clear` | POST | Clear uploaded resumes |
| `/stats` | GET | Get session statistics |
| `/health` | GET | Health check |

### Example API Usage

**Upload resumes:**
```bash
curl -X POST -F "files=@resume.pdf" -F "session_id=abc123" http://localhost:5000/upload
```

**Analyze:**
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"criteria": "Python, 5+ years experience", "session_id": "abc123", "min_score": 60}' \
  http://localhost:5000/analyze
```

## Project Structure
```
resume_app/
├── app.py                 # Flask backend with analysis engine
├── requirements.txt       # Python dependencies
├── README.md             # Documentation
└── static/
    └── index.html        # Single-page frontend application
```

## Requirements

### Python Packages
- Flask >= 2.3.0 — Web framework
- flask-cors >= 4.0.0 — Cross-origin support
- werkzeug >= 2.3.0 — WSGI utilities
- pdfplumber >= 0.10.0 — PDF text extraction
- python-docx >= 1.1.0 — DOCX text extraction
- PyPDF2 >= 3.0.0 — Alternative PDF support

### Browser Support
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Troubleshooting

### Common Issues

**"Upload failed — is the server running?"**
- Ensure Flask is running: `python app.py`
- Check port 5000 is not in use

**PDF extraction returns empty text**
- Some PDFs are scanned images; OCR is not supported
- Try converting to TXT or DOCX format

**Large files not uploading**
- Maximum file size is 32MB
- Try compressing or splitting large PDFs

## License

MIT License — Free for personal and commercial use.
