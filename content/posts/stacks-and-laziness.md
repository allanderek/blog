---
title: "Stacks and Laziness"
tags: [programming, elm]
date: 2025-11-12T10:46:02+00:00
---

I sometimes find that developers do not really have a good grasp on the point of laziness in a programming language, believing that it is mostly an optimisation.
It's not really an optimisation, it's a way of writing generic code which doesn't need to be specialised for a particular use case. I've [made an attempt](/posts/time-extra-posix-to-parts-great-laxy-example/) before to explain why laziness can result in cleaner or less complicated code. In this post I wish to attempt to explain another example where laziness can solve a complexity issue in code, but it comes at some cost, and understanding that cost can go a long way to explaining why laziness is not the norm (aside from the fact that purity is also not the norm).

## Stacks and length in eager languages

Stacks are a relatively simple concept, you want a data structure which allows one to add elements and remove them in a last-in-first-out order. Fortunately, linked-lists are a good data structure for this, because appending to the front of a list, and removing from the front of a list are O(1) operations, i.e. it doesn't matter how long your stack is, the `push` and `pop` operations take the same amount of time. You get this for free, in contrast to a queuing library where the order of items to come out of the queue you wish to be first-in-first-out.

So if you implement a library, or a simple module, for stacks in your application, it's relatively simple, here is an easy solution:

```elm
module Stack exposing (Stack, empty, pop, push)

type Stack a
    = Stack (List a)

empty : Stack a
empty =
    Stack []

push : a -> Stack a -> Stack a
push a (Stack l) =
    Stack (a :: l)
    

pop : Stack a -> (Stack a, Maybe a)
pop (Stack l) =
    case l of
        [] ->
            (Stack [], Nothing)
        top :: rest ->
            (Stack rest, Just top)
```

Now, there is a commonly wished-for primative in such a module `length`, which returns the size or length of the current stack. There are two ways to implement this, and they have opposite advantages/disadvantages and hence are useful in different circumstances, first the obvious solution, which is just to calculate the size of the stack when asked:

```elm
module Stack exposing (Stack, empty, length, pop, push)
-- module as above with
length : Stack a -> Int
length (Stack l) ->
    List.length l
```

This has the great advantage that you incur no cost in storage or time if you never call the `length` function. So if your stack use case doesn't require ever knowning how long the stack is, this is perfect. However, the disadvantage is that this operation is O(n), that means the time it takes to compute the length is dependent on how large the stack is, it also means that subsequent calls to `length` will still take O(n) time, even if the stack has changed very little in the meantime. For example, this is a poor implementation if your use case means you always check the length of the stack immediately before/after adding an element (e.g. you may have a stack length limit). It's also bad if you have very long stacks.

The alternative is to keep count of the length of the stack as you add elements to it:


```elm
module Stack exposing (Stack, empty, length, pop, push)

type Stack a
    = Stack (List a) Int

empty : Stack a
empty =
    Stack [] 0

push : a -> Stack a -> Stack a
push a (Stack l n) =
    Stack (a :: l) (n + 1)
    

pop : Stack a -> (Stack a, Maybe a)
pop (Stack l) =
    case l of
        [] ->
            (Stack [] 0, Nothing)
        top :: rest ->
            (Stack rest (n - 1), Just top)

length : Stack a -> Int
length (Stack _ n) =
    n
```

So note now the `length` operation is O(1) (constant time) regardless of how long the stack is. But you incur a cost everytime you add/remove from the stack. So this is useful in the opposite cases to the above, if you regularly inspect the length of the stack this is great, and particularly so if your stacks can grow to a large size, but in the case that you never call `length` you are performing needless calculation.

So, in an eager language, the library/module author must choose which of these two use cases they are providing for and do so, although of course one library could easily provide both modules. If your program has both use cases, then you will need both modules. And if your use case *changes*, then you will need to update your module (or use the other one if you already have it).

## Laziness conceptually solves this issue

This problem of requiring two separate modules for two separate use cases is exactly the kind of issue that laziness is intended to solve.
The promise is, that one can just implement the second solution, that is keep track of the length of the stack. If the `length` primitive is never evaulated then great, you will never incur the cost of all those calculations to keep track of the size of the stack, that's exactly what lazy evaluation promises.

However, although the size value itself is not kept track of, the implementation unfortunately needs to keep track of all the unevaluated thunks. Each time an item is pushed or popped from the stack, a thunk is added.

## Space leaks

If your use case does the following:
1. Many items are pushed/popped from the stack
2. You never evaluate the `length` of the stack

You will end up with a space leak as more and more thunks are accumulated in place of the actual `size` value. What's particularly bad is that the size of this accumulation of thunks is in proportion to the number of `push` and `pop` operations that have been performed **not** the size of the stack, so even if your stack never grows above a small number of elements, the number of thunks accumulated is unbounded.

It's clear that even if you never evaulate the stack's `length` you would likely be better off just keeping track of the size of the stack eagerly, that is, the extra (and needless) computation that you do is better than the storage costs for all the thunk accumulation. For this reason, most stack implementations in lazy languages mark the `size` value as "strict", so that it is evaluated eagerly. This also means that the lazy language ends up with the same problem as the eager language, that is, if you really care about performance then you need two versions of your stack module if you have two use cases, one that uses `length` and one that does not.


## Conculsion

In practice, the overhead of (eagerly) keeping track of the size of a stack is pretty small for all but highly specialised use cases. So in either lazy or eager languages one just implements the solution which maintains the size of the stack (and does so eagerly in the lazy language). But this problem illustrates a broader patter. Laziness can simplify API design and eliminate certain trade-offs. But it often does not come for free and a particular problem is one of space leaks caused by accumulated deferred computations. This can be difficult for a user to reason about, and is likely why laziness is not the norm.
