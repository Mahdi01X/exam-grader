"""Exports : tableur classe (xlsx) et PDF annoté par copie."""
from __future__ import annotations
import io
from typing import Iterable

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)
from reportlab.lib import colors

from app.models.copy import StudentCopy
from app.models.exam import Exam
from app.models.grade import QuestionGrade
from app.models.rubric import RubricItem


def class_xlsx(exam: Exam, rubric: list[RubricItem], copies: list[StudentCopy],
               grades_by_copy: dict[int, list[QuestionGrade]]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Notes"

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="1E40AF")

    headers = ["Identifiant"] + [f"Q{r.question_number} / {r.points_max}" for r in rubric] + ["Total", "Total max", "Statut"]
    for col, h in enumerate(headers, start=1):
        c = ws.cell(row=1, column=col, value=h)
        c.font = header_font
        c.fill = header_fill

    total_max = sum(r.points_max for r in rubric)

    for row, copy in enumerate(copies, start=2):
        ws.cell(row=row, column=1, value=copy.student_identifier)
        grades = {g.rubric_item_id: g for g in grades_by_copy.get(copy.id, [])}
        total = 0.0
        for col, r in enumerate(rubric, start=2):
            g = grades.get(r.id)
            pts = (g.final_points if g and g.final_points is not None else (g.proposed_points if g else 0.0))
            ws.cell(row=row, column=col, value=round(pts, 2))
            total += pts
        ws.cell(row=row, column=len(headers) - 2, value=round(total, 2))
        ws.cell(row=row, column=len(headers) - 1, value=round(total_max, 2))
        ws.cell(row=row, column=len(headers), value=copy.status.value)

    for col in ws.columns:
        max_len = max((len(str(c.value)) for c in col if c.value is not None), default=10)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 40)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def annotated_pdf(exam: Exam, copy: StudentCopy, rubric: list[RubricItem],
                  grades: list[QuestionGrade]) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=1.5 * cm, rightMargin=1.5 * cm)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"<b>{exam.title}</b>", styles["Title"]))
    story.append(Paragraph(f"Matière : {exam.subject or '—'}", styles["Normal"]))
    story.append(Paragraph(f"Étudiant : <b>{copy.student_identifier}</b>", styles["Normal"]))
    story.append(Spacer(1, 0.5 * cm))

    grades_by_q = {g.rubric_item_id: g for g in grades}
    total_pts = 0.0
    total_max = 0.0

    data = [["Question", "Points", "Règle", "Justification", "Conf."]]
    for r in rubric:
        g = grades_by_q.get(r.id)
        pts = g.final_points if g and g.final_points is not None else (g.proposed_points if g else 0.0)
        total_pts += pts
        total_max += r.points_max
        policy_name = g.applied_policy.name if g and g.applied_policy else "—"
        justification = (g.justification if g else "—")[:240]
        confidence = f"{g.confidence:.2f}" if g else "—"
        data.append([
            Paragraph(f"<b>Q{r.question_number}</b><br/>{r.intitule[:120]}", styles["BodyText"]),
            f"{pts:.2f} / {r.points_max:.2f}",
            policy_name,
            Paragraph(justification, styles["BodyText"]),
            confidence,
        ])
    data.append(["", f"<b>{total_pts:.2f} / {total_max:.2f}</b>", "", "", ""])

    table = Table(data, colWidths=[4 * cm, 2.5 * cm, 3 * cm, 6 * cm, 1.5 * cm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E40AF")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -2), 0.25, colors.grey),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#F1F5F9")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]))
    story.append(table)

    # Transcriptions détaillées par question
    story.append(PageBreak())
    story.append(Paragraph("<b>Détail des transcriptions</b>", styles["Heading2"]))
    for r in rubric:
        g = grades_by_q.get(r.id)
        story.append(Paragraph(f"<b>Q{r.question_number} — {r.intitule[:200]}</b>", styles["Heading3"]))
        story.append(Paragraph(f"<i>Attendu :</i> {r.expected_answer[:500]}", styles["BodyText"]))
        if g:
            story.append(Paragraph(f"<i>Transcription :</i> {(g.extracted_text or '—')[:1000]}", styles["BodyText"]))
            story.append(Paragraph(f"<i>Justification :</i> {g.justification or '—'}", styles["BodyText"]))
        story.append(Spacer(1, 0.2 * cm))

    doc.build(story)
    return buf.getvalue()
