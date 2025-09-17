---
title: "Programming language websites"
tags: [ programming, languages ]
date: 2025-09-17T09:05:57+00:00
---

I'm interested in programming languages and often look at the websites for new/isoteric programming languages.
Today, after reading [Moonbit developers are lying to you](https://bitemyapp.com/blog/moonbit-developers-are-lying-to-you/) I was interested in the moonbit language and so I visited the [website](https://www.moonbitlang.com/). I noticed a few things on the website that I find relatively common when looking at programming language websites and thought I would detail them here.

This will seem like a bit of a negative post, but remember I'm going over a website here, I'm not critiquing the actual language which I have not yet tried.
If anyone from moonbit were to read this, take this as a light *constructive* critique.

## Lack of a card

Programming languages are categorised over many axes. To name but a few:
* Dynamically/Statically typed
* Weakly/strongly typed
* compiled/interpreted/both
* Imperative/object-oriented/functional/array/stack/relational/logic/something else
* Significant whitespace or not

I find it very surprising that most languages do not state something like this front and centre. Mostly we get some kind of generic 'aim' for the language.
Here is moonbit's at the time of writing: "Next Generation Coding Platform. Fast, simple, and scale."

Very few languages asprire to be "slow, complicated and non-scalable".
The "Next generation coding platform" is again a bit fuzzy, is anyone building a "Previous generation coding platform"? I guess this does tell me that moonbit is likely to be a bit experimental, it's *not* likely to be a consolodation language. A consolodation language is one that tries to take the best parts from existing similar languages and leave out the mistakes. It would *seem* that moonbit is attempting to be somewhat groundbreaking.

Still, is this language statically typed? Does it have a main target such as Javascript, or the JVM, or executable binaries? It aims to be fast, are we talking C fast, or Go fast, or faster than Python fast?

Scrolling down a bit we do get *some* information but it's frustratingly vague:

> * Expressive multi-paradigm design, combining the best of dynamic and static, functional and practical
> * Data-oriented language with a robust type system
> * Multiple backend support including WebAssembly, JavaScript and more.

It's the combining part I'm mostly failing with here? Combining in what sense? Is it statically or dynamically typed or can you mix and match, in which some parts of the program are statically typed and some parts are dynamically typed? What does 'practical' mean here?

I'm still a little unsure what a 'Data-oriented language' is, but that's on me. A 'robust type system' seems like a good point, I take it to mean 'strongly' typed. But strongly typed languages can be either [statically or dynamically](https://blog.poleprediction.com/posts/dynamically-typed-statically-typed-metaprogramming/#first-a--point-of-terminology) typed, so I'm still unsure on that point.

Okay great, multiple backend support. 


## Focus on minor QoL point

Straight after the first "section" "Fast, simple, and scale", we have a section "Why Moonbit".
Unfortunately this fails to answer my question at all. We have some tabbed code examples:

* Simple - Looks very similar to 'Hello world' in 90% of languages, but I'll grant it does lean 'simple'.
* Functional - This looks more 'modern' than 'functional' to me. It has similar features to Rust. As a sidepoint it's something of a good point for functional languages that a lot of non-functional languages have adapted many of the features first found in functional languages.
* Range pattern - This is the one I wish to talk about, see below
* JSON builtin - Okay could be good, but seems strangely a bit specific, it suggests a Web language.

Anyway, it's the "Range pattern" point I wish to talk about. This is most of the code shown in the 'Range pattern' tab:

```moonbit
///|
fn sign(x : Int) -> Int {
  match x {
    _..<Zero => -1
    Zero => 0
    Zero..<_ => 1
  }
}

///|
fn classify_char(c : Char) -> String {
  match c {
    'a'..='z' => "lowercase"
    'A'..='Z' => "uppercase"
    '0'..='9' => "digit"
    _ => "other"
  }
}
```

So basically, the point is that you can match against, not just a single value, but a range of values.
This is, at best, a minor quality of life improvement. It's just a tiny feature. This just does not come up in non-educational code very often.
Even if it did, it's still just a minor syntactic improvement on the other options available. Why is this shown as one of the showcase pieces of code?
It is almost the first thing you see on the web page. Why are the developers so proud of this really very minor feature of their language? Not only that, but a feature that really doesn't tell you much about the rest of the language, this feature could basically present itself in pretty much any kind of language.
Imagine you went to the Python home page and the second thing it tells you is "oh hey you can write 0 < x < 10 rather than 0 < x && x < 10". I mean, both are *kind* of cool, but neither would tempt me to learn a language I wasn't otherwise going to.

I'm even tempted to suggest that such syntactic sugar items are a bit of a negative sign. It's a negative sign that the developers are keen on syntactic sugar rather than on keeping the language small. Some syntax sugar is great, but each one means a developer now has at least two ways to express the same thing. As that number grows code becomes less readable, as different programmers make different choices. But this is really by-the-by, the point here is that good or bad a minor syntax point doesn't seem to me to deserve such prime real estate.


As a very minor side-point 'JSON built-in' can be a good or bad point. When something is built-in, it means that the integration itself was not expressible in the language, otherwise it wouldn't be built-in, it would simply be a library. Imagine if a language said "Fibonacci built-in", you would wonder why you cannot simply write a function to compute the fibonacci sequence. Of course there may be some very good reason for having JSON built-in. My point here is that that mere fact is not automatically a point in favour.

Another small side-point, there are these unusual bits of syntax `///|` which proceed each top-level definition, but no explanation. They look like comments, perhaps they are something like doc comments that are non-optional? But then why make them non-optional if you can just put an empty `///|`? 

## The rest

The rest of the web page is fine enough. There is some talk of an A.I. friendly language design, which sounds good, albeit I might consider that to be the same as a human friendly language design. Still, I've certainly found that LLM coding assistants are better the simpler the language all else being equal. All else isn't equal of course and the LLMs are better at the more popular languages, but still, it makes sense at this time to design your language for LLMs **and** humans.

There is something about a Cloud IDE, but interestingly the LSP implementation is implemented in Javascript, but Moonbit as I understand it, compiles to Javascript, so why isn't the LSP written in in Moonbit?

Anyway, my main gripe here is that I have reached the bottom of the front page of the web page and I still don't **really** know what moonbit is.

## Generic claims

I'm picking a little on Moonbit here, but it's suprisingly common for a programming language's main site to say very little about the language. Interestingly they mostly state things that do *not* differentiate the language from other languages. I suspect this has something to do with a perception that programmers have some non-negotiable demands, but personally I think these are mostly "must have LSP implementation".  Of course particular programmers have other non-negotiable demands such as "must be object-oriented", "must be statically typed", "must compile to Javascript", but the point is that non-negotiable demands rarely distinguish the language.

Here's a look at some other languages and the **main** points they claim on the entry point to their website:

1. [Python](https://www.python.org) "Python is a programming language that lets you work quickly and integrate systems more effectively."
    * Does anyone design a language specifically to let you work slowly and integrate systems really ineffectively? I guess it kind of tells you where the focus is.
2. [Mojo](https://www.modular.com/mojo) "One language, any hardware. Pythonic syntax. Systems-level performance."
    * Actually think is pretty good. It tells me the language is portable, it has a pythonic **syntax** and systems-level performance. The jibe I get is that if you like Python but demand higher performance, mojo is for you. It doesn't *quite* say whether it's a python-like language, e.g. is it dynamically typed? Still, not bad.
3. [Elm](https://elm-lang.org/) "A delightful language for reliable web applications."
    * A bit vague. It states web applications but really they mean front-end web applications. It doesn't say that it is statically typed, functional etc. 
4. [Gren](https://gren-lang.org/) "A programming language for simple and correct applications"
    * One of those ones that could surely apply to pretty much any language. I'm not sure why you want your application to be simple? Perhaps you want your implementation to be as simple as possible, but you might have complex requirements. Obviously, everyone wants correct applications.
5. [Java](https://www.java.com/en/) "Oracle Java is the #1 programming language and development platform. It reduces costs, shortens development timeframes, drives innovation, and improves application services. Java continues to be the development platform of choice for enterprises and developers."
    * Firmly in the aspirations category. The benefits are basically all ones that **all** programming languages aspire to, and it's highly dubious to make that claim here. I don't know from what data they are claiming number 1 spot, but I would agree that it continues to be **a common** choice for enterprises.
6. [Julia](https://julialang.org/) "Fast, dynamic, reproducible, composable, general, open source"
    * These are headings underwhich more  wordy detail is given. At least we know right from the start that Julia is dynamically typed. Fast at first light might seem a vague aspiration that all languages have, but actually the section states that it compiles to native code, somewhat unusual for a dynamically typed language. So from the first two points I get that the language is targetted at giving the benefits of a dynamically typed languages, with at least less of a performance hit. The rest of the points are a bit more vague, Reproducible; most languages can have this now. Composable: A bit more dubious, but at least here we are staking the claim that multiple dispatch is a killer feature. General: I'll be honest this is mostly waffle, but I guess the point is it's not a DSL. Open source: Okay cool, I like that clarity, I don't think it's much of a distinguishing point, but open source is non-negotiable for many programmers.
7. [C#](https://learn.microsoft.com/en-us/dotnet/csharp/) This simply doesn't make any attempt to tell you what C# is, and seems to assume you know and already want to learn. Maybe it's not the "homepage of the language", I got here from wikipedia.
8. [Go](https://go.dev/) "Build simple, secure, scalable systems with Go. An open-source programming language supported by Google. Easy to learn and great for teams. Built-in concurrency and a robust standard library. Large ecosystem of partners, communities, and tools"
    * Again with the 'build simple systems' does this mean you cannot build complex ones? Cool, open source stated up front, and also the language has backing of a major corporation that isn't going anywhere anytime soon. 'Easy to learn and great for teams', aspiration. Built-in concurrency is indeed a feature of Go, but you still have not said what kind of language it is. 'Robust standard library': aspiration. Fair point, there is indeed a large eco-system and when one evaluates a language what one is really evaluating is the language + eco-system, unless you're doing some kind of academic evaluation. Still, a lot of unknowns from this. How about saying it is an imperative language in the C family, with runtime garbage collection? (I might snarkily add that the developers deliberately chose to ignore programming language research when designing the language).
9. [Ruby](https://www.ruby-lang.org/en/) "A dynamic, open source programming language with a focus on simplicity and productivity. It has an elegant syntax that is natural to read and easy to write."
    * This starts off great, I know it's dynamic and open source. After that it gets into aspiration territory. I guess we know that it prioritises simplicity over performance. An elegant syntax ... is somewhat subjective, and again begs the question does anyone deliberately design an inelegant syntax which is unnatural to read and difficult to write? Okay yes some people do do that, but it's mostly for fun.
10. [Scheme](https://www.scheme.org/) "Scheme is a classic programming language in the Lisp family. It emphasizes functional programming and domain-specific languages but adapts to other styles. Known for its clean and minimalist design, Scheme is one of the longest-lived and best-studied dynamic languages, and has many fast and portable implementations."
    * This is actually great. I think you know exactly where you are. Admittedly you might be a *bit* lost if you don't know what Lisp is, but at least you have something obvious to search for. The "clean and minimalist design" might seem a touch aspirational but here it is making a claim that this is widely recognised as true for Scheme. 
11. [Haskell](https://www.haskell.org/) "Enjoy long-term maintainable software you can rely on. Declarative, statically typed code."
    * Okay the first part is a bit aspirational, but sets the focus, and is really kind of part of the logo. "Declarative, statically typed code". I mean I don't know why they don't use the term "pure functional" as opposed to 'Declarative', but still, right off the bat you know where you stand here. Also a little stange that laziness is not being mentioned. However, the page quickly gives more details under the heading 'Why Haskell?'. I think this is mostly great and very informative. I might quibble with some of it, the tooling is said to be excellent, but I've generally considered it sub-par, aside from the compiler itself. But I guess that's just my opinion.
12. [O'Caml](https://ocaml.org/) "An industrial-strength functional programming language with an emphasis on expressiveness and safety"
    * I think I understand what they mean by 'industrial-strength', they are basically saying that this is not an academic language, it is actually usuable for serious applications. 'an emphasis on expressiveness and safety' is somewhat aspirational. I'm a little surprised that you have to scroll down, to hear about garbage collection, and I cannot find anywhere that says what is somewhat unique about O'Caml, that is that it is both an object-oriented and a functional language (I would say that it's a functional language that has objects). A lot of what else is written is the aspirational 'First class editor and tooling'. In fact, I'm surprised that is above 'Fast compiler and applications', the O'Caml compiler is genuinely fast and it can produce genuinely fast code. This is less aspirational and more or less just fact. Though I do like the quote regarding 'Exceptionally robust and reliable'.


The general vibe I often get is a bunch of aspirational and vague claims, mostly involving 'simple', 'fast', and 'robust'. What is lacking from many of these is what distinguishes the language from most similar languages. 









