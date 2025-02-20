---
title: if as syntax possibility
date: 2017-01-14T15:18:08Z
tags: ["python", "syntax"]
---
I have a small niggle that comes up in my Python programming. I'm going to describe it and propose a possible addition to the Python programming language that would mostly solve the problem. However, I have not thought through this language modification at all thoroughly so at the moment it's just a germ of an idea. It wouldn't be a major change or fix any important problem in any case, it would just solve my own personal peeve.

## Properties

First of all, a brief reminder of the very useful 'property' decorator in Python.
You may have an attribute on a class which is initially a simple value. However,
at some point later you realise that you need to calculate that attribute everytime
it is accessed. You may have something like:

    class Person(object):
        def __init__(self, gender):
            self.gender = gender
            self.age = 0

You then realise that this means you would have to continually update the person's
age. So instead you implement `age` as a "property":

    class Person(object):
        def __init__(self, gender):
            self.gender = gender
            self.dob = datetime.today()

        @property
        def age(self):
            return (datetime.today() - self.dob).years

For the most part I like this ability and use it frequently. You may even have
two distinct classes which both implement a particular protocol, part of which
is that the object in question must have a particular attribute. It may be that
for one kind of object the attribute is indeed a simple attribute, but that for
another it must be calculated.

So properties are, I think, generally a good addition to the language. One
downside is that sometimes a simple attribute access, `my_object.my_attribute`
can be a more expensive operation than it looks because it is actually
implemented as a property.

## Peeve

In Python I find myself doing something like the following quite often:

    if object.attribute:
        do_something(object.attribute)
    else:
        do_something_else(object)

For example, I might be showing a user of a web application why they cannot
perform some action they are attempting to:

    if post.unpublishable_reasons:
        for reason in post.unpublishable_reasons:
            flask.flash(reason)
        return render_template('error.html', ...)
    else:
        return render_template('published.html', ...)

Where `post.unpublishable_reasons` might be a property on a `class` which may
take some time to calculate:

    class Post(database.Model):
        ....
        @property
        def unpublishable_reasons(self):
            ... something that takes time and ultimately calculates reasons...
            return reasons

Which then leads me to have code like:

    reasons = post.unpublishable_reasons
    if reasons:
        for reason in reasons:
            flask.flash(reason)
        return render_template('error.html', ...)
    else:
        return render_template('published.html', ...)

This just irks me as a little inelegant. So I confess that I would quite like
Python to allow something like:

    if post.unpublishable_reasons as reasons:
        for reason in reasons:
            flask.flash(reason)
        return render_template('error.html', ...)
    else:
        return render_template('published.html', ...)

## Comprehensions

This might also partially solve a problem with comprehensions in that you can
filter-then-map but not map-then-filter. A filter-then-map looks like:

    positive_doubles = [i * 2 for i in my_numbers if i > 0]

We first filter on each number (whether it is greater than zero) then each of
those numbers which makes it through the filter is multiplied by two. It's a bit
awkward to do the opposite, which is mapping the value first and then filtering
on the result of the map. So if we wanted all the squares of a list of numbers
that are less than 100 we require to do the operation twice:

    small_squares = [i * i for i in my_numbers if (i * i) < 100]

Notice we had to have `i * i` twice. It might be that the operation in question
is quite expensive, so instead we can have two comprehensions:

    small_squares = [x for x in (i * i for i in my_numbers) if x < 100]
    
~~Of course if the list is very long this might be a bit slow because we iterate
through it twice.~~ Edit. Not true as we use a generator on the inner loop as
pointed out in the comments below.

Now if we allow some kind of if-as syntax we might be able to do something like:

    new_list = [y for x in old_list if f(x) as y]

This doesn't allow general filtering but would allow filtering out of falsey values.
I'm much less keen on this as I feel if Python were to attack the map-then-filter
problem for comprehensions then it should solve it completely.

In particular this would not work for the `small_squares` example, for that we
would need to allow something like:

    small_squares = [x for i in my_numbers if (i * i as x) > 100]

Note that this is even more of an extension than that proposed. That is assigning
`x` to a particular sub-expression of the condition.


