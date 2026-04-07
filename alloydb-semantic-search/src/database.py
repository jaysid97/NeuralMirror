from collections.abc import Generator

from google.cloud.alloydb.connector import Connector, IPTypes
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .config import settings


_connector: Connector | None = None
_engine: Engine | None = None
SessionLocal: sessionmaker[Session] | None = None


def _build_engine() -> Engine:
	if settings.use_alloydb_connector:
		global _connector
		_connector = Connector(refresh_strategy="lazy")

		def getconn():
			return _connector.connect(
				settings.alloydb_instance_uri,
				"pg8000",
				user=settings.db_user,
				password=settings.db_password,
				db=settings.db_name,
				ip_type=IPTypes.PRIVATE,
			)

		return create_engine(
			"postgresql+pg8000://",
			creator=getconn,
			pool_pre_ping=True,
			pool_size=5,
			max_overflow=2,
		)

	if not settings.database_url:
		raise ValueError("DATABASE_URL must be set when USE_ALLOYDB_CONNECTOR is false")

	return create_engine(settings.database_url, pool_pre_ping=True)


def init_db() -> None:
	global _engine, SessionLocal
	if _engine is None:
		_engine = _build_engine()
		SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
	if SessionLocal is None:
		init_db()
	if SessionLocal is None:
		raise RuntimeError("Database session factory was not initialized")

	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()


def shutdown_db() -> None:
	global _connector, _engine
	if _engine is not None:
		_engine.dispose()
		_engine = None
	if _connector is not None:
		_connector.close()
		_connector = None
