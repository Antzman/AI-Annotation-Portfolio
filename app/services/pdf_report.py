from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab import __file__ as reportlab_path

from app.models.quality import QUALITY_CATEGORIES
from app.services.report_data import SECTION_DETAILS
from app.services.quality_validation import QUALITY_LABELS
from app.services.attention_validation import ISSUE_LABELS, SEVERITY_LABELS

NAVY = colors.HexColor("#183556")
BLUE = colors.HexColor("#2867C7")
PALE_BLUE = colors.HexColor("#EEF4FC")
INK = colors.HexColor("#263A52")
MUTED = colors.HexColor("#65758B")
GRID = colors.HexColor("#C7D3E1")
PALE_GREY = colors.HexColor("#F4F7FA")
WHITE = colors.white

_FONT_DIRECTORY = Path(reportlab_path).parent / "fonts"
pdfmetrics.registerFont(TTFont("Vera", str(_FONT_DIRECTORY / "Vera.ttf")))
pdfmetrics.registerFont(TTFont("Vera-Bold", str(_FONT_DIRECTORY / "VeraBd.ttf")))
pdfmetrics.registerFont(TTFont("Vera-Italic", str(_FONT_DIRECTORY / "VeraIt.ttf")))
pdfmetrics.registerFont(
    TTFont("Vera-BoldItalic", str(_FONT_DIRECTORY / "VeraBI.ttf"))
)
registerFontFamily(
    "Vera",
    normal="Vera",
    bold="Vera-Bold",
    italic="Vera-Italic",
    boldItalic="Vera-BoldItalic",
)

PAGE_WIDTH, PAGE_HEIGHT = letter
PAGE_MARGIN = 0.62 * inch
CONTENT_WIDTH = PAGE_WIDTH - PAGE_MARGIN * 2


def _styles():
    base = getSampleStyleSheet()
    return {
        "cover-kicker": ParagraphStyle(
            "CoverKicker",
            parent=base["Normal"],
            fontName="Vera-Bold",
            fontSize=9,
            leading=13,
            textColor=BLUE,
            alignment=TA_CENTER,
            spaceAfter=12,
        ),
        "cover-title": ParagraphStyle(
            "CoverTitle",
            parent=base["Title"],
            fontName="Vera-Bold",
            fontSize=28,
            leading=35,
            textColor=NAVY,
            alignment=TA_CENTER,
            spaceAfter=11,
        ),
        "cover-subtitle": ParagraphStyle(
            "CoverSubtitle",
            parent=base["Normal"],
            fontName="Vera",
            fontSize=12,
            leading=17,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=20,
        ),
        "h1": ParagraphStyle(
            "ReportHeading1",
            parent=base["Heading1"],
            fontName="Vera-Bold",
            fontSize=18,
            leading=23,
            textColor=NAVY,
            spaceBefore=5,
            spaceAfter=11,
            keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "ReportHeading2",
            parent=base["Heading2"],
            fontName="Vera-Bold",
            fontSize=12,
            leading=16,
            textColor=BLUE,
            spaceBefore=13,
            spaceAfter=7,
            keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "ReportHeading3",
            parent=base["Heading3"],
            fontName="Vera-Bold",
            fontSize=10,
            leading=14,
            textColor=INK,
            spaceBefore=8,
            spaceAfter=5,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "ReportBody",
            parent=base["BodyText"],
            fontName="Vera",
            fontSize=9,
            leading=13,
            textColor=INK,
            spaceAfter=7,
            wordWrap="CJK",
        ),
        "small": ParagraphStyle(
            "ReportSmall",
            parent=base["BodyText"],
            fontName="Vera",
            fontSize=8,
            leading=11,
            textColor=MUTED,
            spaceAfter=5,
            wordWrap="CJK",
        ),
        "table": ParagraphStyle(
            "ReportTable",
            parent=base["BodyText"],
            fontName="Vera",
            fontSize=7.4,
            leading=10,
            textColor=INK,
            wordWrap="CJK",
        ),
        "table-header": ParagraphStyle(
            "ReportTableHeader",
            parent=base["BodyText"],
            fontName="Vera-Bold",
            fontSize=7.2,
            leading=9,
            textColor=WHITE,
            wordWrap="CJK",
        ),
        "table-label": ParagraphStyle(
            "ReportTableLabel",
            parent=base["BodyText"],
            fontName="Vera-Bold",
            fontSize=7.4,
            leading=10,
            textColor=NAVY,
            wordWrap="CJK",
        ),
        "cover-label": ParagraphStyle(
            "CoverLabel",
            parent=base["BodyText"],
            fontName="Vera-Bold",
            fontSize=8,
            leading=11,
            textColor=NAVY,
        ),
        "cover-value": ParagraphStyle(
            "CoverValue",
            parent=base["BodyText"],
            fontName="Vera",
            fontSize=8,
            leading=11,
            textColor=INK,
            wordWrap="CJK",
        ),
    }


def _text(value):
    if value is None or value == "":
        return "Not provided"
    return str(value)


def _paragraph(value, style, markup=False):
    content = str(value) if markup else escape(_text(value)).replace("\n", "<br/>")
    return Paragraph(content, style)


def _grid_table(rows, widths, repeat_rows=1, paddings=5):
    table = Table(
        rows,
        colWidths=widths,
        repeatRows=repeat_rows,
        splitByRow=1,
        splitInRow=1,
        hAlign="LEFT",
    )
    commands = [
        ("GRID", (0, 0), (-1, -1), 0.45, GRID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), paddings),
        ("RIGHTPADDING", (0, 0), (-1, -1), paddings),
        ("TOPPADDING", (0, 0), (-1, -1), paddings),
        ("BOTTOMPADDING", (0, 0), (-1, -1), paddings),
    ]
    if repeat_rows:
        commands.extend(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ]
        )
    for row_index in range(1 if repeat_rows else 0, len(rows)):
        if row_index % 2 == 0:
            commands.append(
                ("BACKGROUND", (0, row_index), (-1, row_index), PALE_GREY)
            )
    table.setStyle(TableStyle(commands))
    return table


def _status_text(status):
    return {
        "complete": "Complete",
        "in_progress": "In progress",
        "not_started": "Not started",
    }[status]


def _draw_page(canvas, document):
    canvas.saveState()
    canvas.setStrokeColor(GRID)
    canvas.setLineWidth(0.5)
    canvas.line(
        PAGE_MARGIN,
        PAGE_HEIGHT - 0.48 * inch,
        PAGE_WIDTH - PAGE_MARGIN,
        PAGE_HEIGHT - 0.48 * inch,
    )
    canvas.setFont("Vera-Bold", 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(PAGE_MARGIN, PAGE_HEIGHT - 0.37 * inch, "AI ANNOTATION STUDIO")
    canvas.setStrokeColor(GRID)
    canvas.setLineWidth(0.5)
    canvas.line(PAGE_MARGIN, 0.48 * inch, PAGE_WIDTH - PAGE_MARGIN, 0.48 * inch)
    canvas.setFont("Vera", 7)
    canvas.setFillColor(MUTED)
    canvas.drawRightString(PAGE_WIDTH - PAGE_MARGIN, 0.31 * inch, f"Page {document.page}")
    canvas.restoreState()


def _quality_values(exercise):
    return {rating.category: rating for rating in exercise.quality_assessment.ratings} if exercise.quality_assessment else {}


def _cover(story, report, styles):
    story.extend(
        [
            Spacer(1, 0.18 * inch),
            _paragraph("AI ANNOTATION STUDIO", styles["cover-kicker"]),
            _paragraph("Assessment Report", styles["cover-title"]),
            _paragraph("Assessment Overview", styles["cover-subtitle"]),
        ]
    )
    rows = [
        [
            _paragraph("ASSESSMENT STATUS", styles["cover-label"]),
            _paragraph(report["status"], styles["cover-value"]),
        ],
        [
            _paragraph("GENERATED", styles["cover-label"]),
            _paragraph(
                report["generated_at"].strftime("%B %d, %Y %H:%M UTC"),
                styles["cover-value"],
            ),
        ],
        [
            _paragraph("ASSESSMENT PROGRESS", styles["cover-label"]),
            _paragraph(f'{report["completion"]}%', styles["cover-value"]),
        ],
        [
            _paragraph("COMPLETED SECTIONS", styles["cover-label"]),
            _paragraph(
                f'{report["completed_sections"]} of {report["total_sections"]}',
                styles["cover-value"],
            ),
        ],
    ]
    if len(report["exercises"]) == 1:
        exercise = report["exercises"][0]
        rows.insert(
            0,
            [
                _paragraph("ASSESSMENT", styles["cover-label"]),
                _paragraph(exercise.title, styles["cover-value"]),
            ],
        )
        rows.insert(
            1,
            [
                _paragraph("CLIP REFERENCE", styles["cover-label"]),
                _paragraph(exercise.clip_reference or "Not provided", styles["cover-value"]),
            ],
        )
    facts = Table(rows, colWidths=[1.65 * inch, CONTENT_WIDTH - 1.65 * inch])
    facts.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.6, GRID),
                ("BACKGROUND", (0, 0), (0, -1), PALE_BLUE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]
        )
    )
    story.extend(
        [
            Spacer(1, 0.14 * inch),
            facts,
            Spacer(1, 0.12 * inch),
        ]
    )
    if len(report["exercises"]) > 1:
        story.append(_paragraph("Assessments included", styles["h2"]))
        assessment_rows = [
            [
                _paragraph("Assessment", styles["table-header"]),
                _paragraph("Clip reference", styles["table-header"]),
                _paragraph("Status", styles["table-header"]),
                _paragraph("Sections complete", styles["table-header"]),
            ]
        ]
        assessment_rows.extend(
            [
                _paragraph(summary["title"], styles["table"]),
                _paragraph(summary["clip_reference"] or "Not provided", styles["table"]),
                _paragraph(summary["status"], styles["table"]),
                _paragraph(
                    f'{summary["completed_sections"]} of {summary["total_sections"]}',
                    styles["table"],
                ),
            ]
            for summary in report["assessment_summaries"]
        )
        story.append(
            _grid_table(
                assessment_rows,
                [
                    2.0 * inch,
                    CONTENT_WIDTH - 4.15 * inch,
                    1.1 * inch,
                    1.05 * inch,
                ],
            )
        )
    story.append(
        _paragraph(
            "This report presents manually entered observations. Video files are not included or processed.",
            styles["small"],
        )
    )


def _object_action_table(exercise, styles):
    rows = [
        [
            _paragraph("Timestamp", styles["table-header"]),
            _paragraph("Identified object", styles["table-header"]),
            _paragraph(
                "Observed action and additional observations", styles["table-header"]
            ),
        ]
    ]
    for observation in exercise.object_action_observations:
        detail = escape(observation.observed_action)
        if observation.additional_observations:
            detail += (
                "<br/><br/><b>Additional observations:</b> "
                + escape(observation.additional_observations)
            )
        rows.append(
            [
                _paragraph(observation.timestamp, styles["table"]),
                _paragraph(observation.identified_object, styles["table"]),
                _paragraph(detail, styles["table"], markup=True),
            ]
        )
    return _grid_table(rows, [0.85 * inch, 1.1 * inch, CONTENT_WIDTH - 1.95 * inch])


def _movement_table(exercise, styles):
    rows = [
        [
            _paragraph("Timestamp", styles["table-header"]),
            _paragraph("Movement and reasoning", styles["table-header"]),
            _paragraph("Visibility", styles["table-header"]),
            _paragraph("Plausibility", styles["table-header"]),
        ]
    ]
    for observation in exercise.movement_observations:
        description = (
            "<b>Description:</b> "
            + escape(observation.movement_description)
            + "<br/><br/><b>Reasoning:</b> "
            + escape(observation.reasoning)
        )
        if observation.inconsistencies:
            description += (
                "<br/><br/><b>Inconsistencies:</b> "
                + escape(observation.inconsistencies)
            )
        rows.append(
            [
                _paragraph(observation.timestamp, styles["table"]),
                _paragraph(description, styles["table"], markup=True),
                _paragraph(observation.visibility.replace("_", " ").title(), styles["table"]),
                _paragraph(observation.plausibility.title(), styles["table"]),
            ]
        )
    return _grid_table(
        rows,
        [0.75 * inch, CONTENT_WIDTH - 2.4 * inch, 0.85 * inch, 0.8 * inch],
    )


def _quality_table(exercise, styles):
    rows = [
        [
            _paragraph("Category", styles["table-header"]),
            _paragraph("Rating", styles["table-header"]),
            _paragraph("Explanation", styles["table-header"]),
        ]
    ]
    ratings = _quality_values(exercise)
    for category in QUALITY_CATEGORIES:
        if category in ratings:
            rating = ratings[category]
            rows.append(
                [
                    _paragraph(QUALITY_LABELS[category], styles["table-label"]),
                    _paragraph(f"{rating.score} / 10", styles["table"]),
                    _paragraph(rating.explanation, styles["table"]),
                ]
            )
    return _grid_table(rows, [1.45 * inch, 0.65 * inch, CONTENT_WIDTH - 2.1 * inch])


def _attention_table(exercise, styles):
    rows = [
        [
            _paragraph("Timestamp", styles["table-header"]),
            _paragraph("Category / severity", styles["table-header"]),
            _paragraph("Issue, explanation, and suggested correction", styles["table-header"]),
        ]
    ]
    for issue in exercise.quality_issues:
        details = (
            "<b>Issue:</b> "
            + escape(issue.description)
            + "<br/><br/><b>Explanation:</b> "
            + escape(issue.explanation)
        )
        if issue.suggested_correction:
            details += (
                "<br/><br/><b>Suggested correction:</b> "
                + escape(issue.suggested_correction)
            )
        rows.append(
            [
                _paragraph(issue.timestamp, styles["table"]),
                _paragraph(
                    f"{ISSUE_LABELS[issue.category]}<br/>{SEVERITY_LABELS[issue.severity]}",
                    styles["table"],
                    markup=True,
                ),
                _paragraph(details, styles["table"], markup=True),
            ]
        )
    return _grid_table(
        rows,
        [0.85 * inch, 1.35 * inch, CONTENT_WIDTH - 2.2 * inch],
    )


def _assessment_sections(story, report, styles):
    story.append(_paragraph("Assessment results", styles["h1"]))
    if not report["exercises"]:
        story.append(
            _paragraph(
                "No assessments are available. Results cannot be reported until an assessment is created.",
                styles["body"],
            )
        )
        return

    for exercise in report["exercises"]:
        story.append(_paragraph(exercise.title, styles["h2"]))
        if exercise.clip_reference:
            story.append(
                _paragraph(f"Clip reference: {exercise.clip_reference}", styles["small"])
            )
        statuses = report["exercise_sections"][exercise.id]
        status_rows = [
            [
                _paragraph("Section", styles["table-header"]),
                _paragraph("Status", styles["table-header"]),
            ]
        ]
        status_rows.extend(
            [
                _paragraph(label, styles["table-label"]),
                _paragraph(_status_text(statuses[key]), styles["table"]),
            ]
            for key, label in SECTION_DETAILS
        )
        story.append(_grid_table(status_rows, [3.25 * inch, CONTENT_WIDTH - 3.25 * inch]))

        story.append(_paragraph("Object & Action Annotation", styles["h3"]))
        if exercise.object_action_observations:
            story.append(_object_action_table(exercise, styles))
        else:
            story.append(
                _paragraph(
                    "No object/action observations were recorded for this assessment.",
                    styles["body"],
                )
            )

        story.append(_paragraph("Movement & Motion Analysis", styles["h3"]))
        if exercise.movement_observations:
            story.append(_movement_table(exercise, styles))
        else:
            story.append(
                _paragraph(
                    "No movement observations were recorded for this assessment.",
                    styles["body"],
                )
            )

        story.append(_paragraph("Video Quality Assessment", styles["h3"]))
        assessment = exercise.quality_assessment
        if assessment and assessment.overall_score is not None:
            story.append(
                _paragraph(
                    f"Overall score: {assessment.overall_score:.1f} / 10 "
                    "(mean of all five category scores).",
                    styles["body"],
                )
            )
            story.append(_quality_table(exercise, styles))
        elif assessment and assessment.ratings:
            ratings = _quality_values(exercise)
            missing_ratings = [
                QUALITY_LABELS[category]
                for category in QUALITY_CATEGORIES
                if category not in ratings
            ]
            story.append(
                _paragraph(
                    f"Incomplete: {len(ratings)} of 5 category ratings saved. "
                    "Missing ratings: "
                    + ", ".join(missing_ratings)
                    + ". No overall score is reported.",
                    styles["body"],
                )
            )
            story.append(_quality_table(exercise, styles))
        else:
            missing_ratings = [
                QUALITY_LABELS[category] for category in QUALITY_CATEGORIES
            ]
            story.append(
                _paragraph(
                    "No quality ratings were saved. Missing ratings: "
                    + ", ".join(missing_ratings)
                    + ". No overall score is reported.",
                    styles["body"],
                )
            )

        story.append(_paragraph("Annotation Quality Review", styles["h3"]))
        reviewed = any(
            review.section_key == "attention_to_detail" and review.reviewed_at
            for review in exercise.section_reviews
        )
        if exercise.quality_issues:
            if reviewed:
                story.append(
                    _paragraph("Review marked complete.", styles["small"])
                )
            else:
                story.append(
                    _paragraph(
                        "Review not marked complete. The entries below are saved findings only.",
                        styles["small"],
                    )
                )
            story.append(_attention_table(exercise, styles))
        elif reviewed:
            story.append(
                _paragraph(
                    "Review marked complete; no issues were recorded.",
                    styles["body"],
                )
            )
        else:
            story.append(
                _paragraph(
                    "No issues are recorded, and this section has not been marked reviewed.",
                    styles["body"],
                )
            )


def _conclusion(story, report, styles):
    story.append(_paragraph("Overall conclusion", styles["h1"]))
    story.append(_paragraph(report["overall_conclusion"], styles["body"]))
    for conclusion in report["conclusions"]:
        story.append(_paragraph(conclusion, styles["small"]))
    story.append(
        _paragraph(
            "This report presents manually entered observations and ratings. "
            "Clip references are text only; no video was uploaded or processed.",
            styles["small"],
        )
    )


def generate_pdf(report):
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=letter,
        leftMargin=PAGE_MARGIN,
        rightMargin=PAGE_MARGIN,
        topMargin=0.68 * inch,
        bottomMargin=0.72 * inch,
        title=(
            f"AI Annotation Studio Assessment Report: {report['exercises'][0].title}"
            if len(report["exercises"]) == 1
            else "AI Annotation Studio Assessment Report"
        ),
        author="AI Annotation Studio",
    )
    styles = _styles()
    story = _build_story(report, styles)
    document.build(story, onFirstPage=_draw_page, onLaterPages=_draw_page)
    return output.getvalue()


def _build_story(report, styles=None):
    styles = styles or _styles()
    story = []
    _cover(story, report, styles)
    _assessment_sections(story, report, styles)
    _conclusion(story, report, styles)
    return story
