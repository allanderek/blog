---
title: List arguments and isinstance
date: 2017-01-28T11:36:23Z
tags: ["python", "isinstance", "lists", "containers"]
---
More than a decade and a half ago, [Kragen Javier Sitaker](http://canonical.org/~kragen/) wrote a blog post [isinstance() considered harmful](http://canonical.org/~kragen/isinstance/), a lot of which I believe holds up pretty well today. It's well worth reading it in its entirety but the gist is that rather than testing a value against a specific type, you generally wish to check that a value confirms to a particular interface. Or if you prefer, using `isinstance` is imparting [nominative typing](http://wiki.c2.com/?NominativeAndStructuralTyping) in a language where duck typing is the convention.

I came across what I initially thought was a reasonable use of `isintance` and this post is about my attempts to remove the reliance on `isinstance`.

## The case

Writing a web application often involves checking the contents of the current page for specific content. Usually in the form of CSS selectors, or simply text. I had written a simple method to check whether specific texts were contained in any elements matching a given CSS selector. For example, you may have some way of flashing messages and you want to check that after a given request the resulting web page contains the list of messages that you expect.

However, the general idea can be condensed to the more simple task of checking whether a list of texts are present with a main text. So the general idea is something like the following:

```python

def contains_texts(content, texts):
    for t in texts:
        if t not in content:
            return False
    return True

test_content = "abcdefg qwerty"
assert contains_texts(test_content, ['abcdefg', 'qwerty']) # Passes
```

This works fine, but this is in testing code, so we want to make sure that tests do not inadvertently pass. The problem here is that the `texts` argument is intended to be  a list, or more generally, a container of some strings. The potential problem is that it is easy enough to make the mistake of calling this method with a single string. Strings are iterable, so unfortunately the following assertion passes:

```python
test_content = "abcdefg qwerty"
assert contains_texts(test_content, 'gfedcba') # Passes
```

This is because each of the characters in the single string argument are themselves in the main content, although the string itself is not.

A potential fix for this is to use `isinstance` on the argument:

```python
def isinstance_contains_texts(content, texts):
    if isinstance(texts, str):
        return texts in content
    for t in texts:
        if t not in content:
            return False
    return True

test_content = "abcdefg qwerty"
assert isinstance_contains_texts(test_content, 'abcdefg') # Passes
assert not isinstance_contains_texts(test_content, 'gfedcba') # Passes
```

In this case we do the right thing if the method is called with a single string as the argument, but you could of course instead raise an error. So this basically solves our problem, but at the cost of using `isinstance`.

What happens if the content becomes a bytestring, and the input strings themselves are bytestrings:

```python
assert isinstance_contains_texts(b'hello world', [b'hello', b'world']) # Passes
assert isinstance_contains_texts(b'hello world', b'olleh') # Passes
```

We have the same problem as before. We could of course solve this by using `if isintance(texts, str) or isinstance(texts, bytes)`, but that feels like we're not really solving the essence of the problem.

## Without isinstance

So instead of using `isinstance` we could check for what interface is supported by the argument. If we want to check that it is a singleton argument then we would be looking for something supported by strings and bytestrings, but not by, lists, sets, or other general containers:

```python
>>> str_and_bytestring = [x for x in dir('') if x in dir(b'')]
>>> stringy_but_not_listy = [x for x in str_and_bytestring if x not in dir([])]
>>> stringy_but_not_listy
['__getnewargs__', 'capitalize', 'center', 'endswith', 'expandtabs', 'find', 'isalnum', 'isalpha', 'isdigit', 'islower', 'isspace', 'istitle', 'isupper', 'join', 'ljust', 'lower', 'lstrip', 'maketrans', 'partition', 'replace', 'rfind', 'rindex', 'rjust', 'rpartition', 'rsplit', 'rstrip', 'split', 'splitlines', 'startswith', 'strip', 'swapcase', 'title', 'translate', 'upper', 'zfill']
```

Okay so our test could be whether or not the `texts` argument has an attribute `capitalize`:

```python
def interface_contains_texts(content, texts):
    if hasattr(texts, 'capitalize'):
        return texts in content
    for t in texts:
        if t not in content:
            return False
    return True

test_content = "abcdefg qwerty"
assert interface_contains_texts(test_content, 'abcdefg') # Passes
assert not interface_contains_texts(test_content, 'gfedcba') # Passes
assert interface_contains_texts(b'hello world', [b'hello', b'world'])
assert not interface_contains_texts(b'hello world', b'olleh')
```

Sort of success, but this feels as if we're not really writing down what we mean. We don't really care if `texts` has a `capitalize` attribute at all. What we want to avoid is `texts` being a single argument that happens to be iterable. We can check which attributes containers such as lists and sets have that strings or bytestrings do not:

```python
>>> list_and_set = [x for x in dir([]) if x in dir(set())]
>>> str_or_bytestring = dir('') + dir(b'')
>>> listy_but_not_string = [x for x in list_and_set if x not in str_or_bytestring]
>>> listy_but_not_string
['clear', 'copy', 'pop', 'remove']
```

So we can check if the first argument has a 'clear' attribute:

```python
def interface_contains_texts(content, texts):
    if not hasattr(texts, 'clear'):
        return texts in content
    for t in texts:
        if t not in content:
            return False
    return True

test_content = "abcdefg qwerty"
assert interface_contains_texts(test_content, 'abcdefg') # Passes
assert not interface_contains_texts(test_content, 'gfedcba') # Passes
assert interface_contains_texts(b'hello world', [b'hello', b'world']) # Passes
assert not interface_contains_texts(b'hello world', b'olleh') # Passes
```

Unfortunately, you now cannot pass a generator, the following fails with a type error because `interface_contains_texts` attempts to check if the generator is in the given string.

```python
assert interface_contains_texts(test_content, (x for x in test_content.split())) 
```

Unfortunately there is no attribute that is on a list, set, and generator that is *not* on a string or bytestring. But generators do have a `close` attribute so we could do:

```python
def interface_contains_texts(content, texts):
    if not hasattr(texts, 'clear') and not hasattr(texts, 'close'):
        ...
```

This does feel close to what we want. We are saying "If the argument is not a list, set style container, or a generator, then we treat it as one singleton".

## All of this could be avoided

Another way to do this would be to allow a variable number of arguments into the `contains_texts` function:

```python
def variable_args_contains_texts(content, *texts):
    for t in texts:
        if t not in content:
            return False
    return True

test_content = "abcdefg qwerty"
assert variable_args_contains_texts(test_content, 'abcdefg') # Passes
assert not variable_args_contains_texts(test_content, 'gfedcba') # Passes
assert variable_args_contains_texts(test_content, *['abcdefg', 'qwerty']) # Passes
assert variable_args_contains_texts(b'hello world', b'hello', b'world') # Passes
assert not variable_args_contains_texts(b'hello world', b'olleh') # Passes
assert variable_args_contains_texts(test_content, *(x for x in test_content.split())) # Passes
```

This works for all our cases. You do have to star the argument if you already have a list or generator:

```python
assert variable_args_contains_texts(test_content, *['abcdefg', 'qwerty']) # Passes
assert variable_args_contains_texts(test_content, *(x for x in test_content.split())) # Passes
```

However, recall our original problem was that if you accidentally passed in a single string as the argument your test function may quietly, and erroneously, pass. However, if you forget the star to this function:

```python
>>> variable_args_contains_texts(test_content, ['abcdefg', 'qwerty'])
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "<stdin>", line 3, in variable_args_contains_texts
TypeError: 'in <string>' requires string as left operand, not list
```
You get an error. That's quite alright with me, this will flag up immediately that I've written my test incorrectly and I can fix it immediately. Even if I had the original `contains_texts` and update it to this variable args version, when I re-run my test-suite it will let me know of any places I've forgotten to update the call.

## Conclusion

Its debateable whether or not the `interface_contains_texts` version was better than the original `isintance_contains_texts` version. I prefer it because I feel it is a bit more general. I definitely prefer the eventual `variable_args_contains_texts` version. I guess that's the main conclusion for now, that checking your uses of `isinstance` may lead to a better implementation.

Although I was able to use variable arguments to the solve the problem in this case, there will obviously be cases where that fix does not apply. However, the main takeaway is that you don't necessarily have to swap your `isinstance` use for a `hasattr` use, thereby directly translating the use of `isinstance`. It could be that by having a slightly broader look at the general problem you're trying to solve, another solution is available.

