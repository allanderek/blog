---
title: "Lambdas (again) and def syntax"
tags: [ programming, Elm, syntax ]
date: 2026-08-26T10:15:18+00:00
---

I have written about lambdas several times:

* [First regarding lambda syntax in Python](/posts/python-and-lambdas/)
* [Then again about lambda syntax in Elm](/posts/lambdas/)
* [Then again critiquing a post about Python lambdas](/posts/lambdas-again/)

The common theme in all of these is roughly: Does lambda syntax really **need** to exist?
I think the answer is quite clearly, "no". We could get by just fine if we were forced to use definition syntax to create all functions.
However, that doesn't necessarily mean we should remove lambdas from the syntax. On the [Gren discord](https://discord.gg/Chb9YB9Vmh) there is a thread in the language design channel proposing an alternative to removing lambdas, that is; [removing function definition syntax](https://discord.com/channels/1250584603085766677/1540084581149970432).

There are two main reasons that I propose removing lambda syntax:
1. It removes a place where there are two ways to do the same thing
2. It forces you to name all your functions

I'm much more confident that number 1 is a net win. Number 2 is more debateable. It's certainly true that with lambda syntax you can create code that is more difficult to read than it needs to be because you haven't named a unit of computation. I think the example given in the [3rd linked post](/posts/lambdas-again/) is a good one, albeit in Python so I'll translate it here to Elm:

```elm
numbers = [1, 12, 37, 43, 51, 62, 83, 43, 90, 2020]
List.filter (\x -> modBy 2 x == 1) numbers
```
Tell me that it is easier to quickly ascertain what that code is doing than this code:

```elm
numbers = [1, 12, 37, 43, 51, 62, 83, 43, 90, 2020]
isOdd : Int -> Bool
isOdd x = modBy 2 x == 1
List.filter isOdd numbers
```

However, there are a quick couple of rubuttals to this:
1. Sure, but if I give the resulting list a name it's easier `oddNumbers = List.filter (\x -> modBy 2 x == 1) numbers`, and that's more realistic code in the wild.
2. Now you are **forced** to name **everything** and naming things is famously one of the two hard problems in computer science.

So the proposal in the Gren language discord is to keep lambda syntax, but remove function definition syntax. So instead of:
```elm
functionName : T1 -> T2 ... Tn -> T
functionName x1 x2 ... xn =
    ...
```
You would instead write:

```elm
functionName : T1 -> T2 ... Tn -> T
functionName = \x1 x2 ... xn ->
    ...
```

I quite like this proposal. It achieves the inarguable of the two advantages above, that there is now only one way to do something. The syntax for a definition is pretty near identical, although you sort of end up with more indentation, at least at the moment since you end up writing:

```elm
functionName : T1 -> T2 ... Tn -> T
functionName = 
    \x1 x2 ... xn ->
        ...
```
So the function body is twice indented, whereas before it was once indented. I'm relatively sure that could be solved with either some small syntax change or some change to the formatter.

I think this is a more *elegant* solution than removing lambda syntax. It means that the syntax for let definitions is **always** `pattern = expression`, just that sometimes that expression is a lambda expression. I think it would be *very* easy to get used to this. When I started Elm from Haskell, I though the fact that you couldn't (with a minor exception) write function patterns was a bit limiting, e.g. in Haskell you can write:

```haskell
coalesce :: Maybe a -> Maybe a -> Maybe a
coalesce (Just a) _ = Just a
coalesce Nothing (Just b) = Just b
coalesce Nothing Nothing = Nothing
```
In Elm you have to instead write:
```elm
coalesce :: Maybe a -> Maybe a -> Maybe a
coalesce left right =
    case (left, right) = 
        (Just a, _) -> Just a
        (Nothing, Just b) -> Just b
        (Nothing, Nothing) -> Nothing
```
I haven't missed the Haskell syntax a single time and would probably advocate for removing it. It is sometimes very liberating to have a choice taken away from you.
In Elm, never have I paused before writing a function to consider whether I should use definition matching or a case expression.

Lastly, someone, somewhere convinced me that `\_ -> x` was preferable to `always x` (it was probably on the Gren discord since Gren has removed `always`).
I wonder if there are other small functions like this that can be *more* readable as a lambda syntax.

## Conclusion

I'm convinced, I think removing function definition syntax is a good idea.
I still think it's a little weird that functional programmers are often so attached to lambda syntax, even though they rarely use it.
But this proposal would solve that since they would use it all the time.
