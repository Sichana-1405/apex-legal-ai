# 🔍 Interview Integrity Analyzer

> **TCS Tech Day Hackathon — Vidyavardhini College of Engineering, Vasai**
> Theme: AI + Cyber Defense

An AI-powered prototype that assists recruiters in identifying possible interview impersonation, AI-assisted responses, scripted answers, or deepfake interview risks in online hiring sessions.

> ⚖️ **Decision Support Only** — This system does **not** make hiring decisions.

---

## 🚀 Quick Start

### 1. Clone / Navigate to project
```bash
cd interview_integrity_analyzer
```

### 2. Create a virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set your Gemini API key
```bash
# Option A: Copy .env.example and fill in your key
copy .env.example .env
# Then edit .env and replace "your_gemini_api_key_here" with your real key

# Option B: Set environment variable directly
set GEMINI_API_KEY=your_key_here   # Windows
# export GEMINI_API_KEY=your_key   # macOS/Linux

# Option C: Enter the key in the sidebar at runtime (no .env needed)
```

Get a free API key at: https://aistudio.google.com/app/apikey

### 5. Run the app
```bash
streamlit run app.py
```

The app opens at: **http://localhost:8501**

---

## 📁 Project Structure

```
interview_integrity_analyzer/
├── app.py                          ← Home page + session state init
├── .streamlit/
│   └── config.toml                 ← Dark theme config
├── pages/
│   ├── 1_Candidate_Profile.py      ← Step 1: Resume selection / upload
│   ├── 2_Interview_Analysis.py     ← Step 2: Interview Q&A + AI analysis
│   └── 3_Report.py                 ← Step 3: Full report + PDF download
├── models/
│   ├── __init__.py
│   ├── gemini_service.py           ← Google Gemini 2.5 Flash integration
│   └── risk_engine.py              ← Rule-based risk scoring engine
├── utils/
│   ├── __init__.py
│   ├── styles.py                   ← Shared CSS dark theme
│   ├── sample_candidates.py        ← 5 synthetic candidate profiles
│   ├── resume_parser.py            ← PDF / TXT resume parser
│   └── report_generator.py         ← FPDF2 PDF report builder
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🧭 User Workflow

```
Home Page
   ↓
Step 1 — Candidate Profile
   Select a sample candidate (5 available) OR upload a PDF/TXT resume
   ↓
Step 2 — Interview Analysis
   Enter interview question + candidate answer + transcript notes
   Record behavioral observations (eye contact, lip sync, voice, prompting)
   Click "Run AI Analysis"
   ↓
   Gemini 2.5 Flash analyzes resume vs interview response → JSON result
   Rule-based risk engine scores all factors → Risk Score 0–100
   ↓
   View: Gauge chart, skill match, factor breakdown, AI explanation
   ↓
Step 3 — Report
   Full formatted report view
   Download professional PDF report
```

---

## 🤖 AI Analysis Features

### Google Gemini 2.5 Flash
- Compares candidate resume against interview response
- Returns structured JSON with:
  - **Skill Match %** — How well the answer reflects resume claims
  - **Technical Depth** — Weak / Moderate / Strong
  - **Missing Skills** — Skills claimed but not demonstrated
  - **Claims Verified / Unverified** — Resume claim validation
  - **Confidence Score** — AI confidence in genuine skill possession
  - **AI Explanation** — Recruiter-friendly 2–3 sentence summary

### Rule-Based Risk Engine

| Factor | Max Points | Trigger |
|--------|-----------|---------|
| Very Low Skill Match (<30%) | +35 | Gemini skill match result |
| Low Skill Match (30–50%) | +25 | Gemini skill match result |
| Weak Technical Depth | +15 | Gemini depth assessment |
| Poor Eye Contact | +15 | Recruiter dropdown |
| Large Lip Sync Delay | +20 | Recruiter dropdown |
| Robotic Voice | +10 | Recruiter dropdown |
| External Prompting | +15 | Recruiter dropdown |

**Risk Levels:**
- 🟢 **LOW** (0–30): Proceed with standard verification
- 🟡 **MEDIUM** (31–70): Manual review recommended
- 🔴 **HIGH** (71–100): Strong manual review required

---

## 📊 Sample Candidates (Built-in)

| # | Name | Role | Experience | Profile Type |
|---|------|------|------------|--------------|
| 1 | Arjun Sharma | Python Developer | 2 Years | Consistent & Credible |
| 2 | Neha Kapoor | Java Developer | 3 Years | Strong & Verified |
| 3 | Ravi Menon | Data Scientist | 1 Year | Some Skill Exaggeration |
| 4 | Priya Desai | AI/ML Engineer | 4 Years | Senior — High Expectation |
| 5 | Aditya Singh | Full Stack Developer | 2 Years | Consistent Profile |

All candidates are **completely fictional** — generated for prototype testing only.

---

## 📄 PDF Report Contents

1. Cover page with candidate name, risk score, and timestamp
2. Resume summary (truncated to fit)
3. Interview question and candidate answer
4. Behavioral observations (4 indicators)
5. AI analysis results (Gemini output)
6. Risk score visualization box
7. Risk factor breakdown table
8. Recruiter recommendation
9. Legal disclaimer

---

## ⚠️ Important Notes

- **No real deepfake detection** — behavioral signals are simulated via dropdowns
- **No facial recognition or voice biometrics** — prototype only
- **No real PII** — all sample data is synthetic and fictional
- **Gemini fallback** — app works without API key (behavioral scoring only)
- **Decision support only** — human recruiter review is always required

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| AI Engine | Google Gemini 2.5 Flash (`google-generativeai`) |
| PDF Reports | FPDF2 |
| Charts | Plotly |
| Resume Parsing | PyPDF2 |
| Data | Pandas |
| Environment | python-dotenv |

---

## 📦 Dependencies

```
streamlit>=1.31.0
google-generativeai>=0.7.0
python-dotenv>=1.0.0
pandas>=2.0.0
plotly>=5.18.0
PyPDF2>=3.0.0
fpdf2>=2.7.0
Pillow>=10.0.0
```

---

## 🏆 Hackathon Info

- **Event:** TCS Tech Day @ Vidyavardhini College of Engineering, Vasai
- **Theme:** AI + Cyber Defense
- **AI Feature:** Risk scoring + anomaly detection
- **Prototype Scope:** Sample candidate profiles / interview answers; flag mismatch patterns

---

*Built with ❤️ for TCS Tech Day Hackathon | AI + Cyber Defense Track*
