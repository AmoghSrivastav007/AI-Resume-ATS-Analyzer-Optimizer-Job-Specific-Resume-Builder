from pydantic import BaseModel, Field


class ContactInfo(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None
    website: str | None = None


class SkillItem(BaseModel):
    name: str
    category: str | None = None
    proficiency: str | None = None


class WorkExperienceItem(BaseModel):
    company: str
    title: str
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool = False
    description: str | None = None
    bullets: list[str] = Field(default_factory=list)


class EducationItem(BaseModel):
    institution: str
    degree: str | None = None
    field_of_study: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    gpa: str | None = None
    description: str | None = None


class CertificationItem(BaseModel):
    name: str
    issuer: str | None = None
    issue_date: str | None = None
    expiry_date: str | None = None
    credential_id: str | None = None


class ProjectItem(BaseModel):
    name: str
    description: str | None = None
    url: str | None = None
    technologies: list[str] = Field(default_factory=list)
    start_date: str | None = None
    end_date: str | None = None


class LanguageItem(BaseModel):
    name: str
    proficiency: str | None = None


class ResumeExtraction(BaseModel):
    contact: ContactInfo = Field(default_factory=ContactInfo)
    summary: str | None = None
    skills: list[SkillItem] = Field(default_factory=list)
    work_experience: list[WorkExperienceItem] = Field(default_factory=list)
    education: list[EducationItem] = Field(default_factory=list)
    certifications: list[CertificationItem] = Field(default_factory=list)
    projects: list[ProjectItem] = Field(default_factory=list)
    languages: list[LanguageItem] = Field(default_factory=list)


LlmResumeExtraction = ResumeExtraction
