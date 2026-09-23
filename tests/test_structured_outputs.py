import json
import unittest
from unittest.mock import Mock, patch

from openai_service import GenerationUnavailableError, generate_text
from response_schemas import handout_schema, legacy_lesson_schema, lesson_sections_schema, worksheet_schema


def assert_strict_objects(testcase, schema):
    if isinstance(schema, dict):
        if schema.get('type') == 'object':
            testcase.assertFalse(schema.get('additionalProperties'))
            testcase.assertEqual(set(schema.get('required', [])), set(schema.get('properties', {})))
        for value in schema.values():
            assert_strict_objects(testcase, value)
    elif isinstance(schema, list):
        for value in schema:
            assert_strict_objects(testcase, value)


class StructuredOutputTests(unittest.TestCase):
    def test_all_generation_schemas_are_strict_root_objects(self):
        schemas = [
            lesson_sections_schema(['title', 'activities'], {'activities'}),
            legacy_lesson_schema(['Title', 'Assessment']),
            handout_schema(4),
            worksheet_schema(4),
            worksheet_schema(4, mixed=True),
        ]
        for schema in schemas:
            self.assertEqual(schema['type'], 'object')
            assert_strict_objects(self, schema)

    def test_dynamic_schemas_require_exact_requested_counts(self):
        lesson = lesson_sections_schema(['title', 'activities'], {'activities'})
        self.assertEqual(lesson['properties']['sections']['minItems'], 2)
        self.assertEqual(lesson['properties']['sections']['maxItems'], 2)
        self.assertEqual(handout_schema(7)['properties']['questions']['maxItems'], 7)
        mixed = worksheet_schema(3, mixed=True)
        self.assertIn('type', mixed['properties']['questions']['items']['required'])
        regular = worksheet_schema(3)
        self.assertNotIn('type', regular['properties']['questions']['items']['properties'])

    @patch('openai_service.reserve_attempt')
    @patch('openai_service.get_client')
    def test_service_sends_strict_schema_through_responses_text_format(self, client, reserve):
        schema = worksheet_schema(2)
        client.return_value.responses.create.return_value = Mock(status='completed', output_text='{"questions": []}')
        generate_text([{'role': 'user', 'content': 'Create JSON.'}], response_schema=schema,
                      schema_name='worksheet_questions')
        request = client.return_value.responses.create.call_args.kwargs
        self.assertEqual(request['text']['format'], {
            'type': 'json_schema', 'name': 'worksheet_questions', 'strict': True, 'schema': schema,
        })
        self.assertFalse(request['store'])

    @patch('openai_service.get_client')
    def test_invalid_schema_configuration_never_calls_provider(self, client):
        with self.assertRaises(GenerationUnavailableError):
            generate_text([{'role': 'user', 'content': 'Create JSON.'}], response_schema={'type': 'array'})
        with self.assertRaises(GenerationUnavailableError):
            generate_text([{'role': 'user', 'content': 'Create JSON.'}], response_schema={'type': 'object'},
                          schema_name='spaces are invalid')
        client.assert_not_called()


if __name__ == '__main__':
    unittest.main()
