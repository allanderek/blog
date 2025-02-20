---
title: Covering dead code
date: 2017-01-03T12:04:24Z
tags: [ "python", "coverage","maintenance","dead code" ]
---

Dougal Matthews has written a [blog post](http://www.dougalmatthews.com/2016/Dec/16/finding-dead-code-with-vulture/)
detailing how [Vulture](https://pypi.python.org/pypi/vulture) can be used to find some dead code.
For me this was an important reminder not to rely on [coverage analysis](https://pypi.python.org/pypi/coverage/)
to detect dead code and remove it from the your maintenance burden. More generally, whilst I adore
automated analysis tools that assist the developer in maintaining their code,
such automated analysis can give a false sense of completeness, or lead to the
developer believing that their code is "good enough". It is not a problem I have
any solution for though. The rest of the post will try to illuminate this view
point through the example of dead-code removal.

Dead code seems like something that should be automatically detected by tools such as both Vulture and coverage.py and
indeed many instances of dead code *are* automatically detected by such tools. However it is
worth remembering that there are instances of dead code which can never be automatically detected.

As a brief reminder, dead code is code that we should delete. We should delete it generally
because it either has no way of being invoked, or because we no longer require its functionality.
Because the former category has a more or less formal definition much of it can (at least in theory)
be detected automatically. The latter category is often more difficult to detect because there
are no hard rules for it. For example, you may have some code to log the state of a particular object,
and this code **is** invoked by production code. However, the reason for logging
the state of a particular object is no longer required. Pretty much no automated analysis can
detect this because simply writing down the rules for when such code is dead is at best non-trivial.

Here are some example categories of dead code along with how we might detect/track such dead code.

## Unused Variables

If you define a variable, but then never use it, the definition is likely dead-code.

    def my_function():
        x = assigned-expr
        # some code that never uses x

Unless the right-hand side of the definition (`assigned-expr`) has some side-effect
which is important then the assignment is dead-code and should be removed. Note here
that coverage analysis would tell you that the line is being executed.

### Detection

As noted coverage analysis won't work here, and you would have to use something
like Vulture. Many decent IDEs will also warn you about most such circumstances.

## Unused Methods/Class definitions

If you simple define a method or class which you never then invoke. The exception
here is if you're developing a library or otherwise exposing an interface. In this
case you should have some automated tests which should invoke the method/class.

### Detection

Can generally be done by coverage analysis. There are however some tricky situations
which were described in the above mentioned
[blog post](http://www.dougalmatthews.com/2016/Dec/16/finding-dead-code-with-vulture/).
Essentially you may add a unit-test to test a particular method, which later becomes
unused by the actual application but is still invoked by the unit test.

## Unused Counters

At one point, you may have decided to keep a count of some particular occurrence,
such as the number of guesses. Perhaps at one stage you displayed the number of
guesses remaining, but later decided to make the number of guesses unlimited.
You may end up with code that looks something like:

    guesses = 0
    def make_guess():
        guess = get_input()
        global guesses
        guesses += 1
        return guess

Originally your `get_input` looked something like this:

    total_guesses = 20
    def get_input():
        remaining = total_guesses - guesses
        return input('You have {} guesses remaining:'.format(remaining))

But since you decided to give unlimited guesses you got rid of that and it is
now simply:

    def get_input():
        return input("Please input a guess:")

### Detection

Slightly more tricky this one since the variable `guesses` **is** inspected,
it is inspected in the update `guesses += 1`. Still you could make ask that your
automated tool ignore such uses and, in this case, still report the variable as
being defined but not used (perhaps Vulture allows this, I don't know).

However, it is not hard to come up with similar examples in which some value is
maintained but never actually used. For example we might have written something
like:

    if total_guesses - guesses > 0:
        guesses += 1

Which would likely fool most automated analyses.

Of course I've called this category "Counters", but it refers to maintaining any
kind of state that you don't utlimately make use of. You may have originally kept
a list/set of guesses made so far so as to prevent someone making the same guess
more than once. If you later decided against this you might forget to remove
the code which updates the set of guesses that have been made.

## Unused Web Application Routes

You may have a route in your web application which is never linked to by any
part of the rest of your application.
Using [Flask](https://pypi.python.org/pypi/Flask/0.12), for this example:

    @route('/misc/contact', methods=['GET'])
    def contact_page():
        """Display a contact us page"""
        return flask.render_template('contact.jinja')

Now, if, in the rest of your application, you never link to this page, then the
page is not likely to be discovered by a user. You may even have a different
contact page, perhaps called "support" or "feedback". Perhaps this new contact
page was built to replace the older one which it has done, but you left the code for
the old route available.

### Detection

This is tricky. First of all, you may perfectly well have a page which is not
linked to within the remainder of your application but you do want to have
available. For example you may have a route (or routes) for an API used by your
associated mobile application. 

If you have some tests you can use coverage analysis, but if you are doing that
you likely originally had some test which covered this page, even if that unit
test only visited the page and checked that it contained some content, for example
you may have had:

    def test_contact_page(self):
        rv = self.app.get('/misc/contact')
        assert b'id="contact-form"' in rv.data

If this test still runs, then your dead route will still be covered by your tests.
Checking whether or not the method is ever referenced directly will not work because
either such a test will not pick up the unused method because it is used within
the `@route` decorator call, or such a test would ignore that but then flag *all*
your routes as unused.

The only relatively robust way would be to check for calls to
`flask.url_for("test_contact_page")`. Such a check would have to look in templates
as well. It may *still* fail because such a call might never actually be invoked.
So the test would have to check the coverage analysis as well.

# Conclusion

I take it for granted that checking for (and removing) dead code is a useful
activity that improves your code quality and removes some of your technical debt
burden. In other words, I take it for granted that dead code represents a form
of technical debt. With that in mind it seems useful to deploy any automated
analyses which can do part of the job for you. However, any code analysis
tool (whether static or dynamic) that cannot detect **all** (of a class of)
problems, has the disadvantage that it will tend to foster a false sense of completeness.

The hope is that doing the automatable part automatically frees the developer up
to do the non-automatable parts. In practice I've found that there is a tendency
to move the goal-posts from "remove all dead-code" to "remove all dead-code that
the automated analysis complains about". More generally from "maintain code free
from problem X" to "maintain code such that the automated tools do not complain about
problem X".

I'm certainly not arguing not to use such automated analyses. However I don't have
a solution for the problem of this implicit and accidental moving (or rather widening)
of the goal posts.
