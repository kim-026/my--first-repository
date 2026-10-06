import random
import re
from typing import List, Dict, Any

# Curated skill-based question bank specifically keyed by candidate skills
SKILL_QUESTION_TEMPLATES = {
    "python": [
        {
            "type": "coding",
            "question": "In Python, how do generator functions and the 'yield' keyword optimize memory consumption compared to returning a full list? Write or describe a code snippet demonstrating a generator for large data streaming.",
            "hint": "Mention lazy evaluation, iterators, memory footprint, and the difference between return and yield.",
            "keywords": ["generator", "yield", "memory", "lazy", "iterator", "stream", "iteration", "next"]
        },
        {
            "type": "conceptual",
            "question": "Explain the Global Interpreter Lock (GIL) in CPython. How does it impact CPU-bound multi-threading versus I/O-bound concurrency, and what architectural strategies (e.g. multiprocessing, asyncio) mitigate it?",
            "hint": "Address thread-safety, CPython internals, multiprocessing vs threading, and asynchronous event loops.",
            "keywords": ["gil", "interpreter", "lock", "cpu", "i/o", "multiprocessing", "asyncio", "thread", "concurrency"]
        },
        {
            "type": "problem-solving",
            "question": "How do Python decorators work under the hood? How would you implement a parameterized decorator that measures execution time and logs errors for high-throughput APIs?",
            "hint": "Describe closures, first-class functions, functools.wraps, and nested wrapper functions.",
            "keywords": ["decorator", "closure", "wraps", "functools", "wrapper", "execution time", "arguments"]
        }
    ],
    "sql": [
        {
            "type": "coding",
            "question": "Write or outline an SQL query using Window Functions (e.g., DENSE_RANK() or ROW_NUMBER() OVER PARTITION BY) to retrieve the top 3 highest-earning candidates per department, handling ties appropriately.",
            "hint": "Demonstrate understanding of PARTITION BY, ORDER BY, window ranking functions, and CTEs (WITH clause).",
            "keywords": ["dense_rank", "row_number", "partition by", "order by", "window function", "cte", "with", "rank"]
        },
        {
            "type": "problem-solving",
            "question": "When an SQL query with multiple JOINs suffers from slow response times on large tables, what indexing strategies, EXPLAIN plan metrics, and partitioning techniques would you employ to optimize it?",
            "hint": "Discuss B-Tree vs Hash indexes, composite indexes, sequential scans vs index scans, and database query planners.",
            "keywords": ["index", "explain", "composite index", "scan", "execution plan", "foreign key", "cardinality", "partition"]
        },
        {
            "type": "conceptual",
            "question": "Explain the ACID properties of relational databases and how different transaction isolation levels (Read Committed vs Repeatable Read vs Serializable) prevent dirty reads and phantom reads.",
            "hint": "Detail atomicity, consistency, isolation, durability, MVCC, and concurrency anomalies.",
            "keywords": ["acid", "atomicity", "consistency", "isolation", "durability", "dirty read", "phantom read", "transaction"]
        }
    ],
    "machine learning": [
        {
            "type": "conceptual",
            "question": "Explain the bias-variance tradeoff in Machine Learning. What specific regularization techniques (L1 Lasso, L2 Ridge, Dropout) and validation strategies do you use to detect and prevent overfitting?",
            "hint": "Discuss underfitting vs overfitting, validation curves, cross-validation, and penalty terms.",
            "keywords": ["bias", "variance", "overfitting", "underfitting", "regularization", "l1", "l2", "lasso", "ridge", "cross-validation"]
        },
        {
            "type": "scenario",
            "question": "You are deploying a predictive machine learning model to production. How do you monitor for data drift and concept drift post-deployment, and what is your retraining and rollback pipeline strategy?",
            "hint": "Discuss statistical distribution shifts, Kolmogorov-Smirnov test, feature drift, shadow deployment, and automated retraining triggers.",
            "keywords": ["drift", "data drift", "concept drift", "monitoring", "distribution", "retraining", "pipeline", "ground truth", "production"]
        },
        {
            "type": "application",
            "question": "Compare evaluation metrics for an imbalanced classification problem (e.g. Precision, Recall, F1-Score, PR-AUC vs ROC-AUC). Why is standard accuracy misleading in this scenario?",
            "hint": "Explain false positives, false negatives, confusion matrix, precision-recall curve, and minority class impact.",
            "keywords": ["precision", "recall", "f1", "roc-auc", "imbalanced", "confusion matrix", "accuracy", "minority class"]
        }
    ],
    "deep learning": [
        {
            "type": "conceptual",
            "question": "How does the Self-Attention mechanism in Transformer architectures differ from recurrent neural networks (RNNs/LSTMs) when processing sequential dependencies?",
            "hint": "Discuss parallelization, query-key-value vectors, vanishing gradients, and quadratic attention complexity.",
            "keywords": ["attention", "transformer", "query", "key", "value", "rnn", "lstm", "parallel", "gradient"]
        }
    ],
    "react": [
        {
            "type": "application",
            "question": "How does React's Reconciliation engine and Virtual DOM diffing algorithm function? When should you use useMemo, useCallback, and React.memo to optimize re-renders in a heavy dashboard?",
            "hint": "Discuss fiber architecture, shallow comparisons, memoization, and referential equality of props and callbacks.",
            "keywords": ["virtual dom", "reconciliation", "re-render", "usememo", "usecallback", "react.memo", "props", "state", "hooks"]
        },
        {
            "type": "scenario",
            "question": "Compare custom hooks versus global state management (e.g., Redux Toolkit, Zustand, Context API) for a large-scale enterprise application with frequent asynchronous server data synchronization.",
            "hint": "Mention boilerplate, selector subscriptions, state colocation, server-state caching (e.g. React Query), and scalability.",
            "keywords": ["state", "redux", "zustand", "context", "custom hook", "react query", "async", "cache", "store"]
        }
    ],
    "javascript": [
        {
            "type": "conceptual",
            "question": "Explain the JavaScript Event Loop, Call Stack, Microtask Queue (Promises), and Macrotask Queue (setTimeout). In what order will asynchronous callbacks resolve?",
            "hint": "Detail single-threaded non-blocking I/O, promise resolution microtasks, and task queue ordering.",
            "keywords": ["event loop", "call stack", "microtask", "macrotask", "promise", "settimeout", "async", "non-blocking"]
        }
    ],
    "typescript": [
        {
            "type": "application",
            "question": "Explain how TypeScript Generics, Utility Types (e.g. Partial, Pick, Record), and Discriminated Unions enhance type-safety and eliminate runtime bugs in complex APIs.",
            "hint": "Discuss generic constraints, pattern matching on discriminant tags, and compile-time type safety.",
            "keywords": ["generics", "types", "discriminated union", "type-safety", "partial", "pick", "interfaces", "compile"]
        }
    ],
    "docker": [
        {
            "type": "scenario",
            "question": "What best practices do you follow to create secure, minimal multi-stage Docker builds for microservices? How do you manage secrets and minimize image layers and attack surface?",
            "hint": "Discuss distroless/alpine base images, layer caching, non-root users, .dockerignore, and Docker secrets.",
            "keywords": ["docker", "multi-stage", "layers", "image", "alpine", "secrets", "caching", "container", "security"]
        }
    ],
    "kubernetes": [
        {
            "type": "application",
            "question": "Explain the interaction between Deployments, ReplicaSets, Services (ClusterIP vs Ingress), and Pods in Kubernetes. How do Readiness and Liveness Probes prevent service downtime during rolling updates?",
            "hint": "Describe rolling update zero downtime strategy, kube-proxy, readiness endpoints, and pod lifecycle.",
            "keywords": ["kubernetes", "pod", "deployment", "service", "ingress", "probes", "readiness", "liveness", "rolling update"]
        }
    ],
    "aws": [
        {
            "type": "scenario",
            "question": "Design a highly available and scalable cloud architecture on AWS for a high-traffic web application. Detail your use of VPC, ALB, Auto Scaling, ECS/EKS or Lambda, and RDS Multi-AZ.",
            "hint": "Address fault tolerance, public vs private subnets, NAT gateways, multi-AZ failover, and CloudWatch metrics.",
            "keywords": ["aws", "vpc", "alb", "auto scaling", "rds", "multi-az", "s3", "cloudwatch", "availability", "subnets"]
        }
    ],
    "fastapi": [
        {
            "type": "application",
            "question": "How does FastAPI utilize Python type hints, Pydantic, and Starlette to deliver asynchronous request handling, automated schema validation, and OpenAPI documentation?",
            "hint": "Discuss async def / await, dependency injection system (Depends), request body serialization, and data validation.",
            "keywords": ["fastapi", "pydantic", "async", "await", "dependency injection", "depends", "validation", "openapi"]
        }
    ],
    "data engineering": [
        {
            "type": "problem-solving",
            "question": "In building a batch and streaming ETL pipeline, how do you handle schema evolution, idempotent data ingestion, and late-arriving records in a distributed data lake?",
            "hint": "Discuss watermarking, windowing, deduplication keys, Delta Lake/Iceberg ACID tables, and checkpointing.",
            "keywords": ["etl", "pipeline", "streaming", "schema", "idempotent", "batch", "data lake", "deduplication"]
        }
    ],
    "communication": [
        {
            "type": "scenario",
            "question": "Describe a scenario where you had to explain a complex technical architecture or trade-off to non-technical business stakeholders. How did you adapt your communication to build consensus?",
            "hint": "Focus on business value, analogies, risk mitigation, active listening, and stakeholder alignment.",
            "keywords": ["stakeholder", "business", "analogy", "consensus", "communication", "trade-off", "clarity", "collaboration"]
        }
    ],
    "leadership": [
        {
            "type": "scenario",
            "question": "How do you approach mentoring junior software engineers while maintaining sprint velocity and technical excellence in code reviews?",
            "hint": "Discuss constructive feedback, pair programming, documentation, knowledge sharing, and fostering autonomy.",
            "keywords": ["mentoring", "code review", "feedback", "growth", "engineering culture", "best practices", "leadership"]
        }
    ]
}

def generate_mock_questions_for_candidate(
    extracted_skills: List[str],
    candidate_id: int,
    matching_id: int = None,
    desired_count: int = 5
) -> List[Dict[str, Any]]:
    """
    CRITICAL REQUIREMENT:
    Generate 4 to 6 mock assessment questions BASED ON THE CANDIDATE'S OWN EXTRACTED SKILLS.
    """
    questions: List[Dict[str, Any]] = []
    used_questions = set()
    used_skills = set()

    # Normalize candidate skills
    candidate_skills_clean = [s.strip() for s in extracted_skills if s and s.strip()]

    # If candidate skills are empty or very few, ensure at least common skills extracted
    if not candidate_skills_clean:
        candidate_skills_clean = ["Python", "SQL", "Problem Solving", "Communication", "Data Analysis"]

    # Match candidate skills against our question templates
    matching_skill_keys = []
    for cand_skill in candidate_skills_clean:
        cand_lower = cand_skill.lower()
        for key in SKILL_QUESTION_TEMPLATES.keys():
            if key == cand_lower or key in cand_lower or cand_lower in key:
                if key not in matching_skill_keys:
                    matching_skill_keys.append((key, cand_skill))

    # Pick 4-6 questions from candidate's extracted skills
    target_count = max(4, min(6, desired_count))

    # Priority 1: Pick one question from each matched skill
    for key, display_name in matching_skill_keys:
        if len(questions) >= target_count:
            break
        available = [q for q in SKILL_QUESTION_TEMPLATES[key] if q["question"] not in used_questions]
        if available:
            selected = random.choice(available)
            used_questions.add(selected["question"])
            used_skills.add(key)
            questions.append({
                "candidate_id": candidate_id,
                "matching_id": matching_id,
                "skill_name": display_name,
                "question": selected["question"],
                "question_type": selected["type"],
                "difficulty": "Intermediate",
                "sample_answer_hint": selected["hint"],
                "keywords": selected.get("keywords", [])
            })

    # Priority 2: If we still have fewer than target_count, pick alternate questions from candidate's skills
    for key, display_name in matching_skill_keys:
        if len(questions) >= target_count:
            break
        available = [q for q in SKILL_QUESTION_TEMPLATES[key] if q["question"] not in used_questions]
        for item in available:
            if len(questions) >= target_count:
                break
            used_questions.add(item["question"])
            questions.append({
                "candidate_id": candidate_id,
                "matching_id": matching_id,
                "skill_name": display_name,
                "question": item["question"],
                "question_type": item["type"],
                "difficulty": "Advanced",
                "sample_answer_hint": item["hint"],
                "keywords": item.get("keywords", [])
            })

    # Priority 3: Fallback dynamically synthesized questions tailored directly to remaining candidate skills
    for cand_skill in candidate_skills_clean:
        if len(questions) >= target_count:
            break
        cand_clean = cand_skill.strip()
        q_text = (
            f"Based on your demonstrated experience in {cand_clean}, describe a complex challenge or architectural constraint "
            f"you encountered when implementing {cand_clean} in production. What alternative approaches did you consider and how did you measure success?"
        )
        if q_text not in used_questions:
            used_questions.add(q_text)
            questions.append({
                "candidate_id": candidate_id,
                "matching_id": matching_id,
                "skill_name": cand_clean,
                "question": q_text,
                "question_type": "scenario",
                "difficulty": "Intermediate",
                "sample_answer_hint": f"Discuss specific real-world usage of {cand_clean}, technical trade-offs, and outcomes.",
                "keywords": [cand_clean.lower(), "architecture", "production", "trade-off", "performance"]
            })

    # Ensure strictly 4 to 6 questions
    return questions[:target_count]

def evaluate_single_answer(
    question_text: str,
    skill_name: str,
    answer_text: str,
    hint: str = "",
    expected_keywords: List[str] = None
) -> Dict[str, Any]:
    """
    Intelligent AI + Rule-based Answer Evaluation.
    Evaluates:
    - Score out of 10
    - Short feedback
    - Correctness / relevance
    - Areas for improvement
    """
    answer_clean = answer_text.strip()
    words = answer_clean.split()
    word_count = len(words)

    if word_count < 5:
        return {
            "score": 2.0,
            "feedback": "Answer is overly brief and lacks technical depth.",
            "correctness_relevance": "Minimal technical context provided.",
            "improvement_suggestions": f"Elaborate with concrete explanations, code samples, or architecture patterns relevant to {skill_name}."
        }

    # Keyword matching
    if not expected_keywords:
        expected_keywords = [skill_name.lower(), "system", "performance", "process", "implementation", "design"]

    matched_keywords = []
    answer_lower = answer_clean.lower()
    for kw in expected_keywords:
        if kw.lower() in answer_lower:
            matched_keywords.append(kw)

    keyword_ratio = len(matched_keywords) / max(1, len(expected_keywords))

    # Scoring Rubric:
    # 1. Content Length & Completeness: up to 3 points
    # 2. Keyword & Concept Relevance: up to 4 points
    # 3. Structural Clarity & Explanation: up to 3 points
    length_score = min(3.0, (word_count / 40.0) * 3.0)
    keyword_score = min(4.0, (keyword_ratio * 4.0) + (1.0 if skill_name.lower() in answer_lower else 0.0))

    # Technical markers
    tech_markers = ["because", "for example", "trade-off", "optimize", "architecture", "algorithm", "scale", "performance", "def ", "select ", "return", "class "]
    tech_count = sum(1 for tm in tech_markers if tm in answer_lower)
    structure_score = min(3.0, 1.0 + (tech_count * 0.5))

    total_score = round(min(10.0, max(3.0, length_score + keyword_score + structure_score)), 1)

    # Formulate feedback
    if total_score >= 8.5:
        feedback = f"Outstanding technical clarity and thorough grasp of {skill_name} principles."
        correctness = "Highly accurate and directly addresses the core question."
        improvement = "Maintain this level of rigor; could optionally mention niche edge-case failure modes."
    elif total_score >= 7.0:
        feedback = f"Solid answer demonstrating good practical familiarity with {skill_name}."
        correctness = "Accurate and well-structured with clear conceptual backing."
        improvement = f"Add more quantitative metrics or real-world benchmarking examples in {skill_name}."
    elif total_score >= 5.0:
        feedback = f"Satisfactory response covering standard basics of {skill_name}."
        correctness = "Partially accurate; touches on key ideas but lacks detailed operational depth."
        improvement = f"Deepen explanation of underlying mechanics, trade-offs, and failure recovery in {skill_name}."
    else:
        feedback = f"Basic overview provided with limited technical depth for {skill_name}."
        correctness = "Low to moderate relevance; misses crucial technical keywords."
        improvement = f"Review standard design patterns and best practices for {skill_name} in enterprise applications."

    return {
        "score": total_score,
        "feedback": feedback,
        "correctness_relevance": correctness,
        "improvement_suggestions": improvement
    }

def compile_overall_performance(
    question_evaluations: List[Dict[str, Any]],
    candidate_id: int,
    matching_id: int = None
) -> Dict[str, Any]:
    """
    Calculate performance scorecard:
    - Q1 to Q6 scores
    - Total Score
    - Maximum Score
    - Overall Performance Tier
    - Strong Areas & Improvement Areas
    """
    scores = [q.get("score", 0.0) for q in question_evaluations]
    total_score = round(sum(scores), 1)
    max_score = float(len(question_evaluations) * 10)
    percentage = round((total_score / max(1.0, max_score)) * 100.0, 1)

    if percentage >= 85:
        tier = "Exceptional"
    elif percentage >= 70:
        tier = "Strong Hire"
    elif percentage >= 50:
        tier = "Qualified"
    else:
        tier = "Needs Improvement"

    strong_areas = []
    improvement_areas = []

    for q in question_evaluations:
        skill = q.get("skill_name", "Technical Skill")
        score = q.get("score", 0.0)
        if score >= 7.5:
            strong_areas.append(f"{skill} (Score: {score}/10) - demonstrated solid technical mastery")
        else:
            improvement_areas.append(f"{skill} (Score: {score}/10) - needs deeper conceptual or practical practice")

    if not strong_areas:
        strong_areas.append("Demonstrated willingness to tackle diverse scenario questions.")
    if not improvement_areas:
        improvement_areas.append("Continue tracking emerging architectural advancements.")

    analysis = (
        f"Candidate achieved a total assessment score of {total_score}/{max_score} ({percentage}%), "
        f"categorized as '{tier}'. Successfully answered {len(question_evaluations)} skill-tailored questions "
        f"with highest strengths in {', '.join([q['skill_name'] for q in question_evaluations if q.get('score', 0) >= 7.5][:3]) or 'foundational knowledge'}."
    )

    return {
        "candidate_id": candidate_id,
        "matching_id": matching_id,
        "total_score": total_score,
        "maximum_score": max_score,
        "percentage_score": percentage,
        "overall_performance": tier,
        "strong_areas": strong_areas,
        "improvement_areas": improvement_areas,
        "performance_analysis": analysis,
        "scores_breakdown": [
            {"question_index": i + 1, "skill": q.get("skill_name"), "score": q.get("score", 0.0)}
            for i, q in enumerate(question_evaluations)
        ]
    }
