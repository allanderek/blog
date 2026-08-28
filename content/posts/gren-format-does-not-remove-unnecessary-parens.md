---
title: "Gren format does not remove unnecessary parens"
tags: [ programming, gren, syntax ]
date: 2026-08-28T17:39:40+00:00
---

The new `gren-format` tool does not remove unnecessary parentheses. First of all, this is [very nicely documented](https://gilramir.github.io/gren-format-lib/settledDecisions.html#sd4-redundant-parens-are-never-stripped) within a list of *settled decisions*.

This decision might seem surprising, but I think it's right. Why would you put unnecessary parentheses in, unless you thought they increased clarity?

In my first year of a computer science degree (last century), I recall an exam which included questions about operator precedence in C programs.
I recall thinking this was a dumb exam question that tested recall and nothing important. As young and foolish as I was then I think I got that assessment right.
I'm still unsure if I could accurately state the operator precedence rules in most of the languages I use. Firstly, I typically do not write complicated mathematical expressions without giving names to intermediate results. Secondly, if I'm at all unsure I just put the parentheses in and, there is no problem. I often put the parentheses in even if I am sure. I **know** that `*` binds more tightly than `+`, but still I don't see the problem in writing:

```
x + (y * z)
```

I often forget the precedence rules for logical operators and that's because it nearly always reads better with the parentheses in. Consider:

```elm
canEdit : Bool
canEdit =
    isAuthor && withinEditWindow || isModerator && not postLocked
```
If I saw this code in the wild I'd have to stop and think about what it's doing. 
It turns out that `&&` binds more tightly than `||`, so the above is equivalent to:

```elm
canEdit : Bool
canEdit =
    (isAuthor && withinEditWindow) || (isModerator && not postLocked)
```
But I certainly find the latter much more readable.



Here is another interesting one:

```elm
not isArchived && hasSubscribers
```

I think if I read this, I'd open up the repl and check what the precedence is, is this `not (isArchived && hasSubscribers)` or `(not isArchived) && hasSubscribers`? It turns out the answer is the latter, but I'll add the parentheses in whether or not it naturally parses the way I intend.

Now that I think about it, I think operator precedence and associativity are probably mistakes. We probably should have just always forced people to write the parentheses, or **maybe** allowed for only left-associativity.
