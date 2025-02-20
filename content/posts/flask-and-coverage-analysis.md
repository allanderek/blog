---
title: Flask and Coverage Analysis
date: 2016-01-25T15:20:50Z
tags: ["python", "selenium", "testing", "coverage"]
---
# Flask + Coverage Analysis

This post demonstrates a simple web application written in Flask with coverage
analysis for the tests. The main idea should be pretty translatable into most
Python web application frameworks.

### Update

I've updated this scheme and described the update [here](link://slug/update-flask+coverage).

## tl;dr

If you're having difficulty getting coverage analysis to work with Flask then
have a look at my [example repository](https://github.com/allanderek/flask-coverage-example).
The main take away is that you simply start the server in a process of its own
using `coverage` to start it. However, in order for this to work you have to
make sure you can shut the server process down from the test process. To do this
we simply add a new "shutdown" route which is only available under testing. Your
test code, whether written in Python or, say Javascript, can then make a request
to this "shutdown" route once it completes its tests. This allows the server
process to shutdown naturally and therefore allow 'coverage' to complete.

## Introduction

It's a good idea to test the web applications you author. Most web application
frameworks provide relatively solid means to do this. However, if you're doing
browser automated functional tests against a live server I've found that getting
[coverage](https://pypi.python.org/pypi/coverage) to work to be non-trivial. A quick search will reveal similar
difficulties such as [this](http://stackoverflow.com/questions/23745370/setting-up-coverage-py-with-flask)
stack overflow question, which ultimately points to the [coverage documentation
on sub-processes](http://coverage.readthedocs.org/en/latest/subprocess.html).

Part of the reason for this might be that the Flask-Testing extension provides
live server testing class that starts your server in testing mode as part of
the start-up of the test. It then also shuts the server process down, but in
so doing does not allow coverage to complete.

A simpler method is to start the server process yourself under coverage. You
then only need a means to shutdown the server programatically. I do this by
adding a `shutdown` route.


## Example repository

If you just wish to look at the code check out the
[example repository](https://github.com/allanderek/flask-coverage-example).

The README should explain how to work this but roughly:

```shell
    $ git clone https://github.com/allanderek/flask-coverage-example.git
    $ cd flask-coverage-example
    $ . setup.fish # or source setup.sh
    $ python manage.py test
```

You should then be able to look in the `htmlcov` directory to see the source
marked-up with all the lines ran. Specially open the file
`htmlcov/app_main_py.html`.

To see an example of a missing line, locate the lines:

```python
    try:
        check_fraction(50, 100, '50 of 100 is 50%')
        check_fraction(20, 30, '20 of 30 is 66%')
        check_fraction(50, 10, 'Invalid: Fraction greater than Total')
        check_fraction(0, 0, '0 of 0 is 0%')
```

Comment out some of them, say the bottom two, re-run `python manage.py test`
and reload `htmlcov/app_main_py.html` in your browser.

## Server process

**Update:** The code in this section has been updated in the
[update post](link://slug/update-flask+coverage) and in the
[example repository](https://github.com/allanderek/flask-coverage-example).

In the [example repository](https://github.com/allanderek/flask-coverage-example)
if you look in the `manage.py` file you'll see the code to start the server
process. This is in the `run_with_test_server` function which starts the server
*and* an additional process, that should be the process that you use to actually
test the server. This process can be anything you like such as, in the example's
case `pytest app/main.py`, or it could be an external call to casperJS
instance if you want to write your browser tests in Javascript.

However, the main points are:

  * Starting the server process under coverage analysis
  * Waiting for the server process to indicate that it has started listening
  * Then starting your test process
  * Waiting for **both** processes to complete.
  * Finally running `coverage report` and `coverage html`

In a simpler form to that in the example repository this would be:

```python
    import subprocess
    server_command = ['coverage', 'run', '--source', 'app.main',
                      'manage.py', 'run_test_server']
    server = subprocess.Popen(server_command, stderr=subprocess.PIPE)
    for line in server.stderr:
        if line.startswith(b' * Running on'):
            break
    test_command = ['pytest', 'app/main.py']
    test_process = subprocess.Popen(test_command)
    test_process.wait(timeout=60)
    server_return_code = server.wait(timeout=60)
    os.system("coverage report -m")
    os.system("coverage html")
    return server_return_code
```

## Closing down the server

Notice that the above **waits** for the server process to end. Ordinarily the
server process has to be killed since it expects to run indefinitely. To solve
that we add a `shutdown` route. This is done in `manage.py`:


```python
def shutdown():
    """Shutdown the Werkzeug dev server, if we're using it.
    From http://flask.pocoo.org/snippets/67/"""
    func = flask.request.environ.get('werkzeug.server.shutdown')
    if func is None:  # pragma: no cover
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'


@manager.command
def run_test_server():
    """Used by the phantomjs tests to run a live testing server"""
    # running the server in debug mode during testing fails for some reason
    application.config['DEBUG'] = True
    application.config['TESTING'] = True
    port = application.config['TEST_SERVER_PORT']
    # Don't use the production database but a temporary test database.
    application.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///test.db"
    database.create_all()
    database.session.commit()

    # Add a route that allows the test code to shutdown the server, this allows
    # us to quit the server without killing the process thus enabling coverage
    # to work.
    application.add_url_rule('/shutdown', 'shutdown', shutdown,
                             methods=['POST', 'GET'])

    application.run(port=port, use_reloader=False, threaded=True)

    database.session.remove()
    database.drop_all()
```

This code mostly speaks for itself. The `shutdown` method is obviously the one
we wish to call when the tests are done. We add it to the application route
handler via the call to `application.add_url_rule`. An alternative is to use a
decorator to mark routes as 'test-only'. I quite like the method used here since
it means the routes are only ever added at all when we start the test server.

### Startup and Shutdown

For many test strategies you will want to do something before and after the
server runs. In this example we setup the database to use a temporary database,
in which we create all of the tables anew:

```python
    # Don't use the production database but a temporary test database.
    application.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///test.db"
    database.create_all()
    database.session.commit()
```

At the end of the test we remove the database session and drop all of the
contents of the database.

```python
    database.session.remove()
    database.drop_all()
```

In a real test-suite you may well have a way of factoring out this start-up and
tear-down code, but I've left it as simple and test-framework agnostic for this
example as I could.

### At the end of your tests

**Update:** This section is now not required. See the
[update post](link://slug/update-flask+coverage).

Now for this `shutdown` to actually work, your test suite has to call access
the `shutdown` route. There are many ways to write this and it will hugely
depend on your test framework. However, in the example repository it is done
via:

```python
finally:
    driver.get(get_url('shutdown'))
    driver.close()
```

In the `test_my_server` method. **Update:** Not now it isn't as this is not
required at all.

## Conclusion

Go see the [example repository](https://github.com/allanderek/flask-coverage-example).
