---
title: Lazy calculation
date: 2017-01-11T17:47:02Z
tags: ["python", "maintenance"]
---
In many cases whilst programming there is a decision to be made as to whether
to *store* some state, or (re)*caluate* it as and when needed. Obviously every
situation is different and therefore there is no one answer which fits. In this
post I'm going to attempt to explain the distinction and the benefits/drawbacks
of either approach. I hope that just remembering that this choice exists will
force me to make an explicit choice, such that I may think about it a bit more.

# Distinction

The distinction is a little akin to that between eager evaluation and lazy
evalution but it is not the same. The distinction here is about code-maintenance.
I'll start with a very simple example, and then move to a more realistic example
which involves access to a database, which makes the decision a bit more interesting.

Suppose you have a very simple `class` representing a person and the children
that they may have:

    class Person(object):
        def __init__(self, gender):
            self.gender = gender
            self.boys = []
            self.girls = []
        
        def have_baby_girl(self)
            girl = Person('female')
            self.girls.append(girl)
            return girl
        
        def have_baby_boy(self):
            boy = Person('male')
            self.boys.append(boy)
            return boy

Now, suppose somewhere in your code you wish to return the number of children
that a particular person has. You can either keep track of this, or calculate it
on the fly, here is the keep-track-of-it version:

    class Person(object):
        def __init__(self, gender):
            self.gender = gender
            self.boys = []
            self.girls = []
            self.number_of_children = 0
        
        def have_baby_girl(self)
            girl = Person('female')
            self.girls.append(girl)
            self.number_of_children += 1
            return girl
        
        def have_baby_boy(self):
            boy = Person('boy')
            self.boys.append(boy)
            self.number_of_children += 1
            return boy

Here is a possible calculate-it-on-the-fly version:
            
    class Person(object):
        def __init__(self, gender):
            self.gender = gender
            self.boys = []
            self.girls = []
        
        @property
        def number_of_children(self):
            return len(self.boys) + len(self.girls)
        
        def have_baby_girl(self)
            girl = Person('female')
            self.girls.append(girl)
            return girl
        
        def have_baby_boy(self):
            boy = Person('boy')
            self.boys.append(boy)
            return boy

In this particular case I prefer the calculate-it-on-the-fly approach. I like
that I did not have to modify any existing code, I only had to add some. If I
add some other method (suppose an `adopt` method) then in the keep-track-of-it
version I have to make sure I update our state variable `number_of_children`
appropriately. Finally, if we change our definition of what a 'child' is,
suppose they have to be under 18 years-of-age, then keeping track-of-it, might
not work at all, or if it does I have to be very careful about updating parents
whenever a child ages.

In terms of performance, this is often trickty to evaluate correctly. Essentially,
you're asking whether the calculation of the state on the fly, is more expensive,
than code to keep track of it. This of course depends hugely on often you inspect
the state. You may do a lot of work to keep-track of a state variable that is
never inspected, or inspected only very rarely. On the other hand, if it is
inspected often, but not updated much, the calculate-it-on-the-fly approach,
may be needlessly re-doing the exact same computation many times.

As a side-note there is a [lazy](https://pypi.python.org/pypi/lazy/1.2) package
for Python that lets you calculate attributes once when needed, and then stores
the result for later retrieval. Of course if you update anything the calculation
depends upon you have to make sure an invalidate the stored result. I've found
it is useful in the case that an attribute won't ever need to be re-calculated,
but might never need to be calculated at all (and is expensive to do so).

# More interesting example

For in-memory occurrences such as the simple example above, often the choice is
pretty clear. Code is often clearer if you calculate-it-on-the-fly, and only
resort to keep-track-of-it whenever the value is somewhat expensive to calculate,
used very often, or particularly simple to keep track of.

However, the choice becomes more interesting when the calculation of the value
involves some external state, even if keeping-track-of-it is done on the
external state. A common case is when the state is kept in a database. In Python,
you may well be using an ORM to access the external state. 

Consider an online game website, for some game that has four players. Let's
suppose the game is turn-based and players are not expected to be logged in for
the entire duration, but just take their turn whenever they are online. The game
then can be in multiple states: waiting for players, running, finished. So in
some ORM you might describe a game like:

    class Game(database.Model):
        player_one_id = Column(Integer, ForeignKey('user.id'))
        player_two_id = Column(Integer, ForeignKey('user.id'))
        player_three_id = Column(Integer, ForeignKey('user.id'))
        player_four_id = Column(Integer, ForeignKey('user.id'))

        winner_id = Column(Integer, ForeignKey('user.id'))

        .... bunch of other columns that actually describe the game state ....

Now, suppose you wish to display a list of running games for a user, you could
do it something like this:

    class Game(database.Model):
        ... as before ...
        state_names = ['waiting', 'running', 'finished']
        state = Column(Enum(*state_names), nullable=False, default='waiting')

        @staticmethod
        def running_games(user):
            games = Game.query.filter(
                Game.state == 'running',
                or_(
                    Game.player_one_id == user.id,
                    Game.player_two_id == user.id,
                    Game.player_three_id == user.id,
                    Game.player_four_id == user.id,
                )
            ).all()
            return games
        
        @staticmethod
        def open_games(user):
            games = Game.query.filter(
                Game.state == 'waiting',
                and_(
                    Game.player_one_id != user.id,
                    Game.player_two_id != user.id,
                    Game.player_three_id != user.id,
                    Game.player_four_id != user.id,
                )
            ).all()
            return games

Using this way you would have to make sure that when the fourth player joins a
game the state is set to 'running', and when the game finishes the state is set
to 'finished', along with the 'winner' being set.

Instead one could use calculate-it-on-the-fly as in:

    class Game(database.Model):
        ... as before ...
        # No state column

        @staticmethod
        def running_games(user):
            games = Game.query.filter(
                Game.player_one_id != None,
                Game.player_two_id != None,
                Game.player_three_id != None,
                Game.player_four_id != None,
                or_(
                    Game.player_one_id == user.id,
                    Game.player_two_id == user.id,
                    Game.player_three_id == user.id,
                    Game.player_four_id == user.id,
                ),
                Game.winner_id == None
            ).all()
            return games
        
        @staticmethod
        def open_games(user):
            games = Game.query.filter(
                or_(
                    Game.player_one_id == None,
                    Game.player_two_id == None,
                    Game.player_three_id == None,
                    Game.player_four_id == None,
                )
                and_(
                    Game.player_one_id != user.id,
                    Game.player_two_id != user.id,
                    Game.player_three_id != user.id,
                    Game.player_four_id != user.id,
                )
            ).all()
            return games

This could be simplified a bit if we assume that players fill slots in order
such that it is never the case that `Game.player_four_id` is not `None` whilst
one of the others is. 

In this particular case then I think the keep-track-of-it is a little simpler.
But this hugely depends on the logic for joining a game, taking ones turn, and
finishing the game. In particular when a game is finished you have to set the
`winner_id` column anyway, so it seems like not too much of a burden to
additionally set the `state` column.

However, there are many situations in which, calculate-it-on-the-fly is more
appropriate. A common case, occurs when the rules for state changes may change.
For example, in the game case, we may decide that as long as there are two
players, people can play the game, which is therefore `running`. People may
join a `running` game, provided it is not full, and may leave a `running` game.
In this case, calculate-it-on-the-fly simply updates the rules for when a game
is `running`. However, keep-track-of-it, not only has to update its rules for
when to modify a state (including now reverting a game from `running` to
`waiting` when someone leaves a two player game), but must also go through the
database and modify the `state` column of any existing games. To do this, the
database update code will essentially have to mimic the `calculate-it-on-the-fly`
code anyway.

# Conclusion

There is often a choice to be made between maintaining some kind of state up-front,
and calculating it whenever it is required. Both are useful and should be used
depending on the situation. Recalling that there is such a choice may help a
programmer to explicitly make that choice, and perhaps even record the reasons
for it.

