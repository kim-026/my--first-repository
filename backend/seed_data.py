import os
import json
import datetime
from sqlalchemy.orm import Session
from backend.database import SessionLocal, init_db
from backend.models import (
    Company, JobRequirement, Skill, Candidate, ResumeUpload,
    PersonalDetail, Education, Experience, ExtractedResumeData,
    Certification, ResumeSkill, ResumeMatchingSession,
    MatchingAnalysis, SkillMatchResult, MockQuestion, CandidateAnswer, Performance
)
from backend.services.nlp_extractor import SKILL_TAXONOMY

def create_sample_files():
    """Create sample resume files for instant drag-and-drop or test upload."""
    sample_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_resumes")
    os.makedirs(sample_dir, exist_ok=True)

    # 1. Alex Chen - ML Specialist (TXT)
    alex_txt_path = os.path.join(sample_dir, "Alex_Chen_ML_Resume.txt")
    with open(alex_txt_path, "w", encoding="utf-8") as f:
        f.write("""Alex Chen
alex.chen.ai@example.com | +1 (415) 890-1234 | San Francisco, CA
linkedin.com/in/alex-chen-ml | github.com/alexchen-ai

PROFESSIONAL SUMMARY
Senior Machine Learning & Data Systems Engineer with 5+ years of experience designing, training, and deploying large-scale deep learning models, predictive pipelines, and automated NLP architectures.

TECHNICAL SKILLS
Programming Languages: Python, SQL, C++, Bash
AI & Machine Learning: Machine Learning, Deep Learning, NLP, PyTorch, TensorFlow, Scikit-Learn, Pandas, NumPy, Keras, Hugging Face Transformers, LLM, Generative AI
Data & Infrastructure: PostgreSQL, Redis, Apache Spark, Kafka, Docker, Kubernetes, AWS, Git, CI/CD, FastAPI
Soft Skills: Team Collaboration, Leadership, Problem Solving, Agile, Mentorship

WORK EXPERIENCE
Senior Machine Learning Engineer | NeuralScale AI (2022 - Present)
- Architected enterprise NLP question answering pipeline with PyTorch and Transformers, serving 2M daily requests.
- Optimized model inference latency by 45% using ONNX runtime and Docker containerization on AWS EKS.
- Led cross-functional team of 4 data scientists in building automated continuous retraining pipelines.

Machine Learning Developer | Apex Data Labs (2019 - 2022)
- Implemented customer churn prediction system using Python, Scikit-Learn, and SQL on PostgreSQL warehouse.
- Built real-time feature store caching layer with Redis and FastAPI REST endpoints.

EDUCATION
Master of Science in Computer Science | Stanford University (2019)
Bachelor of Science in Software Engineering | UC Berkeley (2017)

CERTIFICATIONS
- AWS Certified Solutions Architect (2023)
- TensorFlow Developer Certificate (2022)
- Deep Learning Specialization - Coursera (2021)
""")

    # 2. Sarah Miller - Full Stack Engineer (TXT / Markdown / Doc)
    sarah_txt_path = os.path.join(sample_dir, "Sarah_Miller_FullStack_Resume.txt")
    with open(sarah_txt_path, "w", encoding="utf-8") as f:
        f.write("""Sarah Miller
sarah.miller.dev@example.com | +1 (206) 555-7890 | Seattle, WA
linkedin.com/in/sarah-miller-web | github.com/sarahmiller-dev

SUMMARY
Versatile Full-Stack Software Engineer with 4 years building high-performance web applications using React, TypeScript, Node.js, and Python.

CORE COMPETENCIES
Languages: JavaScript, TypeScript, Python, HTML5, CSS3, SQL
Frontend: React, Next.js, Redux, Tailwind CSS, Responsive Design
Backend & APIs: Node.js, Express, FastAPI, REST API, GraphQL
Databases: PostgreSQL, MongoDB, Redis, SQLite
DevOps & Cloud: Docker, AWS, Git, GitHub Actions, CI/CD
Soft Skills: Communication, Critical Thinking, Time Management, Teamwork, Agile

PROFESSIONAL EXPERIENCE
Full Stack Developer | CloudFlow Tech (2021 - Present)
- Engineered responsive client dashboard using React 18, TypeScript, and Tailwind CSS.
- Developed backend microservices using Node.js, Express, and PostgreSQL handling 50k active tenants.
- Configured CI/CD automation with GitHub Actions and Docker containers deployed to AWS ECS.

Frontend Developer | PixelCraft Media (2020 - 2021)
- Developed modern web portals with React, Next.js, and RESTful APIs.
- Improved Core Web Vitals score from 62 to 94 through code-splitting and asset optimization.

EDUCATION
Bachelor of Science in Computer Science | University of Washington (2020)

CERTIFICATIONS
- AWS Certified Developer - Associate (2022)
""")

    # 3. David Kumar - Data & Cloud Engineer (TXT)
    david_txt_path = os.path.join(sample_dir, "David_Kumar_DataCloud_Resume.txt")
    with open(david_txt_path, "w", encoding="utf-8") as f:
        f.write("""David Kumar
david.kumar.data@example.com | +1 (512) 440-3321 | Austin, TX
linkedin.com/in/david-kumar-cloud | github.com/davidkumar-data

PROFESSIONAL SUMMARY
Data Engineer with 3+ years experience engineering scalable ETL data pipelines, distributed computing with Spark, and cloud infrastructure on GCP and AWS.

SKILLS
Big Data & Cloud: Apache Spark, Hadoop, Kafka, GCP, AWS, Cloud Computing, Docker, Kubernetes, Terraform
Databases: SQL, PostgreSQL, MySQL, BigQuery, Cassandra
Languages: Python, SQL, Java, Bash
Practices: CI/CD, Data Engineering, Linux, Git, Problem Solving, Adaptability

EXPERIENCE
Data Engineer | DataMesh Solutions (2022 - Present)
- Designed streaming ETL data pipelines using Apache Spark, Kafka, and Google Cloud BigQuery.
- Built automated data quality validation monitors using Python and SQL.

Junior Cloud Engineer | Austin CloudWorks (2021 - 2022)
- Managed Kubernetes clusters and Terraform infrastructure provisioning for client analytics workloads.

EDUCATION
Bachelor of Technology in Information Technology | UT Austin (2021)

CERTIFICATIONS
- Google Professional Data Engineer (2023)
""")

    return sample_dir

def seed_database():
    """Populate database with initial master skills, companies, jobs, and candidates."""
    init_db()
    create_sample_files()
    db: Session = SessionLocal()

    try:
        # Check if already seeded
        if db.query(Company).first():
            print("Database already contains records. Ensuring skills and jobs are updated...")

        # 1. Master Skills Seeding
        existing_skills = {s.SkillName.lower() for s in db.query(Skill).all()}
        for k, v in SKILL_TAXONOMY.items():
            disp = v["display"]
            if disp.lower() not in existing_skills:
                skill_obj = Skill(SkillName=disp, SkillType=v["type"])
                db.add(skill_obj)
                existing_skills.add(disp.lower())
        db.commit()

        # 2. Seed Companies
        companies_data = [
            {
                "name": "Apex AI Technologies",
                "industry": "Artificial Intelligence & Enterprise SaaS",
                "website": "https://apexai.tech",
                "description": "Next-generation generative AI and automated decision intelligence platform."
            },
            {
                "name": "FinTech Nexus Corp",
                "industry": "Financial Technology & Banking APIs",
                "website": "https://fintechnexus.io",
                "description": "High-throughput secure payment routing and credit analysis software."
            },
            {
                "name": "CloudScale Systems",
                "industry": "Cloud Infrastructure & DevOps",
                "website": "https://cloudscale.systems",
                "description": "Distributed cloud orchestration and site reliability engineering platform."
            }
        ]

        companies = []
        for c in companies_data:
            existing = db.query(Company).filter(Company.CompanyName == c["name"]).first()
            if not existing:
                comp = Company(
                    CompanyName=c["name"],
                    Industry=c["industry"],
                    Website=c["website"],
                    Description=c["description"]
                )
                db.add(comp)
                db.flush()
                companies.append(comp)
            else:
                companies.append(existing)
        db.commit()

        # 3. Seed Job Requirements
        jobs_data = [
            {
                "company_id": companies[0].CompanyID,
                "job_title": "Senior Machine Learning Engineer",
                "required_skills": json.dumps(["Python", "SQL", "Machine Learning", "Deep Learning", "PyTorch", "Docker"]),
                "optional_skills": json.dumps(["AWS", "Kubernetes", "FastAPI", "NLP"]),
                "education": "Master's or Bachelor's in Computer Science or related STEM field",
                "experience": "3+ years production ML and software engineering",
                "description": "Lead the architecture and deployment of enterprise machine learning pipelines, deep learning models, and real-time inference microservices."
            },
            {
                "company_id": companies[1].CompanyID,
                "job_title": "Full-Stack Software Engineer (React / Python)",
                "required_skills": json.dumps(["Python", "React", "JavaScript", "SQL", "PostgreSQL", "REST API"]),
                "optional_skills": json.dumps(["Docker", "TypeScript", "FastAPI", "AWS"]),
                "education": "Bachelor's in Computer Science or equivalent practical experience",
                "experience": "2+ years building modern full-stack web applications",
                "description": "Build high-reliability financial portals and APIs with rich interactive React user interfaces and Python backend services."
            },
            {
                "company_id": companies[2].CompanyID,
                "job_title": "Cloud DevOps & Platform Engineer",
                "required_skills": json.dumps(["AWS", "Docker", "Kubernetes", "Linux", "CI/CD", "Python"]),
                "optional_skills": json.dumps(["Terraform", "PostgreSQL", "Bash / Shell", "Microservices"]),
                "education": "Bachelor's in Computer Science, IT, or Engineering",
                "experience": "3+ years cloud infrastructure and container orchestration",
                "description": "Architect, secure, and scale multi-region cloud infrastructure, Kubernetes clusters, and automated continuous deployment pipelines."
            },
            {
                "company_id": companies[0].CompanyID,
                "job_title": "Senior Data Scientist & NLP Researcher",
                "required_skills": json.dumps(["Python", "Machine Learning", "Natural Language Processing", "PyTorch", "SQL"]),
                "optional_skills": json.dumps(["Large Language Models", "LangChain", "Docker"]),
                "education": "Master's or Ph.D. in Computer Science or Artificial Intelligence",
                "experience": "4+ years NLP modeling and research",
                "description": "Conduct cutting-edge research and build retrieval-augmented generation (RAG) and domain-specific LLM evaluation systems."
            }
        ]

        jobs = []
        for j in jobs_data:
            existing = db.query(JobRequirement).filter(
                JobRequirement.JobTitle == j["job_title"],
                JobRequirement.CompanyID == j["company_id"]
            ).first()
            if not existing:
                job_obj = JobRequirement(
                    CompanyID=j["company_id"],
                    JobTitle=j["job_title"],
                    RequiredSkills=j["required_skills"],
                    OptionalSkills=j["optional_skills"],
                    Education=j["education"],
                    Experience=j["experience"],
                    JobDescription=j["description"]
                )
                db.add(job_obj)
                db.flush()
                jobs.append(job_obj)
            else:
                jobs.append(existing)
        db.commit()

        # 4. Seed Pre-populated Candidate Records for Dashboard Demo
        if db.query(Candidate).count() == 0:
            print("Seeding demo candidates with full evaluation records...")

            # Candidate 1: Alex Chen (Matches ML Engineer role strongly)
            cand1 = Candidate(Name="Alex Chen", Email="alex.chen.ai@example.com", Phone="+1 (415) 890-1234")
            db.add(cand1)
            db.flush()

            up1 = ResumeUpload(
                CandidateID=cand1.CandidateID,
                FileType="text/plain",
                FilePath="sample_resumes/Alex_Chen_ML_Resume.txt",
                OriginalFilename="Alex_Chen_ML_Resume.txt",
                FileSize=2150
            )
            db.add(up1)
            db.flush()

            p1 = PersonalDetail(
                CandidateID=cand1.CandidateID,
                UploadID=up1.UploadID,
                Name="Alex Chen",
                Email="alex.chen.ai@example.com",
                Phone="+1 (415) 890-1234",
                Degree="Master of Science",
                Location="San Francisco, CA",
                LinkedIn="https://linkedin.com/in/alex-chen-ml",
                GitHub="https://github.com/alexchen-ai"
            )
            e1 = Education(
                CandidateID=cand1.CandidateID,
                UploadID=up1.UploadID,
                Degree="Master of Science",
                School="Stanford University",
                GraduationYear="2019",
                FieldOfStudy="Computer Science"
            )
            exp1 = Experience(
                CandidateID=cand1.CandidateID,
                UploadID=up1.UploadID,
                JobTitle="Senior Machine Learning Engineer",
                Company="NeuralScale AI",
                Duration="2022 - Present",
                ExperienceYears=4.5,
                WorkExperience="Architected enterprise NLP question answering pipeline with PyTorch and Transformers serving 2M daily requests."
            )
            cert1 = Certification(
                CandidateID=cand1.CandidateID,
                UploadID=up1.UploadID,
                Skill="AWS",
                CertName="AWS Certified Solutions Architect",
                Issuer="Amazon Web Services",
                Year="2023"
            )
            db.add_all([p1, e1, exp1, cert1])

            # Extracted Skills for Candidate 1
            alex_skills = ["Python", "SQL", "Machine Learning", "Deep Learning", "PyTorch", "Docker", "AWS", "FastAPI", "NLP", "Problem Solving"]
            ext1 = ExtractedResumeData(
                UploadID=up1.UploadID,
                RawText="Alex Chen Resume...",
                ParsedJSON=json.dumps({"skills": alex_skills, "experience_years": 4.5})
            )
            db.add(ext1)
            db.flush()

            for sk in alex_skills:
                db.add(ResumeSkill(
                    UploadID=up1.UploadID,
                    ExtractionID=ext1.ExtractionID,
                    SkillName=sk,
                    Proficiency="Advanced" if sk in ["Python", "Machine Learning", "PyTorch"] else "Intermediate",
                    YearsExperience=4.0
                ))

            # Matching Session for Alex Chen with Job 0 (Senior ML Engineer)
            match1 = ResumeMatchingSession(
                UploadID=up1.UploadID,
                RequirementID=jobs[0].RequirementID
            )
            db.add(match1)
            db.flush()

            analysis1 = MatchingAnalysis(
                MatchingID=match1.MatchingID,
                MatchPercentage=96.5,
                SkillGapDetails=json.dumps({
                    "matching_skills": [{"skill": s, "status": "matched"} for s in ["Python", "SQL", "Machine Learning", "Deep Learning", "PyTorch", "Docker"]],
                    "missing_skills": [],
                    "optional_matched": ["AWS", "FastAPI", "NLP"]
                }),
                Explanation="Candidate is an exceptional match. Possesses all 6 mandatory skills plus 3 optional skills.",
                Strengths=json.dumps(["Mastery of PyTorch & Deep Learning", "Production containerization with Docker", "4.5 years experience exceeding requirement"]),
                ImprovementAreas=json.dumps(["Explore emerging multi-modal model architectures."])
            )
            db.add(analysis1)

            # Mock Questions generated strictly based on Alex Chen's skills (Python, SQL, Machine Learning)
            q1_1 = MockQuestion(
                CandidateID=cand1.CandidateID,
                MatchingID=match1.MatchingID,
                SkillName="Python",
                Question="In Python, how do generator functions and the 'yield' keyword optimize memory consumption compared to returning a full list? Write or describe a code snippet demonstrating a generator for large data streaming.",
                QuestionType="coding",
                Difficulty="Intermediate",
                SampleAnswerHint="Explain lazy evaluation and iterator protocol."
            )
            q1_2 = MockQuestion(
                CandidateID=cand1.CandidateID,
                MatchingID=match1.MatchingID,
                SkillName="SQL",
                Question="Write or outline an SQL query using Window Functions (e.g., DENSE_RANK() OVER PARTITION BY) to retrieve the top 3 highest-earning candidates per department.",
                QuestionType="coding",
                Difficulty="Intermediate",
                SampleAnswerHint="Use CTE and DENSE_RANK() OVER (PARTITION BY dept ORDER BY salary DESC)."
            )
            q1_3 = MockQuestion(
                CandidateID=cand1.CandidateID,
                MatchingID=match1.MatchingID,
                SkillName="Machine Learning",
                Question="Explain the bias-variance tradeoff in Machine Learning. What specific regularization techniques (L1, L2, Dropout) and validation strategies do you use to detect and prevent overfitting?",
                QuestionType="conceptual",
                Difficulty="Intermediate",
                SampleAnswerHint="Detail high bias (underfitting) vs high variance (overfitting) and regularization penalties."
            )
            q1_4 = MockQuestion(
                CandidateID=cand1.CandidateID,
                MatchingID=match1.MatchingID,
                SkillName="PyTorch",
                Question="Explain how PyTorch computes gradients via the Autograd computational graph, and why calling optimizer.zero_grad() is essential in the training loop.",
                QuestionType="problem-solving",
                Difficulty="Advanced",
                SampleAnswerHint="Discuss dynamic computation graphs, backward pass gradient accumulation, and memory clearing."
            )
            q1_5 = MockQuestion(
                CandidateID=cand1.CandidateID,
                MatchingID=match1.MatchingID,
                SkillName="Docker",
                Question="What best practices do you follow to create secure, minimal multi-stage Docker builds for machine learning microservices?",
                QuestionType="scenario",
                Difficulty="Intermediate",
                SampleAnswerHint="Distroless/slim images, layer caching, non-root user, .dockerignore."
            )
            db.add_all([q1_1, q1_2, q1_3, q1_4, q1_5])
            db.flush()

            # Answers for Alex Chen
            ans1_1 = CandidateAnswer(
                QuestionID=q1_1.QuestionID,
                CandidateID=cand1.CandidateID,
                Answer="Generators use lazy evaluation via yield, pausing function state and generating one item at a time. This keeps memory O(1) instead of loading gigabytes of data into RAM.",
                Score=9.5,
                Feedback="Comprehensive answer with strong grasp of Python memory management and generators.",
                CorrectnessRelevance="Highly accurate.",
                ImprovementSuggestions="Could provide a two-line generator expression example."
            )
            ans1_2 = CandidateAnswer(
                QuestionID=q1_2.QuestionID,
                CandidateID=cand1.CandidateID,
                Answer="WITH Ranked AS (SELECT *, DENSE_RANK() OVER (PARTITION BY dept_id ORDER BY salary DESC) as rnk FROM employees) SELECT * FROM Ranked WHERE rnk <= 3;",
                Score=10.0,
                Feedback="Flawless SQL query syntax using CTE and window ranking functions.",
                CorrectnessRelevance="100% correct.",
                ImprovementSuggestions="None."
            )
            ans1_3 = CandidateAnswer(
                QuestionID=q1_3.QuestionID,
                CandidateID=cand1.CandidateID,
                Answer="Bias is underfitting error while variance is overfitting to noise. We balance it using L1 Lasso for sparsity, L2 Ridge for weight shrinkage, Dropout in deep networks, and K-Fold cross validation.",
                Score=9.0,
                Feedback="Great conceptual explanation covering both sides of tradeoff and practical remedies.",
                CorrectnessRelevance="Very accurate.",
                ImprovementSuggestions="Mention early stopping as well."
            )
            ans1_4 = CandidateAnswer(
                QuestionID=q1_4.QuestionID,
                CandidateID=cand1.CandidateID,
                Answer="PyTorch builds dynamic DAGs where tensors track grad_fn. Gradients accumulate by default to support recurrent models, so optimizer.zero_grad() prevents accumulation from prior batches.",
                Score=9.0,
                Feedback="Accurate description of PyTorch computational graph and gradient accumulation.",
                CorrectnessRelevance="Strong technical explanation.",
                ImprovementSuggestions="Mention retain_graph=True edge case."
            )
            ans1_5 = CandidateAnswer(
                QuestionID=q1_5.QuestionID,
                CandidateID=cand1.CandidateID,
                Answer="I use multi-stage builds with python-slim base images, copy only wheel packages from builder stage, run as a non-privileged user, and cache pip layers.",
                Score=9.5,
                Feedback="Clear, production-tested container security practices.",
                CorrectnessRelevance="Directly answers modern DevOps standards.",
                ImprovementSuggestions="Mention scanning images with Trivy."
            )
            db.add_all([ans1_1, ans1_2, ans1_3, ans1_4, ans1_5])

            # Performance for Alex Chen
            perf1 = Performance(
                CandidateID=cand1.CandidateID,
                MatchingID=match1.MatchingID,
                TotalScore=47.0,
                MaximumScore=50.0,
                PercentageScore=94.0,
                OverallPerformance="Exceptional",
                StrongAreas=json.dumps(["SQL Window Functions (10/10)", "Python Lazy Iterators (9.5/10)", "Docker Multi-stage Architecture (9.5/10)"]),
                ImprovementAreas=json.dumps(["Edge-case gradient retention in complex loss topologies"]),
                PerformanceAnalysis="Candidate scored 47/50 (94%), demonstrating exceptional depth in Python, SQL, ML, and systems engineering."
            )
            db.add(perf1)

            # Candidate 2: Sarah Miller (Matches Full Stack Role)
            cand2 = Candidate(Name="Sarah Miller", Email="sarah.miller.dev@example.com", Phone="+1 (206) 555-7890")
            db.add(cand2)
            db.flush()

            up2 = ResumeUpload(
                CandidateID=cand2.CandidateID,
                FileType="text/plain",
                FilePath="sample_resumes/Sarah_Miller_FullStack_Resume.txt",
                OriginalFilename="Sarah_Miller_FullStack_Resume.txt",
                FileSize=1890
            )
            db.add(up2)
            db.flush()

            p2 = PersonalDetail(
                CandidateID=cand2.CandidateID,
                UploadID=up2.UploadID,
                Name="Sarah Miller",
                Email="sarah.miller.dev@example.com",
                Phone="+1 (206) 555-7890",
                Degree="Bachelor of Science",
                Location="Seattle, WA",
                LinkedIn="https://linkedin.com/in/sarah-miller-web",
                GitHub="https://github.com/sarahmiller-dev"
            )
            e2 = Education(
                CandidateID=cand2.CandidateID,
                UploadID=up2.UploadID,
                Degree="Bachelor of Science",
                School="University of Washington",
                GraduationYear="2020",
                FieldOfStudy="Computer Science"
            )
            exp2 = Experience(
                CandidateID=cand2.CandidateID,
                UploadID=up2.UploadID,
                JobTitle="Full Stack Developer",
                Company="CloudFlow Tech",
                Duration="2021 - Present",
                ExperienceYears=3.5,
                WorkExperience="Engineered responsive client dashboard using React 18, TypeScript, and Tailwind CSS. Developed backend microservices using Node.js and PostgreSQL."
            )
            db.add_all([p2, e2, exp2])

            sarah_skills = ["React", "JavaScript", "TypeScript", "Python", "SQL", "PostgreSQL", "REST API", "Tailwind CSS", "Node.js", "Docker"]
            ext2 = ExtractedResumeData(
                UploadID=up2.UploadID,
                RawText="Sarah Miller Resume...",
                ParsedJSON=json.dumps({"skills": sarah_skills, "experience_years": 3.5})
            )
            db.add(ext2)
            db.flush()

            for sk in sarah_skills:
                db.add(ResumeSkill(
                    UploadID=up2.UploadID,
                    ExtractionID=ext2.ExtractionID,
                    SkillName=sk,
                    Proficiency="Advanced" if sk in ["React", "JavaScript", "TypeScript"] else "Intermediate",
                    YearsExperience=3.0
                ))

            # Matching Session for Sarah with Job 1 (Full Stack React / Python)
            match2 = ResumeMatchingSession(
                UploadID=up2.UploadID,
                RequirementID=jobs[1].RequirementID
            )
            db.add(match2)
            db.flush()

            analysis2 = MatchingAnalysis(
                MatchingID=match2.MatchingID,
                MatchPercentage=92.0,
                SkillGapDetails=json.dumps({
                    "matching_skills": [{"skill": s, "status": "matched"} for s in ["Python", "React", "JavaScript", "SQL", "PostgreSQL", "REST API"]],
                    "missing_skills": [],
                    "optional_matched": ["Docker", "TypeScript"]
                }),
                Explanation="Candidate is a strong hire for the Full-Stack role with all core skills covered.",
                Strengths=json.dumps(["Extensive React & modern frontend mastery", "Clean TypeScript & API development", "Good PostgreSQL schema design"]),
                ImprovementAreas=json.dumps(["Could expand cloud deployment experience on AWS/GCP."])
            )
            db.add(analysis2)

            # Mock Questions generated strictly based on Sarah Miller's extracted skills (React, JavaScript, TypeScript, PostgreSQL)
            q2_1 = MockQuestion(
                CandidateID=cand2.CandidateID,
                MatchingID=match2.MatchingID,
                SkillName="React",
                Question="How does React's Reconciliation engine and Virtual DOM diffing algorithm function? When should you use useMemo, useCallback, and React.memo to optimize re-renders in a heavy dashboard?",
                QuestionType="application",
                Difficulty="Intermediate",
                SampleAnswerHint="Fiber tree comparison, shallow prop comparison, referential stability."
            )
            q2_2 = MockQuestion(
                CandidateID=cand2.CandidateID,
                MatchingID=match2.MatchingID,
                SkillName="JavaScript",
                Question="Explain the JavaScript Event Loop, Call Stack, Microtask Queue (Promises), and Macrotask Queue (setTimeout). In what order will asynchronous callbacks resolve?",
                QuestionType="conceptual",
                Difficulty="Intermediate",
                SampleAnswerHint="Microtasks run immediately after call stack empties before macrotasks."
            )
            q2_3 = MockQuestion(
                CandidateID=cand2.CandidateID,
                MatchingID=match2.MatchingID,
                SkillName="TypeScript",
                Question="Explain how TypeScript Generics, Utility Types (e.g. Partial, Pick, Record), and Discriminated Unions enhance type-safety and eliminate runtime bugs in complex APIs.",
                QuestionType="application",
                Difficulty="Intermediate",
                SampleAnswerHint="Type-level functions, mapped types, pattern matching with common tag."
            )
            q2_4 = MockQuestion(
                CandidateID=cand2.CandidateID,
                MatchingID=match2.MatchingID,
                SkillName="PostgreSQL",
                Question="When an SQL query with multiple JOINs suffers from slow response times on large tables, what indexing strategies, EXPLAIN plan metrics, and partitioning techniques would you employ to optimize it?",
                QuestionType="problem-solving",
                Difficulty="Intermediate",
                SampleAnswerHint="Check EXPLAIN ANALYZE, seq scan vs index scan, composite indexes."
            )
            q2_5 = MockQuestion(
                CandidateID=cand2.CandidateID,
                MatchingID=match2.MatchingID,
                SkillName="REST API",
                Question="What architectural practices make a RESTful API idempotent and secure against replay attacks and race conditions?",
                QuestionType="scenario",
                Difficulty="Intermediate",
                SampleAnswerHint="Idempotency keys, PUT/DELETE vs POST, JWT expiration, database row locking."
            )
            db.add_all([q2_1, q2_2, q2_3, q2_4, q2_5])
            db.flush()

            ans2_1 = CandidateAnswer(
                QuestionID=q2_1.QuestionID,
                CandidateID=cand2.CandidateID,
                Answer="React compares virtual DOM nodes using fiber keys and shallow prop comparison. React.memo prevents component re-renders unless props change, while useMemo caches expensive computed values and useCallback prevents recreating function pointers.",
                Score=9.0,
                Feedback="Solid understanding of React reconciliation and rendering performance.",
                CorrectnessRelevance="Accurate and practical.",
                ImprovementSuggestions="Mention profiler devtool usage."
            )
            ans2_2 = CandidateAnswer(
                QuestionID=q2_2.QuestionID,
                CandidateID=cand2.CandidateID,
                Answer="The call stack executes synchronous code. When async tasks finish, promises go to microtask queue and timers go to macrotask queue. Microtasks drain completely before the next macrotask is processed.",
                Score=9.0,
                Feedback="Clear explanation of event loop priority queues.",
                CorrectnessRelevance="Accurate.",
                ImprovementSuggestions="Mention requestAnimationFrame queue."
            )
            ans2_3 = CandidateAnswer(
                QuestionID=q2_3.QuestionID,
                CandidateID=cand2.CandidateID,
                Answer="Generics allow reusable types without losing specific signatures. Discriminated unions allow TypeScript to narrow down types in switch statements using a shared type tag.",
                Score=8.5,
                Feedback="Good explanation of type narrowing and generics.",
                CorrectnessRelevance="Clear and to the point.",
                ImprovementSuggestions="Provide an interface snippet."
            )
            ans2_4 = CandidateAnswer(
                QuestionID=q2_4.QuestionID,
                CandidateID=cand2.CandidateID,
                Answer="I run EXPLAIN ANALYZE to identify sequential table scans, create composite indexes matching JOIN keys and WHERE clauses, and use table partitioning by date range.",
                Score=8.5,
                Feedback="Practical approach to query tuning.",
                CorrectnessRelevance="Accurate.",
                ImprovementSuggestions="Mention vacuum and analyze statistics."
            )
            ans2_5 = CandidateAnswer(
                QuestionID=q2_5.QuestionID,
                CandidateID=cand2.CandidateID,
                Answer="We use Idempotency-Key headers in HTTP requests, store processed keys in Redis with TTL, and use database transactions with optimistic locking.",
                Score=9.0,
                Feedback="Excellent real-world architecture for idempotent payment APIs.",
                CorrectnessRelevance="Highly relevant.",
                ImprovementSuggestions="None."
            )
            db.add_all([ans2_1, ans2_2, ans2_3, ans2_4, ans2_5])

            perf2 = Performance(
                CandidateID=cand2.CandidateID,
                MatchingID=match2.MatchingID,
                TotalScore=44.0,
                MaximumScore=50.0,
                PercentageScore=88.0,
                OverallPerformance="Strong Hire",
                StrongAreas=json.dumps(["React Fiber & State Optimization (9.0/10)", "API Idempotency & Security (9.0/10)", "Event Loop Concurrency (9.0/10)"]),
                ImprovementAreas=json.dumps(["Database statistics maintenance and vacuuming strategies"]),
                PerformanceAnalysis="Candidate scored 44/50 (88%), exhibiting strong practical full-stack engineering proficiency."
            )
            db.add(perf2)

            # Candidate 3: David Kumar (Cloud & Data Engineer)
            cand3 = Candidate(Name="David Kumar", Email="david.kumar.data@example.com", Phone="+1 (512) 440-3321")
            db.add(cand3)
            db.flush()

            up3 = ResumeUpload(
                CandidateID=cand3.CandidateID,
                FileType="text/plain",
                FilePath="sample_resumes/David_Kumar_DataCloud_Resume.txt",
                OriginalFilename="David_Kumar_DataCloud_Resume.txt",
                FileSize=1740
            )
            db.add(up3)
            db.flush()

            p3 = PersonalDetail(
                CandidateID=cand3.CandidateID,
                UploadID=up3.UploadID,
                Name="David Kumar",
                Email="david.kumar.data@example.com",
                Phone="+1 (512) 440-3321",
                Degree="Bachelor of Technology",
                Location="Austin, TX",
                LinkedIn="https://linkedin.com/in/david-kumar-cloud",
                GitHub="https://github.com/davidkumar-data"
            )
            e3 = Education(
                CandidateID=cand3.CandidateID,
                UploadID=up3.UploadID,
                Degree="Bachelor of Technology",
                School="UT Austin",
                GraduationYear="2021",
                FieldOfStudy="Information Technology"
            )
            exp3 = Experience(
                CandidateID=cand3.CandidateID,
                UploadID=up3.UploadID,
                JobTitle="Data Engineer",
                Company="DataMesh Solutions",
                Duration="2022 - Present",
                ExperienceYears=2.5,
                WorkExperience="Designed streaming ETL pipelines using Apache Spark, Kafka, and GCP BigQuery. Built automated data validation monitors in Python."
            )
            db.add_all([p3, e3, exp3])

            david_skills = ["Apache Spark", "Hadoop", "Kafka", "GCP", "AWS", "Docker", "Kubernetes", "SQL", "Python", "Data Engineering"]
            ext3 = ExtractedResumeData(
                UploadID=up3.UploadID,
                RawText="David Kumar Resume...",
                ParsedJSON=json.dumps({"skills": david_skills, "experience_years": 2.5})
            )
            db.add(ext3)
            db.flush()

            for sk in david_skills:
                db.add(ResumeSkill(
                    UploadID=up3.UploadID,
                    ExtractionID=ext3.ExtractionID,
                    SkillName=sk,
                    Proficiency="Intermediate",
                    YearsExperience=2.5
                ))

            # Matching Session for David with Job 2 (Cloud DevOps & Platform Engineer)
            match3 = ResumeMatchingSession(
                UploadID=up3.UploadID,
                RequirementID=jobs[2].RequirementID
            )
            db.add(match3)
            db.flush()

            # Missing: Linux, CI/CD
            analysis3 = MatchingAnalysis(
                MatchingID=match3.MatchingID,
                MatchPercentage=74.5,
                SkillGapDetails=json.dumps({
                    "matching_skills": [{"skill": s, "status": "matched"} for s in ["AWS", "Docker", "Kubernetes", "Python"]],
                    "missing_skills": [{"skill": s, "status": "missing"} for s in ["Linux", "CI/CD"]],
                    "optional_matched": ["PostgreSQL"]
                }),
                Explanation="Candidate has solid Cloud and Container skills (AWS, Docker, Kubernetes) but lacks explicit Linux administration and CI/CD pipeline automation experience in resume.",
                Strengths=json.dumps(["Kubernetes and AWS foundation", "Strong Python & Distributed data background"]),
                ImprovementAreas=json.dumps(["Bridge Linux system administration gap", "Acquire CI/CD GitHub Actions/GitLab experience"])
            )
            db.add(analysis3)

            # Mock Questions generated strictly based on David Kumar's extracted skills (Apache Spark, Kafka, Kubernetes, AWS)
            q3_1 = MockQuestion(
                CandidateID=cand3.CandidateID,
                MatchingID=match3.MatchingID,
                SkillName="Apache Spark",
                Question="In building a batch and streaming ETL pipeline, how do you handle schema evolution, idempotent data ingestion, and late-arriving records in a distributed data lake?",
                QuestionType="problem-solving",
                Difficulty="Intermediate",
                SampleAnswerHint="Watermarking, checkpointing, Delta Lake ACID tables."
            )
            q3_2 = MockQuestion(
                CandidateID=cand3.CandidateID,
                MatchingID=match3.MatchingID,
                SkillName="Kubernetes",
                Question="Explain the interaction between Deployments, ReplicaSets, Services (ClusterIP vs Ingress), and Pods in Kubernetes. How do Readiness and Liveness Probes prevent service downtime during rolling updates?",
                QuestionType="application",
                Difficulty="Intermediate",
                SampleAnswerHint="Rolling updates, traffic routing through endpoints, probe thresholds."
            )
            q3_3 = MockQuestion(
                CandidateID=cand3.CandidateID,
                MatchingID=match3.MatchingID,
                SkillName="AWS",
                Question="Design a highly available and scalable cloud architecture on AWS for a high-traffic web application. Detail your use of VPC, ALB, Auto Scaling, ECS/EKS or Lambda, and RDS Multi-AZ.",
                QuestionType="scenario",
                Difficulty="Intermediate",
                SampleAnswerHint="Public/private subnets, ALB health checks, Multi-AZ failover."
            )
            q3_4 = MockQuestion(
                CandidateID=cand3.CandidateID,
                MatchingID=match3.MatchingID,
                SkillName="Docker",
                Question="What best practices do you follow to create secure, minimal multi-stage Docker builds for microservices?",
                QuestionType="scenario",
                Difficulty="Intermediate",
                SampleAnswerHint="Distroless bases, layer order, non-root users."
            )
            db.add_all([q3_1, q3_2, q3_3, q3_4])
            db.flush()

            ans3_1 = CandidateAnswer(
                QuestionID=q3_1.QuestionID,
                CandidateID=cand3.CandidateID,
                Answer="For streaming with Spark, we use watermarking to discard excessively late events and write to Delta Lake which handles schema evolution seamlessly.",
                Score=8.0,
                Feedback="Good explanation of watermarking and Delta Lake.",
                CorrectnessRelevance="Accurate.",
                ImprovementSuggestions="Describe exact watermark syntax."
            )
            ans3_2 = CandidateAnswer(
                QuestionID=q3_2.QuestionID,
                CandidateID=cand3.CandidateID,
                Answer="Deployments manage ReplicaSets which ensure desired pod counts. Readiness probes prevent traffic from hitting pods until warm, while liveness probes restart deadlocked containers.",
                Score=8.5,
                Feedback="Clear description of probes and rolling update mechanics.",
                CorrectnessRelevance="Accurate.",
                ImprovementSuggestions="Explain Ingress controller role."
            )
            ans3_3 = CandidateAnswer(
                QuestionID=q3_3.QuestionID,
                CandidateID=cand3.CandidateID,
                Answer="We set up a VPC across 2 AZs, place ALB in public subnets, application containers in private subnets with auto-scaling groups, and an RDS PostgreSQL database with Multi-AZ standby replica.",
                Score=8.5,
                Feedback="Standard highly available AWS well-architected layout.",
                CorrectnessRelevance="Accurate.",
                ImprovementSuggestions="Mention NAT gateway for outbound updates."
            )
            ans3_4 = CandidateAnswer(
                QuestionID=q3_4.QuestionID,
                CandidateID=cand3.CandidateID,
                Answer="Multi-stage builds allow separating build tools from final runtime, reducing image footprint from 800MB to under 100MB and removing build dependencies.",
                Score=8.0,
                Feedback="Concise and correct benefits of multi-stage containers.",
                CorrectnessRelevance="Accurate.",
                ImprovementSuggestions="Mention security vulnerability scanning."
            )
            db.add_all([ans3_1, ans3_2, ans3_3, ans3_4])

            perf3 = Performance(
                CandidateID=cand3.CandidateID,
                MatchingID=match3.MatchingID,
                TotalScore=33.0,
                MaximumScore=40.0,
                PercentageScore=82.5,
                OverallPerformance="Strong Hire",
                StrongAreas=json.dumps(["Kubernetes Pod Orchestration (8.5/10)", "AWS High Availability Architecture (8.5/10)"]),
                ImprovementAreas=json.dumps(["CI/CD pipeline automation tools", "Linux low-level kernel tuning"]),
                PerformanceAnalysis="Candidate scored 33/40 (82.5%), demonstrating strong foundational cloud skills."
            )
            db.add(perf3)

            db.commit()
            print("Demo candidates seeded successfully!")

        print("Seeding complete!")

    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
