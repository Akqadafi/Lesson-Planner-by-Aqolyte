from form_client import client as form_client
import os
import subprocess
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch, Mock
from docx import Document
import test_handouts as helpers
import app
import pdf_export

class PDFTests(unittest.TestCase):
    setUp=helpers.HandoutTests.setUp
    state=helpers.HandoutTests.state
    post=helpers.HandoutTests.post
    create=helpers.HandoutTests.create
    save=helpers.HandoutTests.save
    @patch('handouts.convert_docx')
    def test_student_teacher_pdf_uses_separate_content(self,convert):
        self.create();self.save()
        def fake(stream):
            text='\n'.join(p.text for p in Document(stream).paragraphs)
            self.captured=text
            return BytesIO(b'%PDF-test')
        convert.side_effect=fake
        for action,secret in [('student_pdf',False),('teacher_pdf',True)]:
            response=self.post(action)
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.mimetype,'application/pdf')
            self.assertEqual('SECRET ANSWER' in self.captured,secret)
    @patch('handouts.convert_docx',side_effect=pdf_export.PDFExportError('PDF test unavailable'))
    def test_pdf_failure_retains_saved_handout(self,convert):
        self.create();self.save();before=self.state()['builder_draft']
        response=self.post('student_pdf')
        self.assertEqual(response.status_code,503)
        self.assertIn(b'PDF test unavailable',response.data)
        self.assertEqual(before,self.state()['builder_draft'])
        self.assertEqual(self.post('student').status_code,200)
    @patch('handouts.convert_docx')
    def test_stale_pdf_export_blocked(self,convert):
        self.create();self.save()
        with self.client.session_transaction() as s:
            d=s['builder_draft'];d['sections'][0]['content']='New';s['builder_draft']=d
        self.assertEqual(self.post('student_pdf').status_code,400)
        convert.assert_not_called()
    @patch('builder.convert_docx',return_value=BytesIO(b'%PDF-test'))
    def test_builder_pdf(self,convert):
        state=self.state()
        response=self.client.post('/builder/',data={'action':'export_pdf','csrf':state['builder_csrf'],'revision':state['builder_draft']['revision']})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.mimetype,'application/pdf')
    @patch('app.convert_docx',return_value=BytesIO(b'%PDF-test'))
    def test_legacy_pdf(self,convert):
        with self.client.session_transaction() as s:
            s['content_type']='Worksheet';s['content']='Question and answer'
        self.assertEqual(self.client.post('/output',data={'download_pdf':'true'}).mimetype,'application/pdf')
    @patch('pdf_export.find_converter',return_value='converter')
    @patch('pdf_export.subprocess.Popen')
    def test_conversion_isolated_and_cleans_up(self,popen,find):
        folders=[]
        def start(command,**kwargs):
            root=Path(command[-1]).parent;folders.append(root)
            self.assertIn(root.as_uri(),command[1])
            (root/'document.pdf').write_bytes(b'%PDF-valid')
            process=Mock(returncode=0);return process
        popen.side_effect=start
        for _ in range(2):self.assertEqual(pdf_export.convert_docx(BytesIO(b'docx')).getvalue(),b'%PDF-valid')
        self.assertNotEqual(folders[0],folders[1])
        self.assertTrue(all(not root.exists() for root in folders))
    @patch('pdf_export.find_converter',return_value='converter')
    @patch('pdf_export.subprocess.Popen')
    def test_missing_or_invalid_output(self,popen,find):
        for output in (None,b'not a pdf'):
            def start(command,**kwargs):
                if output is not None:(Path(command[-1]).parent/'document.pdf').write_bytes(output)
                return Mock(returncode=0)
            popen.side_effect=start
            with self.assertRaises(pdf_export.PDFExportError):pdf_export.convert_docx(BytesIO(b'docx'))
    @patch('pdf_export.find_converter',return_value='converter')
    @patch('pdf_export.subprocess.run')
    @patch('pdf_export.os.killpg',create=True)
    @patch('pdf_export.subprocess.Popen')
    def test_timeout(self,popen,killpg,run,find):
        process=Mock(pid=12345);process.communicate.side_effect=[subprocess.TimeoutExpired('converter',60),(b'',b'')];popen.return_value=process
        with self.assertRaisesRegex(pdf_export.PDFExportError,'too long'):pdf_export.convert_docx(BytesIO(b'docx'))
        if os.name=='nt':run.assert_called_once()
        else:killpg.assert_called_once()
