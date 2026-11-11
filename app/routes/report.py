from io import BytesIO

from flask import Blueprint, abort, render_template, send_file
from werkzeug.utils import secure_filename

from app.services.pdf_report import generate_pdf
from app.services.report_data import build_report_data

bp = Blueprint("report", __name__, url_prefix="/report-preview")


@bp.get("")
def preview():
    return render_template(
        "report/preview.html",
        active_nav="report-preview",
        report=build_report_data(),
        download_error=None,
    )


@bp.get("/download")
def download():
    report = build_report_data()
    if not report["has_assessments"]:
        return (
            render_template(
                "report/preview.html",
                active_nav="report-preview",
                report=report,
                download_error=(
                    "Create at least one assessment before exporting an assessment report."
                ),
            ),
            409,
        )

    pdf = generate_pdf(report)
    profile_name = (
        secure_filename(report["profile"].name)
        if report["profile"] and report["profile"].name
        else "AI-Annotation-Studio"
    )
    filename = (
        f"{profile_name}-report-{report['generated_at'].strftime('%Y-%m-%d')}.pdf"
    )
    response = send_file(
        BytesIO(pdf),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )
    response.headers["Cache-Control"] = "no-store"
    return response
