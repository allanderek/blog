---
title: "Link: Gren format challenges"
tags: [ programming, gren, syntax ]
date: 2026-08-28T11:10:42+00:00
---

Gilbert Ramirez has [written a good post-mortem on the challenges of writing Gren format](https://gilramir.github.io/gren-format-lib/grenFormatChallenges.html).
I'm a huge fan of formatters, and the kind of opinionated formatter that is gren-format (and elm-format) are especially good.
I promise, even if you have strong opinions about formatting and think that you won't get on well with a non-configurable formatter it is well worth getting over that initial grinding of gears. The amount of cognitive load that is reduced by not ~~having to~~ being able to think about formatting decisions is larger than certainly I predicted.

There is also a strange kind of skill you develop in using the formatter as a typing assistant. Once your IDE is setup to run the formatter on save, you develop a kind of knack for knowing the least amount of code you can write which will then be formatted as you wanted.

Anyway, the link is somewhat niche, but interesting to those in that niche. However, I think the last couple of sections are interesting to everyone, and they are short. 

Here are some thoughts:
> **Never rebuild the binary while a fuzzer is running.** This silly mistake bit us a few times. The tests shell out to the formatter, and a rebuild at the same time produces a burst of findings that look exactly like a regression. Oops!

This sounds like good advice, but I didn't understand how a rebuild produces a burst of findings that look like regressions. It also sounds like this could be somehow solved with a script for building, storing the binary somewhere, and then running the fuzzer with that stored binary.

Also:
> **Reusing the compiler’s parser is worth it**, and it means you will reconstruct comment placement from positions. Budget for that.

Yes, reusing the compiler's parser seems worth it. I assume the Gren team were correct in that the reconstructing the comment placement from positions was less work than re-writing the compiler's parser to store them. But that seems like the obvious ideal solution.

And:

> **Decide position-dependent things once, store the decision as a value, and delete the positions before the next stage sees them**. Enforce it with a type, not a review. It doesn’t remove the obligation; it moves it to one function you can reason about.

I **think** this is an instance of *"Parse, don't validate"*, even if maybe *'validate'* is the wrong word here. If not, it's in the same neighbourhood, and both this and *PDV* are specific instances of a more general principle which is admittedly probably hard to articulate. 
