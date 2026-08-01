from datetime import date
from pathlib import Path

import pytest

from experiments.minimal_rag import (
    DEFAULT_KNOWLEDGE_BASE,
    DEFAULT_MAX_CHARACTERS,
    INSUFFICIENT_EVIDENCE_RESPONSE,
    OllamaPayload,
    OllamaResponse,
    RetrievalResult,
    SupportChunk,
    SupportDocument,
    build_grounded_context,
    chunk_document,
    cosine_similarity,
    embed_texts,
    extract_citations,
    generate_grounded_answer,
    load_documents,
    parse_document,
    retrieve_chunks,
    split_body,
    split_long_paragraph,
    validate_answer_citations,
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


def make_chunk(
    document_id: str,
    *,
    position: int = 0,
    content: str = "# Policy\n\nPolicy content.",
) -> SupportChunk:
    return SupportChunk(
        chunk_id=f"{document_id}::chunk-{position:03d}",
        document_id=document_id,
        document_title="Policy",
        position=position,
        heading="Policy",
        heading_level=1,
        parent_headings=(),
        source_path=Path(f"{document_id}.md"),
        content=content,
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


def test_embed_texts_returns_numeric_vectors_from_ollama() -> None:
    captured_payload: OllamaPayload = {}

    def fake_post(endpoint: str, payload: OllamaPayload) -> OllamaResponse:
        assert endpoint == "/api/embed"
        captured_payload.update(payload)
        return {"embeddings": [[1, 0.5], [0, -1]]}

    embeddings = embed_texts(["first", "second"], ollama_post=fake_post)

    assert embeddings == [[1.0, 0.5], [0.0, -1.0]]
    assert captured_payload["model"] == "nomic-embed-text"
    assert captured_payload["input"] == ["first", "second"]


def test_embed_texts_rejects_inconsistent_dimensions() -> None:
    def fake_post(endpoint: str, payload: OllamaPayload) -> OllamaResponse:
        return {"embeddings": [[1.0, 0.0], [1.0]]}

    with pytest.raises(RuntimeError, match="inconsistent dimensions"):
        embed_texts(["first", "second"], ollama_post=fake_post)


def test_cosine_similarity_for_identical_and_orthogonal_vectors() -> None:
    assert cosine_similarity([1.0, 1.0], [1.0, 1.0]) == pytest.approx(1.0)
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_cosine_similarity_rejects_zero_vector() -> None:
    with pytest.raises(ValueError, match="zero-magnitude"):
        cosine_similarity([0.0, 0.0], [1.0, 0.0])


def test_retrieve_chunks_returns_highest_scores_first() -> None:
    chunks = [make_chunk("first"), make_chunk("second"), make_chunk("third")]
    chunk_embeddings = [[1.0, 0.0], [0.8, 0.2], [0.0, 1.0]]

    def fake_embed(texts: list[str]) -> list[list[float]]:
        assert texts == ["Which policy is relevant?"]
        return [[1.0, 0.0]]

    results = retrieve_chunks(
        "Which policy is relevant?",
        chunks,
        chunk_embeddings,
        embed=fake_embed,
        top_k=2,
    )

    assert [result.chunk.document_id for result in results] == ["first", "second"]
    assert results[0].score == pytest.approx(1.0)
    assert results[0].score >= results[1].score


def test_retrieve_chunks_requires_one_embedding_per_chunk() -> None:
    with pytest.raises(ValueError, match="Every chunk"):
        retrieve_chunks("Question", [make_chunk("first")], [])


def test_grounded_context_exposes_document_ids_but_not_chunk_ids() -> None:
    chunk = make_chunk("account-policy", content="# Account\n\nSupported fact.")
    context = build_grounded_context(
        "What is supported?",
        [RetrievalResult(chunk=chunk, score=0.9)],
    )

    assert "DOCUMENT_ID: account-policy" in context
    assert "account-policy::chunk-000" not in context
    assert "Supported fact." in context


def test_extract_citations_returns_unique_document_ids() -> None:
    answer = "First fact [account-policy]. Second fact [billing-policy] [account-policy]."

    assert extract_citations(answer) == {"account-policy", "billing-policy"}


def test_validate_answer_citations_rejects_unretrieved_source() -> None:
    results = [RetrievalResult(chunk=make_chunk("account-policy"), score=0.9)]

    with pytest.raises(ValueError, match="outside retrieved context"):
        validate_answer_citations("Unsupported claim [invented-policy].", results)


def test_validate_answer_citations_accepts_clean_abstention() -> None:
    validate_answer_citations(INSUFFICIENT_EVIDENCE_RESPONSE, [])


def test_generate_grounded_answer_uses_chat_and_validates_citation() -> None:
    results = [RetrievalResult(chunk=make_chunk("account-policy"), score=0.9)]
    captured_payload: OllamaPayload = {}

    def fake_post(endpoint: str, payload: OllamaPayload) -> OllamaResponse:
        assert endpoint == "/api/chat"
        captured_payload.update(payload)
        return {"message": {"content": "Supported answer [account-policy]."}}

    answer = generate_grounded_answer(
        "What is supported?",
        results,
        ollama_post=fake_post,
    )

    assert answer == "Supported answer [account-policy]."
    assert captured_payload["model"] == "llama3.2:3b"
    assert captured_payload["stream"] is False
