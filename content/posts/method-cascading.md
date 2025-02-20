---
title: Method Cascading
date: 2016-02-23T14:54:35Z
tags: ["python", "coding style"]
---
# Method Cascading

Vasudev Ram has a thoughful [post about method chaining/cascading](http://jugad2.blogspot.co.uk/2016/02/examples-of-method-chaining-in-python.html)
that I picked up from [planet python](http://planetpython.org/) in which he
basically argues for the use of method cascading. I'm going to disagree.
Essentially, I simply don't understand any benefit of using cascading. It's a
nice post though and includes some references to other method cascading links.

Method chaining is the writing of multiple method calls directly after one
another, usually on the same line, such as (to take Vasudev's example):

    foo.bar().baz()

Cascading is the specific case of chaining in which each intermediate object
is the same object. To achieve this `bar` must return `self` (in Python, or
`this` in other object oriented languages).

Here is Vasudev's first example:

> Let's say we have a class Foo that contains two methods, bar and baz.
> We create an instance of the class Foo:
>
>     foo = Foo()

> Without method chaining, to call both bar and baz in turn, on the object foo, we would do this:

>     # Fragment 1
>     foo.bar() # Call method bar() on object foo.
>     foo.baz() # Call method baz() on object foo.
>
> With method chaining, we can this:
>
>     # Fragment 2
>     # Chain calls to methods bar() and baz() on object foo.
>     foo.bar().baz()

So the claim for method cascading then is:

> One advantage of method chaining is that it reduces the number of times you
> have to use the name of the object: only once in Fragment 2 above, vs. twice
> in Fragment 1; and this difference will increase when there are more method
> calls on the same object. Thereby, it also slightly reduces the amount of code
> one has to read, understand, test, debug and maintain, overall.
> Not major benefits, but can be useful.

So method cascading reduces the number of times you have to use the name of an
object, but this makes it inherently less explicit that you're operating on the
same object. Looking at `foo.bar().baz()` does not tell me that `baz` is being
called on the same object as `bar`. Unless you're keen on method cascading and
use it yourself, it looks like the opposite.

Method cascading may therefore reduce

 >  the amount of code one has to read, understand, test, debug and maintain, overall.

However it does so, only in a "code-golf" way. There is no point in reducing
the amount of code to understand if by doing so you increase the difficulty with
which you can understand it.

A common example of method cascading is one Vasudev includes, that of string
processing. Here we have a line such as (which I've translated into Python 3):

    print ('After uppercase then capitalize:',
            sp.dup().uppercase().capitalize().rep())

Whilst it is quite nice to be able to do this in one line without using a new
variable name, I would write this without method cascading as:

    duplicate = sp.dup()
    duplicate.uppercase()
    duplicate.capitalize()
    print('After uppercase then capitalize:', duplicate.rep())

Now it is obvious that `dup` returns something new, in this case it is a
duplicate of the original string. It is also clear that `uppercase` and
`capitalize` do *not* return new objects but modify the `duplicate` object.

So, I'm afraid I just don't see the use case for cascading.
