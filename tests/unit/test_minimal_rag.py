from datetime import date
from pathlib import Path

import pytest

from experiments.minimal_rag import (
    DEFAULT_KNOWLEDGE_BASE,
    DEFAULT_MAX_CHARACTERS,
    SupportDocument,
    chunk_document,
    load_documents,
    parse_document,
    split_body,
    split_long_paragraph,
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


def test_chunk_document_preserves_hierarchy_and_source_metadata(tmp_path: Path) -> None:
    source_path = tmp_path / "policy.md"
    document = SupportDocument(
        document_id="billing-policy",
        title="Billing Policy",
        version="1.0",
        last_updated=date(2026, 7, 30),
        product_area="billing",
        source_path=source_path,
        content="""# Billing Policy

## Refunds

Refund requests must be submitted within 30 days.

### Exceptions

Promotional purchases are not refundable.
""",
    )

    chunks = chunk_document(document)

    assert [chunk.chunk_id for chunk in chunks] == [
        "billing-policy::chunk-000",
        "billing-policy::chunk-001",
    ]
    assert chunks[0].parent_headings == ("Billing Policy",)
    assert chunks[1].parent_headings == ("Billing Policy", "Refunds")
    assert chunks[1].heading == "Exceptions"
    assert chunks[1].heading_level == 3
    assert chunks[1].document_id == document.document_id
    assert chunks[1].document_title == document.title
    assert chunks[1].source_path == source_path
    assert chunks[1].content.startswith("# Billing Policy\n## Refunds\n### Exceptions\n\n")


def test_chunk_document_respects_default_size_limit() -> None:
    document = SupportDocument(
        document_id="long-policy",
        title="Long Policy",
        version="1.0",
        last_updated=date(2026, 7, 30),
        product_area="test",
        source_path=Path("long-policy.md"),
        content=f"# Long Policy\n\n## Details\n\n{'word ' * 500}",
    )

    chunks = chunk_document(document)

    assert len(chunks) > 1
    assert all(len(chunk.content) <= DEFAULT_MAX_CHARACTERS for chunk in chunks)
    assert [chunk.position for chunk in chunks] == list(range(len(chunks)))


def test_split_body_keeps_paragraphs_together_when_they_fit() -> None:
    body = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."

    assert split_body(body, max_characters=35) == [
        "First paragraph.\n\nSecond paragraph.",
        "Third paragraph.",
    ]


def test_split_long_paragraph_rejects_word_larger_than_limit() -> None:
    with pytest.raises(ValueError, match="word exceeds"):
        split_long_paragraph("unbreakable", max_characters=5)


def test_chunk_document_rejects_heading_larger_than_limit() -> None:
    document = SupportDocument(
        document_id="heading-policy",
        title="Heading Policy",
        version="1.0",
        last_updated=date(2026, 7, 30),
        product_area="test",
        source_path=Path("heading-policy.md"),
        content="# A heading that is too long\n\nContent.",
    )

    with pytest.raises(ValueError, match="Heading hierarchy exceeds"):
        chunk_document(document, max_characters=10)
