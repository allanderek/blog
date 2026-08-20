---
title: "Link: Mojo is now open source"
tags: [programming, llm, python]
date: 2026-08-20T10:11:17+00:00
---

[Mojo is now open source](https://www.modular.com/blog/mojo-open-source), via [Simon Willison](https://simonwillison.net/2026/Aug/18/mojo-is-now-open-source/).
I was also struck by the same quote as Simon in the [Mojo road map](https://mojolang.org/docs/roadmap/):

> As Mojo matures through phase 3, we believe it will become increasingly compatible with Python code and deeply familiar to Python users, but more efficient, powerful, coherent, and safe. Mojo may or may not evolve into a full superset of Python, and it's okay if it doesn't.

> We're encouraged by how well AI-assisted coding tools already help migrate Python to Mojo today, and we're confident that future tooling and ecosystem maturity will make this evolution even smoother.

I think this is interesting. Until now, there have been many language projects that have felt it a great advantage to piggy-back on the back of some popular language's eco-system. This has taken many forms, including compiling to the target language's virtual machine, or even directly compiling to that language. A recent example is [sky-lang](https://sky-lang.org/), an Elm-inspired functional language that compiles to Go and uses the Go eco-system. Other examples include [Kotlin](https://kotlinlang.org/) and [Scala](https://www.scala-lang.org/) which were functional languages which compiled to Java's virtual machine and intended to take advantage of Java libraries. Similarly [Gleam](https://gleam.run/) is a great functional language that runs on the Erlang virtual machine.

Now there are some reasons to do this other than to use the libraries of the supportive language. For example to take advantage of
> reliability of the highly concurrent, fault tolerant Erlang runtime

(from the Gleam homepage). But either way it strikes me that much of that was done as a way of spreading the language designers' resources as far as possible. In the age of AI-assisted coding this is less necessary.

One issue with piggy-backing on another eco-system is that that eco-system has been designed and implemented assuming the supporting language.
Often, the whole point of the new language is that the supportive language is of a particular paradigm and there is a perceived need for a different paradigm. For example, the Erlang runtime already had Elixir as a functional language, but Elixir was a dynamically typed language (it's now a [gradually typed language](https://elixir-lang.org/blog/2026/06/03/elixir-v1-20-0-released/)) and the creators of Gleam perceived a need for a statically typed functional language. That's great but it means that the eco-system they are piggy-back on is designed to work with a dynamically typed language.

Another perceived reason for piggy-backing on another language is the possibility of gradual adoption. For example, because Elm compiles to Javascript, it's possible to take a large Javascript, e.g. React based project and replace only small components of it with Elm components. This allows for an experimental first try of Elm and also means that if the decision is made to fully adopt Elm and replace the whole React project, it can be done gradually.

I think both of these reasons are less convincing but not entirely unconvincing, given the current state of AI-assisted coding.


