---
title: "Link: python's pre-declared constants are kinda weird"
tags: [programming, link, python]
date: 2026-08-15T11:27:21+00:00
---

A great small post [python's pre-declared constants are kinda weird](https://sebsite.pw/w/20260801-pythonconstants.html) examining Python's constants.
The interesting thing here is that the constants are not treated the same way and hence have slightly different behaviour.
It's a little hard to see how this came about. It's relatively clear that there is no good reason for the constants to behave differently in this way and that the differences are likely an historical anomaly.

The most glaring difference is that `True`, `False`, and `None` are all keywords. But `__debug__`, `NotImplemented`, and `Ellipsis` are not keywords (though `Ellipsis` can be written as `...` which is not a keyword but is dedicated syntax).

It's worth reading the entire post, I think the ending sentence gives a great flavour:
> so in some sense, ... is a real constant, but Ellipsis isn't. weird, right?

That is weird, I think this is a great example of a language feature that has evolved rather than being designed. Perhaps these 6 'constants' were not thought of as a single coherent feature, but instead each arose as with its corresponding need. The fact that we could lump them altogether and treat them identically is only obvious now.

A small note about formal methods, in this case, formally specifying the language. Doing so, may have brought up the kind of things such as `x.True` being a syntax error. On the other hand, these oddities exist and, so far as I know, have not caused any real problems.

There is a [follow up post about string literal weirdness](https://sebsite.pw/w/20260806-pystrings.html).
