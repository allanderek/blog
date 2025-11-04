---
title: "Elm compilation time with large records"
tags: [programming, elm, compilation]
date: 2025-11-04T14:28:00+00:00
---

This post details a problem with the Elm compiler that results in long compilation times or large memory usage (and possibly OOM issues) and a possible way to fix it, as in change your application so that your compilation times are shorter.


I have a large (~150k lines) Elm application and it can take over 2 minutes to compile.
One reason for this is the stored state that the Elm compiler stores in order to avoid some recompilation (or at least re-type-checking) code that hasn't changed.
It stores this information in `.elmi` and `.elmo` files. The `.elmo` files do not seem to grow overly large but the `.elmi` files can.

The Elm compiler is storing information about types in these `.elmi` files. You can see how large the largest `.elmi` (or `.elmo`) files in your project are by doing:

```bash
du -hs elm-stuff/0.19.1/* | sort -h | tail -n 50
```

Here is some sample output:

```bash
11M     elm-stuff/0.19.1/Admin-Entity-Empty.elmi
11M     elm-stuff/0.19.1/Admin-Types-MainMenu.elmi
22M     elm-stuff/0.19.1/Admin-Update-Common.elmi
24M     elm-stuff/0.19.1/Admin-Types-View.elmi
```

As you can see those are pretty large even taking into account that the project is quite large:

```bash
$ du -hs src/
7.8M    src/

$ du -hs elm-stuff/0.19.1/
285M    elm-stuff/0.19.1/
```

I'm not entirely sure if the problem is writing those large `.elmi` out (e.g. in string construction), or parsing them back in. Possibly both.


The reason these files get large is that type aliases are expanded in all places. So for example if you have:

```elm
type alias Point
    { x : Int
    , y : Int
    }

type alias Line
    { start : Point
    , end : Point
    }

myLine : Line
myLine =
    { start = { 0, 0 }
    , end = { 1, 1 }
    }
```

Then this effectively becomes:

```elm
type alias Point
    { x : Int
    , y : Int
    }

type alias Line
    { start :
        { x : Int
        , y : Int
        }
    , end :
        { x : Int
        , y : Int
        }
    }
myLine : 
    { start : { x : Int, y : Int }
    , end : { x : Int, y : Int }
    }
```

This might not seem like a lot, but if a large record type is repeated at various points this can add up quickly.

There is a solution of sorts. You can make large record types opaque, if the above had instead been written as:

```elm
type Point
    = Point 
        { x : Int
        , y : Int
        }

type alias Line
    { start : Point
    , end : Point
    }
myLine : Point
```

Then the custom type `Point` is **not** expanded in the `.elmi` file. Of course this means that you cannot write `myLine.start.x` and in general may be inconvenient.
However, the main takeaway here is, if you're struggling with a long Elm compilation time, the problem *might* be related to large record type aliases. The first thing to do is to use the `du` as above to find where those large `.elmi` files are, and then look in those modules to see if there are record aliases (or that file references large record aliases defined elsewhere) that could be turned into opaque types without it being too unergonomic, then it's a possible solution to your compilation time (or memory) woes.
