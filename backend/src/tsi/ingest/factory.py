"""Wire a real CfbdClient from settings (disk cache + ingest_log ledger)."""

from sqlalchemy.orm import Session, sessionmaker

from tsi.config import Settings
from tsi.ingest.cache import DiskCache
from tsi.ingest.client import CfbdClient
from tsi.ingest.ledger import DbCallLedger


def make_cfbd_client(settings: Settings, session_factory: sessionmaker[Session]) -> CfbdClient:
    return CfbdClient(
        api_key=settings.require_cfbd_key(),
        cache=DiskCache(settings.tsi_cache_dir),
        ledger=DbCallLedger(session_factory),
        monthly_budget=settings.cfbd_monthly_call_budget,
    )
