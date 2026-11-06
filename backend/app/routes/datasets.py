"""
Dataset API Routes
==================
CRUD for evaluation datasets and their test cases.
Datasets provide benchmark expected outputs for accuracy evaluation.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.pipeline import EvaluationDataset, EvaluationTestCase
from app.schemas.pipeline import (
    EvaluationDatasetCreate, EvaluationDatasetRead,
    EvaluationTestCaseCreate, EvaluationTestCaseRead, TestCaseBulkCreate,
)

router = APIRouter(prefix="/datasets", tags=["Evaluation Datasets"])


@router.post("/", response_model=EvaluationDatasetRead, status_code=status.HTTP_201_CREATED)
def create_dataset(data: EvaluationDatasetCreate, db: Session = Depends(get_db)):
    """Create a new evaluation dataset."""
    existing = db.query(EvaluationDataset).filter(EvaluationDataset.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Dataset '{data.name}' already exists")
    dataset = EvaluationDataset(name=data.name, description=data.description)
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return _enrich_dataset(dataset, db)


@router.get("/", response_model=List[EvaluationDatasetRead])
def list_datasets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List all evaluation datasets."""
    datasets = db.query(EvaluationDataset).order_by(EvaluationDataset.created_at.desc()).offset(skip).limit(limit).all()
    return [_enrich_dataset(d, db) for d in datasets]


@router.get("/{dataset_id}", response_model=EvaluationDatasetRead)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """Get a dataset by ID."""
    dataset = db.query(EvaluationDataset).filter(EvaluationDataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
    return _enrich_dataset(dataset, db)


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """Delete a dataset and all its test cases."""
    dataset = db.query(EvaluationDataset).filter(EvaluationDataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
    db.delete(dataset)
    db.commit()


@router.post("/{dataset_id}/test-cases", response_model=List[EvaluationTestCaseRead], status_code=status.HTTP_201_CREATED)
def add_test_cases(dataset_id: int, payload: TestCaseBulkCreate, db: Session = Depends(get_db)):
    """Add test cases to a dataset (bulk)."""
    dataset = db.query(EvaluationDataset).filter(EvaluationDataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")

    created = []
    for tc in payload.test_cases:
        test_case = EvaluationTestCase(
            dataset_id=dataset_id,
            task_id=tc.task_id,
            input=tc.input,
            expected_output=tc.expected_output,
            expected_tool=tc.expected_tool,
            extra_metadata=tc.extra_metadata,
        )
        db.add(test_case)
        created.append(test_case)

    db.commit()
    for tc in created:
        db.refresh(tc)

    return created


@router.get("/{dataset_id}/test-cases", response_model=List[EvaluationTestCaseRead])
def get_test_cases(
    dataset_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=10000),
    db: Session = Depends(get_db),
):
    """List test cases for a dataset."""
    dataset = db.query(EvaluationDataset).filter(EvaluationDataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
    return (
        db.query(EvaluationTestCase)
        .filter(EvaluationTestCase.dataset_id == dataset_id)
        .order_by(EvaluationTestCase.created_at.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.delete("/{dataset_id}/test-cases", status_code=status.HTTP_204_NO_CONTENT)
def clear_test_cases(dataset_id: int, db: Session = Depends(get_db)):
    """Remove all test cases from a dataset."""
    dataset = db.query(EvaluationDataset).filter(EvaluationDataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
    db.query(EvaluationTestCase).filter(EvaluationTestCase.dataset_id == dataset_id).delete()
    db.commit()


def _enrich_dataset(dataset: EvaluationDataset, db: Session) -> EvaluationDatasetRead:
    count = db.query(EvaluationTestCase).filter(EvaluationTestCase.dataset_id == dataset.id).count()
    result = EvaluationDatasetRead.model_validate(dataset)
    result.test_case_count = count
    return result
