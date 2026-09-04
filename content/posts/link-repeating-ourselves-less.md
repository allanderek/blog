---
title: "Link: Repeating ourselves less with M4"
tags: [ programming, dsls ]
date: 2026-09-04T16:22:35+00:00
---

Nimin has a [post regarding the use of the M4 macro processor](https://nemin.hu/httpd-macros/index.html).
It reads nicely as it builds the reader from a straightforward `httpd.conf` file to one written using the M4 macro processor.

M4 is a posix utility [here is the man page](https://man.openbsd.org/m4). I think it's a reasonable choice for a macro processor, as Nimin states:

> It is generally found on all Linux distros and (more relevantly to this post) on all the BSDs, including OpenBSD.

Still, I'd likely not use it for this purpose. I've [written before regarding dsls](/posts/dsls/), and I think this is pretty decent example of one such problem.
One problem is that I'm not familiar with **either** m4 syntax **or** `httpd.conf` syntax. So when I read the resulting file at the end I struggle to extract `m4` syntax from `httpd.conf` syntax.

I think this highlights a difficulty with configuration languages, which is a bit of a subset of dsls. The problem is that you want a single-source of truth for *parts* of your configuration. In Nimin's case the main problem was the setting of the same set of headers for two different servers. Whenever you are repeating yourself, or whenever you are defining something in more than one place, you're basically in the territory of a general purpose programming language. Either the dsl grows to the needs of that, or you end up *generating* the dsl from a general purpose language. That's not to say that the dsl is necessarily worthless, and configuration is an interesting case because it's often not clear what general purpose language you would use for this.

Some programs use the implementing language as the configuration language, this is common in the Python world and it generally suits dynamic languages quite well, but it's not out of the question for a statically typed language. A great example is [xmonad](https://xmonad.org/) a dynamically tiling X11 window manager that is written **and configured** in Haskell.

Many programs use JSON as a configuration language. The only problem is that it doesn't allow factoring out of duplication, or defining constants to be re-used, or even (easily) comments. So [jsonnet](https://jsonnet.org/) is an extension of JSON which basically adds general purpose programming features to it, including functions.

Another possibility is to use a templating language such as [jinja](https://palletsprojects.com/projects/jinja/), or [go templates](https://pkg.go.dev/text/template), which are often used for generating HTML, but can be used for any text-based output. I have used them for generating modelling language files (which are essentially dsls). I found this to work pretty well, and is basically very similar to the `m4` approach described in the [linked post](https://nemin.hu/httpd-macros/index.html).

There is no real conclusion here, none of these approaches are *obviously* better than the others. But if you have complicated configuration files, and in particular if you find yourself duplicating parts of the configuration, consider trying at least one of them.
