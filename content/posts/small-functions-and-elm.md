---
title: "Small functions and Elm"
tags: [programming, elm]
date: 2025-11-17T10:40:47+00:00
---

[Cindy Sridharan](https://copyconstruct.medium.com/) writes an [interesting post](https://copyconstruct.medium.com/small-functions-considered-harmful-91035d316c29) which questions the wisdom of keeping functions small.
Although the author uses the provactive title "Small functions considered harmful" that is actually not their point, which is better stated in the conclusion:
> This post’s intention was neither to argue that DRY nor small functions are inherently bad (even if the title disingenuously suggested so). Only that they aren’t inherently good either.

I've long had a feeling that an urge to keep functions small is counter-productive in many cases, particularly in Elm, and other languages which have nested functions. I think the key point is that you wish to decompose problems into sub-problems well, but that that doesn't have to mean that a function is necessarily short. In this post I'm going to attempt to argue for this by comparing code fragments which are clearly pretty similar structurally but in which one has a single long function and the other does not. In this way I will argue that a simple measurement of how long a function is, is not particularly helpful.

## Nested functions

Let's start off with something fairly simple, a nested function. It's simple in that it is pretty easy to see that these two code fragments are pretty close to equivalent. 

```elm
view : Model -> Html Msg
view model
    let
        viewTitle : String -> Html Msg
        viewTitle title =
            Html.h1 [] [ Html.text title ]
    in
    Html.main_
        []
        [ viewTitle (Route.toTitle model.route)
        , viewBody model
        ]
```
        
```elm
view : Model -> Html Msg
view model
    Html.main_
        []
        [ viewTitle (Route.toTitle model.route)
        , viewBody model
        ]

viewTitle : String -> Html Msg
viewTitle title =
    Html.h1 [] [ Html.text title ]
```

It's a little contrived, in the first instance we probably do not make a `viewTitle` *function* but rather simply a `title : Html Msg` definition.
However, I've kept them the same to show that these two are clearly pretty similar. In fact I prefer the `let-in` version since it makes clear to the user that `viewTitle` is only ever used with `view`. If we stick to the convention of scoping a definition as locally as is possible, then whenever we see an actual top-level definition, we know that it is likely because it is used in more than one place.

In this example it was assumed that `viewBody` was defined elsewhere as a top-level definition, but by the logic above, that's pretty unlikely, since `viewBody` is likely only used here:


```elm
view : Model -> Html Msg
view model
    let
        viewTitle : String -> Html Msg
        viewTitle title =
            Html.h1 [] [ Html.text title ]

        body : Html Msg
        body =
            ... 50 lines which use `model`
    in
    Html.main_
        []
        [ viewTitle (Route.toTitle model.route)
        , body
        ]
```

Or:


```elm
view : Model -> Html Msg
view model
    Html.main_
        []
        [ viewTitle (Route.toTitle model.route)
        , viewBody model
        ]

viewTitle : String -> Html Msg
viewTitle title =
    Html.h1 [] [ Html.text title ]

viewBody : Model -> Html Msg
viewBody model =
    ... 50 lines
```

I can imagine someone factoring out the `body` definition into a separate top-level-definition for reasons of code-indentation. But for actual structure there is clearly no benefit, and actually I would argue that the nested definition is slightly better because of the extra information that is conveyed about `body`, that is, that it is not used outwith the `view` function.

From this, I think it's relatively clear that what we want to avoid in "long functions" is the **body** of the function, the `let-in` is a way of factoring definitions out of the body of the function, whilst keeping those definitions both geographically close and lexically contained within the larger function.

It's worth noting other opinions are available here. I have a disagreement with [Robin Heggelund Hanson]( https://github.com/robinheghan) (creator of the [gren programming language, close sibling of Elm](https://gren-lang.org/)) over whether definitions within a `let-in` scope should have type signatures. I say they should, and he disagrees, most of the disagreement though, I believe, stems from the fact that he believes that whenever a definition becomes large enough to warrant a type signature it should be factored out. I don't see his logic there, I don't see the benefit of this, I think all you achieve is moving a definition further away from its single use site, though it may have the benefit of moving other definitions closer to their use sites. (I also think there are [other good reasons](/posts/let-signatures/) to have signatures on let definitions).

## Definition-body distance

Keeping definitions within the `let-in` part of a parent function's definition does increase the distance from the top-level function's definition to the actual body:

```elm
view: Model -> Html Msg
view model = 
    let
        ... Some 2000 lines of view code
    in
    Html.main_
        []
        [ title
        , body
        ]
```
So here, it's a long way between the `view: Model -> Html Msg` and the `Html.main_`. That may be a good reason for factoring out some of the `let` definitions. In particular, this one likely has a case on the route contained within the `model` and displays potentially entirely different things based on the route. Here it may be worth keeping within the `view` only those parts that are **common** between the different views. So for example you may have a nav bar that is shown on all pages. Factoring out the parts which are **different** on different routes is good organisation. It helps the reader understand the common parts.

Note that what is discussed here is what would help a reader of the code. The organisation is dependent on the problem, here I've suggested that a good way to decide what goes in the `let-in` and what is factored out is based on what is common between the different routes within the application and *not* on length of code, or any attempt to dogmatically stick to short functions or, for that matter, to dogmatically keep anything that **can** be kept within the `let-in` (because it is only used locally). Of course for a different function, you would likely have different criteria for what stays within the `let-in`. You have to think of the problem at hand, rather than stick to a syntax rule, sorry I know the syntax rule is easier to follow, but that's your job as a programmer.

A few side points worth mentioning here, but not related to the main point:
1. You might think of factoring out the nav bar as a separate 'component' or module. That's fine, because its render likely doesn't depend on much else. However, note that you are unlikely to render more than one instance of the same navigation bar, so factoring it out is not necessary. You're also unlikely to re-use that code in a separate project, so again factoring out as a separate module is unnecessary.
2. Haskell's `where` syntax, would help keep the `Html.main_` and `view: Model -> Html Msg` close together. I **think** I still prefer that Elm has exactly one way to introduce intermediate definitions, but still this is worth considering.
3. SML has `local-in-end` which would **both** solve the problem of `Html.main_` to `view: Model -> Html Msg` distance **and** provide extra indentation levels for the sub-definitions. In **addition** you retain the signal that those sub-definitions are only used within the `view`.


## Update functions

In Elm you have an `update` function which takes a current `Model` and `Msg` and returns an updated `Model` as well as a `Cmd Msg`. The `Msg` type can get large, with many variants. Which ultimately means, the `update` function will be long, even if you [split up your `Msg` type](/posts/splitting-up-update/). Because programmers have been trained to have an aversion to long functions, you see a lot of factoring out each case into its own function, like this:

```elm
update : Model -> Msg -> ( Model, Cmd Msg)
update model message =
    case message of
        LoginEmailInput input ->
            updateLoginEmailInput model input
        LoginEmailPassword input ->
            updateLoginPasswordInput model input
        LoginSubmitForm ->
            submitLoginForm model
        ...

updateLoginEmailInput : Model -> String -> ( Model, Cmd Msg)
updateLoginEmailInput model input =
    ( { model | loginEmail = input }
    , Cmd.none
    )
updateLoginPasswordInput : Model -> String -> (Model, Cmd Msg)
updateLoginPasswordInput model input =
    ...
```

And so on. It's worth considering what exactly has been achieved by this. As far as I can tell, pretty close to nothing. For complicated cases, it's quite nice that you have 3 more indentation levels to work with. However a reader of this code, who wants to know what happens when a `LoginEmailInput` message fires, must now first search the file for `LoginEmailInput`, and when that is found, they have to (likely using their IDE goto-definition command) move themselves from that case to the defined function.

Worse still, I may have a function that is actually used within several cases, the fact that I have defined that as a top-level definition (or even between a `let-in` pair at the top of `update`) is a strong signal to the reader that this is used in more than one case. However, that signal is lost if you have used the above pattern of factoring out all of your cases, and hence have many top-level functions most of which are used exactly once.

## Content functions

In many web frameworks templates are used, Elm is different, functions are used to render HTML. This means in *content heavy* / *logic light* parts of your code, you may end up with long functions which are mostly content with little logic. Consider an 'About' page in your app. Most of this is going to be static content, there isn't going to be much logic. Because of this, you may end up with quite large functions, but there isn't much that can be **usefully** factored out. Yes sure, you can break up the large amount of content into separate parts and move those separate parts around in your code, but to what end? Would this help the comprehension of your code? Likely not. You can already give names to your sub-sections if you like:

```elm
aboutPage : Html msg
aboutPage =
    let
        missionSection : Html msg
        missionSection =
            Html.section
                []
                [ Html.h2 [] [ Html.text "Mission" ]
                ...
                ]
        ...

    in
    Html.div
        []
        [ missionSection
        , teamSection
        , philanthropySection
        , legalSection
        ]
```

You may even make a function for say a `titledSection : String -> List (Html msg) -> Html msg`. But the point is, there is no logic going on here, the page renders the same always. So moving out these sections to be top-level declarations in order to keep the main `aboutPage` function under some length limit simply won't have any particular benefits.

## The crux of my point

What are we actually trying to achieve when attempting to keep functions short. I think we're ultimately hoping that we encourage each problem to be broken down into smaller sub-problems that can each be understood independently. I think that is an excellent goal. **However, given functional syntax with nested definitions, the focus on function length is misleading**, a large function may still be broken down into many distinct steps very nicely and moving those sub-steps out of the `let-in` of a function and to the top-level will not help with comprehension.

However, it's just as dogmatic and potentially harmful to have the golden rule be the opposite, that a sub-step should be located as locally as possible. What we ultimately want is to factor out sub-steps in order to help the comprehension of the code. Unfortunately there is no solid syntactic rule to follow. If there were, we would write tooling, for example an elm-review rule, to detect and fix cases where we had deviated from the simple syntactic rule. In the age of LLM code assistance we might be glad there is no simple syntactic rule, otherwise we could easily be replaced by an algorithm. I think the `view` and navigation bar example above is a useful one. No syntactic rule would tell you whether or not to factor out the navigation bar, but it's probably useful to do so, simply because the rendering of the navigation bar is so independent of the rest of the `view` function. Similarly keeping all the 'shell' parts close by, and moving the main body which switches on the current route of the application is also probably correct, because the view function can usefully be seen as "do all the common parts, and then do the route dependent parts". But structuring your code will be a judgement call, start training your judgement by doing that rather than relying on some syntactic rule that restricts your functions to X number of lines.

