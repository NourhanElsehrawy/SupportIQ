from dataclasses import dataclass
from datetime import date
from pathlib import Path

DEFAULT_KNOWLEDGE_BASE = Path("data/sample_knowledge_base")
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


def main() -> None:
    documents = load_documents(DEFAULT_KNOWLEDGE_BASE)

    print(f"Loaded {len(documents)} support documents:")
    for document in documents:
        print(
            f"- {document.document_id}: {document.title} "
            f"[{document.product_area}] ({document.source_path})"
        )


if __name__ == "__main__":
    main()
