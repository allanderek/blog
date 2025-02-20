---
title: In what ways are dynamically typed languages more productive?
date: 2016-05-04T20:41:57Z
tags: ["python", "typing", "testing", "statically typed languages", "dynamically typed languages"]
---
# Introduction

I do not aim to answer the question in the title more raise the question.
The question kind of implies that dynamically typed languages are more
productive in at least some ways. It does not imply that statically typed
languages are less productive in general, or the opposite.

Before going any further, I'm talking about the distinction between static
and dynamic typing which is not the same as strong vs weak typing. Static
means the type checking is done at compilation before the program is run, whilst
dynamic means types are checked whilst the program is running. Not the same as
weak vs strong typing and also not the same as explicit vs implicit typing.

# Background

My PhD involved the development of a novel static type
system. When I begun my PhD I was firmly of the opinion that
statically typed languages were better than dynamically typed
languages. My basic contention was that all the guarantees you get
from static types you get largely for free, so throwing those away is a
stupefying act of self harm. I believe that prior to the turn of the
century (if not a bit later), this the majority view in programming language
research. It is still a position commonly held but I'm unsure whether it may
still be a majority view or not.

New data, should force us to seek out new theories which explain
all of the available data. In the past 20 years, one thing is obvious.
Dynamically typed languages have seen significant growth and success.
Some researchers choose to ignore this. Some explain the success as a
fluke, that such languages have become popular *despite* being
dynamically typed. This is a recurrence of an argument made by
functional programmers/researchers when C++ and then Java became wildly popular.

The prevailing view amongst researchers was that functional languages were inherently
better than Java, but Java got a lot of financial support which meant
that a lot of support was added to, in particular, the standard
library. This meant that programmers were particularly productive
using Java, but that that increase in productivity was mis-attributed
by the programmers to the language, when it should have been placed
firmly in the excellent standard library support. Much of this support
is work that open source programmers are not quite so keen on, because
frankly, it's a bit boring and unrewarding. I personally find this
argument at least lightly compelling.

However, in the first decade of this century, as I said, dynamically typed
languages have had at least significant success. Python, PHP,
and Ruby are the most obvious examples. None of these were backed
financially by any large corporation, at least not prior to their success.
I again suspect that much of the productivity gained with the use of such
languages can be placed in the library support. But that does not explain
where the library support has come from. If dynamically typed languages were so
obviously counter-productive, then why did anyone waste their time
writing library support code in-and-for them?

# Some Wild Hypotheses Appear

I am now going to state some hypotheses to explain this. This does not mean
I endorse any of these.

## Short term vs Long Term

One possible answer. Dynamically typed languages increase *short term*
productivity at the cost of *long term* productivity. I don't personally
believe this but I do find it plausible. However, I do not know of any
evidence for or against this position. I'm not even sure there is much
of a logical argument for it.

The kinds of bugs that functional programming languages help prevent
are the kind of bug that is hard to demonstrate. It is easy enough to show
a bug in an imperative program that would not occur in a functional program
because you do not have mutable state. However, such demonstration bugs
tend to be a bit contrived, and it is hard to show that such bugs come up in
real code frequently. On top of that, to show that functional languages are
more productive one would have to show that by restricting mutable state you
do not lose more productivity than you gain by avoiding such bugs. If you did
manage to show this, you would have a reasonable argument that functional
languages are bad for short-term productivity, due to the restrictions on
mutable state changes, but compensate in greater long-term productivity.

So, a similar kind of argument could be made for statically typed languages.
If you could show that statically typed languages prevent a certain class of
bugs and that the long-term productivity gained from that is more than enough
to compensate for any short-term loss in productivity brought on by restrictions
due to the type-system.

So I will leave my verdict on this hypothesis as, I believe it to be false
but it is plausible. Just to note, there is no great evidence that *either*
statically typed languages have greater long-term productivity,
**or** that dynamically typed languages have greater short-term productivity.

## Testing Tools

A trend that seems to have tracked (ie. correlates with, either via
causation in either direction or by coincidence) the trend in use of
(and success of) dynamically typed languages is the trend towards more
rigorous testing, or rather the rise in popularity of more rigorous testing.
In particular test-driven development style methodologies have gained
significant support.

I believe that having a comprehensive test suite, somewhat dilutes the
benefits gained from a static type system. Here is a good challenge,
try to find a bug that is caught by the type checker, that would not be
caught by a test suite with 100% code coverage.

One possibility is an exhaustive pattern match, however, if your test suite
is not catching this, it's not a great test suite. Still, exhaustive pattern
match tests is something you get more or less for free with a static type checker,
whilst a test suite has to work at it.

It is certainly possible to come up with a bug that is caught by static type checking
and not by a test suite that has full coverage. Here is an example:

```python
    if (a and b):
        x = 1
    else
        x = "1"
    if b:
        return string(x + 2)
    else:
        return x
```

This is a bug, because `b` might be true, whilst `a` is false. Which
would mean that `x` is set to a string, but later treated as an integer,
because `b` is true. A good test suite, will of course catch
this bug. But it is still possible to achieve 100% code coverage (at
the statement) level, and *not* catch this bug. Still, you have to try
quite hard to arrange this.

[Mutation testing](http://en.wikipedia.org/wiki/Mutation_testing),
which tests your tests, rather than your implementation code, should
catch this simple example (because it will mutate the condition
`(a and b)` to be `(a or b)` which won't make any difference if your tests
never caught the bug initially. This will mean that the mutant will
pass all tests, and you should at that point realise your tests are
not comprehensive enough.

## Dynamically Typed Language Benefits

So you should have a comprehensive test suite for all code whether you are
using a statically or dynamically typed language. We may then accept the
theory that a comprehensive test suite somewhat dilutes any benefits of using
a statically typed language. However, that theory does not give any reasaon why
a static type system is detrimental to productivity.

This was always my main contention, that whatever might
be the benefits of static typing, you are getting them for free, so
why not? I honestly do not know what, if any, benefit there is from
having a dynamic type system. I can think of some plausible
candidates, but have no evidence that any of these are true:

1. Freeing the *language* from a type system, allows the language
designers to include some productivity boosting features that are not
available in a statically typed language. I find this suggestion a little weak,
no one has ever been able to point me to such a language feature.
2. Knowing there is no safety net of the type system encourages
developers to test (and document) more. I find this theory more compelling.
3. One can try simple modifications without the need to make many
fiddly changes, such as, for example, adding an exception to a method
signature, often in many places.

I suspect, that if there are significant benefits to using a dynamically
typed language, then it is a combination of 2 and 3, or some other reason.

For the third, a rebuttal often mentions automatic refactoring tools.
Which may well in theory be something of a good rebuttal, but in practice developers simply
don't use such tools often. I'm not sure why not, I myself have never
taken to them. So perhaps there is a productivity gain from using a
dynamically typed language which *would* be all but negated if only
the developers would use automatic refactoring tools, but they don't.
So it *shouldn't* be a productivity win for dynamically typed
languages, but in practice it is (this is all still conjecture).

The second one has some evidence from psychology. There is a lot of
evidence to suggest that safety mechanisms often do not increase
overall safety but simply allow more risky behaviour. A very famous
example is a seat-belt study done in Germany. Wherein mandating the
wearing of seat-belts caused drivers to drive faster. This means that
you are more likely to have a crash, but less likely to be seriously
injured in one. This has similarly been done with anti-lock braking
systems, where the brakes being significantly better did not reduce
accidents but rather increased risky driving so that the number of
accidents remained largely constant.

I mentioned documentation because it's an important one. There are
plenty of libraries for statically typed languages for which the only
documentation for many of the functions/methods is the type signature.
This is often seen as "good enough", or at least good enough to mean
that API documentation is not at the top of the todo stack.
A dynamically-typed language does not typically have signatures for
methods/functions. As a result, they tend to have fewer undocumented
libraries, simply because the developer of the library knows that
their methods will otherwise not be used. If that is the case, what is
the point in the library? So they tend to write *something*, and once
you are writing *something* it isn't so hard to write something
useful.

# Summary

This is getting too long. So I'll stop there for now. The main points are:

1. Dynamically typed languages have had a lot of success this
century, which remains largely unexplained
2. I think that with comprehensive testing, the gains from a static
type system are diluted significantly
3. It might be that dynamically typed language encourage more/better
testing (or have some other non-obvious advantage)
4. Otherwise, there is scant evidence for anything a dynamically
typed language actually does *better*
5. I think an obvious win for statically typed languages would be to
make the type checking phase optional.

I am not sure why we do not really see any examples of languages
that have optional static type checking. In other words languages in which
the user decided when type checking should be done.

As a final point. For dynamically typed languages, it is common to
deploy some form of static analyser. Often these static analysers fall short of
the kind of guarantees afforded by a static type system, but they have
two significant advantages. Firstly, you can run the program without
running the static analyser. In particular, you can run your test
suite, which may well give you more information about the correctness
of your code than a type checker would. Especially in the case that
the type checker fails. It tells you about one specific problem in
your code, but not how the rest of your code does or does not pass
your tests. Secondly you can deploy different static analysers for
different problems. For example a statically typed language has to
decide whether or not to include exceptions in types. A dynamically
typed language can easily offer both. I suppose a statically typed
language *could* offer both as well.
