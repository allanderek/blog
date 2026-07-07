---
title: "Scoring Orders"
tags: [ games, pole-prediction ]
date: 2026-07-06T15:25:36+00:00
---

I haven't ever spoken about the scoring system we use on [pole prediction](https://www.poleprediction.com) to grade Formula One predictions.
There are two systems and I'm particularly fond of the one we use for the season predictions. But first let me explain the session (qualifying, race, etc.) scoring is a relic of an old game we played before I developed pole prediction. This was first played on reddit.

## Session Scoring

The scoring system is relatively simple, you order the top-ten drivers and for each driver you predicted to be in the top-ten you get:
* 4 points for the exact correct position
* 2 points for being one position off
* 1 point for at the driver at least being in the top-ten at all.

Unfortunately this has a number of problems:

Firstly your tenth placed driver may finish 11th, for which you get nothing, even although it was clearly a better prediction, than a 1st place prediction that finished in 7th, which still gets 1 point.

Another problem is that it produces a lot of what feels like either very fortunate or very unfortunate points totals. Here is an example of a particularly unfortunate result. Suppose you predict the teams to come in 2-by-2 in their cars, and they mostly do but unfortunately (like Hamilton and Rosberg in Barcelona 2016), the two Mercedes crash out, so in this case, your top two aren't in the top-ten, everyone else is in order, but two away from their predicted position:

| Prediction  | Result | Points |
| ----------- | -------|--------|
| Antonelli    | Hamilton  | 1 | 
| Russell | Leclerc | 1 | 
| Hamilton | Norris | 1 | 
| Leclerc | Piastri | 1 | 
| Norris | Verstappen |  1 | 
| Piastri | Hadjar | 1 | 
| Verstappen | Lawson | 1 | 
| Hadjar | Lindblad | 1 | 
| Lawson | Gasly | 0 | 
| Lindblad | Collapinto | 0 | 

You receive a grand total of 8 points, even though you were broadly right and simply didn't predict the top two cars to crash out, as basically nobody else did.
Now consider a **random** prediction of the same top ten drivers, I have literally gotten this order with the python one-liner `import random; print(random.sample(range(1, 11), 10))` and it produced the following result:


| Prediction  | Result | Points |
| --------------|------|--------|
| Leclerc    | Hamilton  | 2 | 
| Hamilton  | Leclerc | 2 | 
| Piastri | Norris | 2 | 
| Hadjar | Piastri | 1 | 
| Antonelli | Verstappen |  0 | 
| Lawson | Hadjar | 1 | 
| Verstappen | Lawson | 1 | 
| Norris | Lindblad | 1 | 
| Lindblad | Gasly | 2 | 
| Russell | Collapinto | 0 | 

So this random arrangement scored 12 points. Any random arrangement must score at least 8, because regardless of how bad the predictions are it does have 8 of the top 10 drivers, so they must all score at least 1 point. Partly this illustration goes badly because I picked the pathological case. But the point here is that you can often get 2 or even 4 points for a prediction, even though many of the drivers you predicted to out-perform that driver did not, whilst some you didn't predict to out-perform them did. This feels wrong.

So I think we could get a better scoring system by scoring *order* rather than absolute position. So, for the *season* predictions, that's basically what I've done, but I've done it in an interesting way that accounts for closeness. So I'd like to describe the season scoring.

## Season Scoring

The season predictions occur before the first race, in fact even before the first free practice session of the season. In these, you're not predicting **drivers** but instead **teams**. Now, the key observation here is that whilst you can forget about points magnitude and focus on the *order*, in which case you could use something like a [Spearman's Rank Correlation Coefficient](https://en.wikipedia.org/wiki/Spearman%27s_rank_correlation_coefficient). This works very well where you care about the *order* of elements rather than the absolute size of each element.

However, I *am* concerned with the size of each, in particular, what I'd like to do is punish incorrect predictions that were very wrong, and only slightly punish predictions that were wrong, but not *that* wrong. Consider the following example:

| Prediction A | Prediction B | Result |
|--------------|--------------|--------|
| Mercedes | McLaren | Mercedes |
| Ferrari | Mercedes | McLaren |
| McLaren | Ferrari | Ferrari |

There are three pairs here. You might argue that Prediction A and Prediction B are equally good, both of them have two correct pairs and one incorrect one.

| Pair | Prediction A | Prediction B | 
|------|--------------|--------------|
| Mercedes-McLaren | ✓ | ✗ |
| Mercedes-Ferrari | ✓ | ✓ |
| McLaren-Ferrari | ✗ | ✓ |

However, if I had add *points* here you can see that one prediction is significantly better than the other:

| Prediction A | Prediction B | Result |
|--------------|--------------|--------|
| Mercedes | McLaren | Mercedes - 600 |
| Ferrari | Mercedes | McLaren - 599 |
| McLaren | Ferrari | Ferrari - 300 |


| Pair | Prediction A | Prediction B | 
|------|--------------|--------------|
| Mercedes-McLaren | ✓ | -1 |
| Mercedes-Ferrari | ✓ | ✓ |
| McLaren-Ferrari | -299 | ✓ |

So in this case, clearly Prediction B is better than Prediction A. Although both got one pair wrong, the incorrect pairing for Prediction B was pretty close. Whilst the incorrect pairing for Prediction A was very wrong. With more than three teams you can easily construct a case where Prediction A has more correct pairs than Prediction B, but Prediction B is still better because the incorrect pairs are closer to the correct order:

| Prediction A | Prediction B | Result |
|--------------|--------------|--------|
| Mercedes | McLaren | Mercedes - 600 |
| Ferrari | Mercedes | McLaren - 599 |
| McLaren | RedBull | Ferrari - 300 |
| Red Bull | Ferrari | Red Bull - 299 |


| Pair | Prediction A | Prediction B | 
|------|--------------|--------------|
| Mercedes-McLaren | ✓ | -1 |
| Mercedes-Ferrari | ✓ | ✓ |
| Mercedes-Red Bull| ✓ | ✓
| McLaren-Ferrari | -299 | ✓ |
| McLaren-Red Bull | ✓ | ✓ |
| Ferrari-Red Bull | ✓ | -1 | 

So in this case Prediction B has two wrong pairs, but only has a score of negative 2, whilst Prediction A has only a single wrong pair, but a much worse negative score. Of course this is *something* of a pathological case, but it's not that unlikely, there are many times where there are large gaps in the order.

Now, this scoring system works well, but is a little opaque to show to the users, *and* it can be quite large, for 4 teams there are only 6 pairs, but for the 11 teams in Formula One there are 55 pairs. But we can give an **equivalent** scoring system that is much more intuitive to understand.
For each team A predicted to be in position X we score it as:
* If team A finished at or above position X, then the score is 0.
* If team A finished below position X, the score is the difference in points between the predicted position and their actual points total.

So here is the above scored in that way:

| Prediction A | Prediction B | Result |
|--------------|--------------|--------|
| Mercedes 0 | McLaren -1 | Mercedes - 600 |
| Ferrari -299 | Mercedes 0 | McLaren - 599 |
| McLaren 0 | RedBull -1 | Ferrari - 300 |
| Red Bull 0 | Ferrari 0 | Red Bull - 299 |

So we get the same scoring, Prediction A has a total of -299, whilst Prediction B has a total of -2.
I've found that this system works very well for season predictions for both Formula 1 and football leagues.

## Season predictions for individual races

Could we use a similar scoring system for individual races? The complicated thing is that there isn't really a 'score' for a driver for the race which would determine whether two out-of-order predictions were wrong by a little or a lot. We could, in theory, use the times. There are a few problems:
* Qualifying differences in times are very different from race differences in times.
* What happens when the different qualifying sections are not comparable, for example, Q3 has rain, so the top ten drivers' times are actually worse than everyone else's.
* What happens when someone fails to set a time at all, for example crashing out in Q1 of qualifying or retiring from the race.
* What about lapped cars in the race?

Ultimately I don't think this works. When someone is a point behind someone in season scoring it's easy to determine that they were *close*, if they are 50 points behind it's easy to determine that they were *not* close. But for a single session, particularly a race, often 'closeness' is not really represented by the time difference, it can be a strategy mis-call for example, or a puncture. Or, what happens if there is a full safety-car in the last couple of laps, or even if the race finishes under the safety car? In that case all the time differences will be low, but the race wasn't necessarily that close.

However, for individual sessions we can go back to the idea that the **order** matters, whilst the actual magnitude of the differences does not.
In that case a [Spearman's Rank Correlation Coefficient](https://en.wikipedia.org/wiki/Spearman%27s_rank_correlation_coefficient) works pretty well. It's the edge cases that we need to care about. We wish to punish someone for predicting a driver to be in the top ten, who ultimately didn't make it into the top ten. We can, simply treat every driver outside the top-ten as 11th, this introduces equal-ranks, but we can treat equal ranks the same as a mis-ordering.

The rules then become, for every predicted pair in the top-ten A > B:

* both in top ten, A ahead of B in reality: +1 (concordant)
* both in top ten, B ahead: 0 (discordant)
* A in top ten, B outside (so A genuinely ahead): +1 — A really did beat B
* B in top ten, A outside (so B genuinely ahead): 0 — your order was wrong
* both outside: tied in reality, neither beats the other: 0

Now, this has a problem. The tenth driver you select has almost no bearing on your predictions. You are essentially predicting that they lose 9 pairs they are involved in. If that is the case, then in order to maximise your score you would be better to select a driver for tenth that you think has no chance of finishing *higher* than tenth. Worse, this sort of plays out for more than tenth place. Place 8 and 9 as well, also have 7 and 8 pairs they are predicted to lose, perhaps better to ensure that they lose those rather than aim for the points for 8 > 9, 8 > 10, and 9 > 10. There are only three points available there, but if your 8th place pick actually finished 3rd you could lose out on many points.

Now, this doesn't actually matter if we're just using this on pole prediction as a kind of informational skill indicator, since the actual predictions are still based on the 4, 2, 1 points system, nobody will be incentivised to pick up points in this 'gaming' manner.

We *could* attempt to fix this anyway, we could modify the first rule to be:
* both in top ten, A ahead of B in reality: +2 (concordant)

This means that you would get a potential extra 9 points for getting your 10th place pick correct. But unfortunately that re-introduces one reason we disliked the 4,2, 1 scoring system, that is that having your 10th place pick be 11th is somewhat punished out of proportion. More generally, the 10th place pick is usually something of a bit of luck, since you usually haven't got the exact nine drivers ahead of them correct. If 1 or 2 of the favourite drivers retire, it seems wrong to massively reward someone who gets 10th correct, because they are essentially two places off.

So for now, I've decided to stick with the original formulation, since the incentives to game the lower positions are not a problem since the official scoring system is still in place.

