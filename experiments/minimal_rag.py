import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

DEFAULT_KNOWLEDGE_BASE = Path("data/sample_knowledge_base")
DEFAULT_MAX_CHARACTERS = 800
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


HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$")


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


def main() -> None:
    documents = load_documents(DEFAULT_KNOWLEDGE_BASE)
    chunks = [chunk for document in documents for chunk in chunk_document(document)]

    print(f"Loaded {len(documents)} support documents and created {len(chunks)} chunks:")
    for document in documents:
        print(
            f"- {document.document_id}: {document.title} "
            f"[{document.product_area}] ({document.source_path})"
        )


if __name__ == "__main__":
    main()
