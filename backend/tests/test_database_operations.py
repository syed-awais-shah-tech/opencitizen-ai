"""Direct database operations and model integrity tests."""

from sqlalchemy.orm import Session

from app.models.answer import Answer
from app.models.citation import Citation
from app.models.dataset import Dataset
from app.models.document import Document
from app.models.query import Query
from app.models.uploaded_file import UploadedFile
from app.schemas.datasets import DatasetColumnSchema, DatasetCreate
from app.schemas.documents import DocumentCreate
from app.services.datasets_service import datasets_service
from app.services.documents_service import documents_service


def test_uploaded_file_creation(db_session: Session) -> None:
    """Ensure raw uploaded file records are persisted with hash and path."""
    uploaded = UploadedFile(
        id="uf-001",
        filename="budget_2024.pdf",
        original_filename="budget_2024_signed.pdf",
        mime_type="application/pdf",
        file_size_bytes=8400000,
        storage_path="/uploads/2026/budget_2024.pdf",
        file_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    )
    db_session.add(uploaded)
    db_session.commit()

    retrieved = db_session.get(UploadedFile, "uf-001")
    assert retrieved is not None
    assert retrieved.filename == "budget_2024.pdf"
    assert retrieved.file_size_bytes == 8400000


def test_document_model_crud(db_session: Session) -> None:
    """Ensure Document metadata can be created and retrieved via service."""
    create_payload = DocumentCreate(
        title="Transportation_Master_Plan.pdf",
        department="Department of Transportation",
        category="Urban Planning",
        page_count=42,
        chunk_count=98,
        size_bytes=4200000,
        summary="Strategic transit expansion through 2030.",
    )
    doc_item = documents_service.create_document(db=db_session, payload=create_payload)
    assert doc_item.id.startswith("doc_")
    assert doc_item.title == "Transportation_Master_Plan.pdf"
    assert doc_item.page_count == 42

    # Query back
    retrieved = documents_service.get_document_by_id(db=db_session, document_id=doc_item.id)
    assert retrieved is not None
    assert retrieved.department == "Department of Transportation"

    # List
    list_res = documents_service.get_documents(db=db_session)
    assert list_res.total == 1
    assert len(list_res.items) == 1


def test_dataset_model_crud(db_session: Session) -> None:
    """Ensure Dataset metadata with JSON columns can be persisted and retrieved."""
    create_payload = DatasetCreate(
        name="department_expenses_2023.csv",
        category="Expenditure",
        format="CSV",
        row_count=14280,
        columns_count=3,
        table_name="dept_expenses",
        size_bytes=2400000,
        columns=[
            DatasetColumnSchema(name="department", type="VARCHAR"),
            DatasetColumnSchema(name="amount", type="DOUBLE"),
            DatasetColumnSchema(name="fiscal_year", type="INTEGER"),
        ],
    )
    ds_item = datasets_service.create_dataset(db=db_session, payload=create_payload)
    assert ds_item.id.startswith("ds_")
    assert ds_item.table_name == "dept_expenses"
    assert len(ds_item.columns) == 3

    # Query back
    retrieved = datasets_service.get_dataset_by_id(db=db_session, dataset_id=ds_item.id)
    assert retrieved is not None
    assert retrieved.name == "department_expenses_2023.csv"
    assert retrieved.row_count == 14280

    # List
    list_res = datasets_service.get_datasets(db=db_session)
    assert list_res.total == 1
    assert list_res.items[0].columns[0].name == "department"


def test_query_answer_citation_relationship(db_session: Session) -> None:
    """Ensure queries, answers, and citations maintain relational integrity."""
    query = Query(
        id="qry-test-1",
        session_id="sess-01",
        question="What was the total expenditure for Parks & Rec?",
        status="completed",
    )
    db_session.add(query)
    db_session.flush()

    answer = Answer(
        id="ans-test-1",
        query_id=query.id,
        answer_text="Parks & Rec spent $4.25M in fiscal year 2023.",
        latency_ms=28.5,
        is_placeholder=True,
    )
    db_session.add(answer)
    db_session.flush()

    citation = Citation(
        id="cit-test-1",
        answer_id=answer.id,
        document_title="City_Budget_2024.pdf",
        page_number=14,
        similarity_score=0.912,
        excerpt="Section 3.2 Parks allocation adjusted to $4.25M.",
        chunk_id="chk_p14_001",
        department="Office of Management & Budget",
    )
    db_session.add(citation)
    db_session.commit()

    # Verify relationships
    retrieved_query = db_session.get(Query, "qry-test-1")
    assert retrieved_query is not None
    assert len(retrieved_query.answers) == 1
    assert len(retrieved_query.answers[0].citations) == 1
    assert retrieved_query.answers[0].citations[0].document_title == "City_Budget_2024.pdf"
