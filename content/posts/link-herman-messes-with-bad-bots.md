---
title: "Link: Herman messes with bad bots"
tags: [programming, link]
date: 2025-11-14T11:10:33+00:00
---

Lovely [blog post](https://herman.bearblog.dev/messing-with-bots/) from Herman who operates the [bear blog blogging service](https://bearblog.dev/).
He details a little project of his to mess with the badly behaving bots, but I think it also works well as a read of simply spending some time going down a rabbit hole, mostly enjoying oneself, and also reflecting a little.

He is concerned mostly with the real bad-folk of the Internet, the ones that are looking for exploits:
> Now, the AI scrapers are actually not the worst of the bots. The real enemy, at least to me, are the bots that scrape with malicious intent. I get hundreds of thousands of requests for things like .env, .aws, and all the different .php paths that could potentially signal a misconfigured Wordpress instance.

He sets up a markov chain generator to serve up nonsense to these bots, but he discovers that he is wasting his own resources:
> Unfortunately, an arms race of this kind is a battle of efficiency. If someone can scrape more efficiently than I can serve, then I lose.

Which leads him to consider the most efficient way to serve up non-helpful data:
> So down another rabbit hole I went, writing an efficient garbage server. I started by loading the full text of the classic Frankenstein novel into an array in RAM where each paragraph is a node. Then on each request it selects a random index and the subsequent 4 paragraphs to display.

It's worth [reading the whole thing](https://herman.bearblog.dev/messing-with-bots/), but note his word of caution:
> If you or your website depend on being indexed by Google, this may not be viable. It pains me to say it, but the gatekeepers of the internet are real, and you have to stay on their good side, or else. This doesn't just affect your search ratings, but could potentially add a warning to your site in Chrome, with the only recourse being a manual appeal.

We have all heard the horror stories of manual appeals to the gatekeepers of the internet.


