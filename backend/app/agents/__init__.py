"""Role-specific agents coordinated by the orchestrator.

Each subpackage owns one bounded responsibility:

* ``ingest``        — file intake, hashing, manifests
* ``processing``    — page routing, OCR, structured extraction
* ``indexer``       — chunking, embedding, vector-store writes
* ``retrieval``     — hybrid search and reranking
* ``drafting``      — grounded section-wise generation
* ``audit``         — faithfulness scoring
* ``edit_capture``  — alignment and classification of operator edits
* ``learning``      — style-memory updates from edits
* ``evaluation``    — held-out benchmarks for the four pillars
"""
