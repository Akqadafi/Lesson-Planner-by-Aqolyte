import copy
import json
import unittest
from unittest.mock import patch
import lesson_planner
import worksheet_generator as worksheets
from test_lesson_planner import SAMPLE_INPUT

class OutputContractTests(unittest.TestCase):
    @patch('worksheet_generator.generate_text')
    def test_rejects_incomplete_duplicate_and_malformed_answers(self, model):
        valid={'questions':[{'id':1,'question':'First?','answer':'First answer'},{'id':2,'question':'Second?','answer':'Second answer'}]}
        bad=[{}, {'questions':[]}, {'questions':valid['questions'][:1]}, {'questions':valid['questions']+[valid['questions'][0]]}]
        for field,value in [('id',1),('id',True),('answer',' '),('answer',None),('question',''),('question','x'*4001)]:
            payload=copy.deepcopy(valid);payload['questions'][1][field]=value;bad.append(payload)
        payload=copy.deepcopy(valid);del payload['questions'][1]['answer'];bad.append(payload)
        for payload in bad:
            model.return_value=json.dumps(payload)
            with self.assertRaises(worksheets.WorksheetFormatError):worksheets.generate_worksheet('Fractions',2,'essay')
        model.return_value='Answers only'
        with self.assertRaises(worksheets.WorksheetFormatError):worksheets.generate_worksheet('Fractions',2,'essay')
        model.return_value=json.dumps(valid)
        output=worksheets.generate_worksheet('Fractions',2,'essay','----')
        self.assertEqual(output,'1. First?\n----\n2. Second?\n\nAnswers:\n1. First answer\n----\n2. Second answer')

    @patch('lesson_planner.generate_text')
    def test_invalid_legacy_context_never_calls_ai(self, model):
        for changes in ({'state':'x'*301},{'prior_knowledge':'x'*4001},{'learner_supports':'x'*4001},{'prompt':'bad'},{'prompt':'prompt1','lesson_type':' '},{'topic':None}):
            with self.assertRaises(ValueError):lesson_planner.generate_lesson_plan(dict(SAMPLE_INPUT,**changes))
        model.assert_not_called()

    @patch('worksheet_generator.generate_text', return_value='{"questions": []}')
    def test_malformed_worksheet_keeps_inputs_and_other_draft(self, model):
        import os
        os.environ.setdefault('FLASK_SECRET_KEY', 'test-only-secret')
        import app
        from form_client import client
        browser=client(app.app)
        with browser.session_transaction() as session:
            session['builder_draft']={'sentinel':'saved modular draft'}
        response=browser.post('/worksheet',data={'topic':'Fractions','num_questions':'2','question_types':'essay','grade_level':'5'},follow_redirects=True)
        self.assertEqual(response.status_code,200)
        model.assert_not_called()
        response=browser.post('/output',data={'generate':'1'})
        self.assertEqual(response.status_code,502)
        with browser.session_transaction() as session:
            self.assertEqual(session['worksheet_data']['topic'],'Fractions')
            self.assertEqual(session['builder_draft'],{'sentinel':'saved modular draft'})
            self.assertNotIn('content',session)
        self.assertIn(b'Retry generation',response.data)
