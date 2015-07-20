# -*- coding: utf-8 -*-

# http://www.fullstackpython.com/web-frameworks.html
#
# Common web framework functionality
#
# Frameworks provide functionality in their code or through extensions to
# perform common operations required to run web applications. These common
# operations include:
#
# - URL routing
# - HTML, XML, JSON, and other output format templating
# - Database/NoSQL/cache manipulation
# - Security against Cross-site request forgery (CSRF) and other attacks
# - Session storage and retrieval

# http://groovematic.com/2013/03/tornado-lessons-learned/
#
# Tornado has its own web framework (much like web.py).
# Tornado has its own templating language (quite similar to Jinja).
# Tornado has its own web server.

# http://tornado.readthedocs.org/en/latest/guide.html
import tornado.ioloop           # the Tornado event-loop
import tornado.gen              # the Tornado async framework
import tornado.web              # the Tornado web framework
import tornado.httpclient       # the Tornado API library
import tornado.template         # the Tornado templating language
from tornado.httpclient import AsyncHTTPClient
from tornado.options import define, options

# http://momoko.readthedocs.org/en/latest/
import momoko

import logging
import json


logging.basicConfig(level=logging.INFO)

define('db_database', default='db_database', help='Database name')
define('db_user', default='db_user', help='Database connection username')
define('db_password', default='db_password', help='Database connection password')
define('db_host', default='127.0.0.1')
define('db_port', default='5432')
tornado.options.parse_config_file('sample.conf')


# handles incoming request, this is the C part in MVC
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write('Hello, world')


# handles incoming request
class JsonHandler(tornado.web.RequestHandler):
    def compute_etag(self):
        # Disable etag computation
        return None

    def set_default_headers(self):
        self.set_header('Content-Type', 'application/json')

    def get(self):
        result = {
            'a': self.get_argument('a', default='aaa'),
            'b': self.get_argument('b', default='bbb')
        }
        self.write(json.dumps(result))


# handles incoming request
class QueryPgHandler(tornado.web.RequestHandler):
    # http://tornado.readthedocs.org/en/latest/gen.html#tornado.gen.coroutine
    #
    # Decorator for asynchronous generators.
    #
    # Any generator that yields objects from this module must be wrapped
    # in either this decorator or `engine`.
    #
    # Coroutines may "return" by raising the special exception
    # `Return(value) <Return>`. A coroutine that simply wishes to exit
    # early may use the ``return`` statement without a value.
    #
    # Functions with this decorator return a `.Future`.  Additionally,
    # they may be called with a ``callback`` keyword argument, which
    # will be invoked with the future's result when it resolves.  If the
    # coroutine fails, the callback will not be run and an exception
    # will be raised into the surrounding `.StackContext`.  The
    # ``callback`` argument is not visible inside the decorated
    # function; it is handled by the decorator itself.
    #
    # From the caller's perspective, ``@gen.coroutine`` is similar to
    # the combination of ``@return_future`` and ``@gen.engine``.
    @tornado.gen.coroutine
    def get(self):
        # To execute several queries in parallel, accumulate corresponding futures
        # and yield them at once:
        db_cursors = yield [
            self.application.db.execute('SELECT * FROM auth_user;'),
            self.application.db.execute('SELECT * FROM auth_user;')
        ]

        auth_user_data = list()
        auth_user_data.extend([{'username': r[4]} for r in db_cursors[0].fetchall()])
        auth_user_data.extend([{'username': r[4]} for r in db_cursors[1].fetchall()])

        self.render('template', auth_user=auth_user_data)


# handles incoming request
class QueryHttpHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        # Executes a request, asynchronously returning an `HTTPResponse`.
        response = yield AsyncHTTPClient().fetch('http://localhost:8888/json')
        result = json.loads(response.body)
        auth_user_data = [{'username': result['a']}, {'username': result['b']}]

        self.render('template', auth_user=auth_user_data)

if __name__ == '__main__':

    # An I/O event loop for non-blocking sockets.

    # In general you should use `IOLoop.current` as the default when
    # constructing an asynchronous object, and use `IOLoop.instance`
    # when you mean to communicate to the main thread from a different one.
    #
    # http://groovematic.com/2013/03/tornado-lessons-learned/
    ioloop = tornado.ioloop.IOLoop.current()

    # prepares the application
    application = tornado.web.Application([
        (r'/json', JsonHandler),
        (r'/query/db', QueryPgHandler),
        (r'/query/http', QueryHttpHandler),
    ])

    application.db = momoko.Pool(
        dsn='dbname=%s user=%s password=%s host=%s port=%s' % (
            options.db_database,
            options.db_user,
            options.db_password,
            options.db_host,
            options.db_port),
        size=1,
        max_size=3,
        ioloop=ioloop,
        setsession=('SET TIME ZONE UTC',),
        raise_connect_errors=False,
    )

    logging.info('Connecting to PostgreSQL on [%s]' % options.db_host)
    ioloop.run_sync(lambda: application.db.connect())

    logging.info('Listening on [8888] port')
    application.listen(8888)

    # prepares the web server
    # srv = tornado.httpserver.HTTPServer(application, xheaders=True)

    # listens incoming request on port 8000
    # srv.bind(8888, '')

    # starts the server using 1 process
    # srv.start(1)

    logging.info('Starting IO loop')
    ioloop.start()


# Asynchronous programming with Tornado
# http://lbolla.info/blog/2012/10/03/asynchronous-programming-with-tornado

# MotorEngine MongoDB Async ORM
# https://motorengine.readthedocs.org/en/latest/index.html

