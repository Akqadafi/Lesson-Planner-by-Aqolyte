from form_client import client as form_client
import copy
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
import unittest
import test_builder
import app
from worksheet_generator import generate_worksheet


class ReliabilityAuditTests(unittest.TestCase):
    setUp = test_builder.BuilderTests.setUp
    state = test_builder.BuilderTests.state
    post = test_builder.BuilderTests.post
    create = test_builder.BuilderTests.create
    def test_failed_save_is_atomic(self):
        self.create(mode='scratch', sections=['worksheet', 'answers'])
        self.post('save', content_worksheet='Original question', content_answers='Original answer')
        before = copy.deepcopy(self.state()['builder_draft'])
        response = self.post('save', content_worksheet='Changed question', content_answers='x' * 30001)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.state()['builder_draft'], before)

    def test_overlapping_generation_and_edit_are_rejected(self):
        self.create(mode='scratch', sections=['worksheet'])
        state = self.state()
        data = {'action': 'generate', 'csrf': state['builder_csrf'], 'revision': state['builder_draft']['revision']}
        entered, release = threading.Event(), threading.Event()
        other = form_client(app.app)
        cookie = self.client.get_cookie(app.app.config['SESSION_COOKIE_NAME'])
        other.set_cookie(app.app.config['SESSION_COOKIE_NAME'], cookie.value)
        def generate(*args, **kwargs):
            entered.set()
            if not release.wait(5):
                raise RuntimeError('Test synchronization timed out')
            return json.dumps({'sections': [{'id': 'worksheet', 'content': 'Generated question'}]})
        with patch('builder.generate_text', side_effect=generate) as model, ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(self.client.post, '/builder/', data=data)
            try:
                self.assertTrue(entered.wait(5))
                self.assertEqual(other.post('/builder/', data=data).status_code, 409)
                self.assertEqual(other.post('/builder/', data={**data, 'action': 'save', 'content_worksheet': 'Racing edit'}).status_code, 409)
                self.assertEqual(other.get('/builder/').status_code, 409)
                with other.get('/static/css/builder.css') as asset:
                    self.assertEqual(asset.status_code, 200)
                    self.assertIn(b'box-sizing', asset.data)
                # Another visitor is not serialized behind this session.
                visitor = form_client(app.app)
                self.assertEqual(visitor.get('/health').status_code, 200)
            finally:
                release.set()
            self.assertEqual(future.result(timeout=5).status_code, 302)
            model.assert_called_once()
        self.assertEqual(self.state()['builder_draft']['sections'][0]['content'], 'Generated question')
        self.assertEqual(other.post('/builder/', data=data).status_code, 400)
        self.assertEqual(other.get('/builder/').status_code, 200)

    def test_metadata_contains_no_configuration(self):
        self.assertEqual(self.client.get('/health').json, {'status': 'ok'})
        self.assertEqual(set(self.client.get('/version').json), {'app', 'version'})

    @patch('worksheet_generator.generate_text')
    def test_invalid_delimiter_never_calls_model(self, model):
        for delimiter in ('x' * 21, 'line\nbreak'):
            with self.assertRaises(ValueError):
                generate_worksheet('Fractions', 3, 'essay', delimiter)
            self.assertEqual(self.client.post('/worksheet', data={'topic': 'Fractions', 'num_questions': '3', 'question_types': 'essay', 'delimiter': delimiter}).status_code, 400)
        model.assert_not_called()

