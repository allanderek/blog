---
title: "Link: Elm Queue Shootout"
tags: [ programming, types, elm ]
date: 2025-10-05T14:11:30+00:00
---

Martin Janickek [has a great post "Elm Queues Shootout"](https://martin.janiczek.cz/2025/10/01/elm-queues-shootout.html) which is well worth reading.
He uses property based testing to test several Elm queue libraries. He then benchmarks those libraries as well, though he is cautious to note that for the most part queuing libraries are fast enough and you don't really need to worry about performance unless you have queues of many items in a hot loop somewhere:

> I need to preface this with: this is all on a nanosecond scale. Don’t be wooed by the absolute differences here - does your webapp really care about 0.2ns vs 3ns? Which operations will it do often? The O(1) vs O(N) time complexities will probably be more instructive, though again you have to think about the realistic sizes of your queues. Are they going to hold more than a few hundred items?

He does find one bug in one library for which he has [opened a github issue](https://github.com/owanturist/elm-queue/issues/5). However for the most part queues are relatively straightforward to implement, so it's not surprising that the libraries all mostly pass the property based testing.

The benchmarks mostly show the trade-offs. A particular one is `length`. Either you count the items as they are being added/removed, or you just store the queue and only count the items when necessary. Which style you use, depends on which operations your use-case calls for.

Anyway the main point I wish to make here is that this is the kind of deep dive that we all know that we really should perform for every single one of our dependencies. But we don't, because it's (too) time-consuming. However there are two points that could alleviate this:
1. Janiczek has done this for queuing libraries once and basically this information is available to all. So it's possible that many such reviews could be shared, thus reducing the work for everyone.
2. This does seem like the kind of task that LLM coding agents have recently been just about able to do.

What would be nice about the second part is that it then becomes easier to keep the review up to date, since you simply ask the coding agent to reperform the tests/reviews.

Here is the actionable part of the summary:
> If you need a deque, choose between folkertdev/elm-deque and robinheghan/elm-deque based on the needed API or whether you’ll use fromList or toList more often.

> If you just need a queue, I recommend turboMaCk/queue solely based on having slightly richer API to avh4/elm-fifo.

But it is worth [reading the whole thing](https://martin.janiczek.cz/2025/10/01/elm-queues-shootout.html).
