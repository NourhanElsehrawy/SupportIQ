# SupportIQ Data

## Sample knowledge base

`sample_knowledge_base/` contains fictional SupportIQ Cloud documentation
created for the minimal RAG experiment. It represents the authoritative
company knowledge that the RAG system will search.

The documents are original project fixtures. They are not copied from a real
company, customer, or external dataset. Product names, limits, policies, email
addresses, and procedures are fictional.

Each Markdown file begins with metadata:

```yaml
document_id: stable identifier used by retrieval and citations
title: human-readable document title
version: content version
last_updated: date in YYYY-MM-DD format
product_area: high-level support category
```

`document_id` must remain stable when wording changes. A meaningful policy
change should increment `version` and update `last_updated`.

## External data

External datasets may later provide realistic customer-question phrasing, but
they are not authoritative product documentation. Downloaded datasets belong
under `data/external/` and must not be committed.

Every external source must be documented with:

- source URL;
- dataset version or download date;
- license;
- fields used;
- any filtering or transformation.

## Evaluation data

Evaluation records live in `data/evaluation/rag_questions.jsonl`. Each line is
one JSON object containing:

- `question_id`: stable evaluation-case identifier;
- `question`: customer wording presented to the RAG system;
- `question_type`: direct, paraphrased, multi-document, or unanswerable;
- `expected_source_ids`: documents retrieval should find;
- `expected_answer_facts`: facts a grounded answer should include;
- `answerable`: whether the current knowledge base contains enough evidence.

These records measure retrieval independently from answer generation. They
must not be included in the searchable knowledge base.

For direct and paraphrased questions, the expected source is the primary
document that contains the answer. For multi-document questions, every value in
`expected_source_ids` is required because each document contributes a distinct
fact.
