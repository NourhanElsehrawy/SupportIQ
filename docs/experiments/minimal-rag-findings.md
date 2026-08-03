# Minimal RAG Experiment Findings

## Purpose

This experiment tests whether SupportIQ can retrieve evidence from a controlled
support knowledge base and generate a locally grounded answer before adding a
production API, vector database, or cloud infrastructure.

## Configuration

- Knowledge base: 10 fictional Markdown support documents
- Evaluation dataset: 25 questions
- Chunks: 43
- Chunking: Markdown headings and paragraphs, maximum 800 characters
- Embedding model: `nomic-embed-text`
- Generation model: `llama3.2:3b`
- Retrieval: in-memory cosine similarity
- Retrieval depth: top 3
- Runtime: local Ollama; no paid API or API key

## Retrieval results

The following results were produced on August 3, 2026:

| Metric | Result |
| --- | ---: |
| Answerable questions | 20 |
| Unanswerable questions | 5 |
| Hit@3 | 1.000 |
| MRR@3 | 1.000 |
| Multi-document full coverage@3 | 0.600 |
| Multi-document source recall@3 | 0.800 |
| Complete retrieval misses | 0 |
| Partial multi-document failures | 2 |

Hit@3 and MRR@3 are perfect because every answerable question retrieves at
least one expected document at rank 1. Those metrics do not prove that every
required document was retrieved. Multi-document coverage exposes the missing
evidence.

### Partial multi-document failures

`multi-002` expected both `account-password-reset` and
`account-email-change`. The top three contained `account-email-change` twice
and `troubleshooting-login`, so the password-reset evidence was missing.

`multi-005` expected both `account-email-change` and
`account-password-reset`. The top three contained `account-email-change`
twice and `troubleshooting-login`, again missing the password-reset evidence.

These are retrieval failures. Changing the generation prompt cannot recover
facts that were not placed in the model context.

## Grounded-answer result

The sample password-reset question retrieved the expected password-reset
document at rank 1. The local generation model answered that the link remains
valid for 30 minutes and returned only citations present in the retrieved
context.

The unsupported telephone-support question used during notebook review
returned:

```text
Insufficient evidence in the SupportIQ knowledge base.
```

Citation validation rejects answers with no citation or with a document ID
that was not retrieved. Retrieval and generation are executed separately, so
their failures can be diagnosed independently.

## Observed latency

One local run produced:

| Operation | Observed latency |
| --- | ---: |
| Embed 43 chunks | 5,074 ms |
| Retrieve one question | 2,127 ms |
| Generate one grounded answer | 14,626 ms |
| Average retrieval across 25 questions | 2,248 ms |

These values describe one development-machine run, not a production
benchmark. They vary with model warm-up, available CPU/GPU memory, and other
local workload.

## Limitations

- The knowledge base and evaluation set are small and synthetic.
- Hit@3 and MRR@3 hide incomplete multi-document evidence.
- Generation quality was reviewed on selected examples, not all 25 questions.
- Unanswerable questions still receive nearest-neighbor results, so similarity
  scores alone do not establish a safe abstention threshold.
- No prompt-cost comparison exists because both models run locally.
- No pgvector, reranker, query decomposition, or hybrid search was tested.

## Reproduce

Start Ollama with `nomic-embed-text` and `llama3.2:3b` installed, then run:

```powershell
python -m experiments.minimal_rag --evaluate-retrieval
python -m experiments.minimal_rag
```

The first command evaluates retrieval across all 25 questions. The second
runs one complete retrieval-and-generation example with latency output.

## Conclusion

The baseline is strong for direct and paraphrased questions and successfully
demonstrates local grounded generation. The main measured weakness is complete
evidence retrieval for multi-document questions. That limitation should guide
the next RAG iteration rather than being hidden by the perfect Hit@3 and MRR@3
scores.
