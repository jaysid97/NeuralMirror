import os
from collections.abc import Callable
from typing import Any

from google.cloud.alloydb.connector import Connector, IPTypes
from sqlalchemy.pool import QueuePool


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _build_instance_uri() -> str:
    project_id = _required_env("PROJECT_ID")
    region = _required_env("REGION")
    cluster = _required_env("CLUSTER")
    instance = _required_env("INSTANCE")
    return f"projects/{project_id}/locations/{region}/clusters/{cluster}/instances/{instance}"


def _ip_type_from_env() -> IPTypes:
    ip_type = os.getenv("ALLOYDB_IP_TYPE", "PRIVATE").upper()
    if ip_type == "PUBLIC":
        return IPTypes.PUBLIC
    return IPTypes.PRIVATE


class AlloyDBConnectionPool:
    def __init__(self) -> None:
        self._connector = Connector(refresh_strategy="lazy")
        self._instance_uri = _build_instance_uri()
        self._db_user = _required_env("DB_USER")
        self._db_name = _required_env("DB_NAME")
        self._db_password = os.getenv("DB_PASSWORD")
        self._ip_type = _ip_type_from_env()

        pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
        max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "2"))
        timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))

        self._pool = QueuePool(
            creator=self._connection_creator(),
            pool_size=pool_size,
            max_overflow=max_overflow,
            timeout=timeout,
            pre_ping=True,
        )

    def _connection_creator(self) -> Callable[[], Any]:
        def _connect() -> Any:
            return self._connector.connect(
                self._instance_uri,
                "pg8000",
                user=self._db_user,
                password=self._db_password,
                db=self._db_name,
                ip_type=self._ip_type,
            )

        return _connect

    def get_connection(self) -> Any:
        # Always close the returned connection to return it to the pool.
        return self._pool.connect()

    def close(self) -> None:
        self._pool.dispose()
        self._connector.close()


_pool = AlloyDBConnectionPool()


def get_connection() -> Any:
    return _pool.get_connection()
