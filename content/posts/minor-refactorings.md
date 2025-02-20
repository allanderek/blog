---
title: Minor Refactorings
date: 2017-02-07T14:28:05Z
tags: ["python", "maintenance", "refactoring"]
---
Looking through the code of an open-source Python project I came across code that amounts to the following:

```python
    host_name = self.connection.getsockname()[0]
    if self.server.host_name is not None:
        host_name = self.server.host_name
```

This looks odd because if the condition is `True` then we forget about the `host_name` derived from the call to `self.connection.getsockname`. However it could be that that call has some side-effect. Assuming that it does not we can re-write the above code as:

```python
    if self.server.host_name is not None:
        host_name = self.server.host_name
    else:
        host_name = self.connection.getsockname()[0]
```

Or even, if you prefer:

```python
    host_name = self.server.host_name if self.server.host_name is not None else self.connection.getsockname()[0]
```

Or:

```python
    host_name = self.server.host_name
    if host_name is None:
        host_name = self.connection.getsockname()[0]
```

Or finally:

```python
    host_name = self.server.host_name or self.connection.getsockname()[0]
```

Note that this last version has slightly different semantics in that it will use the call to `getsockname` if `self.server.host_name` is at all falsey, in particular if it is `''`.

I love finding minor refactoring opportunities like this. I enjoy going through code and finding such cases. I believe if a project's source code has many such opportunites it hints that the authors do not engage in routine refactoring. However, this post is more about how such a refactoring interacts with Python's `@property' decorator.

## The `@property` decorator

In this case we call `getsockname`, so when considering our refactoring we have to be careful that there are no significant side-effects. However even if the code had been:

```python
    host_name = self.connection.host_name
    if self.server.host_name is not None:
        host_name = self.server.host_name
```

We would still have to go and check the code to make sure that either `connection` or `host_name` is not implemented as `property` and if so, that they do not have significant side-effects.

One question arises. What to do if it *does* have significant side-effects? Leaving it as is means subsequent readers of the code are likely to go through the same thought process. The code as is, **looks** suspicious.

First off, if I could, I'd refactor `self.connection.host_name` so that it does not have side-effects, perhaps the side-effects are put into a separate method that is called in any case:

```python
    self.connection.setup_host_name()
    if self.server.host_name is not None:
        host_name = self.server.host_name
    else:
        host_name = self.connection.host_name
```

Assuming I don't have the ability to modify `self.connection.host_name`, I could still refactor my own code to have the side-effects separately. Something like:

```python
class Whatever(...):
    def setup_host_name(self):
        self._host_name = self.connection.host_name

    ....
    self.setup_host_name()
    if self.server.host_name is not None:
        host_name = self.server.host_name
    else:
        host_name = self._host_name
```

I think that is better than the easy opt-out of a comment. Obviously in this case we have some control over the class in question since we're referencing `self`. But imagine that `self` was some `other` variable that we don't necessarily have the ability to modify the class of, then a more lightweight solution would be something like:

```python
    if other.server.host_name is not None:
        other.connection.host_name
        host_name = `other`.server.host_name
    else:
        host_name = `other`.connection.host_name
```

This of course assumes that the side-effects in question are not related to `other.server.host_name`. An alternative in either case:

```python
    connection_host_name = other.connection.host_name
    if other.server.host_name is not None:
        host_name = other.server.host_name
    else:
        host_name = connection_host_name
```

I'm not sure that either *really* conveys that `other.connection.host_name` is evaluated for its side-effects. Hence, in this case, I would opt for a comment, but you may disagree.

## Conclusion

The `@property` decorator in Python is very powerful and I love it and use it regularly. However, we should note that it comes with the drawback that it can make code more difficult to evaluate locally.

A comprehensive test-suite would alay most fears of making such a minor refactor.

Finally, finding such code in a code-base is well worth refactoring. The odd bit of code like this is always likely to sneak in unnoticed, and can often be the result of several other simplifications. However, if you find many of these in a project's source code, I believe it is symptomatic of at least one of two things; either the authors don't engage in much refactoring or general code-maintenance, *or* there is a lack of a decent test-suite which makes such refactorings more of a chore.

## Final irrelevant aside

In a [previous post](link://slug/if-as-syntax-possibility) I made a suggestion about `if-as` syntax. I'm still against this idea, however this is the sort of situation it would (potentially) benefit. Our second syntax possibility could have been:

```python
    host_name = self.server.host_name as hn if hn is not None else self.connection.getsockname()[0]
```

Whilst this is shorter and reduces some repetition, it's unclear to me if this is more readable.

