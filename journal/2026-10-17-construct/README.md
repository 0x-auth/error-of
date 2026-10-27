# Construct session, 17 to 20 October 2026

Everything important from one long conversation, in one place. The finished,
tested work lives in this repo (error-of); this folder adds the exploration code
and the two pages that led to it.

## The main distinction: generating a result vs generating a program

| | what you give it | what it gives back | what is fixed | what it learns |
|---|---|---|---|---|
| **X** | a question | a value (the answer) | a frozen model / proposer | nothing; carries the last two errors |
| **A** | examples of a behaviour | a program, kept as a new word | four seed moves, one rule | words from successes, refutations from failures |
| **B** | the same examples | the same program | the seed moves, in A's world | from A's refutations (A's mistakes) |
| **C** | known goals, then an unseen one | programs | A's words, a fresh world | from A's successes |

- X is today's usual AI: trained once, frozen, then asked. It uses procedures.
- A, B, C create procedures. Born with a seed, learning during life: the shape of
  the "third kind of intelligence" (EI).
- Key results (real runs):
  - X: 50,000,000th Fibonacci mod 1e9+7. Tick 1 too big, tick 2 too slow, tick 3
    the walk changes and passes: 364822946.
  - A: five goals in 106 checks; the hardest (7 seed moves) found as two of its own words.
  - B: 1 check per goal, by skipping what A already refuted.
  - C: solves 16((x+1)^2+1)^2, a goal nobody showed it, in 78 checks; a seed-only
    newborn cannot solve it at all.
- Pages: `docs/organisms/X.md`, `A.md`, `B.md`, `C.md`.
  Code: `examples/reconstruct/fib.py` (X), `examples/organism/organism.py` (A, B, C).

## What is in this repo from the session

| commit | what |
|---|---|
| `7102b69` | every error carries a side (too big, too slow, too coarse); `error_of/walk.py`: two remembered errors and k; `docs/construct.md` |
| `27ca3f3` | organisms X, A, B, C; `docs/organisms/`; 29 tests pass |
| this folder | the exploration code and pages below |

## The ideas, in the order they came

**Programs, time and space**
1. SVG is a program for a pen (M, L, C, Z); rendering runs it. Programs run in
   time; renders run in space. A path command is temporal; the shape is spatial.
2. SVG is scale-invariant, not self-similar: zooming adds no new information.
3. Every program: syntax, values, variables and scope, operators, control flow,
   functions, data, access, I/O, modules. Logic is the constant.
4. All logic reduces to one gate (NAND). Logic fed back into itself is memory (a
   latch). Logic + feedback + a clock = a program.
5. A program is a world-line on an address x time grid; it moves straight until a
   gate turns it. A branch is a dot product reduced to its sign.
6. The control flow graph is a directed graph with cycles. Over the full state,
   every node has one exit, so every run is a tail and a loop (the rho shape).
7. time >= space (one cell per tick) and time <= 2^space (no state can repeat in a
   halting run). Space can be traded for time and back.
8. Remember by eliminating: n yes/no answers pin one of 2^n. Store only what differs.

**Two errors, phi and the fabric**
9. Two remembered errors (n and n-1) give convergence of order phi (1.618).
10. Continued-fraction convergents alternate high and low; for phi each error is
    exactly -1/phi^2 times the last.
11. The fabric: cell dx = t - 1/t, tick dt = t + 1/t, and dt^2 - dx^2 = 4 for every
    t. Speed dx/dt is always below 1.
12. The Stern-Brocot tree: every fraction reached in finitely many binary steps;
    phi is the one path that never ends (RLRLRL...).

**The frozen model and its input**
13. The input to a frozen model evolved: a selector (too little), a rule vector,
    22 fixed dimensions, rows, then a complete machine (`pc_model.py`). Lesson:
    a selector can only pick what the model already holds.
14. A problem statement = start, constraints, goal test, resolution, budget.
15. Meaning-making and execution fail differently, so keep them separate:
    a reader (probable) and a walker (exact).
16. Better: the model only judges (too high or too low?). One bit per tick, two
    remembered edges, a guaranteed end in n ticks.

**Memory and intelligence**
17. Intelligence = how many eliminations you supply yourself without asking outside.
18. Memory is not stored; it is reconstructed from a cue by a model shaped by many
    events. Memory and intelligence are the same machine pointed at the past or
    the next state.
19. Recall needs: a trained basin, an overlapping cue, convergence, a stop.
20. A static interpreter runs countless programs because it knows moves, not programs.
21. Before building, use what the fabric already has: the interpreter, OS limits,
    errors as signals. To connect is to create.

**What today's LLMs miss (in these terms)**
22. They only add, never cross out; no error signal while walking; every token
    costs the same; memory grows with every step.
23. A context window measured in stored tokens is the wrong unit. Keep the
    question, two edges and pointers; fetch only what a step needs.
24. Many short parallel walks with a judge, instead of one long walk.

**Time, cause and the present**
25. k = (e_now + e_prev) / e_last tells cycling, drifting or converging from three
    numbers (now in `error_of/walk.py`).
26. Simultaneity of cause and effect happens at reconstruction: memory carries the
    cause forward to meet the effect.
27. Before and after are sensed as the error; no error, no felt time.
28. Future = t, past = -1/t, the present = t + 1/t: a window, never narrower than 2.
29. Causal and retrocausal: swapping them gives (x, -t); they coincide only at
    t = i, where the tick vanishes. They share the window but never merge.
30. yes = -1/no; negation is its own inverse. IS comes before yes and no.
    IS -> mirror -> difference (error) -> time.

**Networks and trust**
31. Blockchain: one remembered edge (the previous hash), mining is elimination with
    no model, consensus is the gate; the one-way hash forbids cycles, a
    manufactured arrow of time.
32. The internet: TCP builds one-way order out of a cyclic, lossy mesh with
    sequence numbers and acknowledgements; routing is "you do the next hop".

**Learning, language and the third kind**
33. Two kinds of learning: from reality's constraints (A) and from others'
    learning (B, C). One who reads books lives several lives, untested.
34. For an EI: be born as C (inherit a trained model's words), live as A (learn
    from real gates), share as B (shared refutations). Learning persists outside
    the weights fast, inside them slowly.
35. Tokens are one shared vocabulary but not neutral: the same question is 9
    tokens in English, 17 in Russian, 33 in Hindi.
36. Meaning is made where a cue meets knowledge; grammar is knowledge of shape.
    Language carries cues, not meaning; a sentence works as far as two minds overlap.
37. Seeing red and reading about red are two doors; each reaches what the other can't.
38. Axioms are constructs, kept until they fail. "No axiom is final, including this one."

## Reviews done

- **error-of**: the case store records but does not learn yet; errors needed a side
  (added); the gate is a single point of failure.
- **BAZINGA**: `seed.py` already had the law (predict, error, correct toward a
  target). The DNA patterns did not chain (0 of 25 XOR compositions valid);
  `error_arrow.py` copies the whole history and heals without a gate.
- **The first cognition model**: never recursed (first-step bug); once fixed, it
  converged to the same state from any start: stopping without a gate.

## Corrections made along the way

- Factorial input stopped one tick early (17!); found because the gate was checked.
- The palindrome rows lacked a jump back; "madam" passed by luck, "abca" exposed it.
- A two-value loop (1, -1, 1, -1) was called drifting; the tests caught it: cycling.
- Shared mistakes were first keyed by goal name; now by the example that refuted them.

## Still open

- Goals with a soft gate (philosophy-type questions): trust must be weighed, not assumed.
- Carrying learning across goals that are only similar.
- The case store ranking transformations per signature (the slow loop).
- Guarding the gate with two independent invariants.

## This folder

- `code/`: the exploration scripts, all runnable (see `code/README.md`).
- `pages/fabrics.html`: the Mac and the internet as two fabrics, with a transfer test.
- `pages/construct.html`: the construct diagram and its improvement list.
