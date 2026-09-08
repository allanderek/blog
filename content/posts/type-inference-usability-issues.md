---
title: "Type inference and usability issues"
tags: [ programming, types ]
date: 2026-09-08T12:08:36+00:00
---

Austin Henley has written a [post titled: Type inference has usability problems](https://austinhenley.com/blog/typeinference.html).
I'm not quite sure he demonstrates the title, but it's definitely a good thought provoking post.

# Answers to specific points

Specific points in Austin's post:

## Go

> You might think, "ok, I'll just not use it" if it is bad. But if you try to avoid it in Go, you will get warnings! Go's linter says that you "should omit type X from declaration of var Y; it will be inferred from the right-hand side". Moreover, all of the examples from Effective Go follow this practice.

Go continues to make decisions I disagree with. This is one of them, fully agree with Austin on this one. What ever you think of type inference it's fairly hard to argue that a system should encourage you to drop type signatures.


## Cognitive load

> There are already a lot of details to consider when comprehending code. I don't want to make this even more difficult on myself by having to remember variable types or have to constantly navigate away to look it up.
>
> And what if you aren't using your code editor? What if you are viewing the code on GitHub? No type information for you!

Quite. I think these are excellent points. We are constantly told that code should be optimised for reading, not for writing. A little bit of extra effort when writing to write down the types of variables probably help comprehension when reading.

## Use it Sparingly

> You certainly don't always have to use type inference. Others have come up with best practices for when to use type inference (e.g., these and these). Another developer listed the benefits of explicit typing to include code-as-documentation and enabling them to follow a Test Driven Development-like process.

I actually think this does work pretty well in Elm, and similar functional languages. Most will place type signatures on their top level definitions at least. I've [written before](/posts/let-signatures/) regarding type-signatures in let-bindings. Also in [a post regarding function length](/posts/small-functions-and-elm/):

> I have a disagreement with [Robin Heggelund Hanson]( https://github.com/robinheghan) (creator of the [gren programming language, close sibling of Elm](https://gren-lang.org/)) over whether definitions within a `let-in` scope should have type signatures. I say they should, and he disagrees, most of the disagreement though, I believe, stems from the fact that he believes that whenever a definition becomes large enough to warrant a type signature it should be factored out. I don't see his logic there, I don't see the benefit of this, I think all you achieve is moving a definition further away from its single use site, though it may have the benefit of moving other definitions closer to their use sites. (I also think there are [other good reasons](/posts/let-signatures/) to have signatures on let definitions).

So I think that both of us agree that type signatures are good for comprehension, it's just our solutions are different. I think all let-bindings should have type signatures, he thinks that if a definition is non-trivial enough to warrant a type-signature then it shouldn't be in the let-binding and should be a top-level definition with a type signature. So both of us are in agreement here with using type-inference sparingly.

## Supposed Benefits: Readability and Saving Keystrokes

In agreement here.

> My response? Go refactor your hideous code.

Yes, if type inference (or more rather removing type signatures) somehow improves the readability of your code, then yes you probably have poorly written code that could be better refactored.

> A weaker argument I have heard is that you have less code to type with type inference! Because my typing speed is definitely the bottleneck when coding.

Yes. As I said above, there is general consensus (I think) among programmers that code should be optimised for **reading** not for writing.


# Other related points

## Elm syntax

Elm syntax doesn't quite allow for all let-bound variables to have an associated signature. Consider:
```elm
update : Model -> Msg -> (Model, Cmd Msg)
update model message =
    let
        (newModel, effect) = 
            updateWithEffect model message
    in
    (newModel, effectToCmd effect)
```
The problem is that there is no way to write the signature for `(newModel, effect)`, you cannot write `(newModel, effect) : (Model, Effect)`.
This could obviously be solved though if there was enough will, if, for example, it was deemed that type-inference was considered detrimental.


## Functional vs Imperative programming languages

Var definitions, because imperative languages allow one to update the value of a variable, it can sometimes make sense to have a type signature on a variable definition for the reason that the initial value is sometimes of a too general type. A common example is a list which is added to, it may start as an empty list, but you want to show that it will only host values of a particular type. Something like:
```python
seive : (Int -> Bool) -> Int -> List Int
seive predicate n =
    result = []
    for i in 0 .. n do:
        if predicate i then
            result.append(i)
    return primes
```

## Type inference as IDE helper

Even if you didn't have type-inference in the **language** per se, but the language (or more rather the type system) was still ammenable to type-inference this could make for a handy IDE tool. Something like "please complete the type signature of this function". Of course, AI tools can often do this too, but with a type-inference algorithm it would generally be correct (it would *always* be a suitable type, but you might want to choose a less general type than the one inferred). More importantly, inferring it would be free, and wouldn't involve sending your code to a third party.


# Conclusion

I like Austin's post, I have penchant for posts which question beliefs and practices which are often taken as given without much associated evidence.
[Here is a good post](https://danluu.com/empirical-pl/) from Dan Luu, which is a literature review for the benefits of static typing, the summary is particularly worth reading. It's good to look through this and realise that the evidence for your belief (in either direction of the static vs dynamic debate) is pretty weak. 
Also, I've [written before](/posts/let-signatures/) regarding type signatures in let-bindings, which for Elm is pretty much the equivalent of advising to eschew type-inference.
