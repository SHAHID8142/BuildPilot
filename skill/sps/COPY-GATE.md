# Copy Gate (portable source of truth)

SPS-owned copy-quality laws. Specialist skills (`copywriting`, SEO copy tools,
AI-humanizer tools) are enhancers only. If a specialist skill is missing, still
enforce this file.

> **Plain-language summary.** When the agent writes words a customer will read —
> headlines, page text, product info, meta descriptions, ads — those words must
> sound like a person, not a robot. No recycled AI phrases. No made-up numbers,
> reviews, or sources. Every claim is either a fact we can point to, or clearly
> someone's opinion. Bangla copy must follow বাংলা একাডেমি spelling (৫ম সংস্করণ,
> ২০২৩), use চলিত রীতি only, and read like a Bangladeshi wrote it — not like
> English translated word by word. A script checks what a script can check; a
> fresh read checks the rest.

## The Gate

1. Copy work begins only after the audience snapshot exists (see
   Prompt-law rules) or the user's brief supplies it.
2. Agent drafts copy per the laws in this file. DESIGN-GATE copy laws
   (structure/conversion) and sps-seo (technical metadata truth) apply at the
   same time — this file adds the language layer, it does not replace them.
3. Agent runs `bash scripts/sps-copycheck.sh <project> --mode advisory`
   while drafting; fix every violation or record why it is a false positive.
4. Agent runs the **Final anti-slop pass** (below) — all six passes, in order.
5. **Stop.** Copy is not deliverable until: (a) check_copy.py passes in
   `--mode deployment` (or every CRITICAL is waived in writing by the user),
   (b) the fresh-context reviewer (SECTION-DOD #52) confirms the prompt-law
   checklist, and (c) the user approves the copy in the section approval packet.
6. On approval: record the copy version + gate result in `./.sps/handoff.md` and
   log the decision in `./.sps/changelog-sps.md`.

## What the gate applies to

Any customer-facing COPY in ANY language, including:

- Marketing text: hero, headlines, section copy, About, service pages.
- Site copy: button labels, form microcopy, empty/loading/error states.
- CMS content: product descriptions, blog posts, category text.
- SEO meta titles/descriptions (language quality only — sps-seo owns
  lengths, duplication, and truth-to-content).
- Ad text, campaign copy, email copy, social captions.
- Translated copy, including CMS i18n Bangla (MULTI-LANGUAGE-I18N.md output is
  a DRAFT, never ship-ready without this gate).

Not covered: code comments, commit messages, internal `.sps/` notes, alt text
semantics (sps-seo owns alt-text SEO; this gate only bans slop patterns in it).

## Hard laws (zero exceptions)

1. **Never fabricate.** No invented statistics, percentages, dates, client
   counts, testimonials, reviews, awards, or sources. If a number or quote is
   not in the approved fact sheet or a real client record, it does not ship.
2. **Every numeral traces.** Every statistic, count, and date in copy must
   match an entry in the fact sheet (`.sps/facts.md` or the client-supplied
   record). Missing entry = delete the number or source it.
3. **Testimonials are real.** Only real, attributed, consented quotes; material
   connections disclosed (FTC 16 CFR 255/465 standard). Never write a
   testimonial on a customer's behalf. Result-claims inside testimonials pass
   the same fact check as body claims.
4. **No disclaimer loopholes.** An outcome promise ("get paid in 24 hours")
   is either true as stated or hedged to what is actually typical. A small
   disclaimer does not rescue a misleading claim.
5. **Specificity over vagueness.** Replace "many", "several", "experts say",
   "up to X%", "industry-leading" with a concrete sourced number or delete it.
6. **Fact or opinion, labeled.** Every claim is (a) factual and sourced, or
   (b) clearly subjective opinion/puffery ("we love what we do"). Objective
   claims (fastest, cheapest, certified, clinically proven) need
   substantiation before ship.
7. **Urgency must be real.** "Limited time", "only N spots", countdowns only
   when a real deadline/limit exists in the fact sheet.
8. **Never claim detector-proof.** The agent never states or implies the copy
   "passes AI detection", is "undetectable", or is guaranteed human-scored.
   The goal is good writing, not evasion.

## Machine-checkable laws (validator-enforced)

Validator: `framework/sps2/tools/check_copy.py` — standalone, stdlib-only, no
network (check_product_proof.py pattern). Two modes: `--mode advisory`
(report, always exit 0, for drafting) and `--mode deployment` (fail-closed,
exit 1 on any CRITICAL — the actual gate). The wrapper
`scripts/sps-copycheck.sh` (byte-identical mirror: `skill/sps/scripts/`) runs
it on a project. Wordlists live in `framework/sps2/tools/copy_lists/`
(EN blocklist, BN blocklist, EN lexicon, সাধু/WB-form table, loanword list) so
they can be curated per language without touching checker code — the AntiSlop
Sampler schema is the model. Lists start from the seed entries in this file
and grow via MISTAKE-PROMOTION when a real failure recurs.

Checks (CRITICAL unless marked WARN):

- **EN stock-phrase blocklist.** One hit = fix (list: `copy_lists/en_blocklist.txt`).
- **BN slop-phrase blocklist.** Direct EN calques + formulaic connectors;
  one hit = fix (`copy_lists/bn_blocklist.txt`).
- **EN AI-lexicon density.** More than 3 distinct hits per 500 words
  (`copy_lists/en_lexicon.txt`).
- **Negative parallelism.** "not just X, but Y" — max 1 per page; 2+ = fix.
- **Rule-of-three frequency.** 3+ triadic lists per page = WARN.
- **Em-dash density.** More than 3 per 1000 words, or any
  "clause — clause — clause" chain = WARN.
- **Sentence-rhythm variance (burstiness).** Across 20+ sentences,
  sentence-length standard deviation < 5 words = WARN (the strongest machine
  signal per Bangla detection literature, arXiv:2502.19286 / HC-Bangla).
- **Hedging stacks.** 2+ hedge tokens in one sentence = WARN.
- **Placeholder/Lorem ipsum text** = fix.
- **Social-proof counts.** "N+ clients"-style patterns must trace to a real
  record — untraceable = delete.
- **সাধু/West Bengal forms.** করিতেছি, তাহার, শ্রেণী, কোনও, কারো … = fix;
  চলিত রীতি and bn-BD spellings only (`copy_lists/bn_sadhu_wb_forms.txt`).
- **Word-initial ড়/ঢ়** — never legal = fix.
- **দাঁড়ি endings.** A Bangla sentence ending with an English period = fix.
- **Loanword spellings.** Variants off the Academy list = WARN
  (`copy_lists/bn_loanwords.tsv`).
- **Pronoun consistency (Bangla).** আপনি and তুমি mixed on one page = fix.

Threshold design: single blocklist hits fail outright; density-style checks
(lexicon, tricolons, em-dashes) fail only above threshold. Generic AI detectors
(GPTZero, ZeroGPT) are unreliable for Bangla — the gate is rule-based +
prompt-based + human pass, never detector-API-based.

## Prompt-law rules (fresh-context review enforces)

These cannot be grepped. They are checked by the fresh-context reviewer
(SECTION-DOD #52) and the adversarial second opinion (HANDOFF-CHECKPOINT
step 4), each answering this checklist explicitly:

- **Audience snapshot exists.** Who the reader is, their top pain, desired
  outcome, awareness stage — before drafting (Copyhackers VoC method).
- **Voice-of-customer language.** Headlines and benefits trace to customer
  phrases (reviews, interviews), not invented marketing vocabulary.
- **Benefit-before-feature framing** in the language itself, not just
  structure (DESIGN-GATE owns the structural law; this checks the wording).
- **Register fit.** আপনি is the default for customer-facing site copy;
  তুমি allowed for a young-consumer brand voice as an explicit per-site tone
  decision recorded in the plan; তুই only for deliberate edgy campaigns;
  never mixed within a page.
- **Naturalness (Bangla).** Read-aloud pass: does it sound like a native
  Bangladeshi marketer wrote it? No অনুবাদ ঘেঁষা (translation-flavored)
  clause order, no long English-style attributive modifiers before nouns.
- **No literal English calques.** Where a natural Bangla verb or idiom
  exists, no untranslated/transliterated jargon ("লেভারেজ করা", "ইউটিলাইজ"
  where ব্যবহার করা is natural).
- **Idiom discipline (বাগধারা).** Idioms fit literal context and register;
  one proverb per section as decoration = flag; plain accurate phrasing wins.
- **Connector discipline (Bangla).** অতএব/ফলস্বরূপ/এছাড়াও/সুতরাং at most
  ~1 per 200 words; never open consecutive paragraphs with the same connector.
- **Reading level.** Grade 6–8 target for general-audience copy; score is a
  screening flag for rewrite, not auto-fail.
- **Headline specificity.** Each headline carries at least one concrete
  element (number, named outcome, specific audience); pure hype
  ("Transform your business today") fails review.
- **Message match.** Ad/campaign promise is echoed in the page H1/hero.
- **Bangla Academy editorial rules.** Prefer established Bangla terms where
  they exist; no English capitalization rules applied to Bangla; one approved
  Bangla rendering per foreign brand/term (transliteration glossary per site).

## Bangla standard (বাংলা — mandatory extra checks)

Authority: **বাংলা একাডেমি, "বাংলা বানানের নিয়ম", ৫ম সংশোধিত ও পরিবর্ধিত
সংস্করণ, ২০২৩** + "প্রমিত বাংলা বানান অভিধান" (২০১৮). Older editions are NOT
the standard; several spellings changed in 2023.

- **চলিত রীতি only.** All finite verbs in চলিত forms. সাধু forms
  (করিতেছি, করিয়াছে, করিব, হইবে, তাহার, আমারে) are errors in any web copy.
  সাধু রীতি belongs to poetry, songs, scripture — never a client site.
- **ণত্ব বিধান.** ণ only per the rules (after ঋ/র/রেফ/ষ/ক্ষ; before ট-বর্গ;
  after প্র/পরা/পরি/নির্/অন্তর্). ণ is WRONG in verb endings (করেন, যাবেন),
  in words with adjacent ত-বর্গ (গ্রন্থ), in foreign words (জার্মান), and in
  the second member of a compound whose first member has র/ঋ/ষ (দুর্নাম).
- **ষত্ব বিধান.** ষ per the তৎসম rules only. ষ is WRONG in the সাৎ প্রত্যয়
  (ভূমিসাৎ), in খাঁটি বাংলা and foreign words (জিনিস, পুলিশ), and after
  অঃ/আঃ-visarga + ক/খ/প/ফ sandhi (পুরস্কার, ভাস্কর, তিরস্কার — never
  পুরষ্কার).
- **ই/ঈ.** ঈ in তৎসম (নদী, শক্তি, বুদ্ধি); ই in foreign words (স্টিল,
  পেন্সিল, রিপোর্ট); 2023 kinship rule: মাসি, দিদি, পিসি, কাকি, দাদি (ি, not ী).
- **উ/ঊ.** ঊ only in তৎসম (পূর্ব, সূর্য, ভূমি, শূন্য); দেশি/বিদেশি words take
  উ (ফুল, জুতো, মুহূর্ত, কুরআন).
- **ড়/ঢ়.** Never word-initial (ডাক্তার, ঢাকা are correct spellings but start
  with ড/ঢ — the ড়/ঢ় letters never begin a word); never after ব/ণ/ত/ঢ
  (অম্বুঢ); after ঋ-কার and র they are correct (হৃড়, বাড়ি, সাড়ে).
- **য-ফলা/ব-ফলা.** তৎসম words per the BANGLADESH (বাংলা একাডেমি) forms:
  আশ্চর্য, কল্যাণ, পূর্ব, প্রকৃতি, কৃতজ্ঞ. West Bengal forms (আশ্চয্য,
  প্রকিতি) are rejected. দেশি/বিদেশি words write full য/ব: দোয়া, সোয়া,
  গোয়াল (not দ্বা/স্বা/গ্বাল).
- **অনুস্বার/বিসর্গ.** ং before ক-বর্গ sounds ঙ but is written ং (সংখ্যা);
  derived forms take ঙ (বাংলা→বাঙালি, রং→রঙিন).
- **চন্দ্রবিন্দু ও হসন্ত-বর্জন.** চাঁদ, পাঁচ, সাঁতার per Academy rules;
  no word-final হসন্ত (পরিষদ, not পরিষৎ).
- **যতিচিহ্ন.** Every Bangla sentence ends with দাঁড়ি (।) — an English
  period at sentence end is an error. কমা for lists/clauses/vocatives;
  ? and ! as in English; no English capitalization conventions.
- **বাংলাদেশ context.** bd vocabulary, not West Bengal: পানি (not জল),
  নামাজ, শ্রেণি, কোনো, কারও. Arabic/Persian loanwords are natural in BD
  copy. Bengali numerals ০১২৩৪৫৬৭৮৯ for bn-BD copy (Latin numerals only
  inside code, prices per client preference, or brand names).

## Final anti-slop pass (run before every copy delivery)

Six passes, in order. Each pass re-reads the copy; a failure returns to
drafting, not to a later pass.

1. **Truth pass.** Every number, count, date, quote, and outcome promise
   traced to the fact sheet or a real record. Anything untraceable is deleted.
2. **Slop-lexicon pass.** Run check_copy.py in advisory mode; rewrite every
   hit with concrete, subject-specific language. No synonym-swapping of
   blocklist phrases — replace with a real claim.
3. **Rhythm pass.** Read the page aloud (or simulate it): vary sentence
   length, break up any three consecutive same-shape sentences, replace one
   symmetric tricolon with 1–2 concrete items, cut every em-dash that a
   comma or colon serves better.
4. **Specificity pass.** Every sentence names something concrete: a number,
   a person, a place, a mechanism, an outcome. Delete or replace every
   abstract quality noun (quality, excellence, solution, innovation) that
   lacks a concrete anchor in its sentence.
5. **Bangla pass (Bangla copy only).** চলিত check, Academy spelling spot-check
   on the validator's flagged words, calque read-aloud, connector count,
   pronoun consistency, দাঁড়ি endings, Bengali numerals.
6. **Fresh-eyes pass.** The fresh-context reviewer (an agent that did not
   author the copy) answers the prompt-law checklist above and gives a
   one-line verdict per item: pass / fix. All fixes applied before the STOP
   in The Gate.

## Abort conditions

Do not deliver copy if:

1. check_copy.py fails in deployment mode with any CRITICAL.
2. Any numeral, testimonial, or source claim lacks a fact-sheet record.
3. Bangla copy contains a সাধু verb form, a WB-standard spelling, or mixed
   আপনি/তুমি addressing.
4. The fresh-context review has not run (copy authored and approved by the
   same agent alone is invalid).
5. The user has not approved the copy in the section approval packet.

## Exceptions

- **Tier 1 quick-fix** (copy edit, single headline swap) may skip the full
  gate run, but still requires the 5-line quick-fix approval packet
  ([APPROVAL-PACKETS.md](APPROVAL-PACKETS.md)) and must not introduce a
  fabrication or a blocklist phrase.
- **Read-only Q&A** never needs the gate.
- **User-supplied copy** shipped verbatim at the user's explicit instruction
  is exempt from language laws, never from the hard laws (fabrication,
  fake urgency). Record the user instruction in the handoff.
- **Non-Bangla, non-English copy** applies the machine checks where lists
  exist and the prompt-law checklist in that language; missing lists are
  logged as a gap, not silently skipped.

## Relationship to existing gates (do not duplicate)

- **DESIGN-GATE.md copy laws** own structure/conversion: above-the-fold,
  one buyer, benefits before features, social proof placement, objection
  handling, CTA verb+outcome, scannability, no padded copy, and the visual
  anti-slop ban list. This gate owns language quality, the Bangla standard,
  tone/humanization, and linguistic slop patterns. Where both touch a rule
  (CTAs, padded copy), DESIGN-GATE's law stands and this gate adds the
  checkable list.
- **sps-seo** owns technical SEO: metadata lengths, canonical, sitemaps,
  JSON-LD, heading hierarchy, alt-text SEO, Core Web Vitals, and its
  anti-hallucination rule ("metadata generated from real page content; never
  invent facts not present in the content") — referenced, not restated, by
  hard law 1. Run seo_audit.py unchanged in deployment mode alongside this gate.
- **SECTION-DOD items 13–16** remain the content DoD anchor; this gate adds
  one condition to item 13 ("copy passes the copy gate") rather than a
  parallel checklist.
- **MULTI-LANGUAGE-I18N.md** (sps-cms) is transport; its Bangla auto-translation
  output is a draft that must pass this gate before ship.

## Memory

After each copy-gate approval: record copy version + gate result in
`./.sps/handoff.md`; log the decision in `./.sps/changelog-sps.md`; recurring
slop failures go to [MISTAKE-PROMOTION.md](MISTAKE-PROMOTION.md) and new
blocklist entries land in `framework/sps2/tools/copy_lists/` via a BuildPilot
PR ([LESSONS.md](LESSONS.md)).
