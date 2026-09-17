import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import Mock, patch
from generation_limits import reserve_attempt, GenerationLimitError
from openai_service import generate_text, GenerationUnavailableError

class GenerationLimitTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.env = patch.dict(os.environ, {'GENERATION_LIMIT_DB':str(Path(self.folder.name)/'limits.db'), 'GENERATION_SESSION_HOURLY':'10', 'GENERATION_GLOBAL_DAILY':'3'})
        self.env.start();self.addCleanup(self.env.stop)
    def test_concurrent_reservations_cannot_exceed_global_limit(self):
        def attempt(_):
            try:reserve_attempt();return True
            except GenerationLimitError:return False
        with ThreadPoolExecutor(max_workers=8) as pool:
            self.assertEqual(sum(pool.map(attempt,range(12))),3)
    def test_windows_reset_and_session_rejection_does_not_charge_global(self):
        with patch.dict(os.environ, {'GENERATION_SESSION_HOURLY':'1','GENERATION_GLOBAL_DAILY':'2'}):
            with patch('generation_limits.time.time',return_value=86401):
                reserve_attempt()
                with self.assertRaisesRegex(GenerationLimitError,'hourly'):reserve_attempt()
            with patch('generation_limits.time.time',return_value=90001):reserve_attempt()
            with patch('generation_limits.time.time',return_value=93601):
                with self.assertRaisesRegex(GenerationLimitError,'daily'):reserve_attempt()
            with patch('generation_limits.time.time',return_value=172801):reserve_attempt()
    def test_bad_configuration_fails_closed(self):
        with patch.dict(os.environ, {'GENERATION_GLOBAL_DAILY':'0'}):
            with self.assertRaisesRegex(GenerationLimitError,'paused'):reserve_attempt()
    @patch('openai_service.get_client')
    def test_failed_response_counts_and_exhaustion_never_calls_provider(self, client):
        client.return_value.responses.create.side_effect=RuntimeError('simulated provider failure')
        for _ in range(3):
            with self.assertRaises(RuntimeError):generate_text([{'role':'user','content':'Test'}])
        with self.assertRaisesRegex(GenerationUnavailableError,'daily'):
            generate_text([{'role':'user','content':'Test'}])
        self.assertEqual(client.return_value.responses.create.call_count,3)
    @patch('openai_service.get_client')
    def test_invalid_input_never_reserves_or_calls_provider(self, client):
        with patch('openai_service.reserve_attempt') as reserve:
            for messages in ([],[{'role':'user','content':'x'*150001}],[{'role':'user','content':None}]):
                with self.assertRaises(GenerationUnavailableError):generate_text(messages)
            reserve.assert_not_called();client.assert_not_called()
    @patch('openai_service.reserve_attempt')
    @patch('openai_service.get_client')
    def test_incomplete_or_invalid_output_is_not_accepted(self, client, reserve):
        for status, text in [('incomplete','Partial lesson'),('completed',''),('completed','x'*200001),('completed',None)]:
            client.return_value.responses.create.return_value=Mock(status=status,output_text=text)
            with self.assertRaises(GenerationUnavailableError):generate_text([{'role':'user','content':'Test'}])
        client.return_value.responses.create.return_value=Mock(status='completed',output_text=' Complete draft ')
        self.assertEqual(generate_text([{'role':'user','content':'Test'}]),'Complete draft')
