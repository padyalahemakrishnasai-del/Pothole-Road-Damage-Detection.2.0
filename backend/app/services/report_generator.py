"""PDF report generator for road damage inspection results.

Uses ReportLab to build an engineering-grade road condition report
including executive metrics, defect breakdown, and visual evidence.
"""
import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from app.core.config import settings
from app.database.models import Analysis


class ReportGenerator:
    """Generates PDF inspection reports for road damage analysis records."""

    @staticmethod
    def generate_pdf(record: Analysis) -> str:
        """
        Build a PDF report from an Analysis database model instance.
        Returns the absolute filepath to the generated PDF.
        """
        out_dir = Path(settings.OUTPUT_DIR)
        out_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = out_dir / f"report_{record.analysis_id}.pdf"

        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        # Custom paragraph styles
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#0F172A'),
            spaceAfter=4
        )
        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#64748B'),
            spaceAfter=15
        )
        h2_style = ParagraphStyle(
            'SectionH2',
            parent=styles['Heading2'],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor('#1E293B'),
            spaceBefore=12,
            spaceAfter=8
        )
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#334155')
        )
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#64748B'),
            alignment=1
        )

        elements = []

        # 1. Header Banner
        header_table = Table(
            [
                [
                    Paragraph("<b>AI ROADGUARD</b> — Road Condition Inspection Report", title_style),
                    Paragraph("<b>AUTOMATED INSPECTION</b>", ParagraphStyle('Badge', fontSize=9, textColor=colors.HexColor('#F59E0B'), alignment=2))
                ]
            ],
            colWidths=[400, 140]
        )
        elements.append(header_table)
        elements.append(Paragraph(f"Analysis ID: {record.analysis_id} • Generated: {record.created_at.strftime('%Y-%m-%d %H:%M:%S UTC') if record.created_at else 'N/A'}", subtitle_style))
        elements.append(Spacer(1, 10))

        # 2. Executive Metrics Summary Table
        prio_color = {
            "Critical": colors.HexColor('#EF4444'),
            "High": colors.HexColor('#F97316'),
            "Medium": colors.HexColor('#F59E0B'),
            "Low": colors.HexColor('#10B981')
        }.get(record.priority_label, colors.HexColor('#64748B'))

        metrics_data = [
            ["Metric", "Value", "Metric", "Value"],
            ["File Analyzed", record.file_name, "Media Type", record.file_type.upper()],
            ["Total Defects", str(record.damage_count), "Avg Confidence", f"{(record.avg_confidence or 0):.1%}"],
            ["Potholes", str(record.pothole_count), "Highest Severity", record.highest_severity or "None"],
            ["Cracks", str(record.crack_count), "Priority Score", f"{record.priority_score or 0}/100"],
            ["Surface Wear", str(record.surface_damage_count), "Priority Level", record.priority_label or "Low"],
        ]

        metrics_table = Table(metrics_data, colWidths=[135, 135, 135, 135])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F8FAFC'), colors.white]),
            ('TEXTCOLOR', (1, 5), (1, 5), prio_color),
            ('TEXTCOLOR', (3, 5), (3, 5), prio_color),
            ('FONTNAME', (1, 5), (1, 5), 'Helvetica-Bold'),
            ('FONTNAME', (3, 5), (3, 5), 'Helvetica-Bold'),
        ]))
        elements.append(metrics_table)
        elements.append(Spacer(1, 15))

        # 3. Recommendation Box
        if record.recommendation:
            elements.append(Paragraph("Maintenance Engineering Recommendation", h2_style))
            rec_table = Table(
                [[Paragraph(f"<b>Prescribed Action:</b> {record.recommendation}", body_style)]],
                colWidths=[540]
            )
            rec_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FEF3C7')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#F59E0B')),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ]))
            elements.append(rec_table)
            elements.append(Spacer(1, 15))

        # 4. Visual Evidence Snapshot (if image available)
        if record.output_image_path and os.path.exists(record.output_image_path):
            try:
                elements.append(Paragraph("Visual Evidence (Annotated Inspection Frame)", h2_style))
                img = RLImage(record.output_image_path, width=5.5 * inch, height=3.0 * inch)
                elements.append(img)
                elements.append(Spacer(1, 15))
            except Exception as e:
                print(f"[Report] Could not attach image: {e}")

        # 5. Detections Table
        detections = record.detections or []
        if detections:
            elements.append(Paragraph(f"Detected Defect Details ({len(detections)} instances)", h2_style))
            det_headers = ["#", "Category", "Confidence", "Severity", "Area Ratio", "BBox [x1,y1,x2,y2]"]
            det_rows = [det_headers]

            for idx, d in enumerate(detections[:30], 1):  # Cap to top 30 for PDF readability
                bbox_str = f"[{int(d['bbox'][0])},{int(d['bbox'][1])},{int(d['bbox'][2])},{int(d['bbox'][3])}]" if "bbox" in d else ""
                det_rows.append([
                    str(idx),
                    d.get("class_name", "Unknown"),
                    f"{d.get('confidence', 0):.1%}",
                    d.get("severity", "N/A"),
                    f"{(d.get('area_ratio', 0) * 100):.2f}%",
                    bbox_str
                ])

            det_table = Table(det_rows, colWidths=[25, 115, 75, 75, 75, 175])
            det_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#334155')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
            ]))
            elements.append(KeepTogether(det_table))
            elements.append(Spacer(1, 20))

        # 6. Disclaimer Footer
        elements.append(Spacer(1, 15))
        elements.append(Paragraph(
            "<b>LEGAL & TECHNICAL DISCLAIMER:</b> This report is generated by an automated computer-vision decision support prototype. "
            "Defect boundaries, severities, and priority indices are advisory heuristics. Final road maintenance authorization, budget allocation, "
            "and repair specifications must be certified through on-site manual engineering inspection by licensed civil authorities.",
            disclaimer_style
        ))

        # Build document
        doc.build(elements)
        return str(pdf_path)


report_generator = ReportGenerator()
