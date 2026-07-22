"""
PDF Report Routes
==================
Generates and returns a PDF report for a given evaluation.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.evaluation import Evaluation
from app.services.pdf_report import generate_pdf_report

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/{evaluation_id}/pdf")
def get_pdf_report(evaluation_id: int, db: Session = Depends(get_db)):
    """Generate and return a PDF report for the given evaluation."""
    ev = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    try:
        pdf_bytes = generate_pdf_report(ev)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    filename = f"CARE_Report_{ev.agent_name.replace(' ', '_')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
