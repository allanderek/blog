---
title: Selenium vs CasperJS
date: 2016-01-08T11:11:40Z
tags: ["python", "selenium", "testing", "casperjs"]
---
Suppose you have a web service using a Python web framework such as Flask.
So you wish to do a full user test by automating the browser. Should you use
the Python bindings to Selenium or CasperJS? In this post I wish to detail some
of the advantages and drawbacks of both.

## Python + Selenium Setup

This is fairly straightforward. You are simply writing some Python code that
happens to call a library which binds to Selenium. In order for this to work
you will need to install phantomJS but using `npm` this is pretty trivial.

## Javascript + CasperJS Setup

I say Javascript, but at least when I'm using casperJS it tends to be from
Coffeescript, but whichever is your fancy works well enough. Similarly to the
above you will need to install casperJS through the `npm` but again this is
pretty trivial.


## Speed

For my sample project the casperJS tests are faster, by quite a bit. This
certainly warrants some more investigation as to exactly why this is the case,
but for now my sample project runs the casperJS tests in around 3 seconds whilst
the Selenium ones take around 12 seconds to do the same amount of work. I'm not
sure whether this is a constant factor or whether it will get worse with more
tests.


## Readability

This of course depends on how easily you can read Coffee/Javascript. For my
money the Python code is a bit easier. The CasperJS code is muddied somewhat
because for each step in the navigation you are obliged to pass in a callback
function, hence a lot of your test code looks something like (in Coffeescript):

    casper.thenOpen (@get_url '/welcome'), ->
      test.assertSelectorHasText 'h1.main-title' 'Welcome to My Homepage'

This means you have to be slightly careful if, for example, you assign to a
variable that you later want to use in your test. I'm fairly certain that some
of my difficulties here are related to being much more familiar with Python than
I am with Coffeescript.

## Multiple Windows

CasperJS has a limitation that during testing you cannot have multiple windows.
Each browser window corresponds to a casper instance. For some reason during
testing you cannot have multiple casper instances. You can do this outwith the
provided test framework. So in theory you could simply write your tests without
the provided test framework. Of course in this case you would lose some of the
convenience of having a test framework available to you.

An obvious example of the use of multiple windows is testing the effects of an
update. Suppose you want one user to, for example, post a comment, and see that
another user can see the comment without necessarily navigating away from their
current page, or even refreshing the entire page.

## Navigation Steps

Certainly for navigation steps which involve loading a new page, casperJS offers
a more reliable solution. There are several work arounds for selenium, and it
does have an 'implicit wait' functionality. But these do not seem to be entirely
reliable. The casperJS solution does require you to be a bit more explicit
about your navigation steps, but that does not appear to be a bad thing, other
than, as noted above, it can obscure the logic of your navigation steps to
some degree.

Navigation steps which do not navigate to a new page, but that you expect to
have some effect, presumably on the DOM, have a similar problem in casperJS as
all navigation steps do in selenium. So, in particular, if you make an AJAX
request and want to see that response causes the DOM to be updated in the way
that you expect, then you have to do some kind of 'waitFor' in both casperJS
and selenium.

## Separation

One pleasing aspect of using casperJS is that your tests are nicely separated
from your Python code. On the other hand this makes it a bit more difficult to
write specific unit tests. I tend to avoid this, but doing so can speed up your
tests dramatically.

## Conclusion

No real conclusion here, both are workable solutions and both have their
drawbacks. Which one you choose will depend entirely on the application that
you have in mind and doing a little both is quite possibly the best solution.
