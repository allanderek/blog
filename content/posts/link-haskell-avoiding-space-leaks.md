---
title: "Link - Avoiding space leaks (in Haskell) at all costs"
tags: [ Haskell, programming, lazy]
date: 2025-12-03T16:20:18+00:00
---

A [good blog post on avoiding space leaks in Haskell](https://chshersh.com/blog/2022-08-08-space-leak.html) showed up on my feed today.
First of all I think it provides some useful and important advice for Haskell programmers.
I think it touches on some of the same issues that I [wrote about recently](/posts/stacks-and-laziness/) in a post regarding stacks and laziness.

The author starts off stating (correctly) that lazy languages are not the norm, nor particularly popular:

> Haskell is a purely functional lazy programming language. The world doesn’t have a lot of lazy-by-default PLs. In fact, all mainstream languages have eager evaluation models.

They then attribute this to lazy being more difficult to implement:

> I tend to think this happened because implementing the lazy evaluation model is more difficult and nobody wanted to bother.

I'm not convinced. I think this happened because lazy evaluation more or less forces your language to be **pure**. If you have side-effects in your language then it's very difficult to reason about when those side-effects will happen if you have lazy evaluation. For whatever reasons, pureness hasn't really caught on in mainstream programming languages, which means neither has lazy evaluation. 

Though as a counterpoint to my own opinion, Elm is a **pure** language that is not lazy, I think there are several reasons for this, but easier implementation for an eager language (which compiles to an eager language (Javascript)) is likely at least part of the reason. Judge for yourself [in this google groups thread from 2013](https://groups.google.com/g/elm-discuss/c/9XxV9L0zoA0/m/cx3UMZ05Gc0J) where Evan Czaplicki (the creator of Elm) discusses why Elm is not lazy. It certainly is not **solely** because of ease of implementation.

I think that having laziness as an evaluation strategy has forced the Haskell language designers to remain *pure* and that has forced some innovation in language design. Whether or not you're a fan of monads and type-classes they are certainly interesting ideas to have emerged from the Haskell community and I'm glad that they exist even if only so that we do not have to guess how effective they may be if implemented in some language. For example, Elm has chosen to eschew type-classes, but might Evan Czaplicki, have made a different choice had Haskell not existed as a reference point?


Anyway I think [the post](https://chshersh.com/blog/2022-08-08-space-leak.html) does a pretty good job of explaining why lazy evaluation might lead to space leaks, and whilst it might allow for more elegant/modular code, that comes at a cost, which is probably too large to pay for most applications.
