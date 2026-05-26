from __future__ import annotations

from datetime import datetime
from typing import Any

from src.agents.shared.llm_client import get_llm_client
from src.agents.support_agent.vector_store import ProductKnowledgeStore
from src.common.settings import get_settings
from src.database.crud import insert_one


def _safe_insert_chat_log(document: dict[str, Any]) -> None:
    try:
        insert_one("chat_logs", document)
    except Exception:
        pass


def _retrieve_chunks(question: str, top_k: int | None = None) -> tuple[list[dict], str, str | None]:
    try:
        settings = get_settings()
        effective_top_k = top_k or settings.rag_top_k

        store = ProductKnowledgeStore()
        chunks = store.search(question, top_k=effective_top_k)

        if chunks:
            return chunks, "azure_embedding_local_json_store", None

        return (
            [],
            "azure_embedding_local_json_store",
            "No relevant product knowledge found in the local vector store.",
        )

    except Exception as exc:
        return [], "retrieval_unavailable", str(exc)


def _build_context(retrieved_chunks: list[dict]) -> str:
    return "\n\n".join(
        [
            f"Source {index + 1}:\n{chunk.get('content', '')}"
            for index, chunk in enumerate(retrieved_chunks)
            if chunk.get("content")
        ]
    ).strip()


def _fallback_answer_from_context(question: str, retrieved_chunks: list[dict]) -> str:
    if not retrieved_chunks:
        return (
            "Product knowledge retrieval is temporarily unavailable, so I cannot verify this answer from the knowledge base right now."
        )

    top_chunk = retrieved_chunks[0]
    product_id = top_chunk.get("product_id") or "the matched product"
    product_name = top_chunk.get("product_name") or product_id
    content = str(top_chunk.get("content") or "").strip()

    if not content:
        return (
            "Relevant product metadata was found, but the product knowledge text is empty. Please rebuild the product knowledge store."
        )

    return (
        f"Based on the retrieved product knowledge for {product_name} ({product_id}), "
        f"the available information is: {content}"
    )


def answer_support_question(question: str) -> dict:
    question = str(question).strip()
    created_at = datetime.utcnow().isoformat()

    retrieved_chunks, retrieval_source, retrieval_error = _retrieve_chunks(
        question=question,
        top_k=None,
    )

    if not retrieved_chunks:
        response = {
            "question": question,
            "answer": (
                "I could not retrieve verified product knowledge for this question right now. "
                "Please check whether the product knowledge JSON store exists and Azure embedding settings are correct."
            ),
            "sources": [],
            "retrieval_source": retrieval_source,
            "retrieval_error": retrieval_error,
            "llm_source": "not_called",
            "llm_error": None,
            "agent": "support_agent",
            "created_at": created_at,
        }

        _safe_insert_chat_log(response)
        return response

    context = _build_context(retrieved_chunks)

    system_prompt = """
You are RetailIQ Support Agent.
You answer customer support questions using only the retrieved product knowledge.
If the information is not available in the context, clearly say that it is not available.
Do not hallucinate product policies.
Keep the response concise, professional, and helpful.
"""

    user_prompt = f"""
Customer Question:
{question}

Retrieved Context:
{context}

Answer briefly using only the retrieved context.
Mention product id if relevant.
"""

    llm_source = "azure_chat"
    llm_error = None

    try:
        llm = get_llm_client()
        answer = llm.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.2,
            max_tokens=400,
        )
    except Exception as exc:
        answer = _fallback_answer_from_context(question, retrieved_chunks)
        llm_source = "context_fallback"
        llm_error = str(exc)

    response = {
        "question": question,
        "answer": answer,
        "sources": retrieved_chunks,
        "retrieval_source": retrieval_source,
        "retrieval_error": retrieval_error,
        "llm_source": llm_source,
        "llm_error": llm_error,
        "agent": "support_agent",
        "created_at": created_at,
    }

    _safe_insert_chat_log(response)
    return response