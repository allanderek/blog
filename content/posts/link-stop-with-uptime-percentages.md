---
title: "Link: Can we stop with the uptime percentages?"
tags: [ programming ]
date: 2026-09-04T14:40:11+00:00
---

Jim Nielsen has [written regarding uptime percentages](https://blog.jim-nielsen.com/2026/stop-with-the-uptime-percentage/).
He makes a compelling point that reporting uptime percentages isn't a very useful measure for a human to ingest.
He suggests a much better one:

> So how about, and I’ll just throw this out there, instead of:
>
> "GitHub Actions: 98.31% uptime."
>
> We say something like:
>
> "GitHub Actions: 12 hours affected in the last 30 days (98.31% uptime)."
>
> One requires you to understand the nonlinear significance of numbers near 100%. The other requires knowing what an hour is.

I can see that sometimes the percentage is useful. For example, if it's a service that your own services depends upon, you care about what percentage of your requests are met, and that is somewhat correlated with the uptime percentage. But if it's a service I actually use, then I care more about human time that it might not be available for. For example, the electricity grid. I'm not sure I really care whether in the next year I can expect the electricity supply to my house to be 99.999% or just 99.99%, or even 99.9%. But I am interested in whether I'll lose 5 minutes, 50 minutes, or 8 hours of electricity in the next year. All of which seem surivable, but if it happened all in one go, and not during the night, then one is a walk around the block, one is an hour of reading a book, and the other is cycle ride and maybe a barbecue.
