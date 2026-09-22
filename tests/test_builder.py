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
from openai_service import GenerationUnavailableError
from bs4 import BeautifulSoup
from docx import Document

def activity_record(session=1, minutes=20, transition=2, objective='Compare fractions.'):
    return {'session':session,'minutes':minutes,'transition_minutes':transition,
        'objective':objective,'grouping':'Pairs','materials':['Fraction strips'],
        'teacher_steps':['Model one comparison.'],'student_directions':['Compare two fractions.'],
        'assessment':'Listen for a correct comparison and explanation.',
        'supports_extensions':'Provide a visual model and an extension problem.'}

def activity_form(section='activities', session=1, minutes=20, transition=2, teacher_steps='Model one comparison.'):
    prefix=f'activity_{section}_'
    return {prefix+'session':str(session),prefix+'minutes':str(minutes),prefix+'transition_minutes':str(transition),
        prefix+'objective':'Compare fractions.',prefix+'grouping':'Pairs',prefix+'materials':'Fraction strips',
        prefix+'teacher_steps':teacher_steps,prefix+'student_directions':'Compare two fractions.',
        prefix+'assessment':'Listen for a correct comparison and explanation.',
        prefix+'supports_extensions':'Provide a visual model and an extension problem.'}

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
        mock.side_effect=GenerationUnavailableError('The API key was not accepted. Update the app configuration.')
        response=self.post('generate')
        self.assertEqual(response.status_code,503)
        self.assertIn(b'API key was not accepted',response.data)
        self.assertEqual(self.state()['builder_draft'],old)
    @patch('builder.generate_text')
    def test_prior_knowledge_is_saved_and_sent_to_generation(self,mock):
        prior='Students can identify numerators and denominators.'
        supports='Provide fraction strips and sentence starters.'
        self.create(mode='scratch',sections=['objectives'],prior_knowledge=prior,supports=supports)
        self.assertEqual(self.state()['builder_draft']['config']['prior_knowledge'],prior)
        mock.return_value=json.dumps({'sections':[{'id':'objectives','content':'Compare fractions.'}]})
        self.assertEqual(self.post('generate').status_code,302)
        context=json.loads(mock.call_args.args[0][1]['content'])
        self.assertEqual(context['prior_knowledge'],prior)
        self.assertEqual(context['supports'],supports)
    @patch('builder.generate_text')
    def test_generated_activity_contract_and_multisession_timing(self,mock):
        self.create(mode='scratch',sections=['warmup','guided'],minutes='30',sessions='2')
        mock.return_value=json.dumps({'sections':[
            {'id':'warmup','activity':activity_record(session=1,minutes=12,transition=3,objective='Recall equivalent fractions.')},
            {'id':'guided','activity':activity_record(session=2,minutes=20,transition=2)},
        ]})
        self.assertEqual(self.post('generate').status_code,302)
        draft=self.state()['builder_draft']
        self.assertEqual(draft['sections'][0]['activity']['minutes'],12)
        self.assertIn('Teacher steps:',draft['sections'][0]['content'])
        timing=builder.timing_summary(draft)
        self.assertEqual([(row['scheduled'],row['over']) for row in timing['rows']],[(15,0),(22,0)])
        page=self.client.get('/builder/')
        self.assertIn(b'12 instruction + 3 transition = 15 of 30 minutes',page.data)

    @patch('builder.generate_text')
    def test_invalid_generated_activity_preserves_draft(self,mock):
        self.create(mode='scratch',sections=['activities'])
        old=self.state()['builder_draft']
        incomplete=activity_record();incomplete.pop('assessment')
        for activity in (incomplete,activity_record(session=2),dict(activity_record(),unexpected='x')):
            mock.return_value=json.dumps({'sections':[{'id':'activities','activity':activity}]})
            self.assertEqual(self.post('generate').status_code,400)
            self.assertEqual(self.state()['builder_draft'],old)

    def test_manual_activity_timing_blocks_overbooked_review(self):
        self.create(mode='scratch',sections=['warmup','guided'],minutes='40',sessions='1')
        values={**activity_form('warmup',minutes=25,transition=2),
                **activity_form('guided',minutes=25,transition=2)}
        self.assertEqual(self.post('save',**values).status_code,302)
        page=self.client.get('/builder/')
        self.assertIn(b'Session 1 is overbooked by 14 minutes',page.data)
        self.assertEqual(self.post('review').status_code,400)
        values={**activity_form('warmup',minutes=15,transition=2),
                **activity_form('guided',minutes=15,transition=2)}
        self.assertEqual(self.post('save',**values).status_code,302)
        self.assertEqual(self.post('review').status_code,302)
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
    @patch('worksheet_generator.generate_text',return_value=json.dumps({'questions':[{'id':i,'question':'Question','answer':'Answer'} for i in range(1,5)]}))
    def test_real_worksheet_choices(self,mock):
        soup=BeautifulSoup(self.client.get('/worksheet').data,'html.parser')
        for choice in soup.select('[name=question_types] option'):
            question,answer='Question','Answer'
            if choice['value']=='multiple_choice':question,answer='Choose\nA. One\nB. Two\nC. Three\nD. Four','A. Explanation'
            if choice['value']=='true_false':answer='True: Explanation'
            if choice['value']=='matching':question,answer='L1: One\nL2: Two\nR1: First\nR2: Second','L1=R1\nL2=R2'
            mock.return_value=json.dumps({'questions':[{'id':i,'question':question,'answer':answer} for i in range(1,5)]})
            if choice['value']=='Mix':
                mock.return_value=json.dumps({'questions':[{'id':1,'type':'short_answer','question':'Question','answer':'Answer'},{'id':2,'type':'Fill in the Blanks','question':'Fill ___','answer':'Blank'},{'id':3,'type':'matching','question':'L1: One\nL2: Two\nR1: First\nR2: Second','answer':'L1=R1\nL2=R2'},{'id':4,'type':'short_answer','question':'Question','answer':'Answer'}]})
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

    def test_long_export_preserves_the_final_section_content(self):
        self.create(mode='scratch',sections=['overview','activities','assessment'])
        content='\n'.join(f'Step {i}: '+('detail ' * 70) for i in range(1,41))
        final='FINAL EXPORT MARKER'
        values={'content_overview':content,'content_assessment':content+'\n'+final,
                **activity_form(teacher_steps=content,minutes=30,transition=3)}
        self.assertEqual(self.post('save',**values).status_code,302)
        exported=self.post('export')
        self.assertEqual(exported.status_code,200)
        doc=Document(BytesIO(exported.data));text='\n'.join(p.text for p in doc.paragraphs)
        self.assertIn('Step 40:',text)
        self.assertIn(final,text)
        self.assertGreater(len(doc.paragraphs),120)

if __name__=='__main__': unittest.main()
