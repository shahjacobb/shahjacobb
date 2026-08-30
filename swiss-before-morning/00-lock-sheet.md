# LOCK SHEET — "Before Morning"

The verbatim lock strings live in `shots.json` under `locks` and are injected into
every prompt by `generate.py`. **Do not retype them into individual prompts.**
Continuity failures in AI film come almost entirely from re-describing the subject
shot by shot. Describe once, reuse the exact bytes.

This file is the human-side casting, wardrobe and vehicle direction behind those
strings.

---

## 1. TALENT — "AVA" (working name)

**Casting read:** 26–29. A young European professional who reads *expensive and
composed*. Refined bone structure, high cheekbones, clean jawline, long neck,
straight posture. Quietly magnetic rather than overtly glamorous — the elegance is
in the stillness, not in effort.

**Do not cast toward:** perfume-ad glamour, influencer energy, a face that reads
over 30, or a flat corporate look. She should read as someone who belongs in the
front cabin, not as someone demonstrating a product.

**Hair & makeup:** glossy dark chestnut, blunt shoulder-length cut with soft
movement — styled, never undone. Groomed brows, satin-neutral makeup with defined
lashes, no lip gloss and no contour. Skin stays real: pores visible, no beauty
retouch pass in the grade.

**Wardrobe — the blazer is the silhouette.** A fitted single-breasted charcoal
wool sports blazer with a sharp shoulder and a nipped waist, over an ivory
fine-knit silk shell, slim tailored black trousers cropped at the ankle, black
leather loafers with a slim silver bit. Jewellery is one fine silver chain and
small silver hoops — nothing that catches light on its own. Structured black
leather cabin bag.

**Layer state — this is the continuity tell. Track it.**

| Shots | Layer |
|---|---|
| 1–2 | Blazer only. Charcoal overcoat folded on the seat beside her. |
| 3–8 | Charcoal architectural wool overcoat worn **open over** the blazer, unbelted. |

The coat going on at the aircraft door in Shot 3 is a story beat, not wardrobe
housekeeping. Before that door she is a passenger being looked after. After it she
is a woman in motion. Shot 3 is the only place the audience should register a
costume change.

---

## 2. VEHICLE

Gloss black BMW M340i, dark chrome trim, black 19-inch double-spoke wheels, warm
ivory leather with dark open-pore wood. Athletic and understated — the car is
never the loudest thing in frame. Kept showroom clean; the only surface interest
is water, because every night exterior is wet.

**Unbranded fallback.** Swap the `vehicle` lock in `shots.json` for:

> `VEHICLE — an original unbadged German performance sedan with M340i proportions,
> no visible manufacturer badges, grille emblems or model lettering, gloss black
> paintwork with dark chrome trim and black 19-inch double-spoke wheels, warm ivory
> leather interior with dark open-pore wood, athletic understated proportions,
> showroom clean.`

and drop the brand lockup from the third end card. Use this if the film ships
without brand approval — see the note in `README.md`.

---

## 3. AIRCRAFT

SWISS International Air Lines A220. It appears in four shots (1, 4, 6, 8) and its
**red navigation light is a character in the film** — it is the thing the match cut
is built on and the last thing we see, crossing the sky over Andermatt. Keep the
red consistent in the grade across all four.

---

## 4. PHOTOGRAPHY

Large-format digital, anamorphic spherical primes, restrained movement on dolly or
gimbal. Real reflections and practical sources only. Deep blacks with no lifted
shadows, subtle 35mm grain, a grade that travels cool-to-warm across the 44
seconds as the film moves from fluorescent night to alpine sunrise.

The grade is the clock. Shot 1 is blue-black and sodium; Shot 8 is pale blue and
gold. Nothing in between should jump.

---

## 5. WHAT WE ARE RULING OUT

The full negative string is in `shots.json` under `locks.negative`. The intent
behind it, in short: no smiling at camera, no gowns, no champagne, no drone orbits,
no drifting or wheelspin, no neon, no generated text or logos, no plastic skin.

Every one of those is the default an image model reaches for when asked for
"luxury car commercial." The negative block exists to keep the film out of that
gravity well.
