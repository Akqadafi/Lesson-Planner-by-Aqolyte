"""Track which lesson inputs a student handout depends on."""
import hashlib
import json


def _digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    ).hexdigest()


def _source(draft, source_id):
    return next((row for row in draft.get('sections', []) if row.get('id') == source_id), None)


def snapshot(draft, source_id):
    """Return the lesson inputs that can materially affect a handout."""
    source = _source(draft, source_id)
    if source is None:
        raise ValueError('The source lesson section is no longer available.')
    config = draft.get('config', {})
    return {
        'source_id': source_id,
        'source_content_hash': _digest(source.get('content', '')),
        'context_hash': _digest({
            'topic': config.get('topic', ''),
            'grade': config.get('grade', ''),
            'objectives': config.get('objectives', ''),
            'sources': config.get('sources', ''),
        }),
    }


def status(draft, handout, legacy_fingerprint=None):
    """Describe whether a handout still matches its relevant lesson inputs."""
    if not handout:
        return None
    source_id = handout.get('source')
    source = _source(draft, source_id)
    if source is None:
        return {
            'stale': True,
            'can_confirm': False,
            'reasons': ['Its source lesson section was removed. Create a new handout from an available section.'],
            'summary': 'its source lesson section was removed',
        }
    stored = handout.get('dependencies')
    if isinstance(stored, dict):
        current = snapshot(draft, source_id)
        reasons = []
        if stored.get('source_id') != source_id or stored.get('source_content_hash') != current['source_content_hash']:
            reasons.append('The source lesson section changed.')
        if stored.get('context_hash') != current['context_hash']:
            reasons.append('The lesson topic, grade, objectives, or source excerpts changed.')
        return {
            'stale': bool(reasons),
            'can_confirm': True,
            'reasons': reasons,
            'summary': ' and '.join(reason[:-1].lower() for reason in reasons) if reasons else 'current',
        }
    stale = legacy_fingerprint is None or handout.get('source_hash') != legacy_fingerprint(draft)
    return {
        'stale': stale,
        'can_confirm': True,
        'reasons': ['This older handout needs one alignment review before source-specific tracking can begin.'] if stale else [],
        'summary': 'this older handout needs an alignment review' if stale else 'current',
    }
