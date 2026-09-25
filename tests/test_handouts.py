from form_client import client as form_client
import os
import json
import unittest
from io import BytesIO
from unittest.mock import patch
from docx import Document
os.environ.setdefault('FLASK_SECRET_KEY','test-only')
os.environ.setdefault('OPENAI_API_KEY','mock-only')
import app
from handouts import fingerprint
from openai_service import GenerationUnavailableError

class HandoutTests(unittest.TestCase):
    def setUp(self):
        app.app.config['TESTING']=True
        self.client=form_client(app.app);self.client.get('/builder/')
        with self.client.session_transaction() as s:
            s['builder_draft']={'config':{'topic':'Fractions','grade':5,'objectives':'Compare fractions','sources':'Teacher excerpt'},
                'sections':[{'id':'activities','content':'Compare one half and two thirds'}],'revision':'initial','reviewed':False}
    def state(self):
        with self.client.session_transaction() as s:return dict(s)
    def post(self,action,**values):
        state=self.state();data={'csrf':state['builder_csrf'],'revision':state['builder_draft']['revision'],'action':action};data.update(values)
        return self.client.post('/handouts/',data=data)
    def create(self):return self.post('create',source='activities',count=2)
    def save(self):return self.post('save',title='Practice',instructions='Explain each answer.',prompt_1='First question',answer_1='SECRET ANSWER ONE',prompt_2='Second question',answer_2='SECRET ANSWER TWO',font=12,space=3,paper='Letter')
    def test_create_without_ai_and_edit(self):
        with patch('handouts.generate_text') as mock:
            self.assertEqual(self.create().status_code,302);mock.assert_not_called()
        self.assertEqual(self.save().status_code,302)
        page=self.client.get('/handouts/');self.assertEqual(page.status_code,200)
        self.assertIn(b'First question',page.data)
    def test_student_teacher_separation(self):
        self.create();self.save()
        for action,expected in [('student',False),('teacher',True)]:
            response=self.post(action);self.assertEqual(response.status_code,200)
            doc=Document(BytesIO(response.data));text='\n'.join(p.text for p in doc.paragraphs)
            self.assertEqual('SECRET ANSWER' in text,expected)
            self.assertIn('First question',text)
    def test_validation_and_stale_submission_preserve_handout(self):
        self.create();self.save();old=self.state()['builder_draft']
        for data in ({'csrf':'wrong'},{'revision':'old'}):
            self.assertEqual(self.post('generate',**data).status_code,400)
        self.assertEqual(self.post('create',source='activities',count=99).status_code,400)
        self.assertEqual(self.state()['builder_draft'],old)
    def test_lesson_change_blocks_export_until_review(self):
        self.create();self.save()
        with self.client.session_transaction() as s:
            d=s['builder_draft'];d['sections'][0]['content']='Changed lesson';s['builder_draft']=d
        handout_page=self.client.get('/handouts/')
        self.assertIn(b'The source lesson section changed.',handout_page.data)
        self.assertEqual(self.post('student').status_code,400)
        self.assertEqual(self.post('confirm').status_code,302)
        self.assertEqual(self.post('student').status_code,200)

    def test_unrelated_lesson_edit_does_not_pause_handout_export(self):
        self.create();self.save()
        with self.client.session_transaction() as s:
            d=s['builder_draft']
            d['sections'].append({'id':'assessment','content':'Check understanding with an exit ticket.'})
            d['config']['sections']=['activities','assessment']
            d['revision']='changed-unrelated'
            s['builder_draft']=d
        page=self.client.get('/handouts/')
        self.assertNotIn(b'Handout review required',page.data)
        self.assertEqual(self.post('student').status_code,200)

    def test_removed_handout_source_requires_replacement(self):
        self.create();self.save()
        with self.client.session_transaction() as s:
            d=s['builder_draft']
            d['sections']=[{'id':'assessment','content':'Check understanding with an exit ticket.'}]
            d['config']['sections']=['assessment']
            d['revision']='removed-source'
            s['builder_draft']=d
        page=self.client.get('/handouts/')
        self.assertIn(b'Its source lesson section was removed.',page.data)
        self.assertNotIn(b'I reviewed alignment with the updated lesson',page.data)
        self.assertEqual(self.post('student').status_code,400)
        self.assertEqual(self.post('confirm').status_code,400)
    @patch('handouts.generate_text')
    def test_generation_atomicity_and_grade_context(self,mock):
        self.create();self.save();old=self.state()['builder_draft']
        for payload in ('bad JSON',json.dumps({'title':'X','instructions':'Y','questions':[]}),json.dumps({'title':'X','instructions':'Y','questions':[{'id':1,'prompt':'Q','answer':'A'},{'id':1,'prompt':'Q','answer':'A'}]})):
            mock.return_value=payload
            self.assertEqual(self.post('generate').status_code,400)
            self.assertEqual(self.state()['builder_draft'],old)
        mock.side_effect=RuntimeError('Unavailable');self.assertEqual(self.post('generate').status_code,503)
        self.assertEqual(self.state()['builder_draft'],old);mock.side_effect=None
        mock.side_effect=GenerationUnavailableError('The AI service is temporarily rate-limited. Wait and retry.')
        response=self.post('generate');self.assertEqual(response.status_code,503)
        self.assertIn(b'temporarily rate-limited',response.data)
        self.assertEqual(self.state()['builder_draft'],old);mock.side_effect=None
        mock.return_value=json.dumps({'title':'Fractions','instructions':'Compare','questions':[{'id':1,'prompt':'Q1','answer':'A1'},{'id':2,'prompt':'Q2','answer':'A2'}]})
        self.assertEqual(self.post('generate').status_code,302)
        context=json.loads(mock.call_args.args[0][1]['content']);self.assertEqual(context['grade'],5)
        self.assertEqual(mock.call_args.kwargs['schema_name'],'lesson_handout')
        self.assertEqual(mock.call_args.kwargs['response_schema']['properties']['questions']['maxItems'],2)
        self.assertIn('Compare one half',context['source']['content'])
    def test_invalid_edit_retains_submitted_text_and_saved_content(self):
        self.create();self.save();old=self.state()['builder_draft']
        response=self.post('save',title='Attempted title',instructions='Explain',prompt_1='New question',answer_1='',prompt_2='Q',answer_2='A',font=12,space=3,paper='Letter')
        self.assertEqual(response.status_code,400);self.assertIn(b'Attempted title',response.data)
        self.assertEqual(self.state()['builder_draft'],old)

    def test_long_twenty_item_exports_preserve_student_teacher_separation(self):
        self.assertEqual(self.post('create',source='activities',count=20).status_code,302)
        values={'title':'Long practice','instructions':'Complete every item.','font':12,'space':8,'paper':'Letter'}
        for i in range(1,21):
            values[f'prompt_{i}']=f'Question {i} '+('student detail ' * 35)
            values[f'answer_{i}']=f'ANSWER {i} '+('teacher detail ' * 35)
        self.assertEqual(self.post('save',**values).status_code,302)
        student=self.post('student');teacher=self.post('teacher')
        self.assertEqual(student.status_code,200);self.assertEqual(teacher.status_code,200)
        student_text='\n'.join(p.text for p in Document(BytesIO(student.data)).paragraphs)
        teacher_text='\n'.join(p.text for p in Document(BytesIO(teacher.data)).paragraphs)
        self.assertIn('Question 20',student_text);self.assertNotIn('ANSWER 20',student_text)
        self.assertIn('Question 20',teacher_text);self.assertIn('ANSWER 20',teacher_text)

if __name__=='__main__':unittest.main()
