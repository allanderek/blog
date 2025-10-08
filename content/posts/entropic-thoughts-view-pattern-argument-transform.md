---
title: "Entropic Thoughts: ViewPattern Argument Transform"
tags: [ programming, types, haskell, elm ]
date: 2025-10-08T11:16:46+00:00
---

The [Entropic Thoughts blog](https://entropicthoughts.com/index) has a [new post: "Non-Obvious Haskell Idiom: ViewPattern Argument Transform"](https://entropicthoughts.com/non-obvious-haskell-idiom-viewpattern-argument-transform) regarding something I didn't know existed in Haskell, and it touches upon something I've [written about before](/posts/missing-language-feature/) so I'd like to say how they are related, and wonder whether this is the correct solution, I don't have a better one.

So first the new feature in Haskell is a *"ViewPattern argument transform"*. What is one of those? Well suppose you have a function such as:

```haskell
someFunction param =
 let
   usefulValue = transform param
 in
 ... in which usefulValue is useed
```

The issue here is that `param` is only used once to transform it into something that is more useful throughtout the rest of the scope of the function.
It would be better if we could somehow remove `param` from scope, so that we do not unnecessarily use it. In Haskell, there is a way to do that, using a *"ViewPattern argument transform"* the function can instead be written as:

```haskell
someFunction (transform -> usefulValue) =
  ... in which usefulValue is useed
```

Now, as I said before, I've [written about about the basic problem that this is solving before](/posts/missing-language-feature/). To recap the example from that post:

```elm
update : Msg -> Model -> ( Model, Cmd Msg)
update message model =
    ...
    RollDice  ->
        let
            newModel : Model
            newModel =
                rollDice model
        in
        ( case newModel.dice == 6 of
            True ->
                { newModel | score = newModel.score * 2 }
            False ->
                newModel
        , Cmd.none
        )
    ...
```

Now notice that `newModel` is used 4 times in the body of the `let-in`. Also note that it is the same type as `model` and hence an easy bug to make is to misuse `model` in place of `newModel`. I chose a `rollDice` example, because that likely uses `elm/random` and the new `Model` that it returns has the updated *seed* for the random number generator. It's a common bug in functional languages to forget to store the new *seed*. It's also likely a pernicious bug because basically everything works more or less as expected. You have to notice that, on certain paths, the subsequent numbers generated are not entirely 'random'. If the seed is sometimes used in some other way as well, then this can be pretty hard to spot. Anyway, this is the problem that *"ViewPattern Argument Transform"* solve. In this case, we would have to factor out the `RollDice` case into a function of its own:

```elm
updateRollDice : Model -> (Model, Cmd Msg)
updateRollDice (rollDice -> newModel) =
    ( case newModel.dice == 6 of
        True ->
            { newModel | score = newModel.score * 2 }
        False ->
            newModel
    , Cmd.none
    )
update : Msg -> Model -> ( Model, Cmd Msg)
update message model =
    ...
    RollDice  ->
        updateRollDice model
    ...
```

Note that we don't even need the name `newModel` now, we can just call this `model`, so we could re-write `updateRollDice` as:
```elm
updateRollDice : Model -> (Model, Cmd Msg)
updateRollDice (rollDice -> model) =
    ( case model.dice == 6 of
        True ->
            { model | score = model.score * 2 }
        False ->
            model
    , Cmd.none
    )
```

Since the name `newModel` was only ever there to distinguish it from `model`. 

So I think this would *mostly* solve the problem that I had written about. There are two things I do dislike about this syntax:
1. It sometimes, as in this example, forces you to factor out code you may not have otherwise chosen to.
2. It feels a little 'magic', until someone explains what happens and why I feel like reading this code in the wild would seem quite opaque.

In my previous blog post I noted that Python does have syntax or this:

```python
>>> x = [1,2,3]
>>> y = x
>>> del x
>>> x
Traceback ...
NameError: name 'x' is not defined
>>> y
[1, 2, 3]
```

This is far more intuitive, but I also noted that in functional languages typically the order of definitions doesn't matter, and that this feels more functional and less imperative. So having a `del <name>` **command** in Elm (or any other functional language) would feel a bit imperative.
I don't have a better solution than either `del` or *"ViewPattern Argument Transform"*, but if I were making a functional language I would consider either feature not quite perfect enough to include. 
