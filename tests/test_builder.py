from form_client import client as form_client
import json
import os
import unittest
from unittest.mock import patch
from io import BytesIO
os.environ['FLASK_SECRET_KEY']='test-only-secret'
os.environ['OPENAI_API_KEY']='mock-only'
import app
import builder
from bs4 import BeautifulSoup
from docx import Document

class BuilderTests(unittest.TestCase):
    def setUp(self):
        app.app.config.update(TESTING=True)
        self.client=form_client(app.app)
        self.client.get('/builder/')
    def state(self):
        with self.client.session_transaction() as s:
            return dict(s)
    def post(self, action, **data):
        state=self.state()
        body={'csrf':state['builder_csrf'],'action':action,'revision':state.get('builder_draft',{}).get('revision','')}
        body.update(data)
        return self.client.post('/builder/',data=body)
    def create(self, **values):
        data={'mode':'preset','preset':'prompt1','topic':'Fractions','grade':'5','students':'25','minutes':'45','sessions':'1','delivery':'classroom'}
        data.update(values)
        return self.post('create',**data)
    def test_three_paths_and_presets(self):
        for preset in builder.PRESETS:
            self.assertEqual(self.create(preset=preset).status_code,302)
            self.assertEqual(self.state()['builder_draft']['config']['sections'],builder.PRESETS[preset][1])
        for mode in ('scratch','customize'):
            self.assertEqual(self.create(mode=mode,sections=['worksheet','answers']).status_code,302)
            self.assertEqual(self.state()['builder_draft']['config']['sections'],['worksheet','answers'])
    def test_form_renders_and_assets(self):
        self.create()
        page=self.client.get('/builder/')
        self.assertEqual(page.status_code,200)
        soup=BeautifulSoup(page.data,'html.parser')
        for asset in soup.select('script[src],link[href]'):
            with self.client.get(asset.get('src') or asset['href']) as response:
                self.assertEqual(response.status_code,200)
        self.assertEqual(len(soup.select('#setup [name=mode]')),3)
    def test_invalid_context_rejected_without_losing_draft(self):
        self.create()
        old=self.state()['builder_draft']
        for overrides in ({'grade':'99'},{'minutes':'-1'},{'sessions':'0'},{'topic':' '},{'mode':'scratch','sections':['unknown']},{'mode':'scratch','sections':['title','title']}):
            self.assertEqual(self.create(**overrides).status_code,400)
            self.assertEqual(self.state()['builder_draft'],old)
    def test_csrf_and_stale_revision(self):
        self.create()
        self.assertEqual(self.client.post('/builder/',data={'action':'save'}).status_code,400)
        self.assertEqual(self.post('save',revision='stale').status_code,400)
    @patch('builder.generate_text')
    def test_generation_and_failure_are_atomic(self,mock):
        self.create(mode='scratch',sections=['worksheet','answers'])
        mock.return_value=json.dumps({'sections':[{'id':'worksheet','content':'1. 2+2?'},{'id':'answers','content':'1. 4'}]})
        self.assertEqual(self.post('generate').status_code,302)
        old=self.state()['builder_draft']
        for payload in ('bad json',json.dumps({'sections':[{'id':'worksheet','content':'Partial'}]}),json.dumps({'sections':[{'id':'worksheet','content':'x'},{'id':'worksheet','content':'x'}]})):
            mock.return_value=payload
            self.assertEqual(self.post('generate').status_code,400)
            self.assertEqual(self.state()['builder_draft'],old)
        mock.side_effect=RuntimeError('network unavailable')
        self.assertEqual(self.post('generate').status_code,503)
        self.assertEqual(self.state()['builder_draft'],old)
    @patch('builder.generate_text')
    def test_section_regeneration_preserves_other_content_and_resets_review(self,mock):
        self.create(mode='scratch',sections=['worksheet','answers'])
        self.post('save',content_worksheet='Question',content_answers='Answer')
        self.post('review')
        mock.return_value=json.dumps({'sections':[{'id':'worksheet','content':'New question'}]})
        self.assertEqual(self.post('regenerate',section='worksheet').status_code,302)
        d=self.state()['builder_draft']
        self.assertEqual(d['sections'][1]['content'],'Answer')
        self.assertFalse(d['reviewed'])
    def test_reorder_remove_add_edit_export(self):
        self.create(mode='scratch',sections=['worksheet','answers'])
        self.post('save',content_worksheet='Question\nSecond line',content_answers='Answer')
        self.post('down',section='worksheet')
        self.assertEqual(self.state()['builder_draft']['sections'][0]['id'],'answers')
        self.post('remove',section='answers')
        self.post('add',section='assessment')
        self.assertEqual(self.post('review').status_code,400)
        self.post('save',content_worksheet='Question\nSecond line',content_assessment='Exit ticket')
        self.post('review')
        exported=self.post('export')
        doc=Document(BytesIO(exported.data))
        text='\n'.join(p.text for p in doc.paragraphs)
        self.assertIn('Teacher reviewed',text)
        self.assertIn('Question\nSecond line',text)
        self.post('up',section='assessment')
        self.assertFalse(self.state()['builder_draft']['reviewed'])
    @patch('worksheet_generator.generate_text',return_value='Questions\nAnswers:\nAnswers')
    def test_real_worksheet_choices(self,mock):
        soup=BeautifulSoup(self.client.get('/worksheet').data,'html.parser')
        for choice in soup.select('[name=question_types] option'):
            response=self.client.post('/worksheet',data={'topic':'Fractions','grade_level':'4','num_questions':'4','question_types':choice['value']},follow_redirects=True)
            response=self.client.post('/output',data={'generate':'1'},follow_redirects=True)
            self.assertEqual(response.status_code,200,choice['value'])
        self.assertIn('grade 4',mock.call_args.args[0][1]['content'])
    def test_legacy_invalid_numbers_rejected(self):
        self.client.post('/prompt_selection',data={'prompt':'prompt3'})
        response=self.client.post('/home',data={'topic':'Fractions','grade_level':'99','number_of_words':'-100','number_of_students':'-2'})
        self.assertEqual(response.status_code,400)
    def test_legacy_navigation_preserves_modular_draft(self):
        self.create()
        old=self.state()['builder_draft']
        self.client.post('/redirect_choice',data={'choice':'worksheet'})
        self.assertEqual(self.state()['builder_draft'],old)
        self.client.post('/prompt_selection',data={'prompt':'prompt3'})
        self.assertEqual(self.state()['builder_draft'],old)
    def test_rendered_arrange_operation(self):
        self.create(mode='scratch',sections=['title','assessment'])
        self.assertEqual(self.post('unused',operation='down',section='title').status_code,302)
        self.assertEqual(self.state()['builder_draft']['sections'][0]['id'],'assessment')
    def test_html_escaped(self):
        self.create(mode='scratch',sections=['title'])
        self.post('save',content_title='<script>alert(1)</script>')
        page=self.client.get('/builder/')
        self.assertNotIn(b'<script>alert(1)</script>',page.data)
        self.assertIn(b'&lt;script&gt;',page.data)

if __name__=='__main__': unittest.main()
