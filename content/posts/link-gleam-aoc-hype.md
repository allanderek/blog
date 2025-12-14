---
title: "Link: I Tried Gleam for Advent of Code, and I Get the Hype"
tags: [ programming, gleam ]
date: 2025-12-11T11:14:31+00:00
---

[Link: I Tried Gleam for Advent of Code, and I Get the Hype](https://blog.tymscar.com/posts/gleamaoc2025/)

Nice, short and thoughtful [blog post](https://blog.tymscar.com/posts/gleamaoc2025/) regarding trying out Gleam for the advent of code this year, and liking it.
I think this is quite a good advert for generally using the advent of code as a way to try out new programming languages and tools.

This makes me want to try out Gleam as well, something that's been on my to do list for a while, perhaps it will make my new year's resolution list.

A couple of points from the section [Where Gleam fought me a bit](https://blog.tymscar.com/posts/gleamaoc2025/#file-io-is-not-in-the-standard-library):

### A small standard library
A smaller standard library, the author is a little good-cop/bad-cop about this, the section is titled with the word "fought", but then in both cases (file I/O and regex not being in the standard library) the author writes to the tune of:
>  It is fine, I just did not expect basic file IO to be outside the standard library.

Personally, I think a small standard library is a good thing. Firstly it somewhat forces the language to have a good package management story, so that it is trivial to add libraries for things like file I/O and regex. If the language doesn't have a good package management story then that should be the complaint, not the fact that some common functionality is not in the standard library. Though note, package management story, includes ease of installing and tracking dependencies, but also ease of finding such dependencies and potentially comparing competing ones. I believe Gleam has at least good tooling around package management and a central repository meaning discovery is also good.

Secondly, if something is in the standard library it becomes the default way to do that something. If it turns out that there is a better design, it's harder for the better design to gain traction.

Lastly, once something is in the standard library other packages tend to assume it, that's great where we are confident it is correct, for example it's great that there is a single `Order` type and not several defined in different libraries which are essentially defined in the same way. So you never find yourself converting between, say `Sort.Order` and `HashMap.Order`. However, that's obviously less great, if the standard library implementation is not obviously optimal.


### List pattern matching limitation

This is an interesting proposal:

> You can do `[first, ..rest]` and you can do `[first, second]`.
> But you cannot do `[first, ..middle, last]`.
> It is not the end of the world, but it would have made some parsing cleaner.

That is quite a cool proposal, **however**, note that `[first, ..middle, last]` would make pattern matching `O(n)` in the length of the list, as opposed to `O(n)` in the length of the **pattern**. I feel that such a pattern might lead to easily writing "accidentally quadratic" code.
