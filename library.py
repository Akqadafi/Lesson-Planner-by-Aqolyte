"""Routes for the browser-scoped saved lesson library."""
import copy
import secrets
from flask import Blueprint, redirect, render_template, request, session, url_for

from builder import csrf
from lesson_store import (
    MAX_PLANS, MAX_VERSIONS, RETENTION_DAYS, delete_plan, get_plan,
    get_version, list_plans, list_versions, rename_plan, save_plan,
)


bp = Blueprint('library', __name__, url_prefix='/library')


def owner_id():
    if 'lesson_library_owner' not in session:
        session['lesson_library_owner'] = secrets.token_urlsafe(32)
    session.permanent = True
    return session['lesson_library_owner']


def _activate(plan, draft, saved_digest):
    draft = copy.deepcopy(draft)
    draft['revision'] = secrets.token_hex(12)
    session['builder_draft'] = draft
    session['library_plan_id'] = plan['id']
    session['library_plan_name'] = plan['name']
    session['library_saved_digest'] = saved_digest


def _page(error=None, status=200, selected=None):
    owner = owner_id()
    plans = list_plans(owner)
    plan = get_plan(owner, selected) if selected else None
    if selected and plan is None:
        return render_template('library.html', plans=plans, selected=None, versions=[], token=csrf(),
            error='That saved lesson is unavailable in this browser library.', retention_days=RETENTION_DAYS,
            max_plans=MAX_PLANS, max_versions=MAX_VERSIONS), 404
    versions = list_versions(owner, plan['id']) if plan else []
    return render_template('library.html', plans=plans, selected=plan, versions=versions, token=csrf(),
        error=error, retention_days=RETENTION_DAYS, max_plans=MAX_PLANS, max_versions=MAX_VERSIONS), status


@bp.get('/')
def index():
    return _page()


@bp.get('/<plan_id>')
def detail(plan_id):
    return _page(selected=plan_id)


@bp.post('/save')
def save():
    draft = session.get('builder_draft')
    if not draft:
        return _page('Create or open a lesson before saving it.', 400)
    current = session.get('library_plan_id')
    name = request.form.get('name') or session.get('library_plan_name') or draft.get('config', {}).get('topic')
    try:
        result = save_plan(owner_id(), draft, name, current)
    except ValueError as exc:
        return _page(str(exc), 400, current)
    session['library_plan_id'] = result['id']
    session['library_plan_name'] = result['name']
    session['library_saved_digest'] = result['digest']
    return redirect(url_for('builder.index'))


@bp.post('/<plan_id>/open')
def open_plan(plan_id):
    plan = get_plan(owner_id(), plan_id)
    if plan is None:
        return _page('That saved lesson is unavailable in this browser library.', 404)
    _activate(plan, plan['draft'], plan['draft_digest'])
    return redirect(url_for('builder.index'))


@bp.post('/<plan_id>/rename')
def rename(plan_id):
    try:
        name = rename_plan(owner_id(), plan_id, request.form.get('name'))
    except ValueError as exc:
        return _page(str(exc), 400, plan_id)
    if session.get('library_plan_id') == plan_id:
        session['library_plan_name'] = name
    return redirect(url_for('library.detail', plan_id=plan_id))


@bp.post('/<plan_id>/delete')
def delete(plan_id):
    try:
        delete_plan(owner_id(), plan_id)
    except ValueError as exc:
        return _page(str(exc), 404)
    if session.get('library_plan_id') == plan_id:
        for key in ('library_plan_id', 'library_plan_name', 'library_saved_digest'):
            session.pop(key, None)
    return redirect(url_for('library.index'))


@bp.post('/<plan_id>/versions/<int:version_id>/restore')
def restore(plan_id, version_id):
    owner = owner_id()
    plan = get_plan(owner, plan_id)
    version = get_version(owner, plan_id, version_id)
    if plan is None or version is None:
        return _page('That saved version is unavailable in this browser library.', 404, plan_id)
    _activate(plan, version['draft'], plan['draft_digest'])
    return redirect(url_for('builder.index'))
