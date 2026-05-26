from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.agents.shared.llm_client import get_embedding_client
from src.common.settings import get_settings


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


class ProductKnowledgeStore:
    def __init__(self):
        settings = get_settings()

        self.settings = settings
        self.product_file = RAW_DATA_DIR / "product_details.csv"

        store_path = Path(settings.product_knowledge_store_path)
        if not store_path.is_absolute():
            store_path = PROJECT_ROOT / store_path

        store_path.parent.mkdir(parents=True, exist_ok=True)

        self.store_path = store_path
        self.embedding_model = settings.azure_openai_embedding_model
        self.chunk_size_words = max(20, settings.embedding_chunk_size_words)
        self.chunk_overlap_words = max(0, settings.embedding_chunk_overlap_words)
        self.min_score = settings.rag_min_score

    @property
    def embedding_client(self):
        return get_embedding_client()

    def status(self) -> dict[str, Any]:
        return {
            "product_file": str(self.product_file),
            "product_file_exists": self.product_file.exists(),
            "store_path": str(self.store_path),
            "store_path_exists": self.store_path.exists(),
            "embedding_model": self.embedding_model,
            "backend": "azure_embedding_local_json_store",
            "retrieval_backend": "local_json_vector_store",
        }

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = df.columns.str.strip().str.lower()
        return df

    def _safe_value(self, row, column: str, default: str = "") -> str:
        if column in row.index and pd.notna(row[column]):
            value = str(row[column]).strip()
            if value:
                return value
        return default

    def _chunk_text(self, text: str) -> list[str]:
        words = text.split()

        if not words:
            return []

        if len(words) <= self.chunk_size_words:
            return [text]

        chunks: list[str] = []
        start = 0

        while start < len(words):
            end = start + self.chunk_size_words
            chunk = " ".join(words[start:end]).strip()

            if chunk:
                chunks.append(chunk)

            if end >= len(words):
                break

            next_start = end - self.chunk_overlap_words

            if next_start <= start:
                next_start = end

            start = next_start

        return chunks

    def _build_compact_knowledge_text(self, row) -> str:
        product_id = self._safe_value(row, "product_id", "unknown")
        product_name = self._safe_value(row, "product_name", product_id)
        category = self._safe_value(row, "category", "general")
        brand = self._safe_value(row, "brand", "generic")
        description = self._safe_value(row, "product_description")
        return_policy = self._safe_value(row, "return_policy")
        faq_answer = self._safe_value(row, "faq_answer")
        review = self._safe_value(row, "review")

        lines = [
            f"Product ID: {product_id}",
            f"Product Name: {product_name}",
            f"Category: {category}",
            f"Brand: {brand}",
        ]

        if description:
            lines.append(f"Description: {description}")

        if return_policy:
            lines.append(f"Return Policy: {return_policy}")

        if faq_answer:
            lines.append(f"FAQ Answer: {faq_answer}")

        if review:
            lines.append(f"Customer Review: {review}")

        return "\n".join(lines).strip()

    def _build_chunks(self) -> list[dict[str, Any]]:
        if not self.product_file.exists():
            raise FileNotFoundError(f"Product file not found: {self.product_file}")

        df = pd.read_csv(self.product_file)
        df = self._normalize_columns(df)

        chunks: list[dict[str, Any]] = []

        for _, row in df.iterrows():
            product_id = self._safe_value(row, "product_id", "unknown")
            product_name = self._safe_value(row, "product_name", product_id)
            category = self._safe_value(row, "category", "general")
            brand = self._safe_value(row, "brand", "generic")

            knowledge_text = self._build_compact_knowledge_text(row)

            for chunk_index, chunk in enumerate(self._chunk_text(knowledge_text)):
                chunks.append(
                    {
                        "id": f"{product_id}-{chunk_index}",
                        "product_id": product_id,
                        "product_name": product_name,
                        "category": category,
                        "brand": brand,
                        "content": chunk,
                    }
                )

        return chunks

    def _load_store(self) -> list[dict[str, Any]]:
        if not self.store_path.exists():
            raise FileNotFoundError(
                f"Vector store not found at {self.store_path}. Run python -m scripts.build_chroma_store first."
            )

        with open(self.store_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, dict) and isinstance(data.get("records"), list):
            return data["records"]

        if isinstance(data, list):
            return data

        raise ValueError("Invalid vector store format. Expected list or {'records': [...]}.")

    def _cosine_similarity(self, vector_a: list[float], vector_b: list[float]) -> float:
        if not vector_a or not vector_b:
            return 0.0

        a = np.array(vector_a, dtype=float)
        b = np.array(vector_b, dtype=float)

        if a.shape != b.shape:
            return 0.0

        a_norm = np.linalg.norm(a)
        b_norm = np.linalg.norm(b)

        if a_norm == 0 or b_norm == 0:
            return 0.0

        return float(np.dot(a, b) / (a_norm * b_norm))

    def build_store(self) -> dict[str, Any]:
        chunks = self._build_chunks()

        if not chunks:
            with open(self.store_path, "w", encoding="utf-8") as file:
                json.dump([], file, ensure_ascii=False, indent=2)

            return {
                "chunks": 0,
                "store_path": str(self.store_path),
                "embedding_model": self.embedding_model,
                "backend": "azure_embedding_local_json_store",
                "retrieval_backend": "local_json_vector_store",
            }

        documents = [chunk["content"] for chunk in chunks]
        embeddings = self.embedding_client.embed_texts(documents)

        if len(embeddings) != len(chunks):
            raise RuntimeError(
                f"Embedding count mismatch. chunks={len(chunks)}, embeddings={len(embeddings)}"
            )

        records: list[dict[str, Any]] = []

        for chunk, embedding in zip(chunks, embeddings):
            record = chunk.copy()
            record["embedding"] = embedding
            records.append(record)

        temp_path = self.store_path.with_suffix(self.store_path.suffix + ".tmp")

        with open(temp_path, "w", encoding="utf-8") as file:
            json.dump(records, file, ensure_ascii=False, indent=2)

        temp_path.replace(self.store_path)

        return {
            "chunks": len(records),
            "store_path": str(self.store_path),
            "embedding_model": self.embedding_model,
            "backend": "azure_embedding_local_json_store",
            "retrieval_backend": "local_json_vector_store",
        }

    def search(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        query = str(query).strip()

        if not query:
            return []

        top_k = max(1, int(top_k or 3))

        store_records = self._load_store()

        if not store_records:
            return []

        query_embeddings = self.embedding_client.embed_texts([query])

        if not query_embeddings:
            return []

        query_embedding = query_embeddings[0]
        scored_results: list[dict[str, Any]] = []

        for record in store_records:
            record_embedding = record.get("embedding", [])
            score = self._cosine_similarity(query_embedding, record_embedding)

            result = {
                "id": record.get("id"),
                "product_id": record.get("product_id"),
                "product_name": record.get("product_name"),
                "category": record.get("category"),
                "brand": record.get("brand"),
                "content": record.get("content"),
                "score": round(score, 4),
                "below_min_score": score < self.min_score,
            }

            scored_results.append(result)

        scored_results.sort(key=lambda item: item["score"], reverse=True)

        filtered_results = [
            item
            for item in scored_results
            if item["score"] >= self.min_score
        ]

        if filtered_results:
            return filtered_results[:top_k]

        return scored_results[:top_k]


def rebuild_product_knowledge_store() -> dict[str, Any]:
    store = ProductKnowledgeStore()
    return store.build_store()