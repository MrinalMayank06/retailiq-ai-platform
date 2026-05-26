from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RetailIQ AI Platform"
    app_env: str = "local"
    app_host: str = "127.0.0.1"
    app_port: int = 8000

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "retailiq"

    # Azure chat / generation settings
    azure_openai_api_key: str = ""
    azure_openai_base_url: str = ""
    azure_openai_model: str = ""
    azure_openai_chat_model: str = ""

    # Azure embedding settings
    azure_openai_embedding_api_key: str = ""
    azure_openai_embedding_base_url: str = ""
    azure_openai_embedding_model: str = "text-embedding-3-large"
    azure_openai_embedding_deployment: str = "text-embedding-3-large"
    azure_openai_embedding_api_version: str = "2024-02-01"

    # Final active local vector cache artifact
    product_knowledge_store_path: str = "artifacts/knowledge/product_knowledge_embeddings.json"

    # Token / retrieval controls
    embedding_chunk_size_words: int = 80
    embedding_chunk_overlap_words: int = 10
    embedding_max_text_chars: int = 1200
    embedding_batch_size: int = 16
    rag_top_k: int = 3
    rag_min_score: float = 0.35

    # Legacy compatibility only.
    # Final runtime uses Azure embeddings + local JSON vector store.
    # These fields prevent old Chroma-related paths from crashing if accidentally referenced.
    chroma_collection_name: str = "retailiq_product_knowledge"
    chroma_persist_dir: str = "artifacts/knowledge/chroma_db"
    local_embedding_model: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()