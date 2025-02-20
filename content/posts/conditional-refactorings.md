---
title: Conditional refactorings
date: 2017-04-21T14:41:48Z
tags: ["python", "refactoring", "conditionals", "requests"]
---
I have been reading through some of the [source code](https://github.com/kennethreitz/requests) from the [requests](http://docs.python-requests.org/en/master/) library. This is one of the more well-known, well-used, well-loved, and well-praised  Python libraries I know of. I came across some conditional code which I personally would refactor. A first refactor I'm pretty confident about whilst a second I'm less certain is an improvement. I'll detail them both and welcome any comments anyone has.

A specific example of this kind of conditional comes in the [adapters module](https://github.com/kennethreitz/requests/blob/master/requests/adapters.py) specifically the [cert_verify method](https://github.com/kennethreitz/requests/blob/master/requests/adapters.py#L200). Here is the code in question, slightly snipped for brevity:

```python
    def cert_verify(self, conn, url, verify, cert):
        """Verify a SSL certificate. This method should not be called from user
        ...
        :param verify: Either a boolean, in which case it controls whether we verify
        """
        if url.lower().startswith('https') and verify:

            cert_loc = None

            # Allow self-specified cert location.
            if verify is not True:
                cert_loc = verify

            if not cert_loc:
                cert_loc = DEFAULT_CA_BUNDLE_PATH

            if not cert_loc or not os.path.exists(cert_loc):
                raise IOError("Could not find a suitable TLS CA certificate bundle, "
                              "invalid path: {0}".format(cert_loc))

            conn.cert_reqs = 'CERT_REQUIRED'

            if not os.path.isdir(cert_loc):
                conn.ca_certs = cert_loc
            else:
                conn.ca_cert_dir = cert_loc
        else:
            conn.cert_reqs = 'CERT_NONE'
            conn.ca_certs = None
            conn.ca_cert_dir = None
```

The two refactors I would consider is the setting of `cert_loc` and the order of the two conditional branches, ie. the `if` and `else` branches.

## Setting `cert_loc`

This kind of pattern is quite common where a variable is set to a particular value and then a condition is evaluated which may result in the variable being updated. In this particular example we have:

```python
    cert_loc = None

    # Allow self-specified cert location.
    if verify is not True:
        cert_loc = verify

    if not cert_loc:
        cert_loc = DEFAULT_CA_BUNDLE_PATH
```

First of all note that `verify` cannot be `Falsey`. So at the end of these conditionals `cert_loc` will either be `DEFAULT_CA_BUNDLE_PATH` if `verify` is exactly `True` or it will be set to whatever `verify` is. So we can write this more succinctly as:

```python
    cert_loc = DEFAULT_CA_BUNDLE_PATH if verify is True else verify
```

If you don't like the conditional *expression* you can do this as:

```python
    if verify is True:
        cert_loc = DEFAULT_CA_BUNDLE_PATH
    else:
        cert_loc = verify
```

All this was only really possible because we knew that `verify` could not be `Falsey`. Still I consider the setting of a variable to a default before then considering whether or not to update it to be a very minor anti-pattern. So imagine that we could not be sure that `verify` is not `Falsey`, we could still re-write our conditional without the default setting as:

```python
    if verify is True or not verify:
        cert_loc = DEFAULT_CA_BUNDLE_PATH
    else:
        cert_loc = verify
```

More generally where you see the pattern:

```python
    x = None
    if cond1:
        x = val1
    if cond2:
        x = val2
    ...
    if not x:
        x = default_x
```

Then you can change this to be:

```python
    if cond1 and val1:
        x = val1
    elif cond2 and val2:
        x = val2
    else:
        x = default_x
```

Sometimes this is awkward if one or more of the `val_?` values are interesting expressions.

One defence of the original style is that you know your variable will be set to *something* so you will never end up with an undefined variable error. However, if this were ever the case then you have not fully written down your logic, and hence the early error is likely a good thing.


## Switch the `if` and `else` branches

A suggestion I often make when you have two branches, such that one is significantly shorter than the other, is to have the shorter branch first. The reason for this is to give the reader less of a "stack" to recall as they are reading through the code. Often when reading code you get to the end of the long branch, to find a shorter second branch but you've forgotten what the original condition was. So, it's tempting to suggest to modify the original condition as:

```python

    if not (url.lower().startswith('https') and verify):
        conn.cert_reqs = 'CERT_NONE'
        conn.ca_certs = None
        conn.ca_cert_dir = None
        cert_loc = None
    else:
        # Allow self-specified cert location.
        if verify is not True:
            cert_loc = verify

        if not cert_loc:
            cert_loc = DEFAULT_CA_BUNDLE_PATH

        if not cert_loc or not os.path.exists(cert_loc):
            raise IOError("Could not find a suitable TLS CA certificate bundle, "
                          "invalid path: {0}".format(cert_loc))

        conn.cert_reqs = 'CERT_REQUIRED'

        if not os.path.isdir(cert_loc):
            conn.ca_certs = cert_loc
        else:
            conn.ca_cert_dir = cert_loc
```

I hesitate to suggest it in this case because the original `if` branch has code which depends upon the condition, namely that `verify` is not `Falsey`. However, more generally this can be something of a win for the person reading the code.

So, two pretty simple refactors, thoughts?

