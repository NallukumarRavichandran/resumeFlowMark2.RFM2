import os
import re
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib import colors

class DocumentConverter:
    """
    Generates professional, ATS-optimized Word (.docx) and PDF (.pdf) documents
    for tailored resumes and cover letters.
    """

    @staticmethod
    def clean_text(text):
        if not text:
            return ""
        # Remove HTML tags if present
        clean = re.sub(r'<[^>]+>', '', text)
        return clean.strip()

    @classmethod
    def save_resume_docx(cls, resume_dict, output_path):
        """Creates a modern ATS-friendly .docx resume"""
        doc = Document()
        
        # Set 0.75 inch margins
        for section in doc.sections:
            section.top_margin = Inches(0.6)
            section.bottom_margin = Inches(0.6)
            section.left_margin = Inches(0.7)
            section.right_margin = Inches(0.7)

        name = resume_dict.get("name") or "Professional Candidate"
        contact_parts = []
        if resume_dict.get("email"):
            contact_parts.append(resume_dict["email"])
        if resume_dict.get("phone"):
            contact_parts.append(resume_dict["phone"])
        if resume_dict.get("location"):
            contact_parts.append(resume_dict["location"])

        # Header Name
        title_p = doc.add_paragraph()
        title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title_p.add_run(name)
        title_run.font.name = "Calibri"
        title_run.font.size = Pt(20)
        title_run.font.bold = True
        title_run.font.color.rgb = RGBColor(30, 41, 59)
        title_p.paragraph_format.space_after = Pt(2)

        # Contact Info
        if contact_parts:
            contact_p = doc.add_paragraph()
            contact_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            c_run = contact_p.add_run(" | ".join(contact_parts))
            c_run.font.name = "Calibri"
            c_run.font.size = Pt(10)
            c_run.font.color.rgb = RGBColor(100, 116, 139)
            contact_p.paragraph_format.space_after = Pt(12)

        # Helper for Section Titles
        def add_section_header(title):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(4)
            run = p.add_run(title.upper())
            run.font.name = "Calibri"
            run.font.size = Pt(11.5)
            run.font.bold = True
            run.font.color.rgb = RGBColor(15, 23, 42)

        # Summary
        summary = resume_dict.get("summary")
        if summary:
            add_section_header("Professional Summary")
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(8)
            run = p.add_run(cls.clean_text(summary))
            run.font.name = "Calibri"
            run.font.size = Pt(10.5)

        # Experience
        experiences = resume_dict.get("experiences") or []
        if experiences:
            add_section_header("Experience")
            for exp in experiences:
                role_p = doc.add_paragraph()
                role_p.paragraph_format.space_before = Pt(4)
                role_p.paragraph_format.space_after = Pt(2)
                
                title_r = role_p.add_run(exp.get("title", "Position"))
                title_r.font.name = "Calibri"
                title_r.font.size = Pt(10.5)
                title_r.font.bold = True
                
                comp = exp.get("company", "")
                if comp:
                    c_r = role_p.add_run(f" — {comp}")
                    c_r.font.name = "Calibri"
                    c_r.font.size = Pt(10.5)
                    c_r.font.italic = True
                    
                dates = exp.get("dates", "")
                if dates:
                    d_r = role_p.add_run(f" ({dates})")
                    d_r.font.name = "Calibri"
                    d_r.font.size = Pt(9.5)
                    d_r.font.color.rgb = RGBColor(100, 116, 139)

                bullets = exp.get("bullets") or []
                if isinstance(bullets, str):
                    bullets = [b.strip("- ") for b in bullets.split("\n") if b.strip()]
                for b in bullets:
                    bp = doc.add_paragraph(style='List Bullet')
                    bp.paragraph_format.space_before = Pt(1)
                    bp.paragraph_format.space_after = Pt(2)
                    b_run = bp.add_run(cls.clean_text(b))
                    b_run.font.name = "Calibri"
                    b_run.font.size = Pt(10)

        # Skills
        skills = resume_dict.get("skills") or []
        if skills:
            add_section_header("Skills & Competencies")
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(8)
            if isinstance(skills, list):
                skills_str = ", ".join(skills)
            else:
                skills_str = str(skills)
            run = p.add_run(skills_str)
            run.font.name = "Calibri"
            run.font.size = Pt(10)

        # Education
        education = resume_dict.get("education") or []
        if education:
            add_section_header("Education")
            for edu in education:
                p = doc.add_paragraph()
                p.paragraph_format.space_before = Pt(3)
                p.paragraph_format.space_after = Pt(2)
                d_run = p.add_run(edu.get("degree", "Degree"))
                d_run.font.name = "Calibri"
                d_run.font.size = Pt(10)
                d_run.font.bold = True
                
                school = edu.get("school", "")
                if school:
                    s_run = p.add_run(f" | {school}")
                    s_run.font.name = "Calibri"
                    s_run.font.size = Pt(10)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        doc.save(output_path)
        return output_path

    @classmethod
    def save_resume_pdf(cls, resume_dict, output_path):
        """Creates a clean ATS-friendly PDF resume"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        pdf = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=45,
            leftMargin=45,
            topMargin=45,
            bottomMargin=45
        )
        
        styles = getSampleStyleSheet()
        normal = styles['Normal']
        
        name_style = ParagraphStyle(
            'ResumeName',
            parent=normal,
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            alignment=1, # Center
            textColor=colors.HexColor('#0f172a')
        )
        
        contact_style = ParagraphStyle(
            'ResumeContact',
            parent=normal,
            fontName='Helvetica',
            fontSize=9.5,
            leading=13,
            alignment=1, # Center
            textColor=colors.HexColor('#64748b')
        )
        
        section_style = ParagraphStyle(
            'ResumeSection',
            parent=normal,
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=15,
            textColor=colors.HexColor('#1e293b'),
            spaceBefore=8,
            spaceAfter=4
        )
        
        body_style = ParagraphStyle(
            'ResumeBody',
            parent=normal,
            fontName='Helvetica',
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor('#334155'),
            spaceAfter=4
        )
        
        bullet_style = ParagraphStyle(
            'ResumeBullet',
            parent=normal,
            fontName='Helvetica',
            fontSize=9.5,
            leading=13,
            leftIndent=15,
            firstLineIndent=-10,
            textColor=colors.HexColor('#334155'),
            spaceAfter=2
        )

        elements = []
        
        # Name & contact
        name = resume_dict.get("name") or "Professional Candidate"
        elements.append(Paragraph(name, name_style))
        elements.append(Spacer(1, 3))
        
        contact_parts = []
        if resume_dict.get("email"):
            contact_parts.append(resume_dict["email"])
        if resume_dict.get("phone"):
            contact_parts.append(resume_dict["phone"])
        if resume_dict.get("location"):
            contact_parts.append(resume_dict["location"])
            
        if contact_parts:
            elements.append(Paragraph(" | ".join(contact_parts), contact_style))
        elements.append(Spacer(1, 10))
        elements.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor('#cbd5e1'), spaceAfter=8))

        # Summary
        summary = resume_dict.get("summary")
        if summary:
            elements.append(Paragraph("PROFESSIONAL SUMMARY", section_style))
            elements.append(Paragraph(cls.clean_text(summary), body_style))
            elements.append(Spacer(1, 6))

        # Experience
        experiences = resume_dict.get("experiences") or []
        if experiences:
            elements.append(Paragraph("EXPERIENCE", section_style))
            for exp in experiences:
                role_str = f"<b>{exp.get('title', 'Role')}</b> — <i>{exp.get('company', '')}</i>"
                if exp.get('dates'):
                    role_str += f" <font color='#64748b'>({exp.get('dates')})</font>"
                elements.append(Paragraph(role_str, body_style))
                
                bullets = exp.get("bullets") or []
                if isinstance(bullets, str):
                    bullets = [b.strip("- ") for b in bullets.split("\n") if b.strip()]
                for b in bullets:
                    elements.append(Paragraph(f"• {cls.clean_text(b)}", bullet_style))
                elements.append(Spacer(1, 4))

        # Skills
        skills = resume_dict.get("skills") or []
        if skills:
            elements.append(Paragraph("SKILLS & COMPETENCIES", section_style))
            skills_str = ", ".join(skills) if isinstance(skills, list) else str(skills)
            elements.append(Paragraph(skills_str, body_style))
            elements.append(Spacer(1, 6))

        # Education
        education = resume_dict.get("education") or []
        if education:
            elements.append(Paragraph("EDUCATION", section_style))
            for edu in education:
                edu_str = f"<b>{edu.get('degree', 'Degree')}</b> | {edu.get('school', '')}"
                elements.append(Paragraph(edu_str, body_style))

        pdf.build(elements)
        return output_path

    @classmethod
    def save_cover_letter_docx(cls, letter_text, company_name, job_title, output_path):
        """Creates a professional business cover letter in .docx format"""
        doc = Document()
        for section in doc.sections:
            section.top_margin = Inches(1.0)
            section.bottom_margin = Inches(1.0)
            section.left_margin = Inches(1.0)
            section.right_margin = Inches(1.0)

        # Date
        dp = doc.add_paragraph()
        d_run = dp.add_run(datetime.now().strftime("%B %d, %Y"))
        d_run.font.name = "Calibri"
        d_run.font.size = Pt(11)
        dp.paragraph_format.space_after = Pt(16)

        # Recipient Block
        recip_p = doc.add_paragraph()
        r1 = recip_p.add_run(f"Hiring Team\n{company_name or 'Hiring Company'}\nRe: Application for {job_title or 'Open Position'}\n")
        r1.font.name = "Calibri"
        r1.font.size = Pt(11)
        r1.font.bold = True
        recip_p.paragraph_format.space_after = Pt(16)

        # Content paragraphs
        clean_letter = cls.clean_text(letter_text)
        paragraphs = [p.strip() for p in clean_letter.split("\n") if p.strip()]
        for p_text in paragraphs:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(10)
            p.paragraph_format.line_spacing = 1.15
            run = p.add_run(p_text)
            run.font.name = "Calibri"
            run.font.size = Pt(11)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        doc.save(output_path)
        return output_path

    @classmethod
    def save_cover_letter_pdf(cls, letter_text, company_name, job_title, output_path):
        """Creates a professional business cover letter in .pdf format"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        pdf = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=60,
            leftMargin=60,
            topMargin=60,
            bottomMargin=60
        )
        
        styles = getSampleStyleSheet()
        normal = styles['Normal']
        
        date_style = ParagraphStyle(
            'LetterDate',
            parent=normal,
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#475569'),
            spaceAfter=14
        )
        
        header_style = ParagraphStyle(
            'LetterHeader',
            parent=normal,
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=16,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=16
        )
        
        body_style = ParagraphStyle(
            'LetterBody',
            parent=normal,
            fontName='Helvetica',
            fontSize=10.5,
            leading=15.5,
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=12
        )

        elements = []
        elements.append(Paragraph(datetime.now().strftime("%B %d, %Y"), date_style))
        elements.append(Paragraph(f"Hiring Team<br/>{company_name or 'Hiring Organization'}<br/><b>Application for {job_title or 'Open Role'}</b>", header_style))

        clean_letter = cls.clean_text(letter_text)
        paragraphs = [p.strip() for p in clean_letter.split("\n") if p.strip()]
        for p_text in paragraphs:
            elements.append(Paragraph(p_text, body_style))

        pdf.build(elements)
        return output_path
