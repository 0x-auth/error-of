# Case study: PDF to HTML, driven by errors

## The assumptions a converter makes

| Assumption | Invariant that checks it | What a violation means |
|---|---|---|
| Words at the same height form one row | I1: every source word appears exactly once in the output | grouping lost or duplicated text |
| Words closer than *k* x font size are one cell | I2: no cell runs a number straight into a word | two columns were joined |
| A total row sums the column above it | I3: checked on the source geometry | the document, or the column reading, is wrong |

I3 is checked against the source positions, not against the output, so it holds
whichever representation is chosen. It works as an observer outside the representation.

## First run: payslip (Aug 2025, one page, 340 words)

| Representation | Merge distance | Violations | What was observed |
|---|---|---|---|
| wide cells | 0.9 x font size | 1 (I2) | 7 fused cells: `306766 Tax Calculation…`, `Payable Days 31.00 Bank A/c No.`, `95344 UAN No.` |
| tight cells | 0.45 x font size | 0 | chosen |

I3 passed on all 7 total rows (GROSS PAY 5,61,060 in three columns, GROSS DED 1,76,976,
tax total 7,51,855, gross salary 67,32,720).

## What the run itself revealed

1. **An invariant can be wrong.** The first version of I2 ("a cell holds a number or
   words, not both") flagged `April 2025` and `Rent - 10% of Basic`. The loop then
   chose the representation that satisfied it best, *word cells*, which split every
   label into single words. A bad invariant steered the system to a worse output.
   Fixed by stating the real boundary: a number running *into* a word.
2. **The extractor's own word detection is an assumption.** Building words from
   characters with a fixed gap split letter-spaced headings (`GROSS P A Y`), which made
   I3 read the wrong column (4,40,449 instead of 5,61,060). Using pdfminer's space
   detection fixed it. The arithmetic invariant caught a character-level error.
3. **An earlier manual conversion of the same payslip swapped "Net Tax" and
   "Total Tax"** to fit expected tax arithmetic. That is an invariant used as an
   authority over the observation. I3 only reports; it never rewrites the source.

## Next representations
- region split: cut a block at its widest gutter into side-by-side tables
- scanned pages: OCR, or a model reading of the page image, as another representation
  checked by the same invariants
