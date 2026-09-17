"""Atomic generation-attempt quotas for processes sharing one local SQLite file."""
from contextlib import closing
import hashlib
import os
from pathlib import Path
import sqlite3
import time
from flask import has_request_context, session

class GenerationLimitError(RuntimeError):
    pass

def reserve_attempt():
    try:
        hourly = int(os.getenv('GENERATION_SESSION_HOURLY', '10'))
        daily = int(os.getenv('GENERATION_GLOBAL_DAILY', '100'))
        if hourly < 1 or daily < 1:
            raise ValueError()
        path = Path(os.getenv('GENERATION_LIMIT_DB', str(Path(__file__).parent / 'instance' / 'generation-limits.sqlite3')))
        path.parent.mkdir(parents=True, exist_ok=True)
        identity = str(getattr(session, 'sid', 'unknown')) if has_request_context() else 'local-script'
        identity = hashlib.sha256(identity.encode()).hexdigest()
        now = int(time.time())
        windows = [('global', now // 86400, daily), ('session:' + identity, now // 3600, hourly)]
        with closing(sqlite3.connect(path, timeout=5)) as db, db:
            db.execute('CREATE TABLE IF NOT EXISTS attempts (scope TEXT, window INTEGER, count INTEGER NOT NULL, PRIMARY KEY(scope, window))')
            db.execute('BEGIN IMMEDIATE')
            for scope, window, limit in windows:
                row = db.execute('SELECT count FROM attempts WHERE scope=? AND window=?', (scope, window)).fetchone()
                if row and row[0] >= limit:
                    label = 'daily app' if scope == 'global' else 'hourly browser-session'
                    raise GenerationLimitError(f'The {label} generation limit has been reached. Try after the limit resets; editing and downloads remain available.')
            for scope, window, limit in windows:
                db.execute('INSERT INTO attempts VALUES (?, ?, 1) ON CONFLICT(scope,window) DO UPDATE SET count=count+1', (scope, window))
            db.execute("DELETE FROM attempts WHERE (scope='global' AND window<?) OR (scope!='global' AND window<?)", (now // 86400 - 1, now // 3600 - 1))
    except GenerationLimitError:
        raise
    except (ValueError, OSError, sqlite3.Error):
        raise GenerationLimitError('Generation limits could not be checked. Generation is paused; editing and downloads remain available.') from None
