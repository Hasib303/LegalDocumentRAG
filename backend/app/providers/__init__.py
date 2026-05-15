"""Provider abstractions for LLM, embedding, reranker, and vision backends.

Each capability is exposed as a ``Protocol``; concrete implementations
(Gemini, Groq, Ollama, sentence-transformers, …) live in sibling modules
and are selected via ``config.yaml``. Swapping a provider is a one-line
config change — no agent code touches a specific SDK.
"""
