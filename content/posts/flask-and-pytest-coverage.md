---
title: Flask and Pytest coverage
date: 2017-02-20T16:27:27Z
tags: ["python", "flask", "tests", "coverage"]
---
I have written before about Flask and obtaining test coverage results
[here](link://slug/flask-+-coverage-analysis)
and with an update
[here](link://slug/update-flask+coverage).
This is pretty trivial if you're writing unit tests that directly call the application, but if you actually want to write tests which animate a browser, for example with selenium, then it's a little more complicated, because the browser/test code has to run concurrently with the server code.

Previously I would have the Flask server run in a separate process and run 'coverage' over that process. This was slightly unsatisfying, partly because you sometimes want coverage analysis of your actual tests. Test suites, just like application code, can grow in size with many utility functions and imports etc. which may eventually end up not actually being used. So it is good to know that you're not needlessly maintaining some test code which is not actually invoked.

We could probably get around this restriction by running coverage in both the server process and the test-runner's process and combine the results (or simply view them separately). However, this was unsatisfying simply because it felt like something that should not be necessary. Today I spent a bit of time setting up the scheme to test a Flask application without the need for a separate process.

I solved this now, by not using Flask's included Werkzeug server and instead using the WSGI server included in the standard-library `wsgiref.simple_server` module. Here is, a minimal example:

```python
import flask

class Configuration(object):
    TEST_SERVER_PORT = 5001

application = flask.Flask(__name__)
application.config.from_object(Configuration)


@application.route("/")
def frontpage():
    if False:
        pass # Should not be covered
    else:
        return 'I am the lizard queen!' # Should be in coverage.



# Now for some testing.
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
import pytest
# Currently just used for the temporary hack to quit the phantomjs process
# see below in quit_driver.
import signal

import threading

import wsgiref.simple_server

class ServerThread(threading.Thread):
    def setup(self):
        application.config['TESTING'] = True
        self.port = application.config['TEST_SERVER_PORT']

    def run(self):
        self.httpd = wsgiref.simple_server.make_server('localhost', self.port, application)
        self.httpd.serve_forever()

    def stop(self):
        self.httpd.shutdown()

class BrowserClient(object):
    """Interacts with a running instance of the application via animating a
    browser."""
    def __init__(self, browser="phantom"):
        driver_class = {
            'phantom': webdriver.PhantomJS,
            'chrome': webdriver.Chrome,
            'firefox': webdriver.Firefox
            }.get(browser)
        self.driver = driver_class()
        self.driver.set_window_size(1200, 760)


    def finalise(self):
        self.driver.close()
        # A bit of hack this but currently there is some bug I believe in
        # the phantomjs code rather than selenium, but in any case it means that
        # the phantomjs process is not being killed so we do so explicitly here
        # for the time being. Obviously we can remove this when that bug is
        # fixed. See: https://github.com/SeleniumHQ/selenium/issues/767
        self.driver.service.process.send_signal(signal.SIGTERM)
        self.driver.quit()


    def log_current_page(self, message=None, output_basename=None):
        content = self.driver.page_source
        # This is frequently what we really care about so I also output it
        # here as well to make it convenient to inspect (with highlighting).
        basename = output_basename or 'log-current-page'
        file_name = basename + '.html'
        with open(file_name, 'w') as outfile:
            if message:
                outfile.write("<!-- {} --> ".format(message))
            outfile.write(content)
        filename = basename + '.png'
        self.driver.save_screenshot(filename)

def make_url(endpoint, **kwargs):
    with application.app_context():
        return flask.url_for(endpoint, **kwargs)

# TODO: Ultimately we'll need a fixture so that we can have multiple
# test functions that all use the same server thread and possibly the same
# browser client.
def test_server():
    server_thread = ServerThread()
    server_thread.setup()
    server_thread.start()

    client = BrowserClient()
    driver = client.driver

    try:
        port = application.config['TEST_SERVER_PORT']
        application.config['SERVER_NAME'] = 'localhost:{}'.format(port)

        driver.get(make_url('frontpage'))
        assert 'I am the lizard queen!' in driver.page_source

    finally:
        client.finalise()
        server_thread.stop()
        server_thread.join()
```

To run this you will of course need `flask` as well as `pytest`, `pytest-cov`, and `selenium`:

```shell
$ pip install flask pytest pytest-cov selenium
```

In addition you will need the `phantomjs` to run:

```shell
$ npm install phantomjs
$ export PATH=$PATH:./node_modules/.bin/
```

Then to run it, the command is:

```shell
$ py.test --cov=./ app.py
$ coverage html
```

The `coverage html` is of course optional and only if you wish to view the results in friendly HTML format.

## Notes

I've not used this extensively myself yet, so there may be some problems when using a more interesting flask application.

Don't put your virtual environment directory in the same directory as `app.py` because in that case it will perform coverage analysis over the standard library and dependencies.

In a real application you will probably want to make a `pytest` fixture out of the server thread and browser client. So that you can use each for multiple separate test functions. Essentially your test function should just be the part inside the `try` clause.

I have not used the `log_current_page` method but I frequently find it quite useful so included it here nonetheless.
