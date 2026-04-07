from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AlloyDB Semantic Search API"
    app_env: str = "dev"

    gcp_project_id: str = "PROJECT_ID"
    gcp_region: str = "us-central1"
    embedding_model: str = "text-embedding-004"

    # Prefer using AlloyDB language connector in Cloud Run.
    use_alloydb_connector: bool = True
    alloydb_instance_uri: str = "projects/PROJECT_ID/locations/REGION/clusters/CLUSTER/instances/INSTANCE"

    db_user: str = "postgres"
    db_password: str = "postgres"
    db_name: str = "appdb"

    # Optional direct connection URL for local/dev scenarios.
    database_url: str | None = None

    vector_dim: int = 768


settings = Settings()
