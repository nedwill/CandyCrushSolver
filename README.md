CandyCrushSolver
================

CandyCrush Optimized!

This program will take a user entered board and return the best possible
sequence of moves as a set of tuples indicating the indices of each swap.

It takes advantage of all the information present in order to provide
the best possible next move(s) for a given board.

Essentially this program plays all sets of legal move sequences from the user-
provided Candy Crush board and returns the sequence with the greatest score
per move.

This program is a good way to get past the tricky levels and expose the great
extent to which this game provides boards that cannot be defeated with near-perfect
play, ensuring that users will get frustrated and purchase powerups.

Some boards are faster to solve than others, so be patient if it takes time. The search
can go 10 or more moves deep at times, including creating and breaking special candies.
Fortunately it should speed up over time as you play more boards. All boards that have
ever been solved are stored in a hash table that is persistent (on disk) between sessions.

More technical info: I recreated the game's core functionality (colored candies, matching,
special candies, combos). I only use sets of moves that can't be affected by falling pieces,
so the moves here are guaranteed to work.

Figuring out the falling behavior in the game was tricky. It's animated so it doesn't appear
to follow a strict pattern, relying on a timer of some sort, but instead, all pieces fall down
one "tick" at a time and pieces that align during these "ticks" are broken if they form a 3-or-more
combo. The 

Note:
Some higher levels including newer types of candies haven't been implemented. Make the
closest possible recreation - this is just a proof of concept!