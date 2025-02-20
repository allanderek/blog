---
title: Selenium and Javascript Events
date: 2016-03-16T18:02:32Z
tags: ["python", "selenium", "testing"]
---
Selenium is a great way to test web applications and it has Python bindings.
I explained in a [previous post](link://slug/flask-+-coverage-analysis) how to
set this up with coverage analysis.

However, writing tests is non-trivial, in particular it is easy enough to write
tests that suffer from race conditions. Suppose you write a test that includes
a check for the existence of a particular DOM element. Here is a convenient method
to make doing so a one-liner. It assumes that you are within a class that has
the web driver as a member and that you're using 'pytest' but you can easily
adapt this for your own needs.

```python
def assertCssSelectorExists(self, css_selector):
    """ Asserts that there is an element that matches the given
    css selector."""
    # We do not actually need to do anything special here, if the
    # element does not exist we fill fail with a NoSuchElementException
    # however we wrap this up in a pytest.fail because the error message
    # is then a bit nicer to read.
    try:
        self.driver.find_element_by_css_selector(css_selector)
    except NoSuchElementException:
        pytest.fail("Element {0} not found!".format(css_selector))
```

The problem is that this test might fail if it is performed too early. If you
are merely testing after loading a page, this should work, however you may be
testing after some click by a user which invokes a Javascript method.

Suppose you have an application which loads a page, and then loads all comments
made on that page (perhaps it is a blog engine). Now suppose you wish to allow
re-loading the list of comments without re-loading the entire page. You might
have an Ajax call.

As before I tend to write my Javascript in Coffeescript, so suppose I have a
Coffeescript function which is called when the user clicks on a
`#refresh-comment-feed-button` button:

```coffee-script
refresh_comments = (page_id) ->
  posting = $.post '/grabcomments', page_id: page_id
  posting.done receive_comments
  posting.fail (data) ->
    ...
```

So this makes an Ajax call which will call the function `receive_comments`
when the Ajax call returns (successfully). We write the `receive_comments` as:

```coffee-script
receive_comments = (data) ->
  ... code to delete current comments and replace them with those returned
```

Typically `data` will be some JSON data, perhaps the comments associated with
the `page_id` we gave as an argument to our Ajax call.

To test this you would navigate to the page in question and check
that there are no comments, then open a new browser window and make two
comments (or alternatively directly adding the comments to the database),
followed by switching back to the first browser window and then
performing the following steps:

```python
    refresh_comment_feed_css = '#refresh-comment-feed-button'
    self.click_element_with_css(refresh_comment_feed_css)
    self.check_comments([first_comment, second_comment])
```
Where `self.check_comments` is a method that checks the particular comments
exist on the current page. This could be done by using
`find_elements_by_css_selector` and then looking at the `text` attributes of
each returned element.

The problem is, that the final line is likely to be run before the results of
the Ajax call invoked from the click on the `#refresh-comment-feed-button` are
returned to the page.

A quick trick to get around this is to simply change the Javascript to somehow
record when the Ajax results are returned and then use Selenium to wait until
the relevant Javascript evaluates to true.


So we change our `receive_comments` method to be:

```coffee-script
comments_successfully_updated = 0
receive_comments = (data) ->
  ... code to delete current comments and replace them with those returned
  comments_successfully_updated += 1
```

Note that we only increment the counter after we have updated the page.

Now, we can update our Selenium test to be:

```python
    refresh_comment_feed_css = '#refresh-comment-feed-button'
    self.click_element_with_css(refresh_comment_feed_css)
    self.wait_for_comment_refresh_count(1)
    self.check_comments([first_comment, second_comment])
```

The `1` argument assumes that this will be the first time the comments are
updated during your test. Of course as you run down your test you can increase
this argument as required. The code for the `wait_for_comment_refresh_count`
is given by:

```python
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
...

class MyTest(object):
    ... # assume that 'self.driver' is set appropriately.
    def wait_for_comment_refresh_count(self, count):
        def check_refresh_count(driver):
            script = 'return comments_successfully_updated;'
            feed_count = driver.execute_script(script)
            return feed_count == count
        WebDriverWait(self.driver, 5).until(check_refresh_count)
```

The key point is executing the Javascript to check the
`comments_successfully_updated` variable with `driver.execute_script`.
We then use a `WebDriverWait` to wait for a maximum of 5 seconds until the
our condition is satisfied.

## Conclusion

Updating a Javascript counter to record when Javascript events have occurred
can allow your Selenium tests to synchronise, that is, wait for the correct time
to check the results of a Javascript event.

This can solve problems of getting a `StaleElementReferenceException` or a
`NoSuchElementException` because your Selenium test is running a check on an
element too early before your page has been updated.
