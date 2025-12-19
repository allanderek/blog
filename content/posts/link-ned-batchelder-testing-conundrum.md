---
title: "Link: A testing conundrum"
tags: [ testing, software development]
date: 2025-12-19T10:18:05+00:00
---

[Link: A testing conundrum](https://nedbatchelder.com/blog/202512/a_testing_conundrum.html)

A thoughtful blog post by Ned Batchelder regarding a difficulty in testing a class that on the face of it should be straightforward to test.
The class seems straightforward to test because:
> This is a pure function: inputs map to outputs with no side-effects or other interactions. It should be very testable.

The code is basically a hashing function, for which he wants "equal" values to hash to the same hash, and *non-equal* values to hash to different hashes.

He uses [Hypothesis](https://hypothesis.readthedocs.io/en/latest/), a property-based testing library, and discovers two difficulties in using that approach to test this class. Firstly, the fact that standard equality `==` in Python was not the same as the equality he was using. However, I think this simply uncovers that his notion of equality is not written down in code anywhere. I think the test suite would be improved by having an explicit equality function even if that equality function is not used in the actual class itself. Sometimes you are forced into writing extra code to facilitate testing and that extra code is not useful, but in this case the equality function would be execellent documentation for what the class considers equal values.

The second difficulty he uncovers is a classic. He wants the properties that two equal values hash to the same hash **and** that two non-equal values hash to different hashes. The first is pretty conducive to property-based testing, you can generate pairs of equal values and check that they hash to the same. Your generation function can specifically generate values that are not considered equal by the standard Python equality test, but you do consider equal, such as sets and dictionaries with the same contents but different orderings. However, the other way is much more difficult to test, that is checking that non-equal values hash to different hashes. To do that, you have to generate two non-equal values and check that their hashes are different, but even if there is a bug in your code two entirely random non-equal values are very likely to hash to different hashes anyway. So you have to specifically generate non-equal values that are likely to collide, which is a much more difficult generation problem.

His class already included a fix for a problem of this nature (which he had previously discovered and fixed) demonstrated by this test function:

```python
def test_dict_collision():
    # Nesting matters.
    h1 = Hasher()
    h1.update({"a": 17, "b": {"c": 1, "d": 2}})
    h2 = Hasher()
    h2.update({"a": 17, "b": {"c": 1}, "d": 2})
    assert h1.digest() != h2.digest()
```

It's difficult to see how property-based testing would have uncovered this, if you hadn't already thought of it and deliberately designed your generation function to uncover it.

