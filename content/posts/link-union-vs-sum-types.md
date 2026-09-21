---
title: "Link: Union vs sum types (2021)"
tags: [ programming, types ]
date: 2026-09-21T15:22:43+00:00
---

[ Viral instruction ](https://viralinstruction.com/) wrote a [blog post way back in 2021 explaining the difference between union and sum types](https://viralinstruction.com/posts/uniontypes/).
I had always used these terms pretty much interchangeable, but this explanation makes sense. I guess I was using 'union type' as a bit of a short hand for **tagged**-union type. I think that Elm has even wrestled with this terminology and they settled on *"custom union type"*, which I'm not overly fond of, but I can see they are going for clarity.

> Union types, sum types and product types are all algebraic data types, which sound super complicated, but the basic concept is actually really simple.

In general type theory is fully of unnessarily grandiose terminology. The kind that seems almost designed to confuse or intimidate people, but are more likely the speaker just trying to sound smart (we all do this). I still use the term polymorphism when I should really use the term *generics* since it's less pompous sounding and also simply describes the underlying concept better. Someone hearing *polymorphism* for the first time likely thinks it's some complicated mathematical concept, whereas *generics* might even allow them to guess correctly, or at least guess at the intended benefits.

Anyway this post does a great job of explaining the differences between union and sum types. It also does a great job of explaining the advantages of Rust style sum types over Julia style union types:

> **Unwrapping forces you to remember you're dealing with a sum type**
> 
> Julia's union types may have less boilerplate because you can use them as if they were concrete types - but that's also a dangerous trap.
> 
> Consider the Julia function `findfirst`, which returns `Union{Int, Nothing}` versus Rust's `iter.position`, returning `Option<usize>`: It's easy to forget `findfirst` can return nothing and not handle that case, introducing a bug. But it's not possible to mistake an `Option<usize>` for a `usize`, because they're incompatible types and you must unwrap the sum type.

At the bottom, they write:

> I'm not convinced this tradeoff between union and sum types is inherent. I think it may be possible to eat your cake and have it, too, but I'm not yet sure how such a system would look like.

The do not seem to have posted something to suggest they found that way to have their cake and eat it too. I don't think [structural tagged-union types](/posts/structural-custom-types/) quite satisfy that, but I think they move you a bit closer.
