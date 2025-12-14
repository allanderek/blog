---
title: "Link: Useful patterns for building HTML tools"
tags: [ programming, LLMs, link ]
date: 2025-12-11T11:14:31+00:00
---

[Self-recommending absolutely bangning post](https://simonwillison.net/2025/Dec/10/html-tools/) from Simon Willison regarding combining HTML, Javascript, and CSS into a single file, which can then be served on static hosting.

The post itself is obviously worth reading, but additionally you can browse his extensive collection of HTML tools:

> You can explore my collection on [tools.simonwillison.net](https://tools.simonwillison.net/)—the by month view is useful for browsing the entire collection.

Some excellent tips including a collection of API resources that provide open CORS headers (which means you will be able to call the API from your HTML file hosted on a different domain name to the API).

> Here are some I like:
> * iNaturalist for fetching sightings of animals, including URLs to photos
> * PyPI for fetching details of Python packages
> * GitHub because anything in a public repository in GitHub has a CORS-enabled anonymous API for fetching that content from the raw.githubusercontent.com domain, which is behind a caching CDN so you don’t need to worry too much about rate limits or feel guilty about adding load to their infrastructure.
> * Bluesky for all sorts of operations
> * Mastodon has generous CORS policies too, as used by applications like phanpy.social







