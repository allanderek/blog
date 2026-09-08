---
title: Poker puzzle
date: 2017-03-04T13:58:36Z
tags: ["poker analysis odds"]
---
[Bill the lizard](dead:http://www.billthelizard.com/) has an 
[excellent post](dead:http://www.billthelizard.com/2017/02/best-poker-hand.html) describing an interesting puzzle as to the most desirable full house in a game of poker. The rest of this post depends upon you having read that puzzle so you may wish to do that now, or skip this post.

::: update

**Update:** The above link seems to be dead now, so I'll just give my description of that puzzle. The question is, in 5-card draw, what is the best full-house to hold? The highest **ranked** full-house is aces-over-kings AAAKK. But this is 5-card draw, so if you have aces-over-X then no-one else can beat your hand with a full-house, even if you have aces-over-twos. So what you want to consider is hands which **can** beat your full-house. Those are 4-of-a-kind, and straight-flushes (including the royal flush 10-J-Q-K-A of the same suit). The pair of your full-house will prevent one 4-of-a-kind hand, regardless of what the pair is. But for straight-flushes, what the pair is affects which straight-flushes are prevented. A pair of Kings, only prevents two royal-flushes, and two straight-flushes running 9-K. In addition, since there are only 4 suits, at least one of your Kings must share a suit with one of your Aces, hence at least one of the royal-flushes is already prevented by one of your three aces. So, we can see that a pair of queens would be better as this would *also* prevent the same two 9-K straight-flushes as well as two 8-Q straight-flushes. Going further, a pair of Jacks would prevent the same 9-K, and 8-Q straight-flushes and additionally two 7-J straight-flushes. Continuing this logic, you can see that it's better to actually have a pair that is *outside* of the royal-flush range, at least one of which is already prevented by one of your three aces. So you want AAA-XX, where X is lower than 10. Note also that an Ace also prevents A-2-3-4-5. But furthermore a 3 prevents more straight-flushes than a 2, since that only prevents A-5, and 2-6, wheres as 3 prevents A-5, 2-6, and 3-7. Similarly a 4 is better, and a 5 is better, but again, at least one of your 5s must share a suit with one of your aces, so you want a pair that is at least 6. So the best full-houses are AAA-XX where X is 6, 7, 8, or 9.

Said in another way. Your full-house AAA-XX, can only be beaten by a (comparitively) small number of hands. Basically 4-of-a-kind, of which there are 13, and straight-flushes, of which there are: 40 (10 in each suit, each one starting from A, 2, 3, 4, 5, 6, 7, 8, 9, 10). So, your full-house can be beaten by only 53 hands, but your full-house makes some of these 53 impossible. None of your opponents can possibly have 4 aces, or 4 Xs, for whatever your pair is. That's true regardless of what X is. So full-houses can be compared by how many straight-flushes they prevent. Each X will prevent 5 (or fewer) straight-flushes. You want to pick your Xs so that they both prevent 5 straight-flushes, so avoid Xs near the ends of the range.

:::

I think this represents an instance where the mathematically correct answer is not correct for other concerns. To be clear, I think the given answer is the mathematically correct answer, and the blog post linked above never suggested to answer anything other than that. In addition, there isn't really any action you can take regardless of which full house you think is better to have, the difference in the odds is small enough not to have any real-world applicability.

To summarise the result above, the idea is that the a full house of three aces over two kings is not as good a hand to have as a full house of three aces over two sixes. This is restricted to a game of five card draw with no wild cards etc. This is because although the AK full house is ranked higher than a full house of A6, they cannot both occur in the same hand. So to decide which you would rather have you have to look at how many possible hands can beat you. Both hands can be beaten by four-of-a-kind or a straight-flush. Because the two sixes break up more possible straight-flushes than the two kings in theory having the A6 full-house will win more hands than the AK full-house and is therefore a better hand to have.

However, this assumes that all straight-flushes are as likely, but this is five-card draw. Two things make a high straight-flush more likely after the draw than a low straight-flush. Firstly, someone with low cards that may make up part of a low straight-flush after the draw, may be bet out of the hand before the draw takes place. Secondly, players are more likely to hold on to higher valued cards going into the draw.

For example, suppose three players against you are dealt:

* Kh, Qh, 8d, 5s, 4s
* 10d, 9s, 5h, 4h, 2d
* Qs, Qc, 5c, 4c, 3c

The first player here has two possible ways of drawing to make a straight-flush, but, if they make it to the draw, they will almost certainly retain the king and queen of hearts and not the 5 and 4 of spades. The second player has just as much chance of making a straight-flush that might beat your full-house, but chances are they won't make it to the draw. The third player actually has a better chance of making a straight-flush but there is a good chance they hold on to the pair of queens. An analogous player with a pair of 6s and J-Q-K of diamonds is a bit more likely to throw away their pair (than a player with a pair of queens) and thus stick around with a chance of beating your full-house with a straight-flush.

So which full-house is the better one to have is dependent upon what you think the odds are of players remaining in the hand with a possibility of a high straight-flush against the probability of a player remaining in the hand with a possibility of a low straight-flush. That isn't something that can be numerically calculated, at least not easily, you might be able to assume perfectly rational players that both do whatever gives them the highest probability of winning and assume others do the same.

