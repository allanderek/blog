---
title: "Needless do notation"
tags: [programming, elm, haskell]
date: 2025-09-18T14:25:21+00:00
---

Cracking [post on the Elm discourse by john_s](https://discourse.elm-lang.org/t/best-way-to-write-intensely-monadic-code-in-elm/10434/6) in response to rupert's question regarding "intensely monadic code".
In his response john_s details some findings from a review of 300k lines of Purescript/Haskell code:

> In surveying over 300K lines of PureScript / Haskell code in 4 large applications I believe the most genuinely needed monadic binds I ever saw in any properly sized function was 4 and was **1 on average!!!**. In other cases,
>   * No Monad was even necessary because it collapsed to identity!!!
>   * Functor was the real operation.
>   * Applicative was the real operation.
>   * The engineer did not understand the State monad or the State monad transformer.
>   * The function was too large.


He details 4 of these patterns. I can almost see how these patterns emerge as more complicated code is thought needed, or even written in the first place, and then that is simplified down, but then that simplification is just not taken down as far as it can go, here is the first pattern:

```elm
noWorkDone = do
  x <- someResult
  pure x

-- the above is basically like the following in Elm
noWorkDone = 
  someResult |> Result.andThen Ok 

-- so... um... this doesn't do anything! It unwraps the result and then re-wraps it 
-- without doing any work
noWorkDone = someResult
```

I think this survey lends credence to the idea that `do` notation was an error, and hence to Elm's rejection of that. I'm not saying it settles the case, but it's definitely a point in favour **not** adding `do` notation to your language.

I did quibble with the second variant of the third pattern, which was given as:

```elm
mostlyApplicative = do
  a <- aResult
  b <- bResult
  c <- f a b
  pure { a, b, c }

-- re-written in PureScript
mostlyApplicative = do
  Tuple a b <- lift2 Tuple aResult bResult
  map (\c -> { a, b, c }) (f a b)  

-- in Elm... this is messy and should be re-framed but I am just trying to make
-- a point of showing only one real `andThen` needed
mostlyApplicative = 
  Result.map2 pair aResult bResult
     |> Result.andThen (\(a, b) -> Result.map (\c -> { a = a, b = b, c = c }) (f a b))
```

I think the `do` notation is very much easier to read. In fact the middle effort here is somewhat unreadable to me.
Here is how I replied:

> Here I find the do notation version at least as readable as the others. In 3a I frankly find the middle `-- re-written in PureScript` pretty unreadable (though I do think it’s instantly recognisable as ‘type-munging’ code, for which you tend to really only have to look at the type signature). However, I think in most actual cases of this pattern, there is a bit of actual logic as well and that can get lost in amongst all the “type munging”. Anyway in 3a I find that the core thing to understand about the code would likely be that `c` is basically the result of applying `f` to `a` and `b` (albeit and then extracting the result), and I find that much easier to see/understand in the `do` notation version than either of the other two. Though I guess if you have more realistic names than `c` and `f` it’s perhaps clearer, e.g. if `c` is actually `distance` and `f` is `getCartesianDistance` and perhaps `a` is `startPoint` and `b` is `endPoint` or something like that.

Anyway food for thought. Here's a [link to john_s's post](https://discourse.elm-lang.org/t/best-way-to-write-intensely-monadic-code-in-elm/10434/6) again.



