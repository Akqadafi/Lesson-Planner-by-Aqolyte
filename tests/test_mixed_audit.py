import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from bs4 import BeautifulSoup
from legacy_choices import CHOICES
import worksheet_generator as worksheet
import lesson_planner
from test_lesson_planner import SAMPLE_INPUT

class MixedAuditTests(unittest.TestCase):
    @patch('worksheet_generator.generate_text')
    def test_mixed_types_and_counts(self, model):
        rows=[{'id':1,'type':'short_answer','question':'Explain','answer':'Explanation'}, {'id':2,'type':'Fill in the Blanks','question':'Fill ___','answer':'Value'}, {'id':3,'type':'matching','question':'L1: One\nL2: Two\nR1: First\nR2: Second','answer':'L1=R1\nL2=R2'}]
        model.return_value=json.dumps({'questions':rows})
        self.assertIn('3. L1:',worksheet.generate_worksheet('Topic',3,'Mix'))
        for field,value in [('type','essay'),('question','No blank')]:
            bad=copy.deepcopy(rows);bad[1][field]=value;model.return_value=json.dumps({'questions':bad})
            with self.assertRaises(worksheet.WorksheetFormatError):worksheet.generate_worksheet('Topic',3,'Mix')
        for count in (1,2):
            model.return_value=json.dumps({'questions':rows[:count]})
            self.assertIn('Answers:',worksheet.generate_worksheet('Topic',count,'Mix'))
    @patch('worksheet_generator.generate_text')
    def test_blank_line_delimiter(self, model):
        model.return_value=json.dumps({'questions':[{'id':i,'question':'Question','answer':'Answer'} for i in (1,2)]})
        output=worksheet.generate_worksheet('Topic',2,'essay',r'\n\n')
        self.assertIn('1. Question\n\n2. Question',output)
        self.assertNotIn(r'\n\n',output)
    def test_all_rendered_legacy_choices_are_supported(self):
        root=Path(__file__).resolve().parents[1]/'templates'
        for path in root.glob('prompt?_form.html'):
            soup=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
            for select in soup.select('select[name]'):
                self.assertEqual(set(CHOICES[select['name']]),{option['value'] for option in select.select('option')})
            self.assertIsNotNone(soup.select_one('[name=prior_knowledge]'))
            self.assertIsNotNone(soup.select_one('[name=learner_supports]'))
            for retired in ('culture_group','socioeconomic_level','experiential_type','disabled','ell','gifted'):
                self.assertIsNone(soup.select_one(f'[name={retired}]'))
    @patch('lesson_planner.generate_text')
    def test_forged_legacy_options_rejected(self, model):
        for change in ({'state':'Atlantis'},{'prompt':'prompt1','lesson_type':'unsupported'}):
            with self.assertRaises(ValueError):lesson_planner.generate_lesson_plan(dict(SAMPLE_INPUT,**change))
        model.assert_not_called()
