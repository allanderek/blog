---
title: Update Flask and Coverage
date: 2016-01-26T14:59:44Z
tags: ["python", "selenium", "testing", "coverage"]
---
# Update: Flask+Coverage Analysis

In a [previous post](link://slug/flask-+-coverage-analysis)
I demonstrated how to get `coverage` analysis working for a Flask web application
in a relatively simple manner. In the section *"At then end of your tests"* I
stated that you needed your tests to clean-up by telling the server to shutdown.
The end of your test code would look something like this:

```python
finally:
    driver.get(get_url('shutdown'))
    ...
```

This could have made things a little fiddly since your test code would have to
make sure to access the `shutdown` route exactly once, regardless of how many
tests were run.

However, I realised that we could remove the burden from the test code by
simply doing this in `manage.py` file.

## Updated `manage.py`

Previously, we had the following code within our `manage.py` script within the
`run_with_test_server` method:

```python
test_process = subprocess.Popen(test_command)
test_process.wait(timeout=60)
server_return_code = server.wait(timeout=60)
```

We now update this to be:

```python
test_process = subprocess.Popen(test_command)
test_process.wait(timeout=60)
port = application.config['TEST_SERVER_PORT']
shutdown_url = 'http://localhost:{}/shutdown'.format(port)
response = urllib.request.urlopen(shutdown_url)
print(bytes.decode(response.read()))
server_return_code = server.wait(timeout=60)
```

Doing so means you can just write your tests without any need to worry about
shutting down the server.
The [example repository](https://github.com/allanderek/flask-coverage-example)
has been appropriately updated.
