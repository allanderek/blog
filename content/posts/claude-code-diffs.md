---
title: "String Claude code diff observation"
tags: [programming]
date: 2025-10-30T10:39:39+00:00
---

Using Claude code I noticed something a little strange, which I at first thought might give some insight into how LLMs are manipulating code, but turns out is probably nothing to do with that an merely how it displays those changes to the user.

Here is a diff proposed by Claude, the task involves removing a link from the navbar of application.

```diff
● Update(src/View.elm)
  ⎿  Updated src/View.elm with 6 removals
       58                                |> ifLoggedIn
       59                            , Html.li []
       60                                [ Html.a
       61 -                                  [ Route.href Route.ImportOpml ]
       62 -                                  [ Html.text "Import OPML" ]
       63 -                              ]
       64 -                              |> ifLoggedIn
       65 -                          , Html.li []
       66 -                              [ Html.a
       61                                    [ Route.href Route.OrganiseFeeds ]
       62                                    [ Html.text "Organise Feeds" ]
       63                                ]
```

The logical thing a human would do would be:


```diff
● Update(src/View.elm)
  ⎿  Updated src/View.elm with 6 removals
       58                                |> ifLoggedIn
       59 -                          , Html.li []
       60 -                              [ Html.a
       61 -                                  [ Route.href Route.ImportOpml ]
       62 -                                  [ Html.text "Import OPML" ]
       63 -                              ]
       64 -                              |> ifLoggedIn
       65                            , Html.li []
       66                                [ Html.a
       61                                    [ Route.href Route.OrganiseFeeds ]
       62                                    [ Html.text "Organise Feeds" ]
       63                                ]
```

Obviously, this makes no difference to the end result, because lines 59 and 60 are identical to lines 65 and 66.

I thought this might be something a bit insightful about how Claude "thinks" about code, but it turns out probably not.
The `diff` algorithm produces the same diff, and I asked Claude itself about how it prepares the diffs for presentation to the user.
Claude claimed not to have definitive knowledge about its own internal implementation but speculated that it did indeed do:

1. Uses string-based editing operations (similar to search-and-replace)
2. Applies those edits to produce the new file
3. Runs a diff algorithm to generate the display you see

So the fact that it displays the non-human version of the diff is not related to how Claude is producing the code changes, it is (likely) only an artefact
of the way Claude uses `diff` to display the proposed changes to the user. 
