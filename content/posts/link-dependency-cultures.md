---
title: "Video Link: Dependency Cultures: Software Should Work"
tags: [ software development ]
date: 2026-07-31T11:00:43+00:00
---

[Video Link: Dependency Cultures: Software Should Work](https://www.youtube.com/watch?v=E82ly38YEEQ)

An interesting talk by Richard Feldman well-known to most Elm developers and now working on his own [Roc programming language](https://roc-lang.org/).

He starts with a very interesting observation, looking at the web pages for various programming languages and their dependencies. He makes the point that these websites are all doing a *very* similar job, although some have a built-in compiler/interpreter for the language so that visitors can try out the language directly on the website. This does change the website considerably from a simple static information page to an interactive app, or usually more a static information page that *contains* an interactive app.

It's worth watching the video but it's safe to say there is *considerable* difference in the number of dependencies these (similar) websites pull in. From a high of 1800, to essentially none.

I think there are two main takeaways from this talk:
1. There is a culture component to how dependencies are managed / used, with some languages having a culture of using many small dependencies and others having a culture of using fewer dependencies.
2. Recently, partly due to AI, there has been something of an increase in worry about the software supply chain, in particular compromised dependencies and now might be a good time to consider some of your dependencies and perhaps reconsider whether you really need them.

The second point can be extended to say, perhaps if you currently have a strategy of "depend on all the things" now is a good time to reconsider that.

Anyway, I was thinking about the way I've used Elm in the past. I've often used Elm for what is *mostly* a static website, but perhaps there is a form with some non-standard validation going on. In that case I've often just decided to do the whole page in Elm because it was less friction for me because I do Elm pages a lot. Of course what I really *should* do is create a static web page with a graceful degraded form (that works if Javascript is disabled) with an Elm component that takes over the form and renders it with the validation etc. etc. But typically I didn't do that because it was more work and I was lazy. With agent coding tools now I'm more likely to do the correct thing.

I suspect some of the language web pages in the sample from the video are doing a similar thing, in that they are doing the website the way the others "always do websites" even if that's not 100% appropriate for what is largely a static information-site. For a start they will feel that they need to 'dogfood' their own stack. So typescript and node will feel like they need to use typescript and node for their own website, even although neither is going to be necessary for a (mostly) static website. 
