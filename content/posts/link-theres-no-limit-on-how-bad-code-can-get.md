---
title: "Link: There's no limit to how bad code can get"
tags: [ programming ]
date: 2026-09-07T14:44:22+00:00
---

Zach Kehs has written an interesting [post titled: There's no limit to how bad code can get](https://zachkehs.com/blog/theres_no_limit_to_how_bad_code_can_get/).

> The re-architectures were always a failure: The system required years of study to properly understand and was constantly changing. It's not politically viable to take so long to design a fix for the system, so naturally everyone attempting to fix things must work with incomplete information. Some of this impatience is from within: If you are trying to design a grand fix for such a prominently painful architecture, you are doing it in part because you want a promotion (and you don't want to wait too long for a promotion).


I think the key part is that the system is constantly changing. So the re-architecture is of a moving target. If it wasn't, it probably wouldn't be worth re-architecting, since if there are no major changes for what do you need the better architecture?

I do wonder though, how much of this changes in the days of LLM coding assistants. We have seen a few high profile projects port their codebase to a new language. Possibly most famously [Bun was ported from Zig to Rust](https://bun.com/blog/bun-in-rust). Another interesting example is the [Ladybird project porting parts from C++ to Rust](https://ladybird.org/posts/adopting-rust/). Both used AI to assist though the Ladybird project is doing things more gradually. Still, the speed with which AI coding agents can do this kind of work does make even re-architectures more plausible. In particular, previously, you had to port/rearchitect whilst the old system was still in development, because the time it would take to port/rearchitect was longer than the organisation could handle a freeze on fixes and features. But now, the time taken for ports/rearchitects can more likely fall within an acceptable window for the organisation to accept a freeze on fixes and features.

Some good comments on [lobste.rs](https://lobste.rs/s/rfn2mn/there_s_no_limit_how_bad_code_can_get), including from [Simon Willison](https://simonwillison.net/2026/Sep/6/theres-no-limit-to-how-bad-code-can-get/).
