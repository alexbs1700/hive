# Hive Game Engine

Domain vocabulary for the Hive board game engine and its terminal UI — a from-scratch implementation of the official ruleset (base game plus the Mosquito, Ladybug, and Pillbug expansions), built as the future environment for a self-play-trained GANN.

## Language

### Board & position

**Board**:
The unbounded hex-grid playing surface. It has no fixed size or edges, only the Cells that happen to be occupied.
_Avoid_: Grid, map

**Cell**:
A single hex position on the Board, addressed by axial coordinates (q, r). A Cell may be empty or hold a Stack.
_Avoid_: Hex, space, tile, square

**Stack**:
The ordered list of Pieces occupying one Cell, bottom to top. Only the topmost Piece in a Stack is in play for adjacency, movement, and surrounding purposes; Pieces beneath it are covered.
_Avoid_: Pile, tower

**Hive**:
The single connected mass of all currently-placed Pieces, of both colors, treated as one graph. This is the rulebook's own term (as in "One Hive Rule"). It is distinct from the project's name — when this document or the code refers to "the Hive" as a domain concept, it means this connected mass of pieces, never the repository or package.
_Avoid_: Swarm, cluster, colony

### Pieces

**Piece**:
A single physical game piece, either in play or in Reserve: one Bug Type belonging to one Player, with a per-type disambiguating number.
_Avoid_: Tile, bug, token, chip

**Bug Type**:
The species a Piece represents — Queen Bee, Beetle, Grasshopper, Spider, Soldier Ant, Mosquito, Ladybug, or Pillbug — which determines its movement rule and any Special Ability.
_Avoid_: Piece type, insect, creature

**Piece Code**:
The canonical text identifier for a Piece: color letter, Bug Type letter, and a disambiguating number assigned in the order each Piece of that type is placed (e.g. `wA1` is White's first Soldier Ant). Used in Move Notation and UI display; distinct from the Piece object itself.
_Avoid_: Piece ID, tag, label

**Reserve**:
The Pieces a Player has not yet placed on the Board. Each Player starts with all 14 of their color's Pieces in Reserve.
_Avoid_: Hand, pool, inventory

### Turns & moves

**Turn**:
One Player's opportunity to act. Turns strictly alternate between the two Players.
_Avoid_: Round, ply

**Move**:
The single action taken during a Turn: exactly one of Placement, Movement, Special Ability, or Pass.
_Avoid_: Action, step

**Placement**:
Introducing a Piece from Reserve onto an empty Cell. Placement is legal by its own adjacency rules regardless of whether the Player's Queen Bee is on the Board yet — only Movement and Special Ability require the Player's own Queen Bee to already be placed.
_Avoid_: Drop, play

**Movement**:
Relocating an already-placed Piece from its current Cell to another Cell, following that Piece's own Bug Type's movement rule (and, for sliding movers, the Freedom to Move Rule).
_Avoid_: Slide (sliding is one specific movement style, not every Bug Type's), step

**Special Ability**:
A Move that relocates a Piece other than by the acting Piece moving itself, granted only to specific Bug Types: the Pillbug's Throw, and a Mosquito's copied ability when it is touching a Pillbug. Kept distinct from Movement because it does not follow the target's own movement rule or the Freedom to Move Rule the way Movement does.
_Avoid_: Power, skill

**Throw**:
The Pillbug's Special Ability: relocating an adjacent Piece (friend or foe) directly to another empty Cell adjacent to the Pillbug, without that Piece being considered to have moved itself. Bound by its own exceptions — it cannot target the Last-Moved Piece, a covered Piece, or a Piece whose removal would break the One Hive Rule, and it cannot cross a narrow gate.
_Avoid_: Push, launch

**Pass**:
A Turn in which the Player has no legal Placement, Movement, or Special Ability available, so play passes to the opponent with no Piece changing.
_Avoid_: Skip, forfeit turn

**Last-Moved Piece**:
The single Piece, if any, that was the subject of the previous Turn's Movement or Throw. It cannot be the subject of a Movement or a Throw on the very next Turn, by either Player. Tracked as part of game state rather than re-derived from history on each legality check.
_Avoid_: Frozen piece, locked piece

**Pinned**:
Our own shorthand, not rulebook language, for a Piece that currently cannot legally be the subject of a Movement or a Throw — because it is covered, because it is the Last-Moved Piece, or because removing it would break the One Hive Rule.
_Avoid_: Stuck, immobile

### Rules & invariants

**One Hive Rule**:
The Hive must remain a single connected mass at every instant, including mid-Move: a Piece may never be left stranded, and no Move may ever split the Hive into two groups, even momentarily.
_Avoid_: Connectivity rule

**Freedom to Move Rule**:
A sliding Piece may not move out of, or into, a position that requires squeezing through a gap flanked by two occupied Cells on both sides (a narrow gate). Does not constrain the Grasshopper's jump, or a Mosquito copying it.
_Avoid_: Sliding rule, gate rule, squeeze rule

### Outcomes

**Win**:
The rulebook outcome when one Player's Queen Bee is completely surrounded (all six neighboring Cells occupied) and the opposing Queen Bee is not. The Player whose Queen Bee is surrounded loses.
_Avoid_: Victory

**Draw**:
A rulebook outcome, and only a rulebook outcome: either the same final Move completes the surrounding of both Queen Bees at once, or the position is a forced, unresolvable repetition (the rulebook leaves detection of this second case to player agreement; this engine does not yet detect it automatically — see [ADR-0001](docs/adr/0001-separate-inconclusive-outcome-from-draw.md)). Never used for an engine-tooling cutoff.
_Avoid_: Tie, stalemate (stalemate is the informal name for the repetition case specifically, not for Draw in general)

**Inconclusive**:
Not a rulebook concept. Reported only by this project's random-move demo runner when its own `max_moves_per_game` safety cap is hit before a Win or Draw occurs. Must never be conflated with Draw.
_Avoid_: Draw, timeout, unresolved

### Notation

**Move Notation**:
The official Hive text format for recording a Placement or Movement: a Piece Code plus, for every Move after the game's first, a Direction Marker locating it relative to an already-placed reference Piece's Piece Code (e.g. `wA1 wQ-`) rather than by absolute coordinate.
_Avoid_: Algebraic notation, coordinate string

**Direction Marker**:
The symbol in Move Notation, attached to a reference Piece Code, identifying which of its six neighboring Cells — or "on top of," for climbing — a Move targets.
_Avoid_: Direction code
