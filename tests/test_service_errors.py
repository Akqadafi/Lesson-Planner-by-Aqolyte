import unittest
from unittest.mock import patch, Mock
import httpx
from openai import RateLimitError, APIConnectionError
from openai_service import generate_text, GenerationUnavailableError

class ServiceErrorTests(unittest.TestCase):
    @patch('openai_service.get_client')
    def test_credit_error_safe_and_actionable(self,client):
        response=httpx.Response(429,request=httpx.Request('POST','https://api.openai.com/v1/responses'))
        client.return_value.responses.create.side_effect=RateLimitError('private provider payload',response=response,body={'code':'credit_balance_exhausted'})
        with self.assertRaises(GenerationUnavailableError) as error:generate_text([])
        self.assertIn('API credits or quota are exhausted',str(error.exception))
        self.assertNotIn('private provider payload',str(error.exception))
    @patch('openai_service.get_client')
    def test_network_error_actionable(self,client):
        client.return_value.responses.create.side_effect=APIConnectionError(request=httpx.Request('POST','https://api.openai.com/v1/responses'))
        with self.assertRaises(GenerationUnavailableError) as error:generate_text([])
        self.assertIn('server',str(error.exception))
