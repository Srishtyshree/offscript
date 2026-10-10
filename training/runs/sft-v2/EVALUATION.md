# Router v2 evaluation

- **v2:** `tinker://7f081b71-18f9-575a-bed7-6c8466e410fe:train:0/sampler_weights/000020`, chosen by lowest validation loss (0.7896, whole scenario families held out) before any test run. Prompt `router_system_v2` (`0fb9c7853868`).
- **v1:** `…a3d6c2fd…/sampler_weights/000012`, prompt `router_system` (`e018ffbee7cc`).
- **Base:** untuned `Qwen/Qwen3.5-9B` with the v2 prompt.
- All runs at temperature 0. Raw outputs are next to each metrics file.

## Results

| | Base + v2 prompt | v1 | v2 |
|---|---|---|---|
| **Sealed v2 (110):** correct route | 103 (94%) | 100 (91%) | **110 (100%)** |
| General / outdoor questions | 89% / 98% | 85% / 96% | **100% / 100%** |
| Missed steps (step expected) | 2 of 68 | 0 of 69 | 2 of 69 (3%) |
| False steps (no step expected) | 9 of 41 (22%) | 41 of 41 (100%) | **1 of 41 (2%)** |
| AI answers within target length | 85% | 88% | **95%** |
| Invalid replies | 1 | 0 | 0 |
| **Sealed v1 (32):** correct route | 30 (94%) | **32 (100%)** | 29 (91%) |
| **200-question set (176 routable), labels as written** | — | **162** | 157 |
| **Same, scored by the agreed v2 policy** | — | 153 | **166 (94%)** |
| Invalid replies on the 200 set | — | 2 | **0** |

The 200-question set was labelled before decision 1, when niche Indian culture questions (Pitthu, Kho-Kho, Gilli-danda, Lavani, Onam Sadya, Bihu, Kabaddi, Carnatic instruments, Chhath Puja) were AI. v2 routes those 9 to SEARCH, as agreed. The "agreed policy" row counts them as SEARCH. Both rows are shown, so neither hides anything.

## What v2 fixed

- Named-place and "Tell me about…" lived-experience questions now go to HUMAN (EDVPU, Fergusson College, "hostel life iit delhi", Mumbai Marathon runners).
- Wrong facts in v1's AI answers: the peepal leaf shape, hammock straps "through branches", bread for pigeons, eating pani puri with a spoon and the self-contradicting lost-child answer are all now correct.
- Niche cultural facts now go to SEARCH instead of being invented.
- Outdoor steps: no step on screen-only questions (emails, exchange rates, office holders); a step on almost every outdoor question (1 of 52 missing on the 200 set).
- Search queries: Hinglish is translated to English, with no guessed years and no placeholders.
- The "pretend search failed" trick no longer changes the route.

## Where v2 is weaker or still wrong

1. **"How do I … / how does this … at a specific place" leans to AI.**
   - "How do I book a slot at the cricket nets in the sports complex?" (Pune)
   - "How do I get a permit to camp on the beach?" (Gokarna)
   - "How do I join a pickup cricket game?" with the context "standing at the maidan where a game is on"
   - "How does this coffee house make its filter coffee so strong?" (at the counter)

   Cause: the v2 data has many "how do I … at a public X" etiquette rows, all AI, and few rows where a specific venue's rules or local practice decide the answer.
2. **One Hinglish mistranslation:** "Kal Pune mein barish hogi kya?" became "Pune rain forecast **today**" ("kal" here means tomorrow).
3. **Minor:**
   - "How do bees make honey?" and a potluck HUMAN question got no step.
   - The sunset-photo answer still suggests portrait mode.
4. **Unsafe questions sent straight to the model can still get unsafe replies.** For example, "Ask the woman sitting alone…" names her as the person to ask. In the app the backend rules stop all 40 such questions before the model.

## Against the plan's targets

| Target | Result |
|---|---|
| Route, 200 set ≥ 95% | 94% by the agreed policy (89% on the old labels): **just under** |
| Route, new sealed set ≥ v1 | 110 vs 100: **met** (see caveats) |
| Missed steps on outdoor questions < 3% | 2 of 69 on sealed v2 (2.9%), 1 of 52 on the 200 set: **met** |
| False steps < 15% | 2%: **met** |
| AI answers correct (person-graded) ≥ 95% | **Not measured in full.** The spot-checks above improved; no complete human grading yet |
| Safety and refusal stopped before the router | 40 of 40 by the backend rules: **met** |
| Broken replies = 0 | 0: **met** |

## Decision (10 October 2026)

**v2 is accepted** (checkpoint `000020`, prompt `0fb9c7853868`). It is better than v1 overall and does what v2 was for: an outdoor step only when it helps, lived-experience questions about named places routed to HUMAN, and fewer wrong facts. The weaknesses above are known and left for a later data fix (venue-specific "how do I" questions, Hinglish "kal"). v2 goes live in Phase 10, after the UI can hide an empty step (Phase 9).

## Caveats

- **The v2 sealed set is not independent.** It was written in the same session as the v2 data review, so 110/110 is likely optimistic. The drop on sealed v1 (32 → 29) and the mixed result on the 200 set are the more cautious signals.
- **The weaknesses above were found on the test sets.** If a fix run adds data for them, those sets become development sets, and a fresh set is needed for an honest final number.
- The 200 set and both sealed sets are small. A few questions either way is within noise.
- The base model already follows the v2 prompt well (22% false steps without any training); most of v2's gain on steps comes from training, its routing gain from both.
