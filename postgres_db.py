import os
import psycopg
from flask import g


class HybridRow(dict):
    """PostgreSQL row supporting both row['column'] and legacy row[0]."""
    def __getitem__(self, key):
        if isinstance(key, int):
            try:
                return tuple(self.values())[key]
            except IndexError:
                raise IndexError(key) from None
        return super().__getitem__(key)


def hybrid_row_factory(cursor):
    def make_row(values):
        description = cursor.description
        if description is None:
            return tuple(values)
        names = [column.name for column in description]
        return HybridRow(zip(names, values))
    return make_row


def get_database_url():
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL is missing. Configure PostgreSQL in Render.")
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url


def get_db():
    if "db" not in g:
        g.db = psycopg.connect(get_database_url(), row_factory=hybrid_row_factory)
    return g.db


def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        if error is not None:
            db.rollback()
        db.close()
