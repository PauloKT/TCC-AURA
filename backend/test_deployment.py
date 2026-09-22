"""Exercise production static delivery without runserver's development handler."""
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import Client, TestCase, override_settings


class ProductionDeliveryTests(TestCase):
    def test_https_pages_and_collected_assets_with_debug_disabled(self):
        with TemporaryDirectory() as static_root:
            with override_settings(DEBUG=False, SECURE_SSL_REDIRECT=True, STATIC_ROOT=static_root):
                call_command('collectstatic', interactive=False, verbosity=0, ignore_patterns=['*.html', '*.cjs'])
                client = Client()
                self.assertEqual(client.get('/login.html').status_code, 301)
                for path in ['/login.html', '/register.html', '/professor.html', '/aluno.html', '/confirmar-presenca.html']:
                    self.assertEqual(client.get(path, secure=True).status_code, 200, path)
                for path in ['/static/app.css', '/static/api.js', '/static/brand.svg']:
                    response = client.get(path, secure=True)
                    self.assertEqual(response.status_code, 200, path)
                    self.assertTrue(b''.join(response.streaming_content), path)
                    response.close()
