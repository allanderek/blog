---
title: "Ladybird overtakes Servo: Why?"
tags: [ programming, types ]
date: 2025-09-10T13:24:27+00:00
---

The success of [Ladybird](https://ladybird.org/) (C++) overtaking [Servo](https://servo.org/) (Rust) challenges some assumptions I have about the programming language productivity, particularly with respect to strong, static typing, and the lack of a satisfying explanation allows me to update my priors a little.

This post was triggered by watching the [latest update video from the Ladybird team](https://youtu.be/wXAAXRsPDXw?si=1NO_0LO08IOdpFdV),
in this we learn that according to the [web-platform-tests](https://staging.wpt.fyi/results/?product=servo&product=ladybird) Ladybird has now overtaken
the Servo project in terms of tests passing. According to [this HackerNews comment](https://news.ycombinator.com/item?id=41217007) in August of 2024 the Servo project was quite far ahead. 

I think this requires some explanation. If I were to start writing a web browser rendering engine today, and my only two choices
were C++ and Rust, I would definitely choose Rust. 

## Priors

It's worth stating my priors, things I think are at least directionally correct concerning programming languages and productivity.

I would think that for most tasks a garbage collected language is more productive than a manual memory management language.
There are obviously some tasks, such as writing the garbage collector itself, that require manual memory management. Even outside of those
tasks for which a garbage collector is simply not possible, there remain a few tasks or environments in which memory leaks and/or performance predictability
are so important that it's probably more productive to manage memory manually rather than debug and fix leaks/issues as they arise.
Nevertheless, I would think that garbage collection is a major boon to productivity for a fairly large majority of tasks.

Similarly I would think for most tasks a strongly statically typed language is more productive than a language that is either weakly or dynamically typed, or both.
Again, there are certainly some cases where I can see that a dynamically typed language may be more appropriate, mostly those in which there is a large degree of
meta programming necessary. For example, a tool that takes in an SQL schema and gives you back a generic admin interface. However, for most tasks, I just find it
hard to believe that the extra guarantees granted by the compiler for a strongly statically typed language are not productivity enhancing.

But note, I know of precious little concrete evidence for either of these two beliefs.

There is a third option between garbage collected language and manual memory management C-style (MMM), and that is Rust-style checked manual memory management (CMMM). Personally I would still believe that a CMMM language is more productive than a MMM language for most tasks. But I'm less confident of that, mostly because I have not spent much time using a CMMM language. Intuitively, I would think that you do spend quite a bit of time satisfying the borrow-checker, but also you don't spend time debugging memory errors, but it's hard to say which would dominate, and again I could imagine that some tasks are better suited to one or the other. It's also possible that you can produce code more quickly with using MMM, but it's more buggy.

The general theme here is that I believe the more **guarantees** a language can give the programmer, the better. These particular guarantees seem to me to hit a sweet-spot where the restrictions that the language must impose to afford those guarantees are worth the benefit.

## Possible explanations


Back to Ladybird which seems to be making quite the progress on what is a pretty audacious project, a modern web browser, written in C++.
Servo, is a web browser rendering engine, written in Rust (so the Servo project is actually smaller in scope).
At some point Servo was ahead of Ladybird in web standard tests, but Ladybird has overtaken it. That removes the possibility that the story is simply that Ladybird
started earlier. It also suggests that Ladybird is making better **progress**, so the question is why?

Given my priors I would expect a Rust project to have more chance of success than a C++ project, all else being equal.
The **two** reasons being that Rust's stronger type system and Rust's memory management scheme should both enhance productivity.

Given that that appears not to be the case it's at least bearish for those two priors. In this section I will explain some possible reasons that a C++ project
appears to be more productive than a Rust project other than the possibility that neither strong types nor checked memory manipulation help significantly.

1. Arnold Kling (lead developer of Ladybird, or someone else on the team) is a rock star programmer.
   * This is one of those explanations that somewhat moves the question back a bit. If Arnold Kling is a rock star programmer, why does he not recognise the productivity enhancing nature of Rust (or some other strongly statically typed language) and use that? If it is some other programmer on the team, why did that person join a team using C++?
2. There are more contributors to Ladybird.
    * Similarly, why? It's possible to do some mental gymnastics and suppose that the kind of programmer who gets involved in an audacious project to write a new web browser rendering engine is the kind of programmer that likes to get near the metal or something. I could possibly be convinced by some such explanation but I certainly haven't managed to convince myself.
3. Ladybird has more focus on web standards tests.
    * I guess this is plausible, but I would say it still rules out any *massive* productivity gains from using Rust over C++.
4. Luck in some form. It's not clear what, perhaps the Ladybird developers chose some better architecture, but the reason they chose it was simply luck. Here 'better' is in the sense of more adapatable/maintainble or in someway productivity enhancing.
    * Very plausible, but again kind of rules out any massive productivity gains.
5. Perhaps Ladybird has some kind of better architecture, that wasn't luck, it was just better design work/foresight by the team.
    * Basically the same answer as 1, if the person/team making the architectural decisions is so much better at it, why do they not see the benefit of guarantees.
6. C++ lends itself well in someway to a better architecture than does Rust.
    * That's quite close to just saying that C++ is more productive. It would at least be saying that by default C++ is more productive and to make Rust more productive you have to think hard about your architecture etc. It sort of says something like "Used well Rust can be more productive than C++, but used poorly it might not be", which is at best highly qualifying the premise that Rust is more productive.
7. A web-browser rendering engine, is one of those tasks (possibly rare, possibly common) where actually a non-checked manual memory management scheme is simply better suited than Rust's checked memory management.
    * But a rendering engine is such a large and quite general project that if this is the case then it suggests such projects are not rare.
8. Neither code base has really seen much actual use from end users - it's possible that the Ladybird code has been produced quicker, but is less secure / more buggy, and that the productivity enhancements from using Rust are still to come. To be clear I am **not** claiming that the Ladybird code is buggier, just that that is plausible explanation in a listing-out-all-possible-explanations kind of way.
    * Hard to judge this one.
9. Some other thing makes Rust less productive than C++, for example the Rust compiler is known for being slow, it is also known that slow compile times can hit programmer productivity as it can break flow. So it could be that whilst CMMM is an improvement on MMM, that effect is dominated by the effect of the longer compile-times.
    * Again hard to judge this one, but if true again rules out major productivity gains from Rust's extra guarantees.
10. I do not know the full history of the Servo project, but from what I understand it originally had full-time salaried developers funded by Mozilla, but Mozilla essentially abandoned the project and it became a Linux Foundation Project entirely run by volunteers. This would obviously cause quite a bit of disruption to the project.
    * Sure, but why did Mozilla see fit to abandon the project? The project had been progressing for 8 years (2012-2020), I think this would be long enough that any large productivity gains would be visible. The Gecko project first saw a release in 1998, so in 2020 it was only 22 years old, compared to 8 (though perhaps with many more developers working on Gecko). Mozilla had all the information to them and bet on Gecko rather than Servo, whilst Servo was clearly a much less mature project, it stills suggests that the Mozilla team were not seeing **massive** productivity gains from using Rust.


## Broader explanations

This post was motivated by the Ladybird vs Servo comparison. But it's not the first time that someone has commented on the apparent lack of success of languages with strong guarantees. It's relatively easy to find opinions about why strongly statically typed languages are not more successful. Often such opinion pieces are discussing success in the sense of adoption of such languages.


One such opinion piece is [Richard Feldman's "Why are functional programming languages not the norm?" talk](https://youtu.be/QyJZzq0v7Z4?si=0Chi5sH241Whs9QP). Which is highly recommended. Nonetheless I find many
such explanations only move the question back. In his talk, Richard discusses ways in which languages become popular. One such is 'killer app'. His example is Ruby,
which (arguably) became popular on the back of the success of Ruby on Rails. But this only moves the question back, why haven't we had a 'killer app' written in
O'Caml, Haskell, Elm, or even Rust?

I'm more interested in success with regards to the fruit of any productivity enhancements. Why do we not
see a lot more successful software that happens to be written in strongly statically typed languages?

## A speculative explanation

An explanation for the general slow adoption of languages with more restrictions and greater guarantees goes something like this:

1. Dynamic/weakly typed languages are indeed more productive in the small, and/or early stages of a project, in particular when a single developer can keep most of the project within their working memory.
2. The gains from static/strong typing come later, once the code base is larger and/or more complicated, and in particular is better for multiple developer teams, and/or developers joining an existing project.
3. But humans make decisions about languages based on how productive it **feels** and/or based on many small side/sample projects.
4. Because of this, many choose weakly/dynamically typed languages. So many projects get started in those languages.
5. Success has a large portion of luck attached to it.
6. Even if statically/strongly typed languages are in the long-run more productive, if many more projects are started in weakly/dynamically typed languages, just by luck some of them will be successful.
7. We do not start enough projects in strongly/statically typed languages to get to the point where the productivity gains are felt.


One problem with this explanation is that, well the Ladybird / Servo example seems to discount it. There is one of each. It could be that there were many C++ web-browser rendering engine projects started and Ladybird is just the most successful of those. Whereas there were far fewer such projects started in Rust, so the most successful one of those is the most successful from a far smaller pool. But that still doesn't really explain how Ladybird has managed to *overtake* Servo.


## Conclusion

All-in-all I still find it very hard to shake my belief that more restrictive languages that afford greater guarantees are simply more productive.
However, the evidence before us suggests that any such gains, must be pretty modest at best. It's just about possible, that starting many more projects
in less productive languages overcomes the productivity effect of the language itself, in terms of visible output. But first of all, that explanation is still firmly in speculation territory. More importantly, I think it's quite clear that we have to assume that there are no **massive** productivity boosts from choosing the correct language. In other words, at least for productivity, the choice of programming language, just doesn't matter that much.
