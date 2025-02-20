---
title: unittest.mock small gotcha - a humbling tale of failure
date: 2017-02-25T12:36:24Z
tags: ["python", "testing", "mock", "standard library", "3.4", "3.5", "3.6"]
---
Developing a small web application I recently had reason to upgrade from Python 3.4 to Python 3.6. The reason for the upgrade was regarding ordering of keyword arguments and not related to the bug in my test code that I then found. I should have been more careful writing my test code in the first place, so I am writing this down as some penance for not testing my tests robustly enough.


## A Simple example program

So here I have a version of the problem reduced down to the minimum required to demonstrate the issue:

```python
import unittest.mock as mock

class MyClass(object):
    def __init__(self):
        pass
    def my_method(self):
        pass

if __name__ == '__main__':
    with mock.patch('__main__.MyClass') as MockMyClass:
        MyClass().my_method()
        MockMyClass.my_method.assert_called_once()
```

Of course in reality the line `MyClass().my_method()` was some test code that indirectly caused the target method to be called.

### Output in Python 3.4

```shell
$ python3.4 mock_example.py
$
```

No output, leading me to believe my assertions passed, so I was happy that my code and my tests were working. As it turned out, my code was fine but my test was faulty. Here's the output in two later versions of Python of the exact same program given above.

### Output in Python 3.5

```shell
$ python3.5 mock_example.py
Traceback (most recent call last):
  File "mock_example.py", line 12, in <module>
    MockMyClass.my_method.assert_called_once()
  File "/usr/lib/python3.5/unittest/mock.py", line 583, in __getattr__
    raise AttributeError(name)
AttributeError: assert_called_once
```

Assertion error, test failing.

### Output in Python 3.6

```shell
$ python3.6 mock_example.py
Traceback (most recent call last):
  File "mock_example.py", line 12, in <module>
    MockMyClass.my_method.assert_called_once()
  File "/usr/lib/python3.6/unittest/mock.py", line 795, in assert_called_once
    raise AssertionError(msg)
AssertionError: Expected 'my_method' to have been called once. Called 0 times.
```

Test also failing with a different error message. Anyone who is (pretty) familiar with the `unittest.mock` standard library module will know `assert_called_once` was introduced in version 3.6, which is my version 3.5 is failing with an attribute error.

## My test was wrong

The problem was, my original test was not testing anything at all. The 3.4 version of the `unittest.mock` standard library module did not have a `assert_called_once`. The mock, just allows you to call any method on it, to see this you can try changing the line:

```python
        MockMyClass.my_method.assert_called_once()
```

to

```python
        MockMyClass.my_method.blahblah()
```

With `python3.4`, `python3.5`, and `python3.6` this yields no error. So in the original program you can avoid the calling `MyClass.my_method` at all:

```python
if __name__ == '__main__':
    with mock.patch('__main__.MyClass') as MockMyClass:
        # Missing call to `MyClass().my_method()`
        MockMyClass.my_method.assert_called_once() # In 3.4 this still passes.
```

This does not change the (original) results, ` python3.4` still raises **no error**, whereas `python3.5` and `python3.6` are raising the original errors.

So although my code turned out to be correct (at least in as much as the desired method was called), had it been faulty (or changed to be faulty) my test would not have complained.

## The Actual Problem

My mock was wrong. I should instead have been patching the actual method within the class, like so:

```python
if __name__ == '__main__':
    with mock.patch('__main__.MyClass.my_method') as mock_my_method:
        MyClass().my_method()
        mock_my_method.assert_called_once()
```

Now if we try this in all version 3.4, 3.5, and 3.6 of python we get:

```shell
$ python3.4 mock_example.py 
$ python3.5 mock_example.py 
Traceback (most recent call last):
  File "mock_example.py", line 12, in <module>
    mock_my_method.assert_called_once()
  File "/usr/lib/python3.5/unittest/mock.py", line 583, in __getattr__
    raise AttributeError(name)
AttributeError: assert_called_once
$ python3.6 mock_example.py 
$ 
```

So Python 3.4 and 3.6 pass as we expect. But Python3.5 gives an error stating that there is no `assert_called_once` method on the mock object, which is true since that method was not added until version 3.6. This is arguably what Python3.4 should have done.

It remains to check that the updated test fails in Python3.6, so we comment out the call to `MyClass().my_method`:

```shell
$ python3.6 mock_example.py 
Traceback (most recent call last):
  File "mock_example.py", line 12, in <module>
    mock_my_method.assert_called_once()
  File "/usr/lib/python3.6/unittest/mock.py", line 795, in assert_called_once
    raise AssertionError(msg)
AssertionError: Expected 'my_method' to have been called once. Called 0 times.
```

This is the test I **should** have performed with my original test. Had I done this I would have seen that the test passed in Python3.4 regardless of whether the method in question was actually called or not.

So now my test works in `python3.6`, fails in `python3.5` because I'm using the method `assert_called_once` which was introduced in `python3.6`. Unfortunately it incorrectly passes in `python3.4`. So if I want my code to work properly for python versions earlier than 3.6, then I can essentially implement `assert_called_once()` with `assert len(mock_my_method.mock_calls) == 1`. If we do this then my test passes in all three version of python and fails in all three if we comment out the call `MyClass().my_method()`.

## Conclusions

I made an error in writing my original test, but my real sin was that I was a bit lazy in that I did not make sure that my tests would fail, when the code was incorrect. In this instance there was no problem with the code only the test, but that was luck. So for me, this served as a reminder to check that your tests can fail. It may be that mutation testing would have caught this error.

