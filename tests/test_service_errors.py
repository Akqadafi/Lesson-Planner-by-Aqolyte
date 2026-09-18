import unittest
from unittest.mock import patch, Mock
import httpx
from openai import APIConnectionError, APIStatusError, APITimeoutError, AuthenticationError, RateLimitError
from openai_service import generate_text, GenerationUnavailableError

@patch("openai_service.reserve_attempt")
class ServiceErrorTests(unittest.TestCase):
    def response(self, status):
        return httpx.Response(status, request=httpx.Request('POST','https://api.openai.com/v1/responses'))

    @patch('openai_service.get_client')
    def test_authentication_error_is_safe_and_actionable(self,client,reserve):
        client.return_value.responses.create.side_effect=AuthenticationError('private provider payload',response=self.response(401),body={'error':{'code':'invalid_api_key'}})
        with self.assertRaises(GenerationUnavailableError) as error:generate_text([{'role':'user','content':'Test'}])
        self.assertIn('API key was not accepted',str(error.exception))
        self.assertNotIn('private provider payload',str(error.exception))

    @patch('openai_service.get_client')
    def test_credit_error_safe_and_actionable(self,client,reserve):
        client.return_value.responses.create.side_effect=RateLimitError('private provider payload',response=self.response(429),body={'code':'credit_balance_exhausted'})
        with self.assertRaises(GenerationUnavailableError) as error:generate_text([{'role':'user','content':'Test'}])
        self.assertIn('API credits or quota are exhausted',str(error.exception))
        self.assertNotIn('private provider payload',str(error.exception))

    @patch('openai_service.get_client')
    def test_rate_limit_error_is_safe_and_actionable(self,client,reserve):
        client.return_value.responses.create.side_effect=RateLimitError('private provider payload',response=self.response(429),body={'error':{'code':'rate_limit_exceeded'}})
        with self.assertRaises(GenerationUnavailableError) as error:generate_text([{'role':'user','content':'Test'}])
        self.assertIn('temporarily rate-limited',str(error.exception))
        self.assertNotIn('private provider payload',str(error.exception))

    @patch('openai_service.get_client')
    def test_timeout_error_is_safe_and_actionable(self,client,reserve):
        client.return_value.responses.create.side_effect=APITimeoutError(request=httpx.Request('POST','https://api.openai.com/v1/responses'))
        with self.assertRaises(GenerationUnavailableError) as error:generate_text([{'role':'user','content':'Test'}])
        self.assertIn('too long to respond',str(error.exception))

    @patch('openai_service.get_client')
    def test_network_error_actionable(self,client,reserve):
        client.return_value.responses.create.side_effect=APIConnectionError(request=httpx.Request('POST','https://api.openai.com/v1/responses'))
        with self.assertRaises(GenerationUnavailableError) as error:generate_text([{'role':'user','content':'Test'}])
        self.assertIn('connect to OpenAI',str(error.exception))

    @patch('openai_service.get_client')
    def test_status_error_is_safe_and_actionable(self,client,reserve):
        client.return_value.responses.create.side_effect=APIStatusError('private provider payload',response=self.response(500),body={'error':{'message':'private details'}})
        with self.assertRaises(GenerationUnavailableError) as error:generate_text([{'role':'user','content':'Test'}])
        self.assertIn('model configuration',str(error.exception))
        self.assertNotIn('private provider payload',str(error.exception))

    @patch('openai_service.get_client')
    def test_incomplete_empty_and_oversized_responses_are_rejected(self,client,reserve):
        for response in (Mock(status='in_progress',output_text='partial'),Mock(status='completed',output_text=' '),Mock(status='completed',output_text='x'*200001)):
            client.return_value.responses.create.return_value=response
            with self.assertRaises(GenerationUnavailableError):generate_text([{'role':'user','content':'Test'}])
