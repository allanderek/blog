---
title: "A.I. Water usage - Empire of A.I."
tags: [ A.I., llms]
date: 2025-11-03T10:42:35+00:00
---

**Update: 2025-11-24** [ Andy Masley has a much more in-depth look](https://andymasley.substack.com/p/empire-of-ai-is-wildly-misleading) at this is issue, including a response from the author, and his response to that response is well worth reading.

I've been following some of the debate on the water usage of LLMs. A lot of people seem concerned that this is a large issue. I'm not sure either way, but I'm coming round to the view that water usage is not a major concern, in comparison to, for example, the energy usage.

On the recommendation of a friend I'm reading "Empire of A.I." by Karen Hao, in the chapter 'Plundered Earth' the author touches on the water issue. I *think* she makes a pretty big error that should have been caught by an editor, but also investigating this error has caused me to update a **little** in favour of the water issue actually being an issue, even if just a small consideration as opposed to being a complete non-issue. So first of all I'll give a couple of links to roughly explain where I think we are in the llm-water-usage issue.

## Rough state of play

First off, [Simon Willison](https://simonwillison.net/) is a highly respected blogger, known for his work with the Python programming language but more recently for his work interogating and using large language models. Simon seems quite convinced that the water usage is not a real issue, [here on October 18th 2025](https://simonwillison.net/2025/Oct/18/) he links to [Andy Masley's post concerning water usage](https://andymasley.substack.com/p/the-ai-water-issue-is-fake). It certainly seems that if you compare the water usage of a 'prompt' to that of other common things there are other places we could worry more about water usage, a key quote:
> Andy also points out that manufacturing a t-shirt uses the same amount of water as 1,300,000 prompts.

I think comparisons to other activies are useful, it's easy to be awed by large numbers, for example the [aiwaterusage](https://aiwaterusage.com/) page lists all the gallons of water used by A.I. companies, but it's hard to judge these numbers if you don't know how much water other industries use, for example cattle, leisure etc.

To show how difficult it is to understand water usage, a great piece is [How Does the US Use Water](https://www.construction-physics.com/p/how-does-the-us-use-water) by Brian Cotter (whose [construction physics blog](https://www.construction-physics.com) is excellent and who has a [new book out](https://www.construction-physics.com/p/my-book-the-origins-of-efficiency-7bf)). Anyway this blog makes a pretty good attempt to piece together how water is generally used. In this he notes that there are consumptive uses of water and non-consumptive uses, and what we're mostly concerned about is water *consumption* not water *use*. For example previous generations of nuclear power plants used 'once-through' cooling systems in which "water would be drawn from some source, run through the cooling system, and then dumped back out into the same source at a slightly raised temperature." So although the water is *used* it's not really *consumed*. However, due to limits on thermal discharge, more recent nuclear power plants recirculate the water to be used again, until it is mostly evapourated. This means that recirculating power plants *use* much less water but *consume* pretty much all of the water they do use. 

However, to illustrate how difficult all of this is, Brian's very thorough blog post made an error when looking at US Data Center water use:
> This is a large amount of water when compared to the amount of water homes use, but it's not particularly large when compared to other large-scale industrial uses. 66 million gallons per day is about 6% of the water used by US golf courses, and it's about 3% of the water used to grow cotton in 2023.

> (Update: These values of data center water consumption are incorrect. See my [follow up post here](https://www.construction-physics.com/p/i-was-wrong-about-data-center-water).)

You can read the [follow-up post here](https://www.construction-physics.com/p/i-was-wrong-about-data-center-water) here is his conclusion:
> So to wrap up, I misread the Berkeley Report and significantly underestimated US data center water consumption. If you simply take the Berkeley estimates directly, you get around 628 million gallons of water consumption per day for data centers, much higher than the 66-67 million gallons per day I originally stated.

> However, the methods used to produce these estimates are debatable, and seem to have been chosen to give the maximum possible value for data center water consumption. If you exclude the water “consumed” by hydroelectric plants via reservoir evaporation, you get something closer to perhaps 275 million gallons per day. And if you take into account the fact that lots of data center operators use renewable energy PPAs (mostly from wind and solar sources), my guess is that you get something closer to 200-250 million gallons per day (though I haven’t run a detailed calculation here).

## My current understanding

So my take here is that figuring out exactly how much water is consumed is difficult, and even defining 'consumed' is non-trivial. Even noting the 'consumed' versus 'used' distinction some 'consumption' is pretty debateable, such as the water lost to evaporation whilst sitting in a hydro-electric damn resevoir.

## Empire of A.I. - Plundered Earth

Here is the passage that caught my eye from the Plundered Earth chapter of Empire of A.I.:

> That summer, as Google filed a report with Chile’s environmental agency for approval of its data center—a largely rubber stamp process—MOSACAT, a water activist group, began combing through all 347 pages of the filing. Buried in its depths, Google said that its data center planned to use an estimated 169 liters of fresh drinking water per second to cool its servers. In other words, the data center could use more than one thousand times the amount of water consumed by the entire population of Cerrillos, roughly eighty-eight thousand residents, over the course of a year. MOSACAT found this unacceptable. Not only would the facility be taking that water directly from Cerrillos’s public water source, it would do so at a time when the nation’s entire drinking water supply was under threat. In 2019, as with Iowa and Arizona, Chile was already nine years and counting into a devastating and historically unprecedented megadrought.

First observation, if you are consuming as much as 1000 times the amount of water used by 88 thousand residents, then you're consuming as much as 88 million people. The population of Chile (according to wikipedia as of 2023) is 19.6m. So it would be more than 4 times the water usage of the entire population of Chile.

But let's do the math as given in the book, what is a 169 litres per second in liters per day?
169 x 60 x 60 x 24 = 14601600 or about 14.6 million litres.
What about a human? Estimates of this vary greatly, but let's call it 150 litres per day, so the amount used by the 88k residents is 150 x 88k which is 13200000 or about 13.2 million. So according to the book's own figures Google's data centre was projected to use about the same amount of water as the 88k residents, not 1000 times as much.

Unless you think the average human uses 150/1000 = 150ml of water per day? Some estimates give around 120-190 litres per day on average for the EU, but some estimates can be as low as 40-50 litres per day particularly low-income or water-stressed regions. But note all of these estimates are for personal consumption, not embedded consumption in which you include the water used to grow your food, make your t-shirts, cars, electronics (and of course data center use), etc.

If we take a step back, the book states that:
> But Cerrillos is also special—in a country where water is privatized, the municipality is home to the nation’s only public water service, which serves up the local groundwater to neighboring communities and, in emergency situations, to other parts of Chile.

If it were possible that Google's new data centre actually used 1000 times as much water as the residents, then that would mean that the water is rather plentiful there since it must be capable of producing at least 1000 times as much water as the residents use. In which case water wouldn't be a concern. It may quickly become a concern if the exact amount of water that the water system can support is 1000 times what the residents use and not 1001 times what the residents use. My point here is that a claim like "one thousand times the amount of water consumed by the entire population of Cerrillos" should make anyone stop and think "can this really be true". On the other hand, a claim that a new data centre would use **about the same amount** of water as the local population should actually be much *more* concerning.

In the same chapter we move from Cerrillos in Chile to the capital of Uruguay Montevideo, there:

> Google’s data center planned to use two million gallons of water a day directly from the drinking water supply, equivalent to the daily water consumption of fifty-five thousand people. With much of Montevideo receiving salt water in their taps not long after, the revelations were explosive.

This time the maths checks out okay. I feel like the editor has dropped the ball a bit here, is it likely that one data centre in Chile uses 1000 x more water than 88k people but another one in Uruguay uses 1 x 55k people? This time though 55k people is just the number that is equal to the water usage of the new data centre, it's nothing to do with the population of Montevideo, which is around 1.2 million. Meaning Google's new data centre would use as much water as 1/20th of the population. Quite a lot but it doesn't seem likely that a 5% increase in the use of water would be the sole cause of the "receiving salt water in their taps".


## Consumptive vs Non-consumptive

Due to the MOSACAT efforts, [Google changed their plans for their new data center in Chile](https://www.reuters.com/technology/google-takes-chile-data-center-plans-back-square-one-environmental-concerns-2024-09-17/):

> "In due course, a new process will begin from scratch for a project that will use air-cooled technology at this very location," Google added.

As I said above, although 1000x claim doesn't appear credible, it's probably *more* concerning if the amount is actually approximately equal to that used by the local residents. Because it is consumptive use then every one of those 169 litres per second would be taken from the local supply. Switching to air-cooling reduces the water use substantially, possibly by more than 95%. However, that does not come for free, doing so likely increases the *energy* consumed by the data centre, possibly by as much as 18%. So there is a trade-off between water and energy used. 


## Conclusion

I do not know enough to make any strong definitive conclusions, other than that calculating energy and water usage of data centers is non-trivial.
Like most modern conveniencies they don't come for free, it will have some environmental impact, but you should consider comparing your use with other similar conveniencies and it doesn't seem likely to me that A.I. data centers are (**yet**) worthy of particular scorn.
More specifically the water consumption of data centers is of concern but manageable, and that the energy usage is probably of more concern. But again I stress this is more of a vague vibe than a firm conclusion.
