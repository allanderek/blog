---
title: Placement of Python Import Statements
date: 2016-02-03T13:08:54Z
tags: ["python"]
---
# Placement of Python Import Statements

[Pep 8 specifies](https://www.python.org/dev/peps/pep-0008/#imports)
that all import statements should be "put at the top of the file, just after any
module comments and docstrings, and before module globals and constants."
However, it does not really specify the logic behind this. I'm going to try to
articulate some reasons to have import statements somewhere other than directly
at the top of the file. I'll also state some arguments for having such
`import` statements at the top.

Note, that
[Pep 8 also specifies](https://www.python.org/dev/peps/pep-0008/#a-foolish-consistency-is-the-hobgoblin-of-little-minds)
that it is important to "know when to be inconsistent -- sometimes the style guide just doesn't
apply. When in doubt, use your best judgment". So the purpose of this post is to
suggest some reasons why you might deviate from the style guide with respect to
`import` statements at the top.


## Conditional Import

There are some obvious reasons not to have a particular `import` statement
directly at the start of the file. The most obvious is if you have an optional
path in your application such that you have an optional dependency. So you may
have something like:

```python
if '--mail' in sys.args:
    import fancy.mail.library.module
```

Knowing that if the `--mail` option is not supplied then the module
`fancy.mail.library.module` is never referenced, hence you can avoid importing
it and avoid failing if the dependency is missing.  You may also do this if the
module in question has a long `import` time, since you want to avoid the penalty
for importing it if it is not going to be used.

Neither of these obvious reasons really breaks the spirit of the PEP. If you do
this at the head of the importing module then although you are *technically*
importing within a conditional statement, you're still doing so at the head of
the module. However, there may be a good reason to perform this test only once.
For example you may write at the *bottom* of your module:

```python
if __name__ == '__main__':
    if '--mail' in sys.args:
        import fancy.mail.library.module as mail
        do_work_with_mailer(mail.mailer())
    else:
        do_normal_work()
```

This means that you only test for the `--mail` option once.

## Bunching Imports With Relevant Code

I find I occasionally wish to bunch related definitions together. When I do so,
they often collectively rely on some imports that are not relevant for the rest
of the module I'm writing.

A good feature of this is that import statements can be kept a bit leaner. When
the import statement is immediately above the code that uses it, you are more
likely to delete it if you ever actually stop using the imported module.
Some code analysis software will indeed help you to tidy up unused imports,
which indeed weakens this point.

One argument against this, is that we have separate "bunches" of code then we
should create a separate modules. I tend to be lean on creating new files. I do
not like to create extra source modules without good reason. I find that doing
so tends to solidify your structure. I have written about single-file
programming at length elsewhere and may revisit the subject here again. But the
whole topic is a bit out of scope here. If you believe in making lots of small
modules, then yes keeping `import` statements near the related code is likely
not a terribly convincing reason to break the PEP 8 guideline. Though note,
doing so, might aid you in breaking out some code into a module of its own.


## Reasons to Abide By Pep 8

One good reason to import modules only at the head of the importing module is
that code within the module can be more easily moved around. If you scatter
`import` statements around your module you have to be careful not to move any
code that depends upon an imported module above that module's import statement.

If you're getting really fancy and placing import statements within non-trivial
branching statements then you have to make sure that code which depends upon
an `import` statement is never executed without the `import` statement.

A reasonable test suite will of course prevent you from making either mistake.
But you simply do not open yourself up to this problem at all if you keep all
of your import statements at the top of the module.

## Conclusion

I find myself sticking most imports at the head of the module, mostly just to
comply with `pep8` because whilst I might not see the immediate benefit of this,
any benefits of scattering the import statements throughout your module are
minimal. So this means that it is generally, for me, worth it to keep the
imports at the top. However, it can be well worth considering breaking such
conventions/guidelines even it just forces you to consider the logic behind the
conventions/guidelines in the first place. Blindly following a coding guideline
often ends in using it where inappropriate.
