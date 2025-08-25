---
title: "Left-to-right programming and where syntax"
tags: [elm, programming]
date: 2025-08-19T11:48:17+00:00
---

Graic has a nice post up discussing [left-to-right programming](https://graic.net/p/left-to-right-programming), the main tagline is that "Programs should be valid as they are typed".

I agree with this idea, the main thing that the post points out, is that if definitions come *after* use, it is difficult for the IDE to help with auto-completion and/or hints (such as undefined variables). The first example is Python's list comprehensions when typing out the line:

```python
words_on_lines = [line.split() for line in text.splitlines()]
```

when you get to

```python
words_on_lines = [l
```

There is no way for the IDE to help you complete `line`, since it isn't defined yet, and when you get to `line.` there is no way for the IDE to show you what members are on the `line` object since again, `line` has not yet been defined.


This all makes sense to me. When programming in Haskell, if you need to make some sub definitions, you can do so with `let` syntax or `where` syntax. Here is the same function defined using `let` and `where` syntax.

```haskell
circleAreaLet :: Double -> Double
circleAreaLet radius = 
  let radiusSquared = radius * radius
  in pi * radiusSquared

circleAreaWhere :: Double -> Double
circleAreaWhere radius = pi * radiusSquared
  where radiusSquared = radius * radius
```

In Elm, we only have `let` syntax. I sometimes had a small pining after `where` syntax, but mostly I enjoyed that I didn't have to make the choice.
I think Graic's left-to-right argument is interesting, I **think** it **mostly** argues for `let-in` syntax. Since when writing the `pi * radiusSquared` part the `radiusSquared` is already available to you. However, note, the whole thing is not syntactically correct until after the `in` is typed. That's not true of the `where` syntax, when the whole thing is parseable immediately.

A final point, is that with type inference, out-of-order definitions can be helped somewhat. If you use a function that you haven't yet defined, the IDE can predict the type of the function based on its usage. So it could for example start off the definition of the function for you. I don't know that any IDE does this yet.

In the era of A.I. auto-completions though, it's a little difficult to know which is better, but I could imagine sometime in the future the A.I. autocompleter, using the type-checker to aid its prediction, in which case it could benefit from the same help as the human, and we would still be arguing for left-to-right programming.
