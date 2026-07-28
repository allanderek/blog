---
title: "Link: Functional Programming from First Principles"
tags: [ software development, functional programming ]
date: 2026-07-28T15:07:16+00:00
---

[Link: Functional Programming from First Principles: Part 1 motivation](https://www.endoflineblog.com/functional-programming-from-first-principles-part-1-motivation)
An interesting start to what looks like a series of articles on functional programming. I've often found that once people give functional programming a real and proper try they get it quite quickly, but that many programmers resist it. Perhaps they give it a half-hearted try but it's almost as if they *want* to dislike it. There may be some selection effects going on here, so perhaps there are people that give it a real and solid try but *still* give-up as it's not to their tastes, but I never hear of them because they're not in my circles.

Anyway the link above is a good attempt at motivation. I have a few quibbles, but it's still a good read.

## Quibble one

Firstly, the author spends quite a bit of time defining what, *mathematically*, is a function. But I'm not quite sure why any programmer should care. I think the author's point is that functional programming languages (which are strictly pure) do map on to mathematical functions quite well, but there isn't any logic to say why that would *necessarily* be a good thing for programming.

## Quibble two

My next quibble is the only thing I actually disagree with in the article. It concerns *"lamdba syntax"* or anonymous functions. The author writes (my emphasis):
> Practically, it means that functions need to satisfy a few conditions to be considered first-class in a given language:
> 1. Functions can be passed to other functions as arguments.
> 2. Functions can be returned from other functions.
> 3. **The language has function literals (similarly to number or string literals), often called lambda expressions, or anonymous functions.**

Here is [what I wrote regarding anonymous functions](/posts/lambdas/):
> Lambda expressions though are a sort of staple of functional languages. For no particularly good reason a language is not seen as functional if it doesn’t have lambda expressions.

I stand-by this statement, and the author of the linked post doesn't explain why anonymous functions are relevant to whether or not a language is considered functional. To be clear, I'm not *here* arguing that anonymous functions are not useful/good feature, but rather that they have nothing to do with whether or not a language is functional. They may influence whether or not a language is **considered** to be functional, but they shouldn't. My original point was also not that lambdas were necessarily bad, just unnecessary, and therefore strange in Elm's syntax which is very frugal, I wrote:

> So overall, I think occasionally a lambda is convenient, but there are already a couple of places in the grammar where Elm decides frugality is more important than convenience, for example, record update expressions in which the expression being updated must be an unqualified variable name. So lambdas seem at least inconsistent.

So again here my argument is not so much that lambdas are bad, just inconsistent with a language being as frugal as possible, and my main quibble with the linked article is that author is perpetuating the idea that lambdas are somehow a requirement for a language to be considered functional.
If you want more lambda comment [I had more to say](/posts/lambdas-again/) when I came across an article describing lambdas in Python.

## Quibble three

The author defines four-levels of functional programming. I think these are great and map very well with my experience of functional programming languages.
My quibble though is that the author makes what I think is a *very* common mistake in discussing the benefit of laziness, with that being tied to either or both of
* Avoiding unnecessary computation
* Allowing for infinite data structures

I think both of these are pretty minor, the second one certainly. The first one is not even necessarily true, you can unfortunately end up with space leaks and those space leaks are ultimately executing code that isn't required, I [wrote about this in relation to stacks and laziness](/posts/stacks-and-laziness/), and I also [linked to a post about Haskell space leaks](/posts/link-haskell-avoiding-space-leaks/).

Anyway, I feel I am once again forced to point out that the main motivation for laziness is that it allows for more elegant/modular/reusable code, I [demonstrated a good example](/posts/time-extra-posix-to-parts-great-laxy-example/) using a calendar application. Again though, I'm not saying that lazy languages **achieve** the ability to write more elegant/modular/reusable code, there are problems, in particular space leaks, but I am saying that that is the major motivation, or point, of lazy-by-default, not any attempt to avoid unnecessary computation, which it *may* do, although compilers are quite good, or allowing for infinite data structures, which it surely does, but how often do they really come up?

## Conclusion

I may have had three quibbles but I think [the linked article](https://www.endoflineblog.com/functional-programming-from-first-principles-part-1-motivation) is a good read for anyone interested in functional programming.
