---
title: "Legal standing analogy"
tags: [programming]
date: 2025-09-23T13:34:58+00:00
---

[Dillon Kearns](https://dillonkearns.github.io/) of [elm-pages](https://elm-pages.com/) and [elm-radio](https://elm-radio.com/) fame has a really good analogy for feature requests, whether they be feature requests for an end-user application or API changes to a software library, or even say changes to a programming language.

His analogy is legal standing. Legal standing, in the US, is the requirement that a person bringing a case to court must have a sufficient connection to the issue. This usually means that the plaintiff must show:
1. Injury - They have suffered, are suffering, or are about to suffer a real harm
2. Causation - the harm in question is caused by the law or the defendent
3. Redressability - If the court gives a verdict in the plaintiff's favour this will likely remedy the harm caused.

So for example, eventual Supreme Court Justice Ruth Bader Ginsburg, before joining the supreme court wished to challenge the law so as to make it unconstitutional to discriminate on the basic of sex. To do so, she could not just show up at the supreme court and argue (however articulately) that discrimination on the basis of sex was morally wrong. Instead, she had to look for plaintiffs who could show direct injury from laws that treated men and woman differently. She typically did this using *male* plaintiffs which might have helped with the all-male (at the time) supreme court, for example [Weinberger v. Wiesenfeld (1975)](https://en.wikipedia.org/wiki/Weinberger_v._Wiesenfeld), Ginsburg represented Stephen Wiesenfeld, a widower denied Social Security survivor benefits available to widows but not widowers. Wiesenfeld clearly had standing: he personally lost benefits because of sex-based discrimination, and a court ruling could restore them.

What does all this have to do with software? Dillon Kearns makes the analogy with a feature request. One should not simply decide that a feature might be a nice idea, instead you should have 'standing'. Meaning that you can show that someone has been 'harmed' by the lack of this feature, and that the proposed feature would indeed remedy the harm caused. For example, if you are the maintainer of an open source library, with a given API, when someone suggests a change to the API, you can ask them to show specific code that is awkward (or impossible) to write with the current API, and how that code would be improved with the new suggested API. This of course wouldn't settle the case for whether or not the proposed change should be accepted, it may be that that particular code is improved, but the costs of the change are too large. However, having such 'feature standing' acts as a good triage on feature proposals. 

Note that it's important the code is *real* code and not some hypothetical example. A hypothetical example might be useful to describe the change you wish to make, but isn't sufficient for having 'software standing'.

In addition, before proposing a new feature (or a change to an existing one), consider whether you can find 'standing'. Can you find examples of *real* code that would be improved by the proposal you are suggesting. If the suggestion is not strictly an addition, then you might also use the opportunity to consider whether you can find real code that would be harmed by your suggestion.

Overall, I think this is a cracking analogy.
