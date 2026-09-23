import copy
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import json

from bs4 import BeautifulSoup

import app
import lesson_store
from form_client import client as form_client


class LessonLibraryTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.environment = patch.dict(os.environ, {'LESSON_LIBRARY_DB': str(Path(self.folder.name) / 'library.sqlite3')})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        app.app.config['TESTING'] = True
        self.client = form_client(app.app)
        self.client.get('/builder/')
        self.create_draft()

    def state(self, client=None):
        with (client or self.client).session_transaction() as session:
            return dict(session)

    def token(self, client=None):
        return self.state(client)['builder_csrf']

    def create_draft(self):
        state = self.state()
        response = self.client.post('/builder/', data={
            'csrf': state['builder_csrf'], 'revision': '', 'action': 'create', 'mode': 'scratch',
            'preset': 'prompt1', 'topic': 'Fractions', 'grade': '5', 'students': '25',
            'minutes': '45', 'sessions': '1', 'delivery': 'classroom', 'sections': ['objectives'],
        })
        self.assertEqual(response.status_code, 302)
        state = self.state()
        self.client.post('/builder/', data={
            'csrf': state['builder_csrf'], 'revision': state['builder_draft']['revision'],
            'action': 'save', 'content_objectives': 'Compare fractions.',
        })

    def save(self, name='Fractions lesson'):
        return self.client.post('/library/save', data={'csrf': self.token(), 'name': name})

    def test_save_update_reopen_and_saved_state(self):
        self.assertEqual(self.save().status_code, 302)
        state = self.state()
        plan_id = state['library_plan_id']
        self.assertEqual(self.client.get('/library/').status_code, 200)
        self.assertIn(b'Fractions lesson', self.client.get('/library/').data)
        self.assertIn(b'>Saved<', self.client.get('/builder/').data)

        draft = copy.deepcopy(state['builder_draft'])
        draft['sections'][0]['content'] = 'Compare and explain fractions.'
        with self.client.session_transaction() as session:
            session['builder_draft'] = draft
        self.assertIn(b'Unsaved changes', self.client.get('/builder/').data)
        self.assertEqual(self.save().status_code, 302)
        with lesson_store.connection() as database:
            self.assertEqual(database.execute('SELECT COUNT(*) FROM lesson_versions WHERE plan_id=?', (plan_id,)).fetchone()[0], 2)

        with self.client.session_transaction() as session:
            draft = copy.deepcopy(session['builder_draft'])
            draft['sections'][0]['content'] = 'Temporary change'
            session['builder_draft'] = draft
        self.assertEqual(self.client.post(f'/library/{plan_id}/open', data={'csrf': self.token()}).status_code, 302)
        self.assertEqual(self.state()['builder_draft']['sections'][0]['content'], 'Compare and explain fractions.')

    def test_versions_restore_as_unsaved_and_keep_current_saved_copy(self):
        self.save()
        state = self.state(); plan_id = state['library_plan_id']
        with self.client.session_transaction() as session:
            draft = copy.deepcopy(session['builder_draft'])
            draft['sections'][0]['content'] = 'Second saved version'
            session['builder_draft'] = draft
        self.save()
        versions = lesson_store.list_versions(self.state()['lesson_library_owner'], plan_id)
        oldest = versions[-1]
        self.assertEqual(self.client.post(
            f'/library/{plan_id}/versions/{oldest["id"]}/restore', data={'csrf': self.token()}
        ).status_code, 302)
        self.assertEqual(self.state()['builder_draft']['sections'][0]['content'], 'Compare fractions.')
        self.assertIn(b'Unsaved changes', self.client.get('/builder/').data)
        self.assertEqual(lesson_store.get_plan(self.state()['lesson_library_owner'], plan_id)['draft']['sections'][0]['content'], 'Second saved version')

    def test_rename_delete_and_owner_isolation(self):
        self.save(); state = self.state(); plan_id = state['library_plan_id']
        self.assertEqual(self.client.post(f'/library/{plan_id}/rename', data={'csrf':self.token(),'name':'Renamed lesson'}).status_code,302)
        self.assertIn(b'Renamed lesson',self.client.get(f'/library/{plan_id}').data)

        outsider = form_client(app.app); outsider.get('/builder/')
        self.assertNotIn(b'Renamed lesson', outsider.get('/library/').data)
        self.assertEqual(outsider.get(f'/library/{plan_id}').status_code,404)
        self.assertEqual(outsider.post(f'/library/{plan_id}/open',data={'csrf':self.token(outsider)}).status_code,404)

        self.assertEqual(self.client.post(f'/library/{plan_id}/delete',data={'csrf':self.token()}).status_code,302)
        self.assertNotIn('library_plan_id',self.state())
        self.assertIsNone(lesson_store.get_plan(state['lesson_library_owner'],plan_id))

    @patch('builder.generate_text')
    def test_generation_checkpoints_unsaved_edits_for_recovery(self, model):
        self.save(); state=self.state(); plan_id=state['library_plan_id']; owner=state['lesson_library_owner']
        draft=copy.deepcopy(state['builder_draft'])
        draft['sections'][0]['content']='Unsaved work before generation'
        with self.client.session_transaction() as session:
            session['builder_draft']=draft
        model.return_value=json.dumps({'sections':[{'id':'objectives','content':'Generated objective'}]})
        state=self.state()
        response=self.client.post('/builder/',data={'csrf':state['builder_csrf'],
            'revision':state['builder_draft']['revision'],'action':'generate'})
        self.assertEqual(response.status_code,302)
        versions=lesson_store.list_versions(owner,plan_id)
        checkpoint=next(version for version in versions if version['reason']=='Before AI generation')
        recovered=lesson_store.get_version(owner,plan_id,checkpoint['id'])
        self.assertEqual(recovered['draft']['sections'][0]['content'],'Unsaved work before generation')
        self.assertEqual(lesson_store.get_plan(owner,plan_id)['draft']['sections'][0]['content'],'Compare fractions.')

    def test_library_mutations_require_csrf_and_preserve_saved_data(self):
        self.save(); state=self.state(); plan_id=state['library_plan_id']; owner=state['lesson_library_owner']
        self.assertEqual(self.client.post(f'/library/{plan_id}/rename',data={'name':'Forged'}).status_code,400)
        self.assertEqual(self.client.post(f'/library/{plan_id}/delete').status_code,400)
        plan=lesson_store.get_plan(owner,plan_id)
        self.assertEqual(plan['name'],'Fractions lesson')

    def test_version_limit_and_no_duplicate_unchanged_snapshot(self):
        with patch.object(lesson_store,'MAX_VERSIONS',2):
            self.save(); state=self.state(); plan_id=state['library_plan_id']
            self.save()
            for number in (2,3):
                with self.client.session_transaction() as session:
                    draft = copy.deepcopy(session['builder_draft'])
                    draft['sections'][0]['content']=f'Version {number}'
                    session['builder_draft'] = draft
                self.save()
            self.assertEqual(len(lesson_store.list_versions(self.state()['lesson_library_owner'],plan_id)),2)

    def test_retention_and_clear_cache_preserve_library_access_key(self):
        self.save(); before=self.state()['lesson_library_owner']
        self.client.post('/clear_cache',data={'csrf':self.token()})
        self.assertEqual(self.state()['lesson_library_owner'],before)
        with lesson_store.connection() as database:
            database.execute('UPDATE lesson_plans SET updated_at=0')
        with patch.object(lesson_store,'RETENTION_DAYS',1):
            self.assertEqual(lesson_store.list_plans(before),[])


if __name__ == '__main__':
    unittest.main()
