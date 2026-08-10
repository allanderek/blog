---
title: "Link: Danluu.pl: Programming language and token efficiency"
tags: [programming, link, llm]
date: 2026-08-10T14:00:59+00:00
---

In a somewhat non-specific titled blog post: [What's the best programming language for coding agents?](https://danluu.com/pl-tokens/), Dan Luu takes the time to actually investigate the question of which programming languages are more efficient in their token usage. Well technically the token usage of LLM models when writing in those programming languages.

Primarily he's interested in the claims that dynamic programming languages are more token efficient because the model needn't write any type annotations.
He is skeptical and I think the skepticism is warranted:
1. That is basically a claim that it's more token efficient to simply write less code, so it's simply a claim that concise languages are more token efficient than verbose ones **and** that dynamically typed languages are more concise than statically typed ones.
2. Many statically typed languages have type inference so if there were some gain to omitting the type annotations that could still be done.
3. If this were true, wouldn't it be better to have the model output condensed minified code and if you ever need a human to read it they can simply put it through a formatter first? Or have the model output the minified code and then immediately run it through a formatter, and whenever it reads code run it through a minifier first? I realise that minifying usually obscures names but you could turn that off.
4. The reasoning tokens also count for something so if the model has to reason more in language A than language B that might offset any tokens saved by language A being more concise.
5. I would think this is mostly a question of how many iterations on the code the model needs. Language A might be more concise but if code is more likely correct in language B then the model might need fewer iterations and that seems likely to swamp the fact that language A is more concise.

Note, as far as tokens are concerned it doesn't matter whether code is iterated upon because the code failed to compile, or because the tests failed. I mean it *might* do, it depends if reading the test failures is worse than reading the compiler errors. It's easy enough to imagine fewer iterations in either the direction of statically or dynamically typed languages
* The static type checking may force a couple of iterations to satisfy the type checker that aren't actually needed.
* Then again a type error can prevent a whole class of runtime errors.

Anyway the blog post does not settle this question, but it is well worth reading to make it clear that this question is indeed unsettled.

Here are some tenative conclusions that he draws from his experiments:
> Languages with a lot of bad code out there (e.g., PHP) will perform worse
>   * Appears to be false on these tasks

> Because it's so easy to re-write now, you should use a powerful language (like Haskell)
>   * Appears to be false on these tasks

> You should use a popular language
>   * There's weak support for this statement

Like a good scientist he also pre-registered some hypotheses and evaluates them as:

> High confidence (95%): the overall dynamic vs. static language claim won't hold
> * This seems correct

> Low confidence (60%): static languages will be somewhat better than dynamic at ultra effort
> * There's not enough information to determine this conclusively, but if we had to make a binary correct/incorrect call, I would call this incorrect

> High confidence (98%): the "weird" language supremacy of something like J won't hold
> * This seems correct

> [from a draft reader]: "dynamic is better on small-scale, but gets overtaken by static as the size of the project grows"
> * Not supported by these tasks (static languages didn't seem to do substantially better than dynamic on the much larger Pandoc task vs. the smaller Zstd task), but the tasks and the presentation of the tasks are so different that it's unclear if this is because task-size scaling or because of other differences


But I found the following observation interesting:
> By the way, a major reason Clojure improves by so much in the Pandoc eval compared to the Zstd eval is that, in the Zstd eval, 36/40 medium and 5/40 ultra Clojure programs had test failures because byte conversion throws on 128–255 (maybe unchecked-byte should've been used?) and they used this conversion inappropriately.

This suggests that the choice of language is highly problem dependent and not only that but problem dependent in a way that is not easy to predict.
This potentially suggests the correct thing to do for some problems is to have multiple goes at it with different stacks.


