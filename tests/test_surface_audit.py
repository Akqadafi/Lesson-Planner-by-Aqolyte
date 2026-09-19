import unittest
from pathlib import Path

import app


class SurfaceAuditTests(unittest.TestCase):
    def test_route_and_method_inventory_is_explicit(self):
        expected = {
            '/': {'GET'}, '/about': {'GET'}, '/builder/': {'GET','POST'},
            '/choose': {'GET'}, '/clear_cache': {'POST'}, '/contact': {'GET'},
            '/design-options/': {'GET'}, '/design-options/<option>': {'GET'},
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
            'corporate_base.html','design_options.html','generation_error.html','generation_ready.html','handouts.html','home.html',
            'landing.html','products.html','prompt0_form.html','prompt1_form.html',
            'prompt2_form.html','prompt3_form.html','prompt4_form.html','prompt5_form.html',
            'second_landing.html','unit_plan.html','worksheet_display.html','worksheet_input_form.html',
        }
        self.assertEqual(templates, expected_templates)
        static = {path.relative_to(root/'static').as_posix() for path in (root/'static').rglob('*') if path.is_file()}
        self.assertEqual(static, {'builder.js','css/builder.css','css/corporate.css','css/design-options.css','css/styles.css','img/logo.png','img/logo2.png'})

    def test_ui_previews_are_safe_and_link_to_real_tools(self):
        client = app.app.test_client()
        index = client.get('/design-options/')
        self.assertEqual(index.status_code, 200)
        self.assertIn(b'Teacher workspace', index.data)
        for option in ('workspace', 'guided', 'studio'):
            response = client.get(f'/design-options/{option}')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'/builder/', response.data)
            self.assertIn(b'/worksheet', response.data)
        self.assertEqual(client.get('/design-options/unknown').status_code, 404)

    def test_corporate_home_explains_company_and_first_product(self):
        response = app.app.test_client().get('/')
        self.assertEqual(response.status_code, 200)
        for text in (b'Aqolyte LLC', b'Web products', b'Education tools', b'Applied AI', b'Aqolyte Lesson Planner'):
            self.assertIn(text, response.data)
        for destination in (b'href="/about"', b'href="/products"', b'href="/contact"'):
            self.assertIn(destination, response.data)
        self.assertNotIn(b'href="/builder/"', response.data)
        self.assertIn(b'Explore Lesson Planner', response.data)

    def test_corporate_pages_share_theme_and_one_product_launch(self):
        client = app.app.test_client()
        pages = {path: client.get(path) for path in ('/', '/about', '/products', '/contact')}
        for path, response in pages.items():
            self.assertEqual(response.status_code, 200, path)
            self.assertIn(b'css/corporate.css', response.data, path)
            self.assertIn(b'AQOLYTE', response.data, path)
            self.assertNotIn(b'bootstrap', response.data.lower(), path)
        self.assertEqual(pages['/products'].data.count(b'href="/builder/"'), 1)
        self.assertIn(b'mailto:ceo@aqolyte.com', pages['/contact'].data)
        for path in ('/', '/about', '/contact'):
            self.assertNotIn(b'href="/builder/"', pages[path].data, path)
