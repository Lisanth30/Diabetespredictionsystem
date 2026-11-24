"""
PDF Generation Utility for Diabetes Prediction Reports using ReportLab.
Creates a modern, executive-grade clinical screening report with zero text overlap,
color-coded biomarker statuses, simple explanation, daily food guide, and control plan.
"""

import io
from xml.sax.saxutils import escape

from reportlab.graphics.shapes import Drawing, Rect
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from ml.explain import analyze_parameters, generate_prevention_protocol


def _safe(text):
    """Escape XML special characters for ReportLab Paragraph markup."""
    return escape(str(text if text is not None else ''))


def _build_probability_bar(probability, fill_color, width=136, height=8):
    """Creates a clean horizontal progress bar graphic for the risk scorecard."""
    d = Drawing(width, height + 2)
    pct = max(0.0, min(100.0, float(probability or 0.0)))
    # Track
    d.add(Rect(0, 1, width, height, rx=4, ry=4, fillColor=colors.HexColor('#e2e8f0'), strokeColor=None))
    # Fill
    fill_w = max(6.0, (pct / 100.0) * width) if pct > 0 else 0
    if fill_w > 0:
        d.add(Rect(0, 1, fill_w, height, rx=4, ry=4, fillColor=fill_color, strokeColor=None))
    return d


def generate_prediction_pdf(prediction_data, user_name, user_email):
    """
    Generates a byte stream containing the redesigned modern clinical PDF screening report.
    """
    buffer = io.BytesIO()

    page_w, page_h = letter
    margin_x = 36
    content_w = page_w - (margin_x * 2)  # 540 pt

    # Palette
    navy_dark = colors.HexColor('#0f172a')
    teal_primary = colors.HexColor('#4f46e5')
    teal_dark = colors.HexColor('#4338ca')
    teal_light = colors.HexColor('#a5b4fc')
    slate_text = colors.HexColor('#1e293b')
    slate_muted = colors.HexColor('#475569')
    slate_light = colors.HexColor('#64748b')
    surface_alt = colors.HexColor('#f8fafc')
    border_soft = colors.HexColor('#e2e8f0')

    risk_level = prediction_data.get('risk_level', 'Low')
    probability = float(prediction_data.get('probability', 0.0))
    report_id = prediction_data.get('id', 'N/A')
    formatted_date = prediction_data.get('formatted_date', 'N/A')

    if risk_level == 'High':
        risk_color = colors.HexColor('#dc2626')
        risk_dark = colors.HexColor('#991b1b')
        risk_bg = colors.HexColor('#fef2f2')
        risk_border = colors.HexColor('#fca5a5')
        risk_badge_text = 'HIGH RISK — CRITICAL'
    elif risk_level == 'Medium':
        risk_color = colors.HexColor('#d97706')
        risk_dark = colors.HexColor('#92400e')
        risk_bg = colors.HexColor('#fffbeb')
        risk_border = colors.HexColor('#fcd34d')
        risk_badge_text = 'MODERATE RISK — WARNING'
    else:
        risk_color = colors.HexColor('#059669')
        risk_dark = colors.HexColor('#065f46')
        risk_bg = colors.HexColor('#ecfdf5')
        risk_border = colors.HexColor('#6ee7b7')
        risk_badge_text = 'LOW RISK — NORMAL'

    # Compute real clinical parameter analysis & simple guide from existing engine
    user_inputs = {
        'Pregnancies': float(prediction_data.get('pregnancies', 0) or 0),
        'Glucose': float(prediction_data.get('glucose', 0) or 0),
        'BloodPressure': float(prediction_data.get('blood_pressure', 0) or 0),
        'SkinThickness': float(prediction_data.get('skin_thickness', 0) or 0),
        'Insulin': float(prediction_data.get('insulin', 0) or 0),
        'BMI': float(prediction_data.get('bmi', 0) or 0),
        'DiabetesPedigreeFunction': float(prediction_data.get('diabetes_pedigree_function', 0) or 0),
        'Age': float(prediction_data.get('age', 0) or 0),
    }
    param_factors = analyze_parameters(user_inputs)
    protocol = generate_prevention_protocol(risk_level, param_factors, user_inputs)
    simple_guide = protocol.get('simple_guide', {})

    # Canvas Header & Footer Callbacks
    def draw_first_page(canvas, doc_obj):
        canvas.saveState()
        # Full-bleed dark executive header band
        banner_h = 74
        canvas.setFillColor(navy_dark)
        canvas.rect(0, page_h - banner_h, page_w, banner_h, fill=1, stroke=0)
        # Teal accent bottom stripe on header
        canvas.setFillColor(teal_primary)
        canvas.rect(0, page_h - banner_h, page_w, 4, fill=1, stroke=0)

        # Brand title (left)
        canvas.setFillColor(colors.white)
        canvas.setFont('Helvetica-Bold', 19)
        canvas.drawString(margin_x, page_h - 36, 'HealthGuard AI')

        canvas.setFillColor(teal_light)
        canvas.setFont('Helvetica-Bold', 8)
        canvas.drawString(margin_x, page_h - 52, 'DIABETES RISK SCREENING & METABOLIC HEALTH REPORT')

        # Report meta (right)
        canvas.setFillColor(colors.white)
        canvas.setFont('Helvetica-Bold', 9.5)
        canvas.drawRightString(page_w - margin_x, page_h - 33, f'Report ID: #HG-{report_id}')

        canvas.setFillColor(colors.HexColor('#cbd5e1'))
        canvas.setFont('Helvetica', 8.5)
        canvas.drawRightString(page_w - margin_x, page_h - 49, f'Date: {formatted_date}')

        _draw_footer(canvas, doc_obj)
        canvas.restoreState()

    def draw_later_pages(canvas, doc_obj):
        canvas.saveState()
        # Subtle compact top bar on continuation pages
        canvas.setFillColor(navy_dark)
        canvas.rect(0, page_h - 32, page_w, 32, fill=1, stroke=0)
        canvas.setFillColor(teal_primary)
        canvas.rect(0, page_h - 34, page_w, 2, fill=1, stroke=0)

        canvas.setFillColor(colors.white)
        canvas.setFont('Helvetica-Bold', 9.5)
        canvas.drawString(margin_x, page_h - 21, 'HealthGuard AI  |  Clinical Screening Summary')
        canvas.setFillColor(colors.HexColor('#cbd5e1'))
        canvas.setFont('Helvetica', 8.5)
        canvas.drawRightString(page_w - margin_x, page_h - 21, f'Report #HG-{report_id}  |  {user_name}')

        _draw_footer(canvas, doc_obj)
        canvas.restoreState()

    def _draw_footer(canvas, doc_obj):
        canvas.setStrokeColor(border_soft)
        canvas.setLineWidth(0.75)
        canvas.line(margin_x, 34, page_w - margin_x, 34)
        canvas.setFillColor(slate_light)
        canvas.setFont('Helvetica', 7.5)
        canvas.drawString(
            margin_x,
            21,
            'HealthGuard AI Screening Report  |  Educational Risk Assessment (Not a Formal Medical Diagnosis)'
        )
        canvas.setFont('Helvetica-Bold', 7.5)
        canvas.drawRightString(page_w - margin_x, 21, f'Page {doc_obj.page}')

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=margin_x,
        leftMargin=margin_x,
        topMargin=88,
        bottomMargin=46,
    )

    styles = getSampleStyleSheet()

    # Dedicated typography styles with clean, non-overlapping leading
    micro_label = ParagraphStyle(
        'MicroLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7,
        leading=9,
        textColor=slate_light,
    )
    meta_value = ParagraphStyle(
        'MetaValue',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=navy_dark,
    )
    section_title = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=navy_dark,
        spaceBefore=12,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        'BodyClean',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.75,
        leading=12.5,
        textColor=slate_text,
    )
    small_muted = ParagraphStyle(
        'SmallMuted',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=slate_muted,
    )
    risk_kicker_style = ParagraphStyle(
        'RiskKicker',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=10,
        textColor=risk_dark,
    )
    risk_heading_style = ParagraphStyle(
        'RiskHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=20,
        textColor=risk_color,
    )
    risk_explain_style = ParagraphStyle(
        'RiskExplain',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.6,
        leading=12.5,
        textColor=slate_text,
    )
    score_label_style = ParagraphStyle(
        'ScoreLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=10,
        alignment=1,
        textColor=slate_muted,
    )
    score_number_style = ParagraphStyle(
        'ScoreNumber',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        alignment=1,
        textColor=risk_color,
    )
    score_sub_style = ParagraphStyle(
        'ScoreSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        alignment=1,
        textColor=slate_light,
    )
    th_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
    )
    disclaimer_style = ParagraphStyle(
        'DisclaimerClean',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.8,
        leading=11.2,
        textColor=colors.HexColor('#78350f'),
    )

    story = []

    # ------------------------------------------------------------------
    # 1. Patient Profile Metadata Strip (4 Clean Columns)
    # ------------------------------------------------------------------
    patient_cells = [
        [
            Paragraph('PATIENT NAME', micro_label),
            Paragraph('EMAIL ADDRESS', micro_label),
            Paragraph('AGE', micro_label),
            Paragraph('SCREENING MODEL', micro_label),
        ],
        [
            Paragraph(_safe(user_name), meta_value),
            Paragraph(_safe(user_email), meta_value),
            Paragraph(f"{int(user_inputs['Age'])} Years", meta_value),
            Paragraph('Logistic Regression AI', meta_value),
        ],
    ]
    patient_table = Table(patient_cells, colWidths=[140, 195, 75, 130])
    patient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), surface_alt),
        ('BOX', (0, 0), (-1, -1), 0.75, border_soft),
        ('LINEBEFORE', (0, 0), (0, -1), 3.5, teal_primary),
        ('LINEAFTER', (0, 0), (2, -1), 0.5, border_soft),
        ('TOPPADDING', (0, 0), (-1, 0), 7),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 1),
        ('TOPPADDING', (0, 1), (-1, 1), 1),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 9),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 11))

    # ------------------------------------------------------------------
    # 2. Modern Risk Assessment Scorecard (Zero Overlap!)
    # ------------------------------------------------------------------
    simple_headline = simple_guide.get('simple_headline', '')
    simple_explanation = simple_guide.get('simple_explanation', '')

    left_inner = Table(
        [
            [Paragraph('OVERALL ASSESSMENT RESULT', risk_kicker_style)],
            [Paragraph(_safe(risk_badge_text), risk_heading_style)],
            [Paragraph(f"<b>{_safe(simple_headline)}</b>", risk_explain_style)],
            [Paragraph(_safe(simple_explanation), risk_explain_style)],
        ],
        colWidths=[350],
    )
    left_inner.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))

    prob_bar = _build_probability_bar(probability, risk_color, width=132, height=7)
    right_inner = Table(
        [
            [Paragraph('RISK PROBABILITY', score_label_style)],
            [Paragraph(f'{probability:.1f}%', score_number_style)],
            [prob_bar],
            [Paragraph('AI Screening Score', score_sub_style)],
        ],
        colWidths=[150],
    )
    right_inner.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('BOX', (0, 0), (-1, -1), 0.75, risk_border),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (0, 0), 8),
        ('BOTTOMPADDING', (0, 0), (0, 0), 2),
        ('TOPPADDING', (0, 1), (0, 1), 0),
        ('BOTTOMPADDING', (0, 1), (0, 1), 4),
        ('TOPPADDING', (0, 2), (0, 2), 2),
        ('BOTTOMPADDING', (0, 2), (0, 2), 4),
        ('TOPPADDING', (0, 3), (0, 3), 1),
        ('BOTTOMPADDING', (0, 3), (0, 3), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 9),
        ('RIGHTPADDING', (0, 0), (-1, -1), 9),
    ]))

    scorecard = Table([[left_inner, right_inner]], colWidths=[370, 170])
    scorecard.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), risk_bg),
        ('BOX', (0, 0), (-1, -1), 1.25, risk_border),
        ('LINEBEFORE', (0, 0), (0, -1), 4.5, risk_color),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (0, 0), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(scorecard)

    # Critical warning signs strip for High Risk
    warning_signs = simple_guide.get('warning_signs', [])
    if risk_level == 'High' and warning_signs:
        story.append(Spacer(1, 8))
        warn_text = (
            "<font color='#991b1b'><b>CRITICAL WARNING SIGNS — See a Doctor Right Away If You Notice:</b></font><br/>"
            + '  •  '.join(_safe(w) for w in warning_signs)
        )
        warn_table = Table([[Paragraph(warn_text, body_style)]], colWidths=[content_w])
        warn_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fff1f2')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#fda4af')),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(warn_table)

    # ------------------------------------------------------------------
    # 3. Clinical Biomarker Breakdown Table (With Real Status Colors)
    # ------------------------------------------------------------------
    story.append(Paragraph('Submitted Health Parameters & Clinical Status', section_title))

    level_color_map = {
        'safe': '#059669',
        'caution': '#d97706',
        'warning': '#d97706',
        'danger': '#dc2626',
        'neutral': '#475569',
    }

    param_rows = [[
        Paragraph('Parameter', th_style),
        Paragraph('Your Value', th_style),
        Paragraph('Healthy Reference', th_style),
        Paragraph('Clinical Status', th_style),
    ]]

    for f in param_factors:
        lvl_hex = level_color_map.get(f.get('level', 'neutral'), '#475569')
        val_display = f"{f.get('value')} {f.get('unit', '')}".strip()
        param_rows.append([
            Paragraph(f"<b>{_safe(f.get('label', f.get('name')))}</b>", body_style),
            Paragraph(f"<b>{_safe(val_display)}</b>", body_style),
            Paragraph(_safe(f.get('normal_range', '')), small_muted),
            Paragraph(f"<font color='{lvl_hex}'><b>{_safe(f.get('status', 'Recorded'))}</b></font>", body_style),
        ])

    param_table = Table(param_rows, colWidths=[165, 100, 125, 150], repeatRows=1)
    param_styles = [
        ('BACKGROUND', (0, 0), (-1, 0), teal_dark),
        ('BOX', (0, 0), (-1, -1), 0.75, border_soft),
        ('LINEBELOW', (0, 0), (-1, -1), 0.4, border_soft),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, 0), 7),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 7),
        ('TOPPADDING', (0, 1), (-1, -1), 5.5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]
    for i in range(1, len(param_rows)):
        if i % 2 == 0:
            param_styles.append(('BACKGROUND', (0, i), (-1, i), surface_alt))
    param_table.setStyle(TableStyle(param_styles))
    story.append(param_table)

    # ------------------------------------------------------------------
    # 4. Daily Food Guide (What to Take vs What to Avoid + Sample Meal Plan)
    # ------------------------------------------------------------------
    foods_eat = simple_guide.get('foods_to_eat', [])
    foods_avoid = simple_guide.get('foods_to_avoid', [])
    meal_plan = simple_guide.get('sample_meal_plan', [])

    food_section = [Paragraph('Daily Food Guide: What to Take & What to Avoid', section_title)]

    eat_bullets = '<br/>'.join(
        f"<font color='#16a34a'><b>&#8226;</b></font> {_safe(item)}" for item in foods_eat
    )
    avoid_bullets = '<br/>'.join(
        f"<font color='#dc2626'><b>&#8226;</b></font> {_safe(item)}" for item in foods_avoid
    )

    food_table = Table(
        [
            [
                Paragraph("<font color='#166534'><b>FOODS TO TAKE DAILY</b></font>", body_style),
                Paragraph("<font color='#991b1b'><b>FOODS TO AVOID / LIMIT</b></font>", body_style),
            ],
            [
                Paragraph(eat_bullets, body_style),
                Paragraph(avoid_bullets, body_style),
            ],
        ],
        colWidths=[content_w / 2.0, content_w / 2.0],
    )
    food_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#dcfce7')),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#fee2e2')),
        ('BACKGROUND', (0, 1), (0, 1), colors.HexColor('#f0fdf4')),
        ('BACKGROUND', (1, 1), (1, 1), colors.HexColor('#fef2f2')),
        ('BOX', (0, 0), (0, -1), 0.75, colors.HexColor('#86efac')),
        ('BOX', (1, 0), (1, -1), 0.75, colors.HexColor('#fca5a5')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 9),
        ('RIGHTPADDING', (0, 0), (-1, -1), 9),
    ]))
    food_section.append(food_table)

    if meal_plan:
        food_section.append(Spacer(1, 7))
        meal_headers = [Paragraph(f"<font color='#4338ca'><b>{_safe(m['meal'].upper())}</b></font>", micro_label) for m in meal_plan]
        meal_bodies = [Paragraph(_safe(m['menu']), small_muted) for m in meal_plan]
        meal_table = Table([meal_headers, meal_bodies], colWidths=[content_w / len(meal_plan)] * len(meal_plan))
        meal_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eef2ff')),
            ('BACKGROUND', (0, 1), (-1, 1), colors.white),
            ('BOX', (0, 0), (-1, -1), 0.75, border_soft),
            ('INNERGRID', (0, 0), (-1, -1), 0.4, border_soft),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 7),
            ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ]))
        food_section.append(meal_table)

    story.append(KeepTogether(food_section))

    # ------------------------------------------------------------------
    # 5. Step-by-Step Control & Action Plan
    # ------------------------------------------------------------------
    control_title = simple_guide.get('control_title', 'What to Do Next')
    control_steps = simple_guide.get('control_steps', [])

    control_section = [Paragraph(_safe(control_title), section_title)]
    step_rows = []
    for step in control_steps:
        step_rows.append([
            Paragraph(
                f"<b>{_safe(step.get('title', ''))}</b><br/><font color='#475569'>{_safe(step.get('detail', ''))}</font>",
                body_style
            )
        ])

    if step_rows:
        step_table = Table(step_rows, colWidths=[content_w])
        step_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), surface_alt),
            ('BOX', (0, 0), (-1, -1), 0.75, border_soft),
            ('LINEBEFORE', (0, 0), (0, -1), 3.5, risk_color),
            ('LINEBELOW', (0, 0), (-1, -2), 0.4, border_soft),
            ('TOPPADDING', (0, 0), (-1, -1), 5.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5.5),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        control_section.append(step_table)

    story.append(KeepTogether(control_section))
    story.append(Spacer(1, 10))

    # ------------------------------------------------------------------
    # 6. Medical Disclaimer Box (Kept Together — Never Clipped)
    # ------------------------------------------------------------------
    disclaimer_text = (
        "<b>CLINICAL DISCLAIMER:</b> This screening report is generated by a machine learning model (Logistic Regression) "
        "for educational and early risk-awareness purposes only. <b>It is NOT a medical diagnosis or prescription.</b> "
        "Always consult a licensed physician for certified lab tests (Fasting Blood Sugar, HbA1c) and medical guidance."
    )
    disclaimer_box = Table([[Paragraph(disclaimer_text, disclaimer_style)]], colWidths=[content_w])
    disclaimer_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fffbeb')),
        ('BOX', (0, 0), (-1, -1), 0.9, colors.HexColor('#f59e0b')),
        ('LINEBEFORE', (0, 0), (0, -1), 3.5, colors.HexColor('#f59e0b')),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(KeepTogether([disclaimer_box]))

    doc.build(story, onFirstPage=draw_first_page, onLaterPages=draw_later_pages)
    buffer.seek(0)
    return buffer.getvalue()
