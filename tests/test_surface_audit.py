import unittest
from pathlib import Path

import app


class SurfaceAuditTests(unittest.TestCase):
    def test_route_and_method_inventory_is_explicit(self):
        expected = {
            '/': {'GET'}, '/about': {'GET'}, '/builder/': {'GET','POST'},
            '/choose': {'GET'}, '/clear_cache': {'POST'}, '/contact': {'GET'},
            '/features': {'GET'}, '/handouts/': {'GET','POST'}, '/health': {'GET'},
            '/home': {'GET','POST'}, '/output': {'GET','POST'}, '/products': {'GET'},
            '/prompt_selection': {'GET','POST'}, '/redirect_choice': {'POST'},
            '/second_landing': {'GET'}, '/version': {'GET'}, '/worksheet': {'GET','POST'},
        }
        actual = {
            rule.rule: set(rule.methods) - {'HEAD','OPTIONS'}
            for rule in app.app.url_map.iter_rules() if rule.endpoint != 'static'
        }
        self.assertEqual(actual, expected)

    def test_production_template_and_static_inventory_is_explicit(self):
        root = Path(__file__).resolve().parents[1]
        templates = {path.relative_to(root/'templates').as_posix() for path in (root/'templates').rglob('*') if path.is_file()}
        expected_templates = {
            'about.html','builder.html','choose.html','contact.html','features.html',
            'generation_error.html','generation_ready.html','handouts.html','home.html',
            'landing.html','products.html','prompt0_form.html','prompt1_form.html',
            'prompt2_form.html','prompt3_form.html','prompt4_form.html','prompt5_form.html',
            'second_landing.html','unit_plan.html','worksheet_display.html','worksheet_input_form.html',
        }
        self.assertEqual(templates, expected_templates)
        static = {path.relative_to(root/'static').as_posix() for path in (root/'static').rglob('*') if path.is_file()}
        self.assertEqual(static, {'builder.js','css/builder.css','css/styles.css','img/logo.png','img/logo2.png'})
