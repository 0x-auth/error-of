"""
A model whose only job is to answer the way some program P would.

Frozen lexicon: each content word maps to one base operation.
A sentence is accepted only if every content word maps to an operation
and the operations compose into a program with an end (a value).
Otherwise the answer is "no P": there is no program for this input.
"""
import re

FILLER = {"i", "need", "the", "of", "all", "a", "an", "what", "is", "me", "give"}

# frozen meanings: word -> (kind, operation)
LEXICON = {
    "primes":  ("source", lambda n: [k for k in range(2, n) if all(k % d for d in range(2, int(k**.5) + 1))]),
    "numbers": ("source", lambda n: list(range(1, n))),
    "evens":   ("source", lambda n: list(range(2, n, 2))),
    "below":   ("bound",  None),
    "total":   ("reduce", len),
    "number":  ("reduce", len),
    "count":   ("reduce", len),
    "highest": ("reduce", max),
    "largest": ("reduce", max),
    "lowest":  ("reduce", min),
    "sum":     ("reduce", sum),
}

def run(sentence):
    words = re.findall(r"[a-z]+|\d+", sentence.lower())
    content = [w for w in words if w not in FILLER]
    unknown = [w for w in content if w not in LEXICON and not w.isdigit()]
    if unknown:
        return f"no P (no meaning for: {', '.join(unknown)})"
    nums = [int(w) for w in content if w.isdigit()]
    sources = [LEXICON[w][1] for w in content if w in LEXICON and LEXICON[w][0] == "source"]
    reducers = [LEXICON[w][1] for w in content if w in LEXICON and LEXICON[w][0] == "reduce"]
    if len(sources) != 1 or len(nums) != 1 or not reducers:
        return "no P (does not compose into a program with an end)"
    reduce_ = reducers[0]
    program = f"{reduce_.__name__}({[k for k, v in LEXICON.items() if v[1] is sources[0]][0]} below {nums[0]})"
    return f"{program} = {reduce_(sources[0](nums[0]))}"

if __name__ == "__main__":
    for s in ["i need the total number  of all the primes below 100",
              "I need the the highest primes below 100",
              "give me the sum of all evens below 50",
              "what is the meaning of life"]:
        print(f"{s!r}\n   -> {run(s)}")
