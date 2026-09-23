from form_client import client as form_client
import json
import unittest
from io import BytesIO
from unittest.mock import patch
from docx import Document
import app
import lesson_planner
from test_lesson_planner import SAMPLE_INPUT

class ReliabilityTests(unittest.TestCase):
    @patch('lesson_planner.generate_text')
    def test_all_six_require_complete_exact_sections(self,mock):
        for preset,sections in lesson_planner.SECTION_ORDER.items():
            data=dict(SAMPLE_INPUT,prompt=preset,lesson_type='inquiry_based')
            valid={'sections':[{'title':name,'content':f'Material for {name}'} for name in sections]}
            malformed=[{}, {'sections':valid['sections'][:-1]},
                {'sections':valid['sections']+[valid['sections'][0]]},
                {'sections':valid['sections']+[{'title':'Surprise','content':'Unexpected'}]},
                {'sections':[dict(row) for row in valid['sections']]}, '', 'not json']
            malformed[4]['sections'][0]['content']=''
            for payload in malformed:
                mock.return_value=json.dumps(payload) if isinstance(payload,dict) else payload
                with self.subTest(preset=preset,payload=str(payload)[:40]):
                    with self.assertRaises(lesson_planner.LessonFormatError):
                        lesson_planner.generate_lesson_plan(data)
            mock.return_value=json.dumps(valid)
            result,order=lesson_planner.generate_lesson_plan(data)
            self.assertEqual(list(result),sections)
    @patch('lesson_planner.generate_text',return_value='{"sections":[{"title":"Assessment","content":"incomplete"}]}')
    def test_failure_preserves_inputs_and_previous_draft(self,mock):
        client=form_client(app.app)
        with client.session_transaction() as s:
            s['prompt']='prompt3'
            s['content_type']='Lesson Plan'
            s['content']={'Title':'Previous lesson'}
            s['input_data']=dict(SAMPLE_INPUT)
        client.post('/home',data=SAMPLE_INPUT,follow_redirects=True)
        response=client.post('/output',data={'generate':'1'},follow_redirects=True)
        self.assertEqual(response.status_code,502)
        with client.session_transaction() as s:
            self.assertEqual(s['input_data']['topic'],SAMPLE_INPUT['topic'])
            self.assertNotIn('content',s)
            self.assertEqual(s['previous_lesson']['content']['Title'],'Previous lesson')
        response=client.post('/output',data={'restore_previous':'1'},follow_redirects=True)
        self.assertEqual(response.status_code,200)
        self.assertIn(b'Previous lesson',response.data)
    def test_table_text_order_and_no_duplicates(self):
        doc=Document(app.html_to_docx('<h1>Before</h1><table><tr><th>Task</th><th>Minutes</th></tr><tr><td><p>Read</p><p>Discuss</p></td><td>15</td></tr></table><p>After</p>'))
        self.assertEqual(len(doc.tables),1)
        self.assertEqual(doc.tables[0].cell(1,0).text,'Read\nDiscuss')
        self.assertEqual(doc.tables[0].cell(1,1).text,'15')
        self.assertEqual([p.text for p in doc.paragraphs],['Before','After'])
        self.assertEqual([x.tag.split('}')[-1] for x in doc.element.body],['p','tbl','p','sectPr'])
    def test_spans_nested_tables_lists_and_breaks(self):
        doc=Document(app.html_to_docx('<table><tr><th colspan="2">Activities</th></tr><tr><td rowspan="2">Group</td><td>A<br>B</td></tr><tr><td><table><tr><td>Nested</td></tr></table></td></tr></table><ol><li>First</li><li>Second</li></ol><p>Line one<br>Line two</p>'))
        self.assertEqual(doc.tables[0].cell(0,0).text,'Activities')
        self.assertEqual(doc.tables[0].cell(1,1).text,'A\nB')
        self.assertEqual(doc.tables[0].cell(2,1).tables[0].cell(0,0).text,'Nested')
        self.assertEqual(doc.paragraphs[0].style.name,'List Number')
        self.assertEqual(doc.paragraphs[-1].text,'Line one\nLine two')
    def test_export_excludes_controls_and_rejects_bad_geometry(self):
        doc=Document(app.html_to_docx('<p>Lesson</p><form><p>Download button</p></form>'))
        self.assertEqual([p.text for p in doc.paragraphs],['Lesson'])
        with self.assertRaises(ValueError):
            app.html_to_docx('<table><tr><td rowspan="99">Bad span</td></tr></table>')

if __name__=='__main__':unittest.main()
