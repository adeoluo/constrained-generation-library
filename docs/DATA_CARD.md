# Data Card - Constrained Generation Library

## Source
- **No dataset.** The library operates on a schema the caller provides and a deterministic fake
  model. There is no training data, download, or network access.

## Composition
- A schema is an ordered list of typed properties. The default demonstration schema has a string,
  an integer, a boolean, and an enum.
- The vocabulary is a small set of JSON-ish token strings (letters, digits, structural punctuation,
  the words true and false, and an end-of-sequence marker).

## Labels and supervision
- There is no supervision. The automaton defines validity; there are no labels.

## Provenance and licensing
- Authored for this repository under the MIT license. No third-party data is included.

## Filtering and contamination
- Not applicable: outputs are generated under a constraint and validated against the same schema.

## Known limitations
- The demonstration schema and vocabulary are small by design so the mechanism is clear and every
  run is fast and deterministic.
