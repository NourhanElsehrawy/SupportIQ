import json
import math
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_KNOWLEDGE_BASE = Path("data/sample_knowledge_base")
DEFAULT_MAX_CHARACTERS = 800
DEFAULT_TOP_K = 3
OLLAMA_BASE_URL = "http://localhost:11434"
EMBEDDING_MODEL = "nomic-embed-text"
GENERATION_MODEL = "llama3.2:3b"
INSUFFICIENT_EVIDENCE_RESPONSE = "Insufficient evidence in the SupportIQ knowledge base."
REQUIRED_METADATA = {
    "document_id",
    "title",
    "version",
    "last_updated",
    "product_area",
}


@dataclass(frozen=True)
class SupportDocument:
    """A support document with metadata needed for retrieval and citations."""

    document_id: str
    title: str
    version: str
    last_updated: date
    product_area: str
    source_path: Path
    content: str


@dataclass(frozen=True)
class SupportChunk:
    """A retrievable section that retains its source-document context."""

    chunk_id: str
    document_id: str
    document_title: str
    position: int
    heading: str
    heading_level: int
    parent_headings: tuple[str, ...]
    source_path: Path
    content: str


@dataclass(frozen=True)
class RetrievalResult:
    """A support chunk and its semantic similarity to a question."""

    chunk: SupportChunk
    score: float


OllamaResponse = dict[str, object]
OllamaPayload = dict[str, object]
OllamaPost = Callable[[str, OllamaPayload], OllamaResponse]
EmbedTexts = Callable[[list[str]], list[list[float]]]


HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$")
CITATION_PATTERN = re.compile(r"\[([^]\n]+)\]")


def parse_document(path: Path) -> SupportDocument:
    """Parse one Markdown document with the experiment's front-matter format."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    if not lines or lines[0] != "---":
        raise ValueError(f"{path} must start with a front-matter delimiter")

    try:
        closing_delimiter = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError(f"{path} is missing the closing front-matter delimiter") from exc

    metadata: dict[str, str] = {}
    for line in lines[1:closing_delimiter]:
        key, separator, value = line.partition(":")
        key = key.strip()
        value = value.strip()

        if not separator or not key or not value:
            raise ValueError(f"{path} contains invalid metadata: {line!r}")
        if key in metadata:
            raise ValueError(f"{path} contains duplicate metadata key: {key}")
        metadata[key] = value

    missing_fields = REQUIRED_METADATA - metadata.keys()
    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise ValueError(f"{path} is missing required metadata: {missing}")

    content = "\n".join(lines[closing_delimiter + 1 :]).strip()
    if not content:
        raise ValueError(f"{path} contains no document content")

    try:
        last_updated = date.fromisoformat(metadata["last_updated"])
    except ValueError as exc:
        raise ValueError(f"{path} has an invalid last_updated date") from exc

    return SupportDocument(
        document_id=metadata["document_id"],
        title=metadata["title"],
        version=metadata["version"],
        last_updated=last_updated,
        product_area=metadata["product_area"],
        source_path=path,
        content=content,
    )


def load_documents(directory: Path) -> list[SupportDocument]:
    """Load Markdown documents in deterministic filename order."""
    if not directory.is_dir():
        raise ValueError(f"Knowledge-base directory does not exist: {directory}")

    paths = sorted(directory.glob("*.md"))
    if not paths:
        raise ValueError(f"Knowledge-base directory contains no Markdown files: {directory}")

    documents = [parse_document(path) for path in paths]
    document_ids = [document.document_id for document in documents]

    if len(set(document_ids)) != len(document_ids):
        raise ValueError("Knowledge base contains duplicate document IDs")

    return documents


def split_long_paragraph(paragraph: str, max_characters: int) -> list[str]:
    """Split one oversized paragraph at word boundaries."""
    pieces: list[str] = []
    current_words: list[str] = []

    for word in paragraph.split():
        candidate = " ".join([*current_words, word])
        if len(candidate) <= max_characters:
            current_words.append(word)
            continue

        if not current_words:
            raise ValueError(f"A word exceeds the {max_characters}-character limit")
        pieces.append(" ".join(current_words))
        current_words = [word]

    if current_words:
        pieces.append(" ".join(current_words))

    return pieces


def split_body(body: str, max_characters: int) -> list[str]:
    """Pack complete paragraphs into pieces within a character limit."""
    paragraphs = [
        paragraph.strip() for paragraph in re.split(r"\n\s*\n", body) if paragraph.strip()
    ]
    pieces: list[str] = []
    current_paragraphs: list[str] = []

    for paragraph in paragraphs:
        if len(paragraph) > max_characters:
            if current_paragraphs:
                pieces.append("\n\n".join(current_paragraphs))
                current_paragraphs = []
            pieces.extend(split_long_paragraph(paragraph, max_characters))
            continue

        candidate = "\n\n".join([*current_paragraphs, paragraph])
        if len(candidate) <= max_characters:
            current_paragraphs.append(paragraph)
        else:
            pieces.append("\n\n".join(current_paragraphs))
            current_paragraphs = [paragraph]

    if current_paragraphs:
        pieces.append("\n\n".join(current_paragraphs))

    return pieces


def chunk_document(
    document: SupportDocument,
    max_characters: int = DEFAULT_MAX_CHARACTERS,
) -> list[SupportChunk]:
    """Split a Markdown document by headings while retaining source metadata."""
    sections: list[tuple[str, int, tuple[str, ...], str]] = []
    heading_stack: list[tuple[int, str]] = []
    current_heading: str | None = None
    current_level: int | None = None
    current_parents: tuple[str, ...] = ()
    current_lines: list[str] = []

    def save_current_section() -> None:
        if current_heading is None or current_level is None:
            return
        body = "\n".join(current_lines).strip()
        if body:
            sections.append((current_heading, current_level, current_parents, body))

    for line in document.content.splitlines():
        match = HEADING_PATTERN.match(line)
        if not match:
            current_lines.append(line)
            continue

        save_current_section()
        level = len(match.group(1))
        heading = match.group(2).strip()
        while heading_stack and heading_stack[-1][0] >= level:
            heading_stack.pop()

        current_heading = heading
        current_level = level
        current_parents = tuple(value for _, value in heading_stack)
        current_lines = []
        heading_stack.append((level, heading))

    save_current_section()

    chunks: list[SupportChunk] = []
    for heading, level, parents, body in sections:
        hierarchy = [*parents, heading]
        heading_text = "\n".join(
            f"{'#' * hierarchy_level} {value}"
            for hierarchy_level, value in enumerate(hierarchy, start=1)
        )
        body_limit = max_characters - len(heading_text) - 2
        if body_limit <= 0:
            raise ValueError("Heading hierarchy exceeds the chunk-size limit")

        for body_piece in split_body(body, body_limit):
            position = len(chunks)
            chunks.append(
                SupportChunk(
                    chunk_id=f"{document.document_id}::chunk-{position:03d}",
                    document_id=document.document_id,
                    document_title=document.title,
                    position=position,
                    heading=heading,
                    heading_level=level,
                    parent_headings=parents,
                    source_path=document.source_path,
                    content=f"{heading_text}\n\n{body_piece}",
                )
            )

    return chunks


def post_ollama(
    endpoint: str,
    payload: OllamaPayload,
    *,
    base_url: str = OLLAMA_BASE_URL,
) -> OllamaResponse:
    """Send one JSON request to the local Ollama HTTP API."""
    request = Request(
        f"{base_url}{endpoint}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=300) as response:  # noqa: S310
            decoded: object = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        details = exc.read().decode("utf-8")
        raise RuntimeError(f"Ollama rejected the request: {details}") from exc
    except URLError as exc:
        raise RuntimeError("Ollama is not reachable. Start Ollama and try again.") from exc

    if not isinstance(decoded, dict) or not all(isinstance(key, str) for key in decoded):
        raise RuntimeError("Ollama returned an invalid JSON response")

    return decoded


def embed_texts(
    texts: list[str],
    *,
    ollama_post: OllamaPost = post_ollama,
) -> list[list[float]]:
    """Create local embeddings with the configured Ollama model."""
    if not texts or any(not text.strip() for text in texts):
        raise ValueError("Embedding input must contain non-empty text")

    response = ollama_post(
        "/api/embed",
        {"model": EMBEDDING_MODEL, "input": texts},
    )
    raw_embeddings = response.get("embeddings")
    if not isinstance(raw_embeddings, list) or len(raw_embeddings) != len(texts):
        raise RuntimeError("Ollama returned an invalid number of embeddings")

    embeddings: list[list[float]] = []
    for raw_embedding in raw_embeddings:
        if not isinstance(raw_embedding, list) or not raw_embedding:
            raise RuntimeError("Ollama returned an invalid embedding")
        if any(
            not isinstance(value, int | float) or isinstance(value, bool) for value in raw_embedding
        ):
            raise RuntimeError("Ollama returned a non-numeric embedding value")
        embeddings.append([float(value) for value in raw_embedding])

    dimensions = {len(embedding) for embedding in embeddings}
    if len(dimensions) != 1:
        raise RuntimeError("Ollama returned embeddings with inconsistent dimensions")

    return embeddings


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Calculate cosine similarity between equal-length, non-zero vectors."""
    if len(left) != len(right):
        raise ValueError("Embedding vectors must have the same dimensions")

    dot_product = sum(a * b for a, b in zip(left, right, strict=True))
    left_magnitude = math.sqrt(sum(value * value for value in left))
    right_magnitude = math.sqrt(sum(value * value for value in right))
    if left_magnitude == 0 or right_magnitude == 0:
        raise ValueError("Cannot compare a zero-magnitude embedding")

    return dot_product / (left_magnitude * right_magnitude)


def retrieve_chunks(
    question: str,
    chunks: list[SupportChunk],
    chunk_embeddings: list[list[float]],
    *,
    embed: EmbedTexts = embed_texts,
    top_k: int = DEFAULT_TOP_K,
) -> list[RetrievalResult]:
    """Embed a question and return the most similar chunks in memory."""
    if not question.strip():
        raise ValueError("Question must not be empty")
    if len(chunks) != len(chunk_embeddings):
        raise ValueError("Every chunk must have one embedding")
    if top_k <= 0:
        raise ValueError("top_k must be greater than zero")

    question_embedding = embed([question])[0]
    ranked = sorted(
        (
            RetrievalResult(
                chunk=chunk,
                score=cosine_similarity(question_embedding, chunk_embedding),
            )
            for chunk, chunk_embedding in zip(chunks, chunk_embeddings, strict=True)
        ),
        key=lambda result: result.score,
        reverse=True,
    )
    return ranked[:top_k]


def build_grounded_context(question: str, results: list[RetrievalResult]) -> str:
    """Build the customer question and citable retrieved context for the LLM."""
    context_blocks = [
        f"DOCUMENT_ID: {result.chunk.document_id}\nCONTENT:\n{result.chunk.content}"
        for result in results
    ]
    context = "\n\n---\n\n".join(context_blocks)
    return f"CUSTOMER QUESTION:\n{question}\n\nCONTEXT:\n{context}\n"


def extract_citations(answer: str) -> set[str]:
    """Extract bracketed source identifiers from a generated answer."""
    return set(CITATION_PATTERN.findall(answer))


def validate_answer_citations(answer: str, results: list[RetrievalResult]) -> None:
    """Reject missing or fabricated citations in a non-abstaining answer."""
    citations = extract_citations(answer)
    if answer == INSUFFICIENT_EVIDENCE_RESPONSE:
        if citations:
            raise ValueError("An insufficient-evidence response must not contain citations")
        return

    if not citations:
        raise ValueError("A grounded answer must contain at least one citation")

    retrieved_document_ids = {result.chunk.document_id for result in results}
    invalid_citations = citations - retrieved_document_ids
    if invalid_citations:
        invalid = ", ".join(sorted(invalid_citations))
        raise ValueError(f"Answer contains citations outside retrieved context: {invalid}")


def generate_grounded_answer(
    question: str,
    results: list[RetrievalResult],
    *,
    ollama_post: OllamaPost = post_ollama,
) -> str:
    """Generate and validate an answer using only retrieved context."""
    if not results:
        raise ValueError("At least one retrieval result is required")

    system_message = (
        "You are a SupportIQ customer-support assistant. "
        "Use only facts explicitly stated in the supplied context. "
        "If any passage supports the question, answer with those supported details. "
        "Explain different account types or conditions when relevant. "
        "After each supported statement, cite only the value following DOCUMENT_ID "
        "in square brackets. For example, if the context says DOCUMENT_ID: "
        "account-policy, write [account-policy]. Do not write "
        "[DOCUMENT_ID: account-policy]. Never cite headings or invent IDs. "
        "Only when no passage addresses the question, reply exactly: "
        f"{INSUFFICIENT_EVIDENCE_RESPONSE}"
    )
    response = ollama_post(
        "/api/chat",
        {
            "model": GENERATION_MODEL,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": build_grounded_context(question, results)},
            ],
            "stream": False,
            "options": {"temperature": 0},
        },
    )

    raw_message = response.get("message")
    if not isinstance(raw_message, dict):
        raise RuntimeError("Ollama returned an invalid chat message")
    raw_answer = raw_message.get("content")
    if not isinstance(raw_answer, str) or not raw_answer.strip():
        raise RuntimeError("Ollama returned an empty answer")

    answer = raw_answer.strip()
    validate_answer_citations(answer, results)
    return answer


def main() -> None:
    documents = load_documents(DEFAULT_KNOWLEDGE_BASE)
    chunks = [chunk for document in documents for chunk in chunk_document(document)]
    chunk_embeddings = embed_texts([chunk.content for chunk in chunks])
    question = "How long is a password-reset link valid?"
    results = retrieve_chunks(question, chunks, chunk_embeddings)
    answer = generate_grounded_answer(question, results)

    print(f"Loaded {len(documents)} documents and created {len(chunks)} chunks.")
    print(f"Embedding model: {EMBEDDING_MODEL}")
    print(f"Question: {question}")
    for rank, result in enumerate(results, start=1):
        print(
            f"{rank}. {result.chunk.document_id} / {result.chunk.chunk_id} "
            f"(score={result.score:.4f})"
        )
    print(f"Answer: {answer}")


if __name__ == "__main__":
    main()
