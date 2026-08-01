"""
utils/sample_candidates.py
───────────────────────────
Five fully synthetic candidate profiles for hackathon demonstration.
All names, companies, institutions, and contact details are fictional.
"""

# ─────────────────────────────────────────────────────────────────────────────
# Sample Candidates Dataset
# ─────────────────────────────────────────────────────────────────────────────

SAMPLE_CANDIDATES = [
    {
        "id": 1,
        "name": "Arjun Sharma",
        "role": "Python Developer",
        "experience": "2 Years",
        "avatar": "👨‍💻",
        "skills_summary": "Python, Django, REST APIs, PostgreSQL, Redis",
        "education": "B.Tech CSE — Nexora Institute of Technology (2022)",
        "risk_profile": "Consistent & Credible",
        "resume_text": """
ARJUN SHARMA
Python Developer
📧 arjun.sharma@devmail.io  |  📞 +91 98201 34567  |  📍 Pune, Maharashtra
GitHub: github.com/arjunsharma-dev  |  LinkedIn: linkedin.com/in/arjunsharma-py

──────────────────────────────────────────────────────────────
PROFESSIONAL SUMMARY
──────────────────────────────────────────────────────────────
Python Developer with 2 years of professional experience building RESTful APIs and
backend systems using Django and Flask. Solid understanding of database design,
caching strategies, and agile development workflows. Comfortable with code reviews,
unit testing, and CI/CD pipelines. Looking to grow into a senior backend engineering
role within a product-first team.

──────────────────────────────────────────────────────────────
EDUCATION
──────────────────────────────────────────────────────────────
B.Tech in Computer Science and Engineering
Nexora Institute of Technology, Pune  |  2018 – 2022  |  CGPA: 8.2/10

──────────────────────────────────────────────────────────────
TECHNICAL SKILLS
──────────────────────────────────────────────────────────────
Programming Languages : Python (Primary), SQL, Bash scripting
Frameworks            : Django, Django REST Framework, Flask, FastAPI (basic)
Databases             : PostgreSQL, MySQL, Redis
Tools & Platforms     : Git, GitHub, Docker (basic), Postman, Linux (Ubuntu), VS Code
Testing               : pytest, unittest, Postman API tests
Concepts              : REST APIs, OOP, MVC, JWT Auth, RBAC, SDLC, Agile/Scrum

──────────────────────────────────────────────────────────────
WORK EXPERIENCE
──────────────────────────────────────────────────────────────
Junior Python Developer  |  Orbitix Solutions Pvt. Ltd., Pune
July 2022 – Present  (2 years)

• Developed and maintained 3 REST API modules for the internal project management platform
• Implemented JWT authentication and role-based access control (RBAC)
• Optimized PostgreSQL queries reducing average API response time by 22%
• Wrote pytest unit tests with 80%+ coverage for all owned modules
• Resolved 55+ bugs tracked via JIRA; participated in bi-weekly code reviews
• Collaborated in 2-week Scrum sprints with a cross-functional team of 8

──────────────────────────────────────────────────────────────
PROJECTS
──────────────────────────────────────────────────────────────
1. E-Commerce Backend API
   Built a full RESTful backend for a mid-sized e-commerce client: product catalogue,
   cart management, order lifecycle, and Stripe payment integration.
   Handled 5,000+ daily API requests in staging environment.
   Tech: Python, Django REST Framework, PostgreSQL, Redis, Stripe API, Docker

2. ETL Data Pipeline
   Developed a nightly ETL pipeline to ingest, transform, and load 100K+ records
   from 3 external data sources into a PostgreSQL analytics warehouse.
   Reduced data latency from 24 hours to 4 hours.
   Tech: Python, Pandas, SQLAlchemy, Celery, PostgreSQL

──────────────────────────────────────────────────────────────
CERTIFICATIONS
──────────────────────────────────────────────────────────────
• Python Professional Certificate — DataCamp (2022)
• Django REST Framework Masterclass — Udemy (2022)
• SQL for Backend Engineers — Coursera (2023)

──────────────────────────────────────────────────────────────
STRENGTHS
──────────────────────────────────────────────────────────────
Detail-oriented | Strong debugging skills | Collaborative | Consistent delivery

LANGUAGES: English (Fluent), Hindi (Native), Marathi (Intermediate)
""",
    },
    {
        "id": 2,
        "name": "Neha Kapoor",
        "role": "Java Developer",
        "experience": "3 Years",
        "avatar": "👩‍💻",
        "skills_summary": "Java, Spring Boot, Microservices, Docker, AWS, MySQL",
        "education": "B.E. IT — Skyline College of Engineering (2021)",
        "risk_profile": "Strong & Verified",
        "resume_text": """
NEHA KAPOOR
Senior Java Developer
📧 neha.kapoor.java@techvault.io  |  📞 +91 97345 88921  |  📍 Bengaluru, Karnataka
GitHub: github.com/nehakapoor-java  |  LinkedIn: linkedin.com/in/nehakapoor-java

──────────────────────────────────────────────────────────────
PROFESSIONAL SUMMARY
──────────────────────────────────────────────────────────────
Experienced Java Developer with 3 years of hands-on expertise in Spring Boot
microservices architecture, REST API design, and AWS cloud deployment. Delivered 4
production-grade microservices currently serving 50,000+ users. Proficient in
containerization with Docker, CI/CD automation, and relational database optimization.
Strong background in banking domain applications with emphasis on security and uptime.

──────────────────────────────────────────────────────────────
EDUCATION
──────────────────────────────────────────────────────────────
B.E. in Information Technology
Skyline College of Engineering, Bengaluru  |  2017 – 2021  |  CGPA: 8.5/10

──────────────────────────────────────────────────────────────
TECHNICAL SKILLS
──────────────────────────────────────────────────────────────
Programming Languages : Java 17, SQL, Bash
Frameworks            : Spring Boot 3.x, Spring Security, Spring Data JPA, Hibernate
Architecture          : Microservices, REST, Event-driven (Kafka basic)
Cloud & DevOps        : AWS EC2, S3, RDS, Docker, GitHub Actions CI/CD, Maven
Databases             : MySQL, PostgreSQL, Redis
Testing               : JUnit 5, Mockito, Postman, SonarQube
Tools                 : IntelliJ IDEA, Git, JIRA, Swagger/OpenAPI

──────────────────────────────────────────────────────────────
WORK EXPERIENCE
──────────────────────────────────────────────────────────────
Java Developer (Mid-Level)  |  FinAxis Technologies Pvt. Ltd., Bengaluru
August 2021 – Present  (3 years)

• Architected and built 4 Spring Boot microservices for a digital banking platform
• Implemented OAuth 2.0 + Spring Security for authentication across 3 services
• Containerized all services with Docker; orchestrated via AWS ECS
• Set up GitHub Actions CI/CD pipelines reducing deployment time by 40%
• Mentored 2 junior developers; led internal Spring Boot knowledge-sharing sessions
• Maintained 99.8% uptime SLA over 18 consecutive months

──────────────────────────────────────────────────────────────
PROJECTS
──────────────────────────────────────────────────────────────
1. Digital Banking Microservices Platform
   Core contributor to a 6-service banking platform (account management, transactions,
   notifications, KYC, reporting, auth). Responsible for account-service and transaction-service.
   Tech: Java, Spring Boot, MySQL, Docker, AWS ECS, Kafka (basic), Redis

2. Inventory Management System
   Built a full inventory and supply-chain management system for a logistics client
   with role-based dashboards, real-time stock alerts, and PDF report generation.
   Tech: Java, Spring Boot, Spring Security, PostgreSQL, Thymeleaf, JasperReports

──────────────────────────────────────────────────────────────
CERTIFICATIONS
──────────────────────────────────────────────────────────────
• AWS Certified Developer – Associate (2023)
• Spring Boot Professional – Udemy (2022)
• Java SE 17 Developer — Oracle Certified (2022)

LANGUAGES: English (Fluent), Hindi (Native), Kannada (Basic)
""",
    },
    {
        "id": 3,
        "name": "Ravi Menon",
        "role": "Data Scientist",
        "experience": "1 Year",
        "avatar": "📊",
        "skills_summary": "Python, Scikit-learn, Pandas, Power BI, SQL",
        "education": "M.Sc. Data Science — Vortex University (2023)",
        "risk_profile": "Some Skill Exaggeration Possible",
        "resume_text": """
RAVI MENON
Data Scientist | ML Enthusiast
📧 ravi.menon.datascience@mailhub.io  |  📞 +91 87654 23001  |  📍 Hyderabad, Telangana
GitHub: github.com/ravimenon-ds  |  Kaggle: kaggle.com/ravimenon2025

──────────────────────────────────────────────────────────────
PROFESSIONAL SUMMARY
──────────────────────────────────────────────────────────────
Data Scientist with 1 year of professional experience and advanced expertise in
TensorFlow, PyTorch, deep learning, and computer vision systems. Skilled in
building production-ready ML pipelines and deploying AI models on AWS SageMaker.
Passionate about applying cutting-edge deep learning techniques to solve complex
business problems. Strong experience with NLP, GANs, and transformer architectures.

──────────────────────────────────────────────────────────────
EDUCATION
──────────────────────────────────────────────────────────────
M.Sc. in Data Science
Vortex University of Technology, Hyderabad  |  2021 – 2023  |  CGPA: 7.6/10

──────────────────────────────────────────────────────────────
TECHNICAL SKILLS
──────────────────────────────────────────────────────────────
Programming Languages : Python, R, SQL
Deep Learning         : TensorFlow (Advanced), PyTorch (Advanced), Keras
ML Libraries          : Scikit-learn, XGBoost, LightGBM
NLP                   : BERT, GPT (API), SpaCy, NLTK, transformers
Computer Vision       : OpenCV, YOLO, ResNet, GANs
Data Tools            : Pandas, NumPy, Matplotlib, Seaborn, Power BI
Cloud                 : AWS SageMaker (Advanced), Google Colab, S3
Other                 : Git, Jupyter Notebook, Docker (basic)

──────────────────────────────────────────────────────────────
WORK EXPERIENCE
──────────────────────────────────────────────────────────────
Junior Data Analyst  |  Trendline Business Solutions, Hyderabad
September 2023 – Present  (1 year)

• Prepared weekly operational and sales reports using Excel and Power BI
• Wrote SQL queries to extract data from the reporting database for business reviews
• Assisted senior analyst in cleaning and preparing datasets for quarterly analysis
• Created 3 Power BI dashboards used by the operations and sales teams

──────────────────────────────────────────────────────────────
PROJECTS
──────────────────────────────────────────────────────────────
1. Customer Churn Prediction (Kaggle)
   Participated in a Kaggle churn prediction challenge using a tutorial-based approach.
   Achieved top 38% leaderboard position with a basic XGBoost model.
   Tech: Python, XGBoost, Scikit-learn, Pandas, Kaggle

2. Fake News Detector
   Built a fake news classifier using TF-IDF + Logistic Regression on a standard
   Kaggle dataset. Achieved 94% accuracy (known benchmark).
   Tech: Python, Scikit-learn, NLTK, Pandas, Jupyter Notebook

──────────────────────────────────────────────────────────────
CERTIFICATIONS
──────────────────────────────────────────────────────────────
• Deep Learning Specialization — Coursera / deeplearning.ai (2023)
• TensorFlow in Practice — Coursera (2023)
• Computer Vision with Python — Udemy (2024)

LANGUAGES: English (Fluent), Telugu (Native), Hindi (Intermediate)
""",
    },
    {
        "id": 4,
        "name": "Priya Desai",
        "role": "AI/ML Engineer",
        "experience": "4 Years",
        "avatar": "🤖",
        "skills_summary": "Python, PyTorch, TensorFlow, NLP, MLOps, AWS SageMaker",
        "education": "M.Tech AI — Apex Technical University (2020)",
        "risk_profile": "Senior Profile — High Expectation",
        "resume_text": """
PRIYA DESAI
Senior AI/ML Engineer
📧 priya.desai@aicraft.io  |  📞 +91 99876 12345  |  📍 Chennai, Tamil Nadu
GitHub: github.com/priyadesai-ml  |  Scholar: scholar.google.com/priyadesai (2 papers)

──────────────────────────────────────────────────────────────
PROFESSIONAL SUMMARY
──────────────────────────────────────────────────────────────
AI/ML Engineer with 4 years of specialized experience designing and deploying
end-to-end machine learning systems across NLP, computer vision, and recommendation
systems. Co-authored 2 peer-reviewed publications on efficient transformer architectures.
Demonstrated success reducing model inference latency by 40% via ONNX quantization.
Leads a team of 4 engineers and drives the MLOps culture in a fast-moving AI startup.

──────────────────────────────────────────────────────────────
EDUCATION
──────────────────────────────────────────────────────────────
M.Tech in Artificial Intelligence
Apex Technical University, Chennai  |  2018 – 2020  |  CGPA: 9.4/10
Best Thesis Award — "Efficient Attention Mechanisms for Edge Inference"

B.E. in Computer Science
Techbridge College of Engineering, Chennai  |  2014 – 2018  |  CGPA: 8.9/10

──────────────────────────────────────────────────────────────
TECHNICAL SKILLS
──────────────────────────────────────────────────────────────
ML Frameworks : PyTorch, TensorFlow, JAX, Hugging Face Transformers, ONNX
NLP           : BERT, RoBERTa, T5, GPT fine-tuning, RAG pipelines, LangChain
Computer Vision: YOLO v8, Detectron2, OpenCV, Mask R-CNN, image segmentation
MLOps         : MLflow, Weights & Biases, Kubeflow, Docker, Kubernetes, Airflow
Cloud         : AWS SageMaker, GCP Vertex AI, Azure ML Studio
Data Eng.     : PySpark, Pandas, Feature Stores (Feast), BigQuery

──────────────────────────────────────────────────────────────
WORK EXPERIENCE
──────────────────────────────────────────────────────────────
Senior ML Engineer  |  Visionix AI Pvt. Ltd., Chennai
March 2022 – Present  (3 years 4 months)

• Leads team of 4 ML engineers; owns architecture decisions and model releases
• Established company's first MLOps framework (MLflow + Airflow + Docker/K8s)
• Delivered 5 client AI products across fintech, manufacturing, and retail
• Built document intelligence pipeline processing 10K+ documents/day at 1.2s p95 latency

ML Engineer  |  NeuralBridge Technologies, Chennai
July 2020 – February 2022  (1 year 8 months)

• Built NLP models for intent classification in customer support chatbot
• Deployed models via FastAPI on AWS; maintained 99.3% uptime over 18 months

──────────────────────────────────────────────────────────────
PROJECTS
──────────────────────────────────────────────────────────────
1. Document Intelligence Platform (Production)
   OCR → layout analysis → NER → structured JSON extraction for 10K+ docs/day
   Tech: PyTorch, Hugging Face, Tesseract, FastAPI, Docker, Kubernetes, AWS

2. Multimodal Recommendation Engine
   Combined text (sentence-transformers) + visual (ResNet-50) for product recs.
   22% CTR improvement over collaborative filtering baseline in A/B test.
   Tech: PyTorch, FAISS, FastAPI, PostgreSQL, MLflow

3. Edge-Optimized Defect Detection (Published)
   Lightweight CNN for PCB defect detection; 40% latency reduction via ONNX.
   Published in Journal of Intelligent Manufacturing Systems (2022).
   Tech: PyTorch, ONNX, OpenCV, Raspberry Pi

──────────────────────────────────────────────────────────────
CERTIFICATIONS
──────────────────────────────────────────────────────────────
• AWS Certified Machine Learning – Specialty (2022)
• MLOps Specialization — Coursera (2023)
• Kubeflow Certified Practitioner — Linux Foundation (2023)

LANGUAGES: English (Fluent), Tamil (Native), Hindi (Intermediate)
""",
    },
    {
        "id": 5,
        "name": "Aditya Singh",
        "role": "Full Stack Developer",
        "experience": "2 Years",
        "avatar": "🌐",
        "skills_summary": "React.js, Node.js, MongoDB, PostgreSQL, Docker, AWS",
        "education": "B.Tech CSE — Greenfields Institute of Technology (2022)",
        "risk_profile": "Consistent Profile",
        "resume_text": """
ADITYA SINGH
Full Stack Developer
📧 aditya.singh.dev@byteworks.io  |  📞 +91 94567 80234  |  📍 Surat, Gujarat
GitHub: github.com/adityasingh-fs  |  Portfolio: adityasingh.dev

──────────────────────────────────────────────────────────────
PROFESSIONAL SUMMARY
──────────────────────────────────────────────────────────────
Full Stack Developer with 2 years of professional experience building responsive web
applications, RESTful APIs, and cloud-hosted services. Proficient in React.js for
frontend and Node.js/Express for backend development. Strong understanding of database
design, JWT authentication, and CI/CD deployment pipelines. Contributed to 4 production
applications serving 8,000+ active users across e-commerce and SaaS domains.

──────────────────────────────────────────────────────────────
EDUCATION
──────────────────────────────────────────────────────────────
B.Tech in Computer Science and Engineering
Greenfields Institute of Technology, Surat  |  2018 – 2022  |  CGPA: 7.6/10

──────────────────────────────────────────────────────────────
TECHNICAL SKILLS
──────────────────────────────────────────────────────────────
Languages      : JavaScript (ES6+), TypeScript (Intermediate), Python (basic), SQL
Frontend       : React.js, Redux Toolkit, Next.js (basic), HTML5, CSS3, Tailwind CSS
Backend        : Node.js, Express.js, REST APIs, GraphQL (basic), Socket.io
Databases      : PostgreSQL, MongoDB, Redis
DevOps & Cloud : Docker, Nginx, AWS EC2 & S3, Vercel, Netlify, GitHub Actions CI/CD
Testing        : Jest, React Testing Library, Postman
Tools          : Git, Figma (basic), JIRA, VS Code, Linux

──────────────────────────────────────────────────────────────
WORK EXPERIENCE
──────────────────────────────────────────────────────────────
Full Stack Developer  |  Hexacode Solutions Pvt. Ltd., Surat
June 2022 – Present  (2 years)

• Developed and maintained 4 client-facing web applications (retail, healthcare, logistics)
• Led React.js migration of a legacy jQuery portal — reduced bundle size by 35%
• Integrated Razorpay payment gateway and real-time SMS/email notification services
• Mentored 1 junior developer; conducted fortnightly code review sessions
• Maintained 99.5% uptime for all hosted applications on AWS EC2 with Nginx

──────────────────────────────────────────────────────────────
PROJECTS
──────────────────────────────────────────────────────────────
1. PetCare Booking Platform (Live — 2,200+ users)
   Full-stack pet services booking platform with real-time slot booking, Razorpay
   payment, email/SMS notifications, and admin dashboard.
   Tech: React.js, Node.js, Express.js, PostgreSQL, Redis, Docker, AWS EC2

2. HR Leave Management System
   Internal HR portal for a 200-person company with role-based dashboards
   (Employee / Manager / HR Admin), leave tracking, and PDF report generation.
   Tech: React.js, Redux, Node.js, PostgreSQL, PDFKit, Docker

3. Real-time Chat App
   Group chat application with WebSocket (Socket.io), JWT auth, and message history.
   Tech: React.js, Node.js, Socket.io, MongoDB, JWT

──────────────────────────────────────────────────────────────
CERTIFICATIONS
──────────────────────────────────────────────────────────────
• React – The Complete Guide — Udemy (2022)
• Node.js Developer Course — Udemy (2022)
• Docker Essentials — Linux Foundation (2023)

LANGUAGES: English (Fluent), Hindi (Fluent), Gujarati (Native)
""",
    },
]


def get_candidate_by_id(candidate_id: int) -> dict:
    """Return a candidate dict by ID, or None if not found."""
    return next((c for c in SAMPLE_CANDIDATES if c["id"] == candidate_id), None)


def get_candidate_names() -> list[str]:
    """Return list of candidate display names for selection UI."""
    return [f"{c['avatar']} {c['name']} — {c['role']}" for c in SAMPLE_CANDIDATES]
