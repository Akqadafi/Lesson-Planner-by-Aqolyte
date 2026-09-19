import os
os.environ.setdefault('FLASK_SECRET_KEY','test-only-secret')
import unittest
from unittest.mock import patch
from bs4 import BeautifulSoup
import app
from form_client import client
from worksheet_generator import validate_type

class TypeAndRecoveryTests(unittest.TestCase):
    def test_type_contracts(self):
        valid=[('multiple_choice','Choose\nA. One\nB. Two\nC. Three\nD. Four','B. Explanation'),('true_false','Statement','False: Explanation'),('matching','L1: One\nL2: Two\nR1: First\nR2: Second','L1=R2\nL2=R1'),('Fill in the Blanks','The ___ is blue.','Sky')]
        for kind,question,answer in valid:
            validate_type({'question':question,'answer':answer},kind)
        invalid=[('multiple_choice','A. One\nB. One\nC. Three\nD. Four','A. Explanation'),('multiple_choice',valid[0][1],'E. Wrong'),('true_false','Statement','Maybe'),('matching',valid[2][1],'L1=R1\nL2=R1'),('matching',valid[2][1],'L1=R9\nL2=R2'),('Fill in the Blanks','No blank','Answer')]
        for kind,question,answer in invalid:
            with self.assertRaises(ValueError):validate_type({'question':question,'answer':answer},kind)

    @patch('app.generate_worksheet')
    def test_worksheet_errors_preserve_fields_and_escape_html(self, model):
        browser=client(app.app)
        response=browser.post('/worksheet',data={'topic':'<script>alert(1)</script>','grade_level':'5','num_questions':'0','question_types':'essay','delimiter':'###'})
        self.assertEqual(response.status_code,400)
        soup=BeautifulSoup(response.data,'html.parser')
        self.assertEqual(soup.select_one('[name=topic]')['value'],'<script>alert(1)</script>')
        self.assertEqual(soup.select_one('[name=num_questions]')['value'],'0')
        self.assertEqual(soup.select_one('[name=question_types] option[selected]')['value'],'essay')
        self.assertTrue(soup.select_one('[role=alert]'))
        self.assertNotIn(b'<script>alert(1)</script>',response.data)
        model.assert_not_called()

    def test_lesson_error_preserves_teacher_described_context(self):
        browser=client(app.app)
        with browser.session_transaction() as session:session['prompt']='prompt3'
        response=browser.post('/home',data={'topic':'Plants','grade_level':'99','number_of_students':'25','number_of_words':'500','prior_knowledge':'Students know plant parts.','learner_supports':'Use labeled diagrams.'})
        self.assertEqual(response.status_code,400)
        soup=BeautifulSoup(response.data,'html.parser')
        self.assertEqual(soup.select_one('[name=topic]')['value'],'Plants')
        self.assertEqual(soup.select_one('[name=grade_level]')['value'],'99')
        self.assertEqual(soup.select_one('[name=prior_knowledge]').text,'Students know plant parts.')
        self.assertEqual(soup.select_one('[name=learner_supports]').text,'Use labeled diagrams.')
