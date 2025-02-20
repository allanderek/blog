---
title: Test First and Mutation Testing
date: 2016-02-19T10:14:43Z
tags: ["python", "testing", "mutation testing", "scc"]
---
# Test First and Mutation Testing

I'm going to argue that mutation testing has a strong use in a test first
development environment and I'll conclude by proposing a mechanism to link
mutation testing to the source code control mechanism to further aid test first
development.

## Test First

Just to be clear, when I say 'test first' I mean development in which before
writing a feature, or fixing a bug, you first write a test which should only
pass once you have completed that feature. For the purposes of this post you
needn't be doing that for every line of code you write. The idea here applies
whether you are writing the odd feature by first writing a test for it, or
whether you have a strict policy of writing no code until there is a test for
it.

## Mutation Testing

Mutation testing is the process of automatically changing some parts of your
source code generally to check that your test suite is not indifferent to the
change. For example, your source code may contain a conditional statement
such as the following:

```python
    if x > 0:
        do_something()
```

Now if we suppose that the current condition is correct, then changing it to
a similar but different condition, for example `x >= 0` or `x > 1` then
presumably this would turn correct code into incorrect code. If your tests are
comprehensive then at least one of them should fail due to the now incorrect
code.

## Fail First

It's easy enough to unintentionally write a test that always passes, or perhaps
passes too easily. One of the reasons for writing the test first is to make sure
that it fails when the feature has not yet been implemented (or fixed). However,
often such a test can fail for trivial reasons. For example you may write a unit
test that fails simple because the method it tests is not yet defined. Similarly
a web test may fail because the route is not yet defined. Unless you continue to
run the test during development of your feature you won't necessarily know that
your test is particularly effective at catching when your feature is broken.


## Fail After

Whether you write the test before your new feature or after the feature is
ready, mutation testing can assist with the problem of non-stringent tests.
Mutation testing can assist in reassuring you that your new test is effective at
catching errors, whether those errors are introduced when the feature is
developed or through later changes. If you apply lots of mutations to your code
and your new test never fails then there is a strong likelihood that you have an
ineffective test that passes too easily.


## Source Code control

A feature I would like to add to a mutation test package is to integrate with
a source code control mechanism such as Git. The mutation tester must choose
lines of the program to mutate. However, your new test is presumably aimed at
testing the new code that you write. Hence we could use the source code control
mechanism to mutate lines of code that are newer than the test or some specified
commit. That way we would focus our mutation testing to testing the efficacy of
the new test(s) with respect to the new or changed lines of code.

This does not preclude doing general mutation testing for features that, for
example, depend upon a lot of existing code. Perhaps your new feature is simply
a display of existing calculations.

## Conclusion

In summary:

  * Mutation testing helps find tests that are ineffective.
  * This plays particularly well with a test first development process in which
    the test often fails the first time for trivial reasons, thus giving you
    false assurance that your test can fail.
  * Integrating source code control to target the mutations towards new code
    could improve this significantly, or at least make it a bit more convenient.
