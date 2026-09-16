"""Serialize requests per browser session before Flask reads session state.

This guard protects the single-process local preview. Deployments with multiple
workers/hosts require a shared lock or transactional storage; this is not a quota.
Fixed lock stripes bound memory; a rare collision yields a safe retry response.
"""
import hashlib
from http.cookies import SimpleCookie, CookieError
import threading


class SessionRequestGuard:
    def __init__(self, application, cookie_name, stripes=128):
        self.application = application
        self.cookie_name = cookie_name
        self.locks = [threading.Lock() for _ in range(stripes)]

    def __call__(self, environ, start_response):
        cookies = SimpleCookie()
        try:
            cookies.load(environ.get('HTTP_COOKIE', ''))
        except CookieError:
            return self.application(environ, start_response)
        cookie = cookies.get(self.cookie_name)
        if cookie is None:
            return self.application(environ, start_response)
        index = int.from_bytes(hashlib.sha256(cookie.value.encode()).digest()[:8], 'big') % len(self.locks)
        lock = self.locks[index]
        if not lock.acquire(blocking=False):
            body = b'A request for this browser session is still running. Wait for it to finish, then reload before retrying. Your saved draft is unchanged.'
            start_response('409 Conflict', [('Content-Type', 'text/plain; charset=utf-8'),
                ('Content-Length', str(len(body))), ('Cache-Control', 'no-store'), ('Retry-After', '2')])
            return [body]
        try:
            # Flask saves its session before returning the response iterable.
            # Release here so streaming a download does not block the workspace.
            return self.application(environ, start_response)
        finally:
            lock.release()
