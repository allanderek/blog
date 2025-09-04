---
title: "Link: Where's all the shovelware?"
tags: [ programming, A.I., llms]
date: 2025-09-04T10:34:21+00:00
---

A couple of weeks back after the GPT-5 release, I [wrote a skeptical post](/posts/gpt-5-model-picker) that the
fact that the GPT-5 model picker release was botched was something of a bearish sign for llm-assisted programming:

> Okay, but if OpenAI cannot utilise their own models in coding/dev-ops to avoid a high-profile failure on a very high importance launch, what chance do other companies have? Why hasn’t the A.I. enabled OpenAI to improve their development/deployment strategies to avoid such techincal glitches?


Now [Mike Judge](https://substack.com/@mikelovesrobots) has basically applied that logic more widely in a
[post: Where's the Shovelware? Why AI Coding Claims Don't Add Up](https://mikelovesrobots.substack.com/p/wheres-the-shovelware-why-ai-coding), in which he argues
that if LLMs were really 10xing developers' productivity then we'd see a lot more software being released.

But before he gets to that he describes a little self-experimentation which I think was a pretty good experimental design:

> I’d take a task and I’d estimate how long it would take to code if I were doing it by hand, and then I’d flip a coin, heads I’d use AI, and tails I’d just do it myself. Then I’d record when I started and when I ended. That would give me the delta, and I could use the delta to build AI vs no AI charts, and I’d see some trends. I ran that for six weeks, recording all that data, and do you know what I discovered?

The key point is that he is doing the estimate *before* flipping the coin, so there is less chance for any bias to creep in. Still not **no** chance, the task might be one that he already predicts would be be particularly amenable (or non-amenable) to A.I. speed-up and may adjust his human estimate accordingly, not to mention of course that he might just be trying very hard without the A.I. and deliberately stalling when using the A.I. coding assistant. Still, kudos for just actually doing the experiment, how many commentators on llm-assisted programming have done that?

You can see the resulting chart at the link. Now n is only 31 here, but I think his conclusion holds up pretty well.

> That lack of differentiation between the groups is really interesting though. Yes, it’s a limited sample and could be chance, but also so far AI appears to slow me down by a median of 21%, exactly in line with the METR study. I can say definitively that I’m not seeing any massive increase in speed (i.e., 2x) using AI coding tools. If I were, the results would be statistically significant and the study would be over.

The rest of the post is well worth reading, there are some nice graphs which show a general lack in software production explosion.
It's very interesting that the new github public repositories is basically a horizontal line, I would have thought that at the very least
llm-assisted programming was helping a lot of programmers knock-out (or at least start) their hobby itch-scratching projects. In particular
to **start** such projects, llms do seem really good at providing a skeleton app from which to get started, so I'm shocked we're not seeing more of these.


