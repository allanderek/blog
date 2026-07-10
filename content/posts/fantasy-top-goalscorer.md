---
title: "Fantasy Top Goalscorer"
tags: [ games ]
date: 2026-07-10T10:30:04+00:00
---

Last summer I got interested in fantasy football again. I was interested in creating a game with three properties:
1. A casual to play game, didn't necessarily involve a lot of time or effort
2. Based around simply goals scored, so no complicated scoring system for stats and no rating system for performances
3. Players were unlikely to converge on the same team, or even one or two *"must picks"*
4. The game is self-regulating

To explain the third point, typically in a fantasy football game, each player is assigned a cost, and the goal is to select a squad of players within a particular budget. One issue is that this requires someone to assign each player a cost, so the game server requires an *oracle*. If the oracle is incorrectly setup you can break number 2 because where the oracle is wrong it suggests a 'correct' squad. It is easy to make a player either a *"must pick"* if you have priced them too cheaply, or a *"cannot pick"* if you have priced them too expensively.

A way around this is to have a *market-style* game, in which the value of a player is determined by the users themselves. This avoids the need for an oracle, and thus makes the game easier to run as well. Either you have a *transparent market* in which you allow users to `buy` and `sell` players, or you have a *hidden market* in which a player's value is determined by how popular they are (and that is usually hidden until the competition deadline, hence *hidden* market).

## Transparent market


A traditional transparent market setup for this game would have have something like the ability to `buy` or `sell` player tokens at a given price-per-goal. One disadvantage of this style is that it requires quite a bit of liquidity, i.e. it requires some keen users to put up `buy` and `sell` orders for the more casual players. These players are called *market makers* and you can achieve these by having the game server itself acting as a market maker according to some algorithm. The disadvantage of this is that it risks the game server becoming an oracle of sorts.


## My solution

Here is the game I came up with:
* Each competition involves a set of matches, usually comprising a *"game week"*.
* Each user is afforded a number of *tokens* to distribute amongst players that they think will score, this constitutes a user's allocation `user_allocation` for the given competition.
* The score is determined by the number of goals scored by each player selected
* The scoring system then assigns a value `goal_value` to each goal scored. This is equal to the total number of tokens placed in the competition `total_tokens` divided by the total number of goals scored in the competition `total_goals`. So `goal_value = total_tokens / total_goals`.
* Now each user's allocation `user_allocation_score(player)` for a given player, is equal to the number of goals scored by the player `player_goals` multiplied by `goal_value` and by the number of tokens the user assigned to that player `user_allocation(player)`. So we have
`user_allocation_score(player) = player_goals * goal_value * user_allocation(player)`. Combined these are the `user_allocation_player_scores`.
* The score for a user is the sum of all user allocations scores, so `user_score = sum(user_allocation_player_scores)`

This may sound complicated but it's essentially simple. We take all the tokens placed on the competition and divide them out equally to the users based on the number of goals their selected players scored weighted by the number of tokens they allocated to each goalscorer.

There is a small wriggle if you want tokens to be conserved. Tokens will be consumed by the game if a player scores one or more goals but no tokens were placed on that player. You can solve that, either by having 'bot' players make sure that every player has at least one token. Alternatively when calculating `goal_value` we can take `total_goals` to mean *"the number of goals scored by players backed by at least one token"* rather than the total number of goals scored.

How does this prevent users from converging on the same players? It doesn't really, to address this, each competition had a maximum number of tokens that could be allocated to a single player. So for a given competition we might have 100 tokens per user and a maximum of 30 tokens per player. That would mean each user must select at least 4 players. Hopefully people see that being contrarian might increase the odds of winning the competition if the favoured players do not score. If, for example, many users put the maximum allocation of tokens on, say, Haaland, and he doesn't score, those users which didn't allocate the maximum tokens (or any tokens) to him will have had tokens to spare on other players.

A modification to this strategy to *further* incentivise diversity in user allocations, is to do the same calculation, but you calculate how valuable a given player's goals are and then weight by that. A given player's goals are more valuable if few tokens were placed on that player. Bearing in mind that `total_goals` is likely the number of goals scored by players backed by at least one token, the calculation becomes:
```
user_allocation_score(player) =
    (goal_value x goals x user_allocation(player)) / all_tokens_on_this_player
```
The key point here is the division by `all_tokens_on_this_player`.
A worked example may make this much clearer:

* 100 total tokens in the pot
* User A puts 50 tokens on Haaland
* User B puts 30 tokens on Haaland
* User C puts 20 tokens on Isak
* Haaland scores 2 goals, Isak scores 1 goal
* Total goals by backed players: 3

Calculations:

* `goal_value`: 100 tokens ÷ 3 goals = 33.33 tokens per goal
* Haaland's 2 goals generate: 66.67 tokens total
* Isak's 1 goal generates: 33.33 tokens total

Payouts:

* User A: `(2 × goal_value × 50) ÷ 80 = 41.67 tokens`
* User B: `(2 × goal_value × 30) ÷ 80 = 25.00 tokens`
* User C: `(1 × goal_value × 20) ÷ 20 = 33.33 tokens`

User C does brilliantly here - they get a 67% return whilst the Haaland backers get less than they put in. Why do those users get less? Because their score for their Haaland tokens are divided by the total number of tokens placed on Haaland. The more popular a player is, the less valuable their goals are to each individual user.

Note as well, in the example this game is playable with just 3 users (and those users didn't use their full allocation of tokens). In particular, even if the game server had thousands of users, you could have a private league and play the game privately. This would open up the possibility of two kinds of private leagues. One in which each user's score is calculated as usual using **all** the users on the game server, and then the private league simply shows the order of the participants in the league. The second kind involves doing the score calculation for **only** those players within the private league. This would mean someone could have two very different scores. For example perhaps Haaland is very popular with all users on the server, but very unpopular for the players in a private league. A private league would probably simply show both scores.

The main disadvantage of this system is that it is arguably a little opaque and difficult to explain to users.


## Market style games

Both of these sets of rules are market style games, whereby you allow the mass of users to determine the value of a given player, rather than have some oracle assign values to players.

One interesting feature of this design, is that unlike most market style games, this is a hidden-market game so the user not only has to predict the performance of a player, but also the popularity of a player and thus the value of the player's goals.

A really nice advantage of the game as described is that it's ready to play immediately. There is no need for any oracle, and there is no need for any market makers. The game-server could nonetheless implement some 'bot' players, with some transparent strategies. These can act as benchmarks to actual users to compare against. For example we could have a bot that always distributes its tokens by the current league top goalscorer table, perhaps say 30 tokens to each of the top 3 goal scorers and 10 tokens to the 4th. Or one that always allocates 5% of tokens to the top goalscorer from each team.

## Conclusion

I really like market style games, and I even have a soft-spot for these hidden-market style games. I'd like to see more implementations.
One big advantage of market style games is the ease of setup for the game server. Because you do not need an oracle, you need not become one. This both reduces the effort required **and** reduces the risk of being wrong and hence breaking the game.

Another advantage, is that market style games lean themselves well to 'neutral' scoring. By that, I mean, scores which, first of all can be both positive and negative and secondly for which zero is not a terrible (or terribly good) score. This has the advantage of allowing users to have aggregate scores over many competitions. For example in a football league, you can have a single competition per game-week, and in addition a season league table which simply sums the scores up for each game week. Because the game-week scores are neutral, users can miss a week completely, without it necessarily being a disaster for their season-long score. In the particular game described above, a user can not only decide to skip a week, but also simply risk less than their full allocation of tokens for that game-week.

Of course, such season-long aggregate competitions are *possible* regardless of how you score each competition, but it's difficult to get this right, and doubly difficult to get this right in a way that allows for missed weeks. Games often resort to *"best X weeks"* scoring, but this feels a bit of a hack, and rewards risk-taking over consistency.

