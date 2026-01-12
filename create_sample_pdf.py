"""
Create a sample clinical document PDF for testing.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
import os

# Create PDF
output_path = r"C:\Users\axays\Downloads\clinical_sample.pdf"
doc = SimpleDocTemplate(output_path, pagesize=letter)
story = []
styles = getSampleStyleSheet()

# Title
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontSize=24,
    textColor='darkblue',
    spaceAfter=30,
    alignment=TA_CENTER
)
story.append(Paragraph("Clinical Trial Protocol: Hypertension Management", title_style))
story.append(Spacer(1, 0.2*inch))

# Study Overview
story.append(Paragraph("Study Overview", styles['Heading2']))
content = """
This randomized, double-blind clinical trial evaluates the efficacy and safety of 
ACE inhibitor therapy (Lisinopril) versus calcium channel blocker therapy (Amlodipine) 
in patients with stage 2 hypertension. The study will enroll 500 participants aged 
45-75 years with systolic blood pressure ≥140 mmHg and diastolic blood pressure ≥90 mmHg.
"""
story.append(Paragraph(content, styles['BodyText']))
story.append(Spacer(1, 0.2*inch))

# Primary Objectives
story.append(Paragraph("Primary Objectives", styles['Heading2']))
objectives = """
1. To compare the mean reduction in systolic blood pressure between Lisinopril and 
Amlodipine groups after 12 weeks of treatment.

2. To assess the safety profile of both medications, including monitoring for common 
adverse events such as cough (ACE inhibitors) and peripheral edema (calcium channel blockers).

3. To evaluate patient compliance and quality of life improvements using standardized 
questionnaires.
"""
story.append(Paragraph(objectives, styles['BodyText']))
story.append(Spacer(1, 0.2*inch))

# Dosing Protocol
story.append(Paragraph("Dosing Protocol", styles['Heading2']))
dosing = """
<b>Lisinopril Group:</b> Initial dose of 10 mg once daily, titrated to 20 mg once daily 
after 2 weeks if blood pressure remains uncontrolled (SBP ≥130 mmHg). Maximum dose: 40 mg daily.

<b>Amlodipine Group:</b> Initial dose of 5 mg once daily, titrated to 10 mg once daily 
after 2 weeks if blood pressure remains uncontrolled. Maximum dose: 10 mg daily.

All medications should be taken in the morning with or without food. Patients should 
maintain consistent timing of administration throughout the study.
"""
story.append(Paragraph(dosing, styles['BodyText']))
story.append(Spacer(1, 0.2*inch))

# Inclusion Criteria
story.append(Paragraph("Inclusion Criteria", styles['Heading2']))
inclusion = """
• Adults aged 45-75 years
• Diagnosed with stage 2 hypertension (SBP ≥140 mmHg or DBP ≥90 mmHg)
• No contraindications to ACE inhibitors or calcium channel blockers
• Able to provide informed consent
• BMI between 18.5 and 40 kg/m²
• No history of myocardial infarction or stroke in the past 6 months
"""
story.append(Paragraph(inclusion, styles['BodyText']))
story.append(Spacer(1, 0.2*inch))

# Exclusion Criteria
story.append(Paragraph("Exclusion Criteria", styles['Heading2']))
exclusion = """
• Pregnancy or breastfeeding
• Severe renal impairment (eGFR <30 mL/min/1.73m²)
• History of angioedema
• Current use of more than 2 antihypertensive medications
• Known allergy to ACE inhibitors or calcium channel blockers
• Uncontrolled diabetes (HbA1c >9%)
• Active liver disease with ALT >3x upper limit of normal
"""
story.append(Paragraph(exclusion, styles['BodyText']))
story.append(Spacer(1, 0.2*inch))

# Safety Monitoring
story.append(Paragraph("Safety Monitoring and Adverse Events", styles['Heading2']))
safety = """
All participants will be monitored for adverse events at weeks 2, 4, 8, and 12. 
Common adverse events to monitor include:

<b>ACE Inhibitors (Lisinopril):</b>
- Dry cough (occurs in approximately 10-15% of patients)
- Hyperkalemia (monitor serum potassium levels)
- First-dose hypotension
- Dizziness and fatigue
- Rare: angioedema (requires immediate discontinuation)

<b>Calcium Channel Blockers (Amlodipine):</b>
- Peripheral edema (ankle swelling, occurs in 5-10% of patients)
- Headache
- Flushing
- Dizziness
- Palpitations

Any serious adverse events must be reported to the Data Safety Monitoring Board 
within 24 hours of occurrence.
"""
story.append(Paragraph(safety, styles['BodyText']))
story.append(Spacer(1, 0.2*inch))

# Expected Outcomes
story.append(Paragraph("Expected Outcomes", styles['Heading2']))
outcomes = """
Based on previous studies, we anticipate:

1. Mean systolic blood pressure reduction of 15-20 mmHg in both groups
2. Mean diastolic blood pressure reduction of 8-12 mmHg in both groups
3. Approximately 70-75% of participants achieving blood pressure control (SBP <140 mmHg 
   and DBP <90 mmHg) by week 12
4. Adverse event discontinuation rate of <10% in both groups
5. Improved quality of life scores as measured by SF-36 questionnaire

Statistical analysis will use intention-to-treat principles with a significance 
level of p<0.05. Non-inferiority margin is set at 5 mmHg for systolic blood pressure.
"""
story.append(Paragraph(outcomes, styles['BodyText']))

# Build PDF
doc.build(story)
print(f"PDF created successfully at: {output_path}")
print(f"File size: {os.path.getsize(output_path)} bytes")
