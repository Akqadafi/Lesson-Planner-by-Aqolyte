import json
from io import BytesIO
from unittest.mock import patch
from docx import Document
from docx.oxml.ns import qn
import unittest
import test_handouts as helpers
from handouts import TYPES, document

class HandoutTypeTests(unittest.TestCase):
    setUp=helpers.HandoutTests.setUp
    state=helpers.HandoutTests.state
    post=helpers.HandoutTests.post
    create=helpers.HandoutTests.create
    save=helpers.HandoutTests.save
    def test_all_types_render_and_export(self):
        for kind in TYPES:
            self.assertEqual(self.post('create',source='activities',count=2,kind=kind).status_code,302)
            self.assertEqual(self.save().status_code,302)
            page=self.client.get('/handouts/')
            self.assertEqual(page.status_code,200)
            self.assertIn(TYPES[kind]['name'].encode(),page.data)
            response=self.post('student');self.assertEqual(response.status_code,200)
            doc=Document(BytesIO(response.data))
            writing=[p for p in doc.paragraphs if p.text==' ']
            self.assertEqual(len(writing),0 if kind=='reference' else 6)
    def test_theme_change_preserves_content_without_generation(self):
        self.create();self.save()
        before=self.state()['builder_draft']['handout']
        with patch('handouts.generate_text') as mock:
            response=self.post('save',title=before['title'],instructions=before['instructions'],prompt_1=before['questions'][0]['prompt'],answer_1=before['questions'][0]['answer'],prompt_2=before['questions'][1]['prompt'],answer_2=before['questions'][1]['answer'],font=12,space=3,paper='Letter',theme='classroom',accent='plum')
            self.assertEqual(response.status_code,302);mock.assert_not_called()
        after=self.state()['builder_draft']['handout']
        self.assertEqual(before['questions'],after['questions'])
        doc=Document(document(after));colors=[r.font.color.rgb for p in doc.paragraphs for r in p.runs]
        self.assertIn('633C65',[str(c) for c in colors])
        after['theme']='print';doc=Document(document(after))
        self.assertNotIn('633C65',[str(r.font.color.rgb) for p in doc.paragraphs for r in p.runs])
    def test_type_validation(self):
        self.create();before=self.state()['builder_draft']
        self.assertEqual(self.post('create',source='activities',count=6,kind='exit').status_code,400)
        self.assertEqual(self.post('create',source='activities',count=2,kind='invalid').status_code,400)
        self.assertEqual(before,self.state()['builder_draft'])
    @patch('handouts.generate_text')
    def test_generation_receives_type_guidance(self,mock):
        mock.return_value=json.dumps({'title':'Title','instructions':'Instructions','questions':[{'id':1,'prompt':'Content','answer':'Teacher guidance'}]})
        for kind in TYPES:
            self.post('create',source='activities',count=1,kind=kind)
            self.assertEqual(self.post('generate').status_code,302)
            context=json.loads(mock.call_args.args[0][1]['content'])
            self.assertEqual(context['format_guidance'],TYPES[kind]['guidance'])
