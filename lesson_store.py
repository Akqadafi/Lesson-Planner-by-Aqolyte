'''Anonymous local lesson library with bounded history and owner isolation.'''
import copy
import hashlib
import json
import os
import secrets
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path


RETENTION_DAYS = 90
MAX_PLANS = 25
MAX_VERSIONS = 20


def _path():
    configured = os.getenv('LESSON_LIBRARY_DB')
    path = Path(configured) if configured else Path(__file__).resolve().parent / 'instance' / 'lesson_library.sqlite3'
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _connect():
    database = sqlite3.connect(_path(), timeout=10)
    database.row_factory = sqlite3.Row
    database.execute('PRAGMA foreign_keys = ON')
    database.execute('PRAGMA journal_mode = WAL')
    database.executescript('''
        CREATE TABLE IF NOT EXISTS lesson_plans (
            id TEXT PRIMARY KEY,
            owner_id TEXT NOT NULL,
            name TEXT NOT NULL,
            draft_json TEXT NOT NULL,
            draft_digest TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS lesson_plans_owner_updated
            ON lesson_plans(owner_id, updated_at DESC);
        CREATE TABLE IF NOT EXISTS lesson_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id TEXT NOT NULL,
            owner_id TEXT NOT NULL,
            draft_json TEXT NOT NULL,
            draft_digest TEXT NOT NULL,
            reason TEXT NOT NULL DEFAULT 'Saved version',
            created_at INTEGER NOT NULL,
            FOREIGN KEY(plan_id) REFERENCES lesson_plans(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS lesson_versions_plan_created
            ON lesson_versions(plan_id, created_at DESC, id DESC);
    ''')
    columns = {row['name'] for row in database.execute('PRAGMA table_info(lesson_versions)')}
    if 'reason' not in columns:
        database.execute("ALTER TABLE lesson_versions ADD COLUMN reason TEXT NOT NULL DEFAULT 'Saved version'")
    return database


@contextmanager
def connection():
    database = _connect()
    try:
        yield database
        database.commit()
    except Exception:
        database.rollback()
        raise
    finally:
        database.close()


def _stored_draft(draft):
    value = copy.deepcopy(draft)
    value.pop('revision', None)
    return value


def serialize_draft(draft):
    if not isinstance(draft, dict) or not isinstance(draft.get('config'), dict) or not isinstance(draft.get('sections'), list):
        raise ValueError('There is no valid lesson draft to save.')
    return json.dumps(_stored_draft(draft), sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def draft_digest(draft):
    return hashlib.sha256(serialize_draft(draft).encode('utf-8')).hexdigest()


def _name(value):
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > 120:
        raise ValueError('Lesson name must contain 1–120 characters.')
    return value.strip()


def _label(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%b %d, %Y at %I:%M %p')


def cleanup_expired(now=None):
    now = int(now or time.time())
    cutoff = now - RETENTION_DAYS * 86400
    with connection() as database:
        database.execute('DELETE FROM lesson_plans WHERE updated_at < ?', (cutoff,))


def list_plans(owner_id):
    cleanup_expired()
    with connection() as database:
        rows = database.execute(
            'SELECT id, name, created_at, updated_at FROM lesson_plans WHERE owner_id = ? ORDER BY updated_at DESC',
            (owner_id,),
        ).fetchall()
    return [dict(row, created_label=_label(row['created_at']), updated_label=_label(row['updated_at'])) for row in rows]


def get_plan(owner_id, plan_id):
    cleanup_expired()
    with connection() as database:
        row = database.execute(
            'SELECT * FROM lesson_plans WHERE id = ? AND owner_id = ?', (plan_id, owner_id)
        ).fetchone()
    if row is None:
        return None
    value = dict(row)
    value['draft'] = json.loads(value.pop('draft_json'))
    value['created_label'] = _label(value['created_at'])
    value['updated_label'] = _label(value['updated_at'])
    return value


def list_versions(owner_id, plan_id):
    with connection() as database:
        rows = database.execute(
            '''SELECT id, created_at, draft_digest, reason FROM lesson_versions
               WHERE plan_id = ? AND owner_id = ? ORDER BY created_at DESC, id DESC''',
            (plan_id, owner_id),
        ).fetchall()
    return [dict(row, created_label=_label(row['created_at'])) for row in rows]


def save_plan(owner_id, draft, name, plan_id=None):
    cleanup_expired()
    name = _name(name)
    payload = serialize_draft(draft)
    digest = hashlib.sha256(payload.encode('utf-8')).hexdigest()
    now = int(time.time())
    with connection() as database:
        database.execute('BEGIN IMMEDIATE')
        if plan_id:
            current = database.execute(
                'SELECT draft_digest FROM lesson_plans WHERE id = ? AND owner_id = ?', (plan_id, owner_id)
            ).fetchone()
        else:
            current = None
        if plan_id and current is None:
            raise ValueError('That saved lesson is unavailable in this browser library.')
        if current is None:
            count = database.execute('SELECT COUNT(*) FROM lesson_plans WHERE owner_id = ?', (owner_id,)).fetchone()[0]
            if count >= MAX_PLANS:
                raise ValueError(f'This browser library is limited to {MAX_PLANS} lessons. Delete one before saving another.')
            plan_id = secrets.token_urlsafe(18)
            database.execute(
                '''INSERT INTO lesson_plans
                   (id, owner_id, name, draft_json, draft_digest, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (plan_id, owner_id, name, payload, digest, now, now),
            )
            changed = True
        else:
            changed = current['draft_digest'] != digest
            database.execute(
                '''UPDATE lesson_plans SET name = ?, draft_json = ?, draft_digest = ?, updated_at = ?
                   WHERE id = ? AND owner_id = ?''',
                (name, payload, digest, now, plan_id, owner_id),
            )
        if changed:
            database.execute(
                '''INSERT INTO lesson_versions
                   (plan_id, owner_id, draft_json, draft_digest, reason, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (plan_id, owner_id, payload, digest, 'Saved version', now),
            )
            database.execute(
                '''DELETE FROM lesson_versions WHERE plan_id = ? AND owner_id = ? AND id NOT IN (
                       SELECT id FROM lesson_versions WHERE plan_id = ? AND owner_id = ?
                       ORDER BY created_at DESC, id DESC LIMIT ?
                   )''',
                (plan_id, owner_id, plan_id, owner_id, MAX_VERSIONS),
            )
    return {'id': plan_id, 'name': name, 'digest': digest, 'changed': changed}


def checkpoint_plan(owner_id, plan_id, draft, reason='Before AI generation'):
    payload = serialize_draft(draft)
    digest = hashlib.sha256(payload.encode('utf-8')).hexdigest()
    now = int(time.time())
    with connection() as database:
        database.execute('BEGIN IMMEDIATE')
        plan = database.execute(
            'SELECT 1 FROM lesson_plans WHERE id = ? AND owner_id = ?', (plan_id, owner_id)
        ).fetchone()
        if plan is None:
            return False
        latest = database.execute(
            '''SELECT draft_digest FROM lesson_versions WHERE plan_id = ? AND owner_id = ?
               ORDER BY created_at DESC, id DESC LIMIT 1''',
            (plan_id, owner_id),
        ).fetchone()
        if latest is not None and latest['draft_digest'] == digest:
            return False
        database.execute(
            '''INSERT INTO lesson_versions
               (plan_id, owner_id, draft_json, draft_digest, reason, created_at)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (plan_id, owner_id, payload, digest, reason, now),
        )
        database.execute(
            '''DELETE FROM lesson_versions WHERE plan_id = ? AND owner_id = ? AND id NOT IN (
                   SELECT id FROM lesson_versions WHERE plan_id = ? AND owner_id = ?
                   ORDER BY created_at DESC, id DESC LIMIT ?
               )''',
            (plan_id, owner_id, plan_id, owner_id, MAX_VERSIONS),
        )
    return True


def rename_plan(owner_id, plan_id, name):
    name = _name(name)
    with connection() as database:
        cursor = database.execute(
            'UPDATE lesson_plans SET name = ?, updated_at = ? WHERE id = ? AND owner_id = ?',
            (name, int(time.time()), plan_id, owner_id),
        )
    if cursor.rowcount != 1:
        raise ValueError('That saved lesson is unavailable in this browser library.')
    return name


def delete_plan(owner_id, plan_id):
    with connection() as database:
        cursor = database.execute('DELETE FROM lesson_plans WHERE id = ? AND owner_id = ?', (plan_id, owner_id))
    if cursor.rowcount != 1:
        raise ValueError('That saved lesson is unavailable in this browser library.')


def get_version(owner_id, plan_id, version_id):
    with connection() as database:
        row = database.execute(
            '''SELECT draft_json, draft_digest FROM lesson_versions
               WHERE id = ? AND plan_id = ? AND owner_id = ?''',
            (version_id, plan_id, owner_id),
        ).fetchone()
    if row is None:
        return None
    return {'draft': json.loads(row['draft_json']), 'digest': row['draft_digest']}
