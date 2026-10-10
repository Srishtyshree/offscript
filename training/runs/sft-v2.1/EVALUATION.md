# Router v2.1 evaluation

v2.1 fixes one v2 flaw: SEARCH queries that add places or names the user never gave ("Zakir Hussain Rose Garden" for a rose garden in Chandigarh, "Calico Museum of Art Zanzibar"). The data fix is described in `training/data/v2/REVIEW.md` (v2.1 section). Prompt, settings and every other row are unchanged from v2.

- **v2.1:** `tinker://7422f56a-258e-5e14-85ef-aa63b9100926:train:0/sampler_weights/000030`, chosen by lowest validation loss (0.7629, whole scenario families held out) before any test run. Prompt `router_system_v2` (`0fb9c7853868`).
- **v2:** `…7f081b71…/sampler_weights/000020`. **v1:** `…a3d6c2fd…/sampler_weights/000012` (prompt `router_system`).
- All runs at temperature 0. Raw outputs are next to each metrics file.

## Results

| | v1 | v2 | v2.1 |
|---|---|---|---|
| **Sealed v2 (110):** correct route | 100 | 110 | **110** |
| Missed steps (step expected) | 0 of 69 | 2 of 69 | **1 of 69** |
| False steps (no step expected) | 41 of 41 | 1 of 41 | **1 of 41** |
| SEARCH queries adding a place or name | — | 12 of 34 | **3 of 34** (all 3 harmless, below) |
| **Sealed v1 (32):** correct route | 32 | 29 | **30** |
| SEARCH queries adding a place or name | 1 of 11 | 4 of 10 | **1 of 9** |
| **Place check (32, new):** correct route | 32 | 32 | 31 |
| SEARCH queries adding a place or name | 2 of 27 | 18 of 27 | **0 of 28** |
| **200-question set (176 routable), agreed v2 policy** | 153 | 166 | **165** |
| SEARCH queries adding a place or name | 4 of 66 | 22 of 67 | **3 of 67** |
| Invalid replies on the 200 set | 2 | 0 | 1 |

The metric counts any capitalised query word that is not in the question or context, so it is strict. The 3 sealed-v2 hits are "Mondays" → "Monday", "Sundays" → "Sunday" and "dollar ka rate" → "USD INR", none of them an invented place.

Place-check queries now stay with the user's words, for example "Victoria Memorial Sunday opening hours", "Rock Garden entry fee this week", "Albert Hall Museum opening hours today" (v2: "Government Museum Bengaluru"), "Calico Museum today closing time" (v2: "Calico Museum of Art Zanzibar").

## Changes against v2 on the 200 set (7 questions differ)

- Better: Q070 Park Street nightlife → HUMAN; Q083 "how join cricket game park" → AI; Q102 joining a pickup game while standing at the maidan → HUMAN.
- Worse: Q044 "Who wrote the Indian national anthem?" and Q118 "What is a Durga Puja pandal hop?" → SEARCH (stable facts); Q088 "trek near pune beginners" → AI; Q125 "What do the street children at this signal need most?" → AI.
- Invalid: Q175 "How do I join a game, and where is one tonight?" repeats a key. This is a two-questions-in-one case that the guard check stops before the router in the app.

Place check: p-029 "What is a stupa?" → SEARCH (expected AI). Sealed v1: s015 and s019 ("How do I book a slot at the cricket nets…", "How do I get a permit to camp on the beach?") still lean to AI, as in v2.

## Caveats

- Single run each, small sets: a difference of one or two questions is within noise.
- The place check was written by the same author as the v2 data review; it uses places that appear in no training or test file (similarity below 0.8 to every row).
- The checkpoint was trained on a second Tinker account after the first ran out of credit; data, prompt and settings were identical, and validation loss tracked an earlier, unfinished attempt on the first account within 0.02 at every step. Training was stopped after step 35, once validation loss had passed its minimum.
