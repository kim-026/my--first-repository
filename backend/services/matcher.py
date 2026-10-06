import json
import re
from typing import Dict, List, Any

# Synonyms and aliases mapping
SKILL_ALIASES = {
    "react": ["react", "react.js", "reactjs"],
    "node": ["node", "node.js", "nodejs"],
    "vue": ["vue", "vue.js", "vuejs"],
    "next": ["next", "next.js", "nextjs"],
    "postgres": ["postgres", "postgresql"],
    "mongo": ["mongo", "mongodb"],
    "k8s": ["k8s", "kubernetes"],
    "docker": ["docker", "containerization"],
    "aws": ["aws", "amazon web services"],
    "gcp": ["gcp", "google cloud", "google cloud platform"],
    "azure": ["azure", "microsoft azure"],
    "python": ["python", "python3"],
    "golang": ["golang", "go"],
    "ml": ["ml", "machine learning"],
    "dl": ["dl", "deep learning"],
    "nlp": ["nlp", "natural language processing"],
    "ai": ["ai", "artificial intelligence", "generative ai", "genai"],
    "rest": ["rest", "rest api", "restful", "restful api"],
    "ci/cd": ["ci/cd", "continuous integration", "github actions", "jenkins"]
}

def normalize_skill(skill: str) -> str:
    s = skill.lower().strip()
    s = re.sub(r'[\.\-\_\s]+', ' ', s)
    for canonical, aliases in SKILL_ALIASES.items():
        for alias in aliases:
            alias_norm = re.sub(r'[\.\-\_\s]+', ' ', alias)
            if s == alias_norm or s == alias:
                return canonical
    return s

def skill_matches(candidate_skill: str, job_skill: str) -> bool:
    norm_c = normalize_skill(candidate_skill)
    norm_j = normalize_skill(job_skill)
    if norm_c == norm_j:
        return True
    if norm_c in norm_j or norm_j in norm_c:
        return True
    return False

def parse_skills_list(skills_input: Any) -> List[str]:
    """Parse JSON string, comma-separated string, or list into cleaned string list."""
    if not skills_input:
        return []
    if isinstance(skills_input, list):
        return [str(s).strip() for s in skills_input if str(s).strip()]
    if isinstance(skills_input, str):
        try:
            parsed = json.loads(skills_input)
            if isinstance(parsed, list):
                return [str(s).strip() for s in parsed if str(s).strip()]
        except Exception:
            pass
        return [s.strip() for s in re.split(r'[,;\n]+', skills_input) if s.strip()]
    return []

def calculate_match_analysis(candidate_data: Dict[str, Any], job_req: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare candidate's extracted skills, experience, and education with job requirements.
    Generates:
    - Matching skills
    - Missing skills
    - Optional matched skills
    - Match percentage
    - Skill gap breakdown & improvement roadmap
    - Explanation text & strengths
    """
    candidate_skills = candidate_data.get("all_skills", [])
    if not candidate_skills:
        # Fallback to technical + soft skills
        candidate_skills = [
            s.get("skill_name") for s in candidate_data.get("technical_skills", []) + candidate_data.get("soft_skills", [])
        ]

    required_skills = parse_skills_list(job_req.get("required_skills", ""))
    optional_skills = parse_skills_list(job_req.get("optional_skills", ""))

    matching_skills = []
    missing_skills = []
    skill_results = []

    # Check Required Skills
    for req in required_skills:
        found = False
        matched_candidate_skill = ""
        for cand in candidate_skills:
            if skill_matches(cand, req):
                found = True
                matched_candidate_skill = cand
                break

        if found:
            matching_skills.append({
                "skill": req,
                "matched_as": matched_candidate_skill,
                "status": "matched",
                "score": 1.0
            })
            skill_results.append({
                "skill_name": req,
                "status": "matched",
                "score": 1.0
            })
        else:
            missing_skills.append({
                "skill": req,
                "status": "missing",
                "score": 0.0
            })
            skill_results.append({
                "skill_name": req,
                "status": "missing",
                "score": 0.0
            })

    # Check Optional Skills
    optional_matched = []
    for opt in optional_skills:
        for cand in candidate_skills:
            if skill_matches(cand, opt):
                optional_matched.append(opt)
                skill_results.append({
                    "skill_name": opt,
                    "status": "optional_matched",
                    "score": 0.8
                })
                break

    # Calculate Match Percentage
    # Formula:
    # Required skills score: (matched_req / total_req) * 70 points
    # Experience match: up to 15 points
    # Optional skills bonus: up to 15 points
    total_req = len(required_skills) if required_skills else 1
    req_match_ratio = len(matching_skills) / total_req
    req_points = req_match_ratio * 70.0

    # Experience points
    cand_exp = candidate_data.get("total_experience_years", 2.0)
    job_exp_str = str(job_req.get("experience", "2+ years"))
    req_exp_years = 2.0
    exp_num_match = re.search(r'(\d+)', job_exp_str)
    if exp_num_match:
        req_exp_years = float(exp_num_match.group(1))

    if cand_exp >= req_exp_years:
        exp_points = 15.0
    else:
        exp_points = max(5.0, (cand_exp / max(1.0, req_exp_years)) * 15.0)

    # Optional skills bonus
    opt_points = 0.0
    if optional_skills:
        opt_points = min(15.0, (len(optional_matched) / len(optional_skills)) * 15.0)
    else:
        opt_points = 10.0  # default credit if no optional skills required

    overall_percentage = min(100.0, round(req_points + exp_points + opt_points, 1))

    # Strengths identification
    strengths = []
    matched_names = [m["skill"] for m in matching_skills]
    if matched_names:
        strengths.append(f"Demonstrates strong verified proficiency in key required skills: {', '.join(matched_names[:4])}.")
    if cand_exp >= req_exp_years:
        strengths.append(f"Meets or exceeds required experience criteria ({cand_exp} years vs {req_exp_years} years required).")
    if optional_matched:
        strengths.append(f"Brings valuable bonus domain capabilities: {', '.join(optional_matched)}.")
    if candidate_data.get("certifications"):
        cert_names = [c["cert_name"] for c in candidate_data.get("certifications", [])]
        strengths.append(f"Holds recognized professional certifications: {', '.join(cert_names)}.")

    # Explanation
    job_title = job_req.get("job_title", "Target Role")
    explanation = (
        f"Candidate scored an overall match of {overall_percentage}% for the {job_title} position. "
        f"Out of {len(required_skills)} mandatory requirements, the candidate directly demonstrates {len(matching_skills)} skills "
        f"({', '.join(matched_names) if matched_names else 'None'}). "
    )
    if missing_skills:
        missing_names = [m["skill"] for m in missing_skills]
        explanation += f"Core skill gaps identified: {', '.join(missing_names)}. Targeted upskilling is recommended."
    else:
        explanation += "Outstanding match with zero missing mandatory requirements."

    # Skill Gap Summary Details
    skill_gap_details = {
        "candidate_skills_count": len(candidate_skills),
        "required_skills_count": len(required_skills),
        "matched_skills_count": len(matching_skills),
        "missing_skills_count": len(missing_skills),
        "matching_skills": matching_skills,
        "missing_skills": missing_skills,
        "optional_matched": optional_matched,
        "already_possessed": candidate_skills,
        "needed_improvements": [
            {
                "skill": m["skill"],
                "urgency": "High" if m["skill"] in required_skills[:3] else "Medium",
                "recommended_action": f"Take intensive hands-on project or certification module covering {m['skill']} best practices and real-world architectures."
            }
            for m in missing_skills
        ],
        "learning_roadmap": [
            f"Phase 1: Deep dive into {missing_skills[0]['skill']} architecture and production fundamentals." if missing_skills else "Phase 1: System architecture hardening.",
            f"Phase 2: Build a production-grade project integrating {missing_skills[1]['skill']}." if len(missing_skills) > 1 else "Phase 2: Scalability and performance tuning.",
            "Phase 3: Integration testing, CI/CD pipeline automation, and cloud deployment."
        ]
    }

    improvement_areas = [
        f"Bridge knowledge gap in {m['skill']} through focused architectural exercises."
        for m in missing_skills
    ]
    if not improvement_areas:
        improvement_areas.append("Deepen advanced systems design and large-scale performance benchmarking.")

    return {
        "match_percentage": overall_percentage,
        "matching_skills": matching_skills,
        "missing_skills": missing_skills,
        "optional_matched": optional_matched,
        "strengths": strengths,
        "explanation": explanation,
        "improvement_areas": improvement_areas,
        "skill_gap_details": skill_gap_details,
        "skill_results": skill_results
    }
