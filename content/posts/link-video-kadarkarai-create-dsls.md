---
title: "Video Link: Jayaprabhakar Kadarkarai - Create your own DSLs"
tags: [ software development, dsl ]
date: 2026-08-19T08:57:24+00:00
---

[Video Link: Jayaprabhakar Kadarkarai - Create your own DSLs](https://www.youtube.com/watch?v=uubcJ9Bvt7M&list=PLYHMN-0pC7n8&index=1&t=1519s)

This is technically a link to a talk contained within a video. The entire video is worth watching it's the lightning talks at the first Software Should Work conference.

In this particular lightning talk, Jayaprabhakar Kadarkarai explains why he thinks you should be more willing to create your own DSLs.
He gives an example of one for creating a bounded set of HTML.

I'm not going to entirely disagree with this, but I am going to give some of the case against writing a DSL.
I have [written before](/posts/dsls/) regarding DSLs. In that post I made the case that the problem was one of frequency. Because the task that the DSL is created for is intended to be specific, that means you only use the DSL for that specific task. That means, you don't use it so frequently, so it's easy to lose your skill with it. I made that case using the build tool `make`. Now that case is a lot weaker, although you might lose your skill at that particular DSL, an LLM will not. If it's a private DSL, you can even write your own 'skill' for it. 

However [that post](/posts/dsls/) does write up a main issue, that I think it is the main reason you may wish to reconsider writing your own DSL and instead write a library. The problem is that, although your DSL is great at the specific task for which it was designed, it's not a general purpose programming language. You will, inevitably wish to start doing general purpose programming type things in your DSL. Let's take Jayaprabhakar's DSL for creating a bounded set of HTML elements, which looks something like this:

```
view SignIn:
    card:
        text h1: Welcome back
        input: Username
        input: Password
        button: Sign in
        text caption center: or continue with
        row gap=medium:
            button: Sign in with Google
            button: Sign in with GitHub
```

Because we're programmers we'll inevitably wish to 'remove drudgery', what if we want to give a list of login providers and have a button for each, something like:

```
view SignIn:
    card:
        text h1: Welcome back
        input: Username
        input: Password
        button: Sign in
        text caption center: or continue with
        row gap=medium:
            for all loginProvider in loginProviders:
                button: Sign in with {loginProvider}
```

Once you have variables and looping, you will also eventually want conditionals, and even function calling. Hey, once your project gets big enough perhaps you start calling for namespaces or modules. The point is that sooner or later you find that you are doing one of two things:
1. Generating your DSL code from a general purpose programming language
2. Your DSL is extended and is now a general purpose programming language, albeit a poor one

In the case of 1. you will find that you start off with generating the DSL using just string concatenation and/or string interpolation. This is how everyone starts generating SQL queries in a general purpose language. Then you realise it would be neater if you somehow describe in types the syntax of your DSL and then write a renderer out to the DSLs concrete syntax. So now, your pipeline looks like this:

1. General purpose programming language defines the AST
2. You programmatically build up the AST
3. The AST is rendered out to the concrete syntax of your DSL
4. This is passed to your DSL interpreter which parses it into its own representation of the AST
5. The DSL interpreter renders the AST into HTML

It's clear that you can skip out the concrete syntax of the DSL and just go straight to the AST. You now have two representations of the AST, one in your general puprpose language and one in whatever the DSL interpreter is written in. If those are the same language you can use the same definition. Now you can go directly from your code to the AST for your DSL, and then simply call the routine to have the DSL interpreter's code render the AST to HTML. Congratulations you have now built a library for generating a bounded set of HTML. This is much better than writing a DSL.

In his talk Jayaprabhakar even hints that he is generating the DSL, because he shows that he can create many similar prototypes changing only a few lines of his DSL code.

There are of course some reasons why you might wish to go ahead and write the DSL with concrete syntax anyway.
1. Perhaps your DSL is for non-programmers
2. Perhaps it is intended to be used from multiple programming languages.

For example SQL is readily available to multiple programming languages since all they need to be able to do is generate the concrete syntax of SQL. However, if SQL was a library, then you would need some kind of foreign function interface to call that library from other languages. However, this would mean that SQL-injection errors would never have been a problem.

So there are pros and cons to writing a DSL or a library. My advice, start with a library and create a concrete syntax for the AST only when there is a need for that, my prediction is that that is rare.
