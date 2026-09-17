import unittest
from unittest.mock import patch
from bs4 import BeautifulSoup
import os
os.environ.setdefault("FLASK_SECRET_KEY", "test-only-secret")
os.environ.setdefault("OPENAI_API_KEY", "mock-only")
import app

class LegacySecurityTests(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()
    def token(self):
        page = self.client.get('/worksheet')
        return BeautifulSoup(page.data, 'html.parser').select_one('input[name=csrf]')['value']

    @patch('app.generate_worksheet', return_value='Questions\nAnswers: key')
    def test_get_never_generates_and_post_redirects(self, model):
        token = self.token()
        with self.client.session_transaction() as s:
            s['worksheet_data'] = {'topic':'Fractions','num_questions':2,'question_types':'essay','formatting_delimiter':'----'}
        for _ in range(2):
            page = self.client.get('/output')
            self.assertEqual(page.status_code, 200)
            self.assertIn(b'Generate draft', page.data)
        model.assert_not_called()
        self.assertEqual(self.client.post('/output', data={'csrf':token}).status_code,400)
        model.assert_not_called()
        response = self.client.post('/output', data={'csrf':token,'generate':'1'})
        self.assertEqual(response.status_code,302)
        self.assertEqual(self.client.get('/output').status_code,200)
        self.client.post('/output',data={'csrf':token,'generate':'1'})
        model.assert_called_once()

    @patch('app.generate_worksheet')
    @patch('app.lesson_planner.generate_lesson_plan')
    def test_all_legacy_mutations_reject_missing_wrong_and_foreign_tokens(self, lesson, worksheet):
        self.token()
        foreign=app.app.test_client()
        foreign_token=BeautifulSoup(foreign.get('/worksheet').data,'html.parser').select_one('input[name=csrf]')['value']
        with self.client.session_transaction() as s:
            s['content']='Saved';s['content_type']='Worksheet'
            before=dict(s)
        for path in ('/home','/worksheet','/prompt_selection','/redirect_choice','/output','/clear_cache'):
            for token in ('','wrong',foreign_token):
                self.assertEqual(self.client.post(path,data={'csrf':token,'generate':'1','download_word':'1','restore_previous':'1'}).status_code,400)
                with self.client.session_transaction() as s:self.assertEqual(dict(s),before)
        lesson.assert_not_called();worksheet.assert_not_called()
        self.assertEqual(self.client.get('/clear_cache').status_code,405)
        with self.client.session_transaction() as s:self.assertEqual(dict(s),before)
        self.assertEqual(self.client.post('/clear_cache',data={'csrf':before['builder_csrf']}).status_code,302)
        with self.client.session_transaction() as s:self.assertNotIn('content',s)

    def test_rendered_legacy_forms_have_tokens(self):
        self.token()
        for preset in range(6):
            with self.client.session_transaction() as s:s['prompt']='prompt'+str(preset)
            soup=BeautifulSoup(self.client.get('/home').data,'html.parser')
            forms=soup.select('form')
            self.assertTrue(forms)
            for form in forms:self.assertTrue(form.select_one('input[name=csrf]')['value'])
