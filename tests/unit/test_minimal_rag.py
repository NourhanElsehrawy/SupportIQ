from datetime import date
from pathlib import Path

import pytest

from experiments.minimal_rag import (
    DEFAULT_KNOWLEDGE_BASE,
    load_documents,
    parse_document,
)

DOCUMENT_TEMPLATE = """---
document_id: {document_id}
title: {title}
version: 1.0
last_updated: {last_updated}
product_area: test
---

{content}
"""


def write_document(
    path: Path,
    *,
    document_id: str = "test-document",
    title: str = "Test Document",
    last_updated: str = "2026-07-30",
    content: str = "# Test content",
) -> None:
    path.write_text(
        DOCUMENT_TEMPLATE.format(
            document_id=document_id,
            title=title,
            last_updated=last_updated,
            content=content,
        ),
        encoding="utf-8",
    )


def test_loads_sample_knowledge_base_with_source_metadata() -> None:
    documents = load_documents(DEFAULT_KNOWLEDGE_BASE)

    assert len(documents) == 10
    assert len({document.document_id for document in documents}) == 10

    refund_policy = next(
        document for document in documents if document.document_id == "billing-refund-policy"
    )
    assert refund_policy.title == "Refund Policy"
    assert refund_policy.version == "1.0"
    assert refund_policy.last_updated == date(2026, 7, 30)
    assert refund_policy.product_area == "billing"
    assert refund_policy.source_path == DEFAULT_KNOWLEDGE_BASE / "billing-refund-policy.md"
    assert "30 calendar days" in refund_policy.content
    assert not refund_policy.content.startswith("---")


def test_parse_document_rejects_missing_metadata(tmp_path: Path) -> None:
    document_path = tmp_path / "incomplete.md"
    document_path.write_text(
        """---
document_id: incomplete
title: Incomplete Document
---

# Content
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="missing required metadata"):
        parse_document(document_path)


def test_parse_document_rejects_invalid_date(tmp_path: Path) -> None:
    document_path = tmp_path / "invalid-date.md"
    write_document(document_path, last_updated="not-a-date")

    with pytest.raises(ValueError, match="invalid last_updated date"):
        parse_document(document_path)


def test_parse_document_rejects_empty_content(tmp_path: Path) -> None:
    document_path = tmp_path / "empty.md"
    write_document(document_path, content="")

    with pytest.raises(ValueError, match="contains no document content"):
        parse_document(document_path)


def test_load_documents_rejects_duplicate_document_ids(tmp_path: Path) -> None:
    write_document(tmp_path / "first.md", document_id="duplicate", title="First")
    write_document(tmp_path / "second.md", document_id="duplicate", title="Second")

    with pytest.raises(ValueError, match="duplicate document IDs"):
        load_documents(tmp_path)


def test_load_documents_rejects_missing_directory(tmp_path: Path) -> None:
    missing_directory = tmp_path / "missing"

    with pytest.raises(ValueError, match="directory does not exist"):
        load_documents(missing_directory)
