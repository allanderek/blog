---
title: "Link: Elmi bytes decoders for elmi/elmo files"
tags: [programming, elm, compilation]
date: 2025-11-12T10:37:42+00:00
---

[Previously](/posts/elm-compilation-elmi-files/) I reported on long Elm compilation times and that being related to large `.elmi` files.
In an [Elm discourse thread](https://discourse.elm-lang.org/t/list-of-all-elm-kernerl-functions/10483/5) Warry links to their [new package elm-stuff](https://package.elm-lang.org/packages/Warry/elm-stuff/latest/) for decoding `.elmi` and `.elmo` files. So if you are having Elm compilation time woes, you could potentially use this, to inspect the large `.elmi` files and see exactly what may be causing them to be so large. This may guide you to the best large record files to make opaque to reduce your application's compilation time.
