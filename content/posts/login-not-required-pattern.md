---
title: Login not required pattern
date: 2017-01-26T00:05:26Z
tags: ["python", "flask", "code maintenance"]
---
# Introduction

Typically routes in a web application that require login are explicitly marked as such. Whilst routes that are open to general (anonymous) users, are left unmarked and hence implicitly do not require login. Because the default is to allow all users to visit a particular route, it is easy to forget to mark a route as requiring a login.

I'm going to show a small pattern for making sure that all routes in a web application are explicitly marked as either requiring login or not-requiring login. As an example this will be done in a Python, Flask-based web application using [Flask-Login](https://flask-login.readthedocs.io/en/latest/) but the general idea probably works in at least some other Python web application frameworks. 

# The Basics

Let's start with a very simple Flask web application that just has two routes:

```python
import flask

app = flask.Flask(__name__, static_folder=None)

@app.route('/unprotected')
def unprotected():
    return 'Hello everyone, anonymous users included!'

@app.route('/protected')
def protected():
    return 'Hello users, only those of you logged-in!'

if __name__ == '__main__':
    app.run()
```

Now, obviously we want the `protected` route to only be available to those users who have logged in, whilst the `unprotected` route is available to all. We'll leave the details of how users actually sign-up, log-in and log-out, see the [Flask-Login documentation for examples](https://flask-login.readthedocs.io/en/latest/).

To mark our `protected` route we can use the decorator provided by Flask-Login:

```python
import flask_login
...

@app.route('/protected')
@flask_login.login_required
def protected():
    return 'Hello users, only those of you logged-in!'
...
```

I only added two lines, the import of `flask_login` and a second decorator to the `protected` method. This is how Flask-Login works. You decorate those routes that you wish to be protected. As I said, this scheme is fine, but it is easy enough to forget to mark a route that should be protected.

# Explicitly mark all routes

The scheme I used, was to make a decorator that accepted a parameter. If the parameter is `True` then all routes associated with the decorated view function are marked as requiring login. In addition, this decorator sets an attribute on the view function itself indicating whether or not login is required. We can then check *all* view functions and assert that they have the chosen attribute. So first the new view functions, with a decorator we'll add.

```python
@app.route('/unprotected')
@login_required(False)
def unprotected():
    return 'Hello everyone, anonymous users included!'

@app.route('/protected')
@login_required(True)
def protected():
    return 'Hello users, only those of you logged-in!'
```

So fairly simple stuff. Now to create the decorator:

```python
def login_required(required):
    def decorator(f):
        if required:
            f = flask_login.login_required(f)
        f.login_required = required
        return f
    return decorator
```

This just calls the original `@flask_login.login_required` decorator in the case that the argument is `True`, but in addition adds an attribute to the view function that we can check later.

## Ensure all are marked

So to ensure that all routes have been marked in some way you just need to check all view functions have the `login_required` attribute set:

```python

for name, view_f in app.view_functions.items():
    message = "{} needs to set whether login is required or not".format(name)
    assert hasattr(view_f, 'login_required'), message

if __name__ == '__main__':
    app.run()
```

Now if you run this you will get such an error. That is because you don't set up all of your own routes, in particular Flask provides a `static` route. That's easy enough to ignore though:

```python
ignored_views = ['static']

for name, view_f in app.view_functions.items():
    message = "{} needs to set whether login is required or not".format(name)
    assert name in ignored_views or hasattr(view_f, 'login_required'), message

if __name__ == '__main__':
    app.run()
```

## Tidy up

There are just a couple of small caveats. Firstly, Flask-Login, provides a decorator to indicate that not only is login required, but it must be a *fresh* login. We can just allow passing `"fresh"` as an argument to our `login_required` decorator:

```python
def login_required(required):
    def decorator(f):
        if required == 'fresh':
            f = flask_login.fresh_login_required(f)
        elif required:
            f = flask_login.login_required(f)
        f.login_required = required
        return f
    return decorator
```

To avoid polluting the namespace with our `ignored_views` name and to indicate what the code is doing without needing a comment we can wrap our check in a function:

```python
def check_all_views_declare_login_required():
    ignored_views = ['static']
    
    for name, view_f in app.view_functions.items():
        message = "{} needs to set whether login is required or not".format(name)
        assert name in ignored_views or hasattr(view_f, 'login_required'), message
check_all_views_declare_login_required()

if __name__ == '__main__':
    app.run()
```

## Flask extensions

Many Flask extensions provide their own routes which are mapped to view functions that they have defined. You *could* add those to the `ignored_views` list, but this seems like additional maintenance. Worse, something like [Flask-Admin](https://flask-admin.readthedocs.io/en/latest/) adds a large number of view functions. In addition, if you setup Flask-Admin to automatically generate model views for each of the models in your database, then if you add to your database model it will generate *more* view functions and you will have to update your `ignored_views` list again. The alternative is to perform your `check_all_views_declare_login_required` before you call `init_app` on your `admin` instance. Suppose you have:

```python
import flask
import flask_login

import flask_debugtoolbar
from flask_sqlalchemy import SQLAlchemy

database = SQLAlchemy()
admin = flask_admin.Admin(name='My app', template_mode='bootstrap3')

.... Code to setup the database and add flask-admin model views ...

.... Actual web application code ...

check_all_views_declare_login_required()
# Initialise the Flask-Admin and Flask-DebugToolbar extensions after we have
# checked our own views for declaring login required.
admin.init_app(app)
flask_debugtoolbar.DebugToolbarExtension(app)

if __name__ == '__main__':
    app.run()
```    

## Final code

Just to provide the code in a simplest-as-possible form:


```python
import flask
import flask_login

app = flask.Flask(__name__, static_folder=None)

def login_required(required):
    def decorator(f):
        if required == 'fresh':
            f = flask_login.fresh_login_required(f)
        elif required:
            f = flask_login.login_required(f)
        f.login_required = required
        return f
    return decorator


@app.route('/unprotected')
@login_required(False)
def unprotected():
    return 'Hello everyone, anonymous users included!'

@app.route('/protected')
@login_required(True)
def protected():
    return 'Hello users, only those of you logged-in!'

def check_all_views_declare_login_required():
    ignored_views = ['static']
    
    for name, view_f in app.view_functions.items():
        message = "{} needs to set whether login is required or not".format(name)
        assert name in ignored_views or hasattr(view_f, 'login_required'), message
check_all_views_declare_login_required()

if __name__ == '__main__':
    app.run()
```

# Conclusion

I quite like that I now explicitly state for each route whether I require login or not, rather than relying on a default. You could of course extend this to your particular privileges scheme, for example you may have levels of authentication, such as, administrator, super-user, paid-user, normal-user, anonymous, or whatever.

Because the check is done whenever the module is imported, this check will also be performed when running your test-suite.

This won't work if your view functions are actually view methods because you won't be able to set the attribute on the view *method*. It is for exactly this reason that we had to use a list of `ignored_views` and could not just do:

```python
    static_view_function = app.view_functions['static']
    static_view_function.login_required = False
```


An alternative to this scheme would be to create your own `route` decorator that takes as parameter whether login is required as well as the normal route information. Essentially combine route and login decorators.
