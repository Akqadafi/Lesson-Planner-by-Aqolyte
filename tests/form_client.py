from flask.testing import FlaskClient
from bs4 import BeautifulSoup

class FormClient(FlaskClient):
    """Submit legacy forms with a token fetched from the rendered UI."""
    def post(self, path, *args, **kwargs):
        if path in {'/home','/worksheet','/prompt_selection','/redirect_choice','/output','/clear_cache'}:
            data = dict(kwargs.get('data') or {})
            if 'csrf' not in data:
                page = self.get('/worksheet')
                data['csrf'] = BeautifulSoup(page.data, 'html.parser').select_one('input[name=csrf]')['value']
            kwargs['data'] = data
        return super().post(path, *args, **kwargs)

def client(application):
    return FormClient(application, application.response_class)
