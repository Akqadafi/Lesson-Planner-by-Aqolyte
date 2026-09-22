import os
os.environ.setdefault('FLASK_SECRET_KEY','workflow-only')
import unittest
from io import BytesIO
from bs4 import BeautifulSoup
from docx import Document
from unittest.mock import patch
import app

class WorkflowTests(unittest.TestCase):
    @patch('handouts.generate_text')
    @patch('builder.generate_text')
    def test_manual_draft_to_handout_export_and_revision(self, lesson_ai, handout_ai):
        browser=app.app.test_client()
        def submit(path, action, **values):
            page=browser.get(path)
            soup=BeautifulSoup(page.data,'html.parser')
            form=next(f for f in soup.select('form') if f.select_one('[name=action]') and f.select_one('[name=action]').get('value')==action)
            data={x['name']:x.get('value','') for x in form.select('input[type=hidden][name]')}
            data.update(values)
            return browser.post(path,data=data)
        self.assertEqual(submit('/builder/','create',mode='scratch',preset='prompt1',topic='Fractions',grade='5',students='25',minutes='40',sessions='1',delivery='classroom',sections=['activities']).status_code,302)
        activity={'activity_activities_session':'1','activity_activities_minutes':'20','activity_activities_transition_minutes':'2',
            'activity_activities_objective':'Compare fractions.','activity_activities_grouping':'Pairs',
            'activity_activities_materials':'Fraction strips','activity_activities_teacher_steps':'Model one comparison.',
            'activity_activities_student_directions':'Compare two fractions and explain.',
            'activity_activities_assessment':'Check each comparison and explanation.',
            'activity_activities_supports_extensions':'Provide a visual model and an extension problem.'}
        self.assertEqual(submit('/builder/','save',**activity).status_code,302)
        self.assertEqual(submit('/builder/','review').status_code,302)
        lesson=submit('/builder/','export')
        self.assertIn('Teacher reviewed','\n'.join(p.text for p in Document(BytesIO(lesson.data)).paragraphs))
        self.assertEqual(submit('/handouts/','create',source='activities',kind='practice',count='1').status_code,302)
        self.assertEqual(submit('/handouts/','save',title='Fractions practice',instructions='Explain your reasoning.',prompt_1='Which is larger: 1/2 or 1/3?',answer_1='TEACHER_ONLY: 1/2',font='12',space='3',paper='Letter',theme='print',accent='teal').status_code,302)
        for action,teacher in [('student',False),('teacher',True)]:
            response=submit('/handouts/',action)
            self.assertEqual(response.status_code,200)
            text='\n'.join(p.text for p in Document(BytesIO(response.data)).paragraphs)
            self.assertEqual('TEACHER_ONLY' in text,teacher)
        activity['activity_activities_teacher_steps']='Model one comparison and ask students to explain.'
        self.assertEqual(submit('/builder/','save',**activity).status_code,302)
        self.assertEqual(submit('/handouts/','student').status_code,400)
        self.assertEqual(submit('/handouts/','confirm').status_code,302)
        self.assertEqual(submit('/handouts/','student').status_code,200)
        lesson_ai.assert_not_called();handout_ai.assert_not_called()
    def test_local_navigation_and_assets(self):
        browser=app.app.test_client()
        seen=set()
        for path in ('/','/about','/products','/features','/contact','/choose','/second_landing','/builder/','/worksheet','/output'):
            response=browser.get(path,follow_redirects=True)
            self.assertEqual(response.status_code,200,path)
            for node in BeautifulSoup(response.data,'html.parser').select('a[href],link[href],script[src],img[src]'):
                url=node.get('href') or node.get('src')
                if url.startswith('/') and url not in seen:
                    seen.add(url)
                    with browser.get(url,follow_redirects=True) as asset:
                        self.assertEqual(asset.status_code,200,url)
