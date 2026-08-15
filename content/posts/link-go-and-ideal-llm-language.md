---
title: "Link: Why Go is an Ideal Language for AI-Assisted Software Engineering"
tags: [programming, link, llm, go]
date: 2026-08-15T11:27:15+00:00
---

The Google developers blog has published a post [Why Go is an Ideal Language for AI-Assisted Software Engineering](https://developers.googleblog.com/why-go-is-an-ideal-language-for-ai-assisted-software-engineering/).

How to say this nicely, I don't think much of this post.

First of all, I think this is a great area of active research. Just as we aren't terribly sure about what makes a good programming language for humans, we also do not know exactly what makes a good programming language for LLMs. It does seem that it is useful to have a lot of code from a programming language in the training data for an LLM, but I think that's a slightly different (if more pragmatic) question than what makes a fundamentally good programming language for an LLM. But note also, if we determined some kind of fundamentally good programming language (even a new one) for an LLM we could probably get over the lack of training data in several ways.

If you read the post yourself, you will note that it feels AI-written. I put the first 2000 words through Pangram and it reported that it was 62% human written with 38% written by AI. This was really the mix it gave, I'm not confusing a confidence score with a percentage of the text.

Okay all of that aside, I think I'd like to go through this blog post.

## From writing to reviewing

This section makes the claim that what matters now is how easy a programming language is to *read* rather than *write*.
I would say that has **always** been true.

I also found the following line to be vomit-inducing:
> In other words, AI is increasingly your teammate—a bit of a maverick, but a teammate all the same. What matters most is how we work together as a team.

Not to mention that, again, this has always mattered more.

## Go is for Software Engineering

> As other languages rapidly added features and sought to expand the number of ways to express program logic, Go focused on a larger vision: language design in the service of software engineering.

Okay, it's a reasonable thing to say that having fewer language features is a virtue. That is one of the main things I like about Elm.
But to claim that **your** language is being designed in the service of software engineering whilst all those other languages are not is just nonsense. All languages are trying to provide the best possible environment for software engineering. Some are more niche and focused on small projects, but the vast majority, and pretty much any general-purpose programming language, is attempting to provide a good environment for software engineering.

I think this sentence is a good example of why the blog post sat so poorly with me. The tone is just dreadful.


> Language design in the service of software engineering requires not just a language, but an end-to-end platform with tooling all around the software development life cycle.

Everybody knows this and **every** general-purpose programming language does its level best to provide such an end-to-end platform.

> It requires opinionated simplicity so whole teams can structure, format, and test their code the same way. It requires strong compatibility guarantees so that the code you write today will not only still work in ten years, it will still be good code in ten years. It requires a strong ecosystem, with a global system for dependency management that can scale with your teams. And it requires that it does all these things with sensible, robust security considerations and tools woven throughout.

I don't think any of these "It requires" statements are settled fact. I happen to agree with most of them, though I might quibble with whether or not Go provides them. But it's mostly the tone here that I find very distasteful. The tone is one of "We have all the answers, nobody else does."

## Go is a Platform

> One of the things that most distinguishes Go is that it is not just a language, it’s a platform.

Argh, care to name an example? The fact that languages generally come with a platform is one of the things that makes comparing **languages** so difficult. Most evidence for the efficacy of any one programming language is really evidence for the efficacy (or lack of) of the language's associated platform, or at the very least the combination. Python has such a famously good eco-system there is an [xkcd comic](https://xkcd.com/353/) about it.


> From the start, Go has shipped with a robust, end-to-end toolchain with touchpoints all across the software development life cycle. Out of the box, the Go platform provides a built-in formatter, test framework, dependency management, and advanced security tools

I think the formatter and certainly the test framework were in from the start, but not dependency management or security tools. Modules landed in Go 1.11 in 2018, nine years after Go's first public release, and govulncheck, which I assume is what "advanced security tools" means, arrived in 2022.

I guess I'm nit-picking; it is of course good to provide a solid platform and I think the Go team have mostly managed to do that, even if I disagree quite strongly with some choices in language design. But that's the problem with this post; it seems to take the idea that Go is the best language for humans as a given.


## Go is Readable

> Another of Go’s distinguishing characteristics is that it prioritizes readability over writability.

Every serious programming language on earth has readability as pretty much its main concern. Again, show me a **single** example of a programming language that claims to value writability over readability. Okay, fair enough APL, Perl, J, K etc. do actually value expressiveness over readability, but this proves my point, those languages have to explicitly claim that because the opposite is the default. I would also note that their popularity this century has mostly been a story of decline.

> If a language offers a dozen different ways to express the same logic, an AI model will inevitably generate a fragmented, haphazardly stylized hodgepodge of syntax.

I wholeheartedly agree that for the most part it's better if a language only offers one way to do something. But this is neither new to Go, nor easy to do correctly. Long before Go existed, this line was in the [Zen of Python - 2004](https://peps.python.org/pep-0020/):
> There should be one-- and preferably only one --obvious way to do it.

But also, I'm not totally convinced that an AI model will "inevitably generate a fragmented, haphazardly stylized hodgepodge". I think AI coding agents are pretty consistent in their style, sometimes too much so.

> Go solves this through unyielding consistency. By enforcing a single, standardized format via the built-in gofmt tool and offering a language design that intentionally limits complex abstractions, Go ensures that all code—whether written by a senior engineer, a junior contributor, or an LLM—looks the same. 

Wholeheartedly support this. I think all languages should have an official formatter. I think it's more about collaborating with humans though; most languages do have formatters; they just tend to be configurable and not enforced, but forcing an agent to use one with your settings is trivial.

## Go is Reliable

Mostly agree with this section **but** Go is hardly the most 'hardened' or reliable language. Where are the custom union types? Generics should have been there in the first release. There was a ready-made cautionary tale in Java, which first shipped with no generics and added them later. That example should have informed the first release of Go.

> Paired with Go’s signature compilation speed—orders of magnitude faster than Java, C#, Rust, and other compiled, production-grade languages

Agreed, the speed of the compiler is indeed a major plus point for Go.
Is it more important for humans or an AI agent? Humans can famously lose their *"flow state"* to a slow compiler, but I guess the speed of an AI agent is more bottlenecked by the speed of the tools it is using. So, I'm not sure. In any case, I'd say compiler speed is a good thing for both humans and AI agents, and Go scores very well here.

However, on that note, step forward [OCaml](https://ocaml.org/) that has not just one very fast compiler, but two. It has a bytecode compiler that prioritises compilation speed for development and a native code compiler that prioritises execution speed for production. Although the latter prioritises speed of the compiled program, it's actually pretty fast as compilers go. OCaml is the gold standard here, and it has a better type system than Go.

## Go is Maintainable

Again I think this is debatable. Or at least: compared to what?

> Go’s primary answer to this acceleration lies in its famous compatibility promise

This is useful, but note that it also solidifies poor decisions.


## My Conclusion

Okay fair enough perhaps I'm being a bit harsh, I suppose one can expect the maintainers of Go to consider it the best language ever.
Still, the tone of this piece irritated me badly. Unfortunately I also do not think there is actually much substance here. As I've said above, I think this post could be *mostly* summarised as "AI agents mostly need the same things as humans and we already think Go is the best language for humans".
I don't disagree with the first part of that, but I do not think it is well demonstrated here. Unfortunately the tone of the post removes the 'we already think' part.

There are a lot of plus points made for Go and most of them are correct, but not as unique as the authors seem to think they are. If I were being harsher still, it reads as very insular, as if they simply do not know much of the programming world outside of Go.


