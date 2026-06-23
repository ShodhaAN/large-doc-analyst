from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000

    # AI Model settings
    embedding_model: str = "all-MiniLM-L6-v2"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    # Folder paths
    upload_dir: Path = Path("data/uploads")
    index_dir: Path = Path("data/indexes")

    # Chunking settings
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k_results: int = 5

    class Config:
        env_file = ".env"  # tells Python to read from .env file

# Create one settings object — used everywhere in the project
settings = Settings()

# Create the folders if they don't exist yet
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.index_dir.mkdir(parents=True, exist_ok=True)