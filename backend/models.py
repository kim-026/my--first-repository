import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

# 1. Candidates
class Candidate(Base):
    __tablename__ = "candidates"

    CandidateID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    Name = Column(String(200), nullable=False)
    Email = Column(String(200), nullable=False, index=True)
    Phone = Column(String(50), nullable=True)
    CreatedAt = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    uploads = relationship("ResumeUpload", back_populates="candidate", cascade="all, delete-orphan")
    personal_details = relationship("PersonalDetail", back_populates="candidate", cascade="all, delete-orphan")
    educations = relationship("Education", back_populates="candidate", cascade="all, delete-orphan")
    experiences = relationship("Experience", back_populates="candidate", cascade="all, delete-orphan")
    certifications = relationship("Certification", back_populates="candidate", cascade="all, delete-orphan")
    mock_questions = relationship("MockQuestion", back_populates="candidate", cascade="all, delete-orphan")
    candidate_answers = relationship("CandidateAnswer", back_populates="candidate", cascade="all, delete-orphan")
    performances = relationship("Performance", back_populates="candidate", cascade="all, delete-orphan")


# 2. ResumeUpload
class ResumeUpload(Base):
    __tablename__ = "resume_uploads"

    UploadID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    CandidateID = Column(Integer, ForeignKey("candidates.CandidateID"), nullable=False)
    Date = Column(DateTime, default=datetime.datetime.utcnow)
    FileType = Column(String(50), nullable=False)
    FilePath = Column(String(500), nullable=True)
    OriginalFilename = Column(String(255), nullable=False)
    FileSize = Column(Integer, default=0)

    # Relationships
    candidate = relationship("Candidate", back_populates="uploads")
    extracted_data = relationship("ExtractedResumeData", back_populates="upload", uselist=False, cascade="all, delete-orphan")
    resume_skills = relationship("ResumeSkill", back_populates="upload", cascade="all, delete-orphan")
    matching_sessions = relationship("ResumeMatchingSession", back_populates="upload", cascade="all, delete-orphan")


# 3. PersonalDetail
class PersonalDetail(Base):
    __tablename__ = "personal_details"

    DetailID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    CandidateID = Column(Integer, ForeignKey("candidates.CandidateID"), nullable=True)
    UploadID = Column(Integer, ForeignKey("resume_uploads.UploadID"), nullable=True)
    Name = Column(String(200), nullable=True)
    Phone = Column(String(50), nullable=True)
    Email = Column(String(200), nullable=True)
    Degree = Column(String(200), nullable=True)
    Location = Column(String(200), nullable=True)
    LinkedIn = Column(String(255), nullable=True)
    GitHub = Column(String(255), nullable=True)

    candidate = relationship("Candidate", back_populates="personal_details")


# 4. Education
class Education(Base):
    __tablename__ = "educations"

    EducationID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    CandidateID = Column(Integer, ForeignKey("candidates.CandidateID"), nullable=True)
    UploadID = Column(Integer, ForeignKey("resume_uploads.UploadID"), nullable=True)
    Degree = Column(String(200), nullable=True)
    School = Column(String(255), nullable=True)  # School/University
    GraduationYear = Column(String(50), nullable=True)
    FieldOfStudy = Column(String(200), nullable=True)
    Grade = Column(String(50), nullable=True)

    candidate = relationship("Candidate", back_populates="educations")


# 5. Experience
class Experience(Base):
    __tablename__ = "experiences"

    ExperienceID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    CandidateID = Column(Integer, ForeignKey("candidates.CandidateID"), nullable=True)
    UploadID = Column(Integer, ForeignKey("resume_uploads.UploadID"), nullable=True)
    Degree = Column(String(200), nullable=True)
    JobTitle = Column(String(200), nullable=True)
    Company = Column(String(200), nullable=True)
    Duration = Column(String(100), nullable=True)
    ExperienceYears = Column(Float, default=0.0)
    WorkExperience = Column(Text, nullable=True)  # Detailed work experience notes/bullets

    candidate = relationship("Candidate", back_populates="experiences")


# 6. ExtractedResumeData
class ExtractedResumeData(Base):
    __tablename__ = "extracted_resume_data"

    ExtractionID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    UploadID = Column(Integer, ForeignKey("resume_uploads.UploadID"), nullable=False, unique=True)
    RawText = Column(Text, nullable=True)
    ParsedJSON = Column(Text, nullable=True)  # Complete parsed structured payload in JSON
    ExtractedAt = Column(DateTime, default=datetime.datetime.utcnow)

    upload = relationship("ResumeUpload", back_populates="extracted_data")


# 7. Certification
class Certification(Base):
    __tablename__ = "certifications"

    CertificationID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    CandidateID = Column(Integer, ForeignKey("candidates.CandidateID"), nullable=True)
    UploadID = Column(Integer, ForeignKey("resume_uploads.UploadID"), nullable=True)
    Skill = Column(String(150), nullable=True)
    CertName = Column(String(255), nullable=False)
    Issuer = Column(String(200), nullable=True)
    Year = Column(String(50), nullable=True)

    candidate = relationship("Candidate", back_populates="certifications")


# 8. Company
class Company(Base):
    __tablename__ = "companies"

    CompanyID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    CompanyName = Column(String(200), nullable=False, unique=True)
    Industry = Column(String(150), nullable=True)
    Website = Column(String(255), nullable=True)
    Description = Column(Text, nullable=True)

    job_requirements = relationship("JobRequirement", back_populates="company", cascade="all, delete-orphan")


# 9. JobRequirement
class JobRequirement(Base):
    __tablename__ = "job_requirements"

    RequirementID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    CompanyID = Column(Integer, ForeignKey("companies.CompanyID"), nullable=False)
    JobTitle = Column(String(200), nullable=False)
    RequiredSkills = Column(Text, nullable=False)  # JSON or comma-separated list of required skills
    Education = Column(String(200), nullable=True)
    Experience = Column(String(100), nullable=True)  # e.g., "3+ years", "5-7 years"
    OptionalSkills = Column(Text, nullable=True)  # JSON or comma-separated optional skills
    JobDescription = Column(Text, nullable=True)
    CreatedAt = Column(DateTime, default=datetime.datetime.utcnow)

    company = relationship("Company", back_populates="job_requirements")
    matching_sessions = relationship("ResumeMatchingSession", back_populates="job_requirement", cascade="all, delete-orphan")


# 10. ResumeSkill
class ResumeSkill(Base):
    __tablename__ = "resume_skills"

    ResumeSkillID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ExtractionID = Column(Integer, ForeignKey("extracted_resume_data.ExtractionID"), nullable=True)
    UploadID = Column(Integer, ForeignKey("resume_uploads.UploadID"), nullable=False)
    SkillID = Column(Integer, ForeignKey("skills.SkillID"), nullable=True)
    SkillName = Column(String(100), nullable=False)
    ParsedJSON = Column(Text, nullable=True)
    Proficiency = Column(String(50), default="Intermediate")
    YearsExperience = Column(Float, default=1.0)

    upload = relationship("ResumeUpload", back_populates="resume_skills")
    skill_ref = relationship("Skill")


# 11. Skill (Master skill taxonomy)
class Skill(Base):
    __tablename__ = "skills"

    SkillID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    SkillName = Column(String(100), nullable=False, unique=True, index=True)
    SkillType = Column(String(50), default="technical")  # technical, soft, tool, framework, domain


# 12. ResumeMatchingSession
class ResumeMatchingSession(Base):
    __tablename__ = "resume_matching_sessions"

    MatchingID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    UploadID = Column(Integer, ForeignKey("resume_uploads.UploadID"), nullable=False)
    RequirementID = Column(Integer, ForeignKey("job_requirements.RequirementID"), nullable=False)
    Timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    upload = relationship("ResumeUpload", back_populates="matching_sessions")
    job_requirement = relationship("JobRequirement", back_populates="matching_sessions")
    analysis = relationship("MatchingAnalysis", back_populates="session", uselist=False, cascade="all, delete-orphan")
    skill_match_results = relationship("SkillMatchResult", back_populates="session", cascade="all, delete-orphan")


# 13. MatchingAnalysis
class MatchingAnalysis(Base):
    __tablename__ = "matching_analyses"

    AnalysisID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    MatchingID = Column(Integer, ForeignKey("resume_matching_sessions.MatchingID"), nullable=False, unique=True)
    MatchPercentage = Column(Float, nullable=False, default=0.0)
    SkillGapDetails = Column(Text, nullable=True)  # JSON summary of missing, matched, improvements
    Explanation = Column(Text, nullable=True)
    Strengths = Column(Text, nullable=True)  # JSON array
    ImprovementAreas = Column(Text, nullable=True)  # JSON array

    session = relationship("ResumeMatchingSession", back_populates="analysis")


# 14. SkillMatchResult
class SkillMatchResult(Base):
    __tablename__ = "skill_match_results"

    SkillMatchResultID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    MatchingID = Column(Integer, ForeignKey("resume_matching_sessions.MatchingID"), nullable=False)
    SkillID = Column(Integer, ForeignKey("skills.SkillID"), nullable=True)
    SkillName = Column(String(100), nullable=False)
    MatchStatus = Column(String(50), nullable=False)  # 'matched', 'missing', 'optional_matched', 'partial'
    MatchScore = Column(Float, default=0.0)  # 0.0 to 1.0

    session = relationship("ResumeMatchingSession", back_populates="skill_match_results")
    skill_ref = relationship("Skill")


# 15. MockQuestions
class MockQuestion(Base):
    __tablename__ = "mock_questions"

    QuestionID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    CandidateID = Column(Integer, ForeignKey("candidates.CandidateID"), nullable=False)
    MatchingID = Column(Integer, ForeignKey("resume_matching_sessions.MatchingID"), nullable=True)
    SkillID = Column(Integer, ForeignKey("skills.SkillID"), nullable=True)
    SkillName = Column(String(100), nullable=False)
    Question = Column(Text, nullable=False)
    QuestionType = Column(String(50), default="conceptual")  # conceptual, coding, scenario, problem-solving, application
    Difficulty = Column(String(50), default="Intermediate")  # Easy, Intermediate, Advanced
    SampleAnswerHint = Column(Text, nullable=True)

    candidate = relationship("Candidate", back_populates="mock_questions")
    answers = relationship("CandidateAnswer", back_populates="mock_question", cascade="all, delete-orphan")


# 16. CandidateAnswers
class CandidateAnswer(Base):
    __tablename__ = "candidate_answers"

    AnswerID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    QuestionID = Column(Integer, ForeignKey("mock_questions.QuestionID"), nullable=False)
    CandidateID = Column(Integer, ForeignKey("candidates.CandidateID"), nullable=False)
    Answer = Column(Text, nullable=False)
    Score = Column(Float, default=0.0)  # Out of 10
    Feedback = Column(Text, nullable=True)
    CorrectnessRelevance = Column(Text, nullable=True)
    ImprovementSuggestions = Column(Text, nullable=True)

    mock_question = relationship("MockQuestion", back_populates="answers")
    candidate = relationship("Candidate", back_populates="candidate_answers")


# 17. Performance
class Performance(Base):
    __tablename__ = "performances"

    PerformanceID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    CandidateID = Column(Integer, ForeignKey("candidates.CandidateID"), nullable=False)
    MatchingID = Column(Integer, ForeignKey("resume_matching_sessions.MatchingID"), nullable=True)
    TotalScore = Column(Float, default=0.0)
    MaximumScore = Column(Float, default=50.0)
    PercentageScore = Column(Float, default=0.0)
    OverallPerformance = Column(String(50), default="Qualified")  # Exceptional, Strong Hire, Qualified, Needs Improvement
    StrongAreas = Column(Text, nullable=True)  # JSON array
    ImprovementAreas = Column(Text, nullable=True)  # JSON array
    PerformanceAnalysis = Column(Text, nullable=True)

    candidate = relationship("Candidate", back_populates="performances")
