import datetime
import logging
import os

from flask import Flask, request
from flask_cors import CORS

from config.config import load_config
from controllers import rule_engine_controller


# print a nice greeting.
def say_hello(username="World"):
    return '<p>Hello %s!</p>\n' % username


header_text = '''
    <html>\n<head> <title>Fundscorner Supply Chain Finance API</title> </head>\n<body>'''

instructions = '''
    <p><em>Hint</em>: This is a RESTful web service! Append a username
    to the URL (for example: <code>/Thelonious</code>) to say hello to
    someone specific.</p>\n'''
home_link = '<p><a href="/">Back</a></p>\n'
footer_text = '</body>\n</html>'

__logger = logging.getLogger(__name__)

__logger.info("Loading environment........")
# load_config(args.env)
env_name = os.environ.get('env')

if not env_name:
    env_name = 'prod'

load_config(env_name)

__logger.info("Acquiring application: " + str(datetime.datetime.utcnow()))
application = Flask(__name__)

__logger.info("Acquired application: " + str(datetime.datetime.utcnow()))

application.debug = False

__logger.info("adding application routes: " + str(datetime.datetime.utcnow()))

# add a rule for the index page.
application.add_url_rule(
    '/',
    'index',
    (
        lambda: header_text + say_hello() + instructions + footer_text
    )
)

# add a rule when the page is accessed with a name appended to the site
# URL.
application.add_url_rule(
    '/<username>',
    'hello',
    (
        lambda username: header_text + say_hello(username) + home_link + footer_text
    )
)


@application.route('/api_rules_engine/v1/rules/<rule_name>/execute', methods=['POST'])
def add_invoice_post(rule_name):
    body = request.get_json()
    return rule_engine_controller.execute_rule_engine(rule_name, body)


CORS(application)

if __name__ == "__main__":
    application.run(host='0.0.0.0')
