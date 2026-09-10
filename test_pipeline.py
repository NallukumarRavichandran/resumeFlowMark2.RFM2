import os
import sys
from swooped_engine import SwoopedEngine

sample_resume = b"""Nallukumar Ravichandran
Software Engineer & Full Stack Developer
Email: nallukumar@example.com | Phone: +1-555-0199 | Location: San Francisco, CA

PROFESSIONAL SUMMARY
Experienced Software Engineer with 4+ years of expertise in Full Stack Development, Cloud Architecture, REST APIs, Python, React, and automated testing. Track record of optimizing systems and delivering high-performance features.

WORK EXPERIENCE
Senior Full Stack Engineer - TechCorp Solutions (2022 - Present)
- Designed and built scalable web microservices serving 500k+ daily active users.
- Reduced API response times by 35% through query optimization and caching strategies.
- Spearheaded CI/CD automation pipelines, reducing release deployment cycle by 50%.

Software Engineer - Innovatech Labs (2020 - 2022)
- Built interactive customer dashboards using React, TypeScript, and TailwindCSS.
- Integrated third-party authentication and payment gateways securely.
- Collaborated with product managers and designers to deliver customer-centric workflows.

SKILLS
Python, JavaScript, TypeScript, React, Node.js, FastAPI, PostgreSQL, Docker, AWS, Git, CI/CD

EDUCATION
B.S. in Computer Science - State University (2016 - 2020)
"""

print("[*] Starting end-to-end Swooped.co verification...")

def progress_cb(step, total, msg, data=None):
    print(f"Step {step}/{total}: {msg}")
    if data:
        print("Data:", data)

engine = SwoopedEngine(progress_callback=progress_cb)

result = engine.execute_pipeline(
    resume_bytes=sample_resume,
    filename="Nallukumar_Ravichandran_cv.txt",
    company_name="Facebook",
    job_title="Product Manager",
    job_description="Seeking an experienced Product Manager / Technical Leader skilled in agile execution, cross-functional leadership, software engineering systems, and driving high-impact product roadmaps."
)

print("\n[+] Verification Result:", result)

folder = result["folder_path"]
print(f"\n[*] Checking files in: {folder}")
files = os.listdir(folder)
print("Files created:", files)

# Assertions
assert any(f.endswith("_Tailored_Resume.pdf") for f in files), "Missing Resume PDF"
assert any(f.endswith("_Cover_Letter.pdf") for f in files), "Missing Cover Letter PDF"
assert any(f.endswith("_Tailored_Resume.docx") for f in files), "Missing Resume DOCX"
assert any(f.endswith("_Cover_Letter.docx") for f in files), "Missing Cover Letter DOCX"

print("\n[SUCCESS] REAL SWOOPED PDFS AND DOCX EXPORTS VERIFIED ON DISK!")
