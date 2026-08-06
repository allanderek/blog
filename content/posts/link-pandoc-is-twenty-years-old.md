---
title: "Link: Twenty years of Pandoc"
tags: [ software development, Haskell ]
date: 2026-08-06T10:47:03+00:00
---

[Link: Twenty years of Pandoc](https://pandoc.org/twenty-years-of-pandoc.html)

An interesting look back at the first twenty years of Pandoc by its creator and maintainer John MacFarlane.
If you're not interested in the history of improvements and evolution of Pandoc, you may still find the discussion on the choice of Haskell interesting.
You can read the [Prehistory](https://pandoc.org/twenty-years-of-pandoc.html#prehistory) section for why Haskell was chosen and the
[Retrospective: the choice of Haskell](https://pandoc.org/twenty-years-of-pandoc.html#retrospective-the-choice-of-haskell) section for a discussion of how well that has gone.

Interestingly John never chose Haskell as the best language for a document translator, but rather chose a document translator as the best project in which to learn Haskell.

In the retrospective section he suggests that Haskell was an excellent choice of language for a document translator. I agree. It suits its main strengths and doesn't have a problem with its main weaknesses.

> Its algebraic data types give us a very clean, ergonomic representation of a structured document

Yes, algebraic data types are great for transformations of any data types, that's why such languages have always been good for compiler development, traditionally this has been functional languages but we now see algebraic data types (aka sum types, custom union types, variant types, enum types etc.) being added to more imperative languages such as Rust.

> Its strong type system, which gives you a compiler error if you don’t combine the types of things in the right way

Yes, it's *particularly* useful for transformations that involve multiple input/output types. Whereby you may need to update the intermediate 'abstract document type' when you add a new input/output type and you want to make sure that has not broken any of the current parsing or output phases for existing input/output types.
Again, this is why strong type systems coupled with algebraic data types have always been good for compilers, they often have at least multiple backends and sometimes multiple front-ends too.

This is rather speculative but I might also suggest that this match for functional languages to compilers might have held them back a little. When you develop a language, you are necessarily developing a compiler (and associated tools) for it. For a language designer this often becomes their most significant project, which means that features that are useful/helpful to writing a compiler are accepted more readily than features that are useful/helpful for writing other kinds of applications or programs. But treat that as very speculative, often language designers have some kind of motivation for developing the language outside of writing compilers in it.

> Haskell is a pure language; nothing can have side effects that aren’t explicitly allowed for in the types. 

I don't think the author makes the case for this. Again, a transformation is actually a good program for a pure language, since it's non-interactive. Even a lazy language somewhat shines here, because you do not care *when* computation takes place. The program is invoked and runs to completion. It mostly doesn't matter when the meat of the computation takes place. You can make some kind of case that it's better to do the heavy computation and *then* open the output file, rather than open the output file and then do the heavy computation, but it's minor. If you are instead developing some kind of interactive program, such as a game, that changes the priorities somewhat. It's also not a long running application so space-leaks probably do not show up much. Even general efficiency is only a problem if you are translating either very large or very many documents. Of course, I somewhat agree that purity does indeed help with reasoning about the program and is "extremely useful for preventing bugs".

> The choice of Haskell has also led to a high quality and low volume of contributors (a combination that is good for a project without a lot of resources).

That's a good point. It's very similar in flavour to Paul Graham's essay regarding [The Python Paradox](https://paulgraham.com/pypar.html), in which he basically claims you can get smarter programmers to work on a Python project than a Java project. This was in 2004 and the logic almost certainly does not apply to Python any longer, but likely applies to other currently niche languages.

There is also an interesting section relating current LLMs to Pandoc and asking the question whether Pandoc (or other similar conversion programs) are still relevant. This is a good question, and [the section](https://pandoc.org/twenty-years-of-pandoc.html#whither-pandoc) is worth reading. It gives a great example of the rules for emphasis in markdown/commonmark, and how no amount of complicated rules can ever capture the nuance of the meaning a human would give to complex edge cases, but an LLM might be able to.


Anyway congratulations to John Macfarlane for twenty years of Pandoc. 
