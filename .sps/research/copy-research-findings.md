# RESULT 1

## Summary
Compiled 17 concrete, checkable markers of AI-slop prose for the BuildPilot copywriting gate, covering English and Bangla. English: stock openers ("in today's fast-paced world"), the statistically overrepresented AI lexicon (delve, tapestry, seamless, robust, unlock, elevate, journey...), negative parallelism ("not just X but Y"), rule-of-three abuse, em-dash overuse, hedging stacks, empty praise adjectives, throat-clearing openers and summary-restatement closers, and uniform sentence rhythm (low burstiness). Bangla: literal English calques (অনুবাদ ঘেঁষা), সাধু-চলিত register mixing, connector chains (অতএব/ফলস্বরূপ/এছাড়াও), direct Bangla equivalents of the EN slop lexicon (বর্তমান বিশ্বে, গুরুত্বপূর্ণ ভূমিকা পালন করে, নতুন দিগন্ত উন্মোচন, মসৃণ অভিজ্ঞতা), idiom misuse, and প্রমিত spelling/grammar slips per Bangla Academy rules. Key design principle: score by density/thresholds rather than single hits, and for Bangla use rule-based + prompt checks since off-the-shelf detectors are unreliable for Bengali. Sources: Wired, The Guardian, The Atlantic, MIT Tech Review, CBS News, Gizmodo, Stanford's PubMed delve study, GPTZero/Originality.ai, Bangla Academy (banan.banglaacademy.gov.bd), bn.wikipedia on সাধু/চলিত, and Bengali LLM-detection literature.

## Findings
{
 "rule": "Flag marketing copy opening with formulaic scene-setting openers such as \"In today's fast-paced world...\", \"In the ever-evolving landscape of...\", \"In the digital age...\". These are the single most-cited AI-slop openings; a landing page should open with a concrete claim about the reader/product instead. Checkable: regex match on first sentence.",
 "source": "Reddit r/ChatGPT community lists; GPTZero/Originality.ai vendor lists (via web search)",
 "topic": "EN stock opener: \"In today's fast-paced world\""
}

{
 "rule": "Density-check the lexicon: delve, tapestry (esp. \"rich/vibrant tapestry\"), intricate, multifaceted, realm, landscape (metaphorical), testament, pivotal, crucial, navigate (metaphorical), foster, bolster, garner, showcase, unveil, harness, leverage, robust, seamless, elevate, embark, journey, unlock, meticulous, nuanced, commendable, game-changer, cutting-edge, revolutionize, empower. Stanford's PubMed-abstract study found \"delve\" and similar words spiked hundreds of times above baseline post-ChatGPT. Rule: more than 2-3 of these per 500 words = fail; each should be replaced with concrete, specific language.",
 "source": "Wired 'Why Does ChatGPT Overuse the Word Delve?'; The Guardian 'AI words: how to spot machine-generated text'; Stanford PubMed abstract frequency study; GPTZero/Originality.ai lists",
 "topic": "EN overused AI vocabulary (statistically overrepresented in LLM output)"
}

{
 "rule": "Count occurrences of \"not just X, but Y\" / \"it's not just X — it's Y\" per page. This negative-parallelism frame appears disproportionately in LLM output (RLHF rewards rhetorical polish) and is a top detection tell. Rule: max 1 per page of marketing copy; 2+ = fail. Alternative: state the stronger claim directly without the contrast scaffold.",
 "source": "MIT Technology Review; The Atlantic; CBS News; Gizmodo (web search results)",
 "topic": "EN negative parallelism: \"not just X but Y\""
}

{
 "rule": "LLM prose habitually delivers lists of exactly three (\"innovation, integrity, and impact\"; \"fast, reliable, and affordable\"). Checkable: count triadic comma lists per page; uniform tricolon density (e.g., 3+ per section, or every list having exactly 3 items) = fail. Vary list length and prefer 1-2 concrete items over symmetric triples.",
 "source": "CBS News; Wired; Gizmodo (web search results)",
 "topic": "EN rule-of-three / tricolon abuse"
}

{
 "rule": "Em dashes used as dramatic aside separators are the most-discussed AI tell (models overuse them relative to human baselines). Checkable: em-dash count per 1000 words above ~2-3 = flag; also flag the pattern \"clause — clause — clause\". Copywriters now scrub em dashes specifically to avoid being accused of using ChatGPT. Use commas, colons, or separate sentences instead.",
 "source": "The Atlantic 'The Em Dash Is the AI Writing Tell'; Wired; CBS News",
 "topic": "EN em-dash overuse"
}

{
 "rule": "Flag formulaic openers that delay the point: \"It's important to note that...\", \"It's worth noting...\", \"In today's world...\", \"When it comes to...\", \"Let's explore/dive into...\". Rule: the first sentence of any section must carry content, not preamble; regex-match these frames as fail.",
 "source": "Reddit r/ChatGPT slop-phrase lists; GPTZero/Originality.ai vendor lists (via web search)",
 "topic": "EN throat-clearing openings"
}

{
 "rule": "LLM text ends sections by restating what was just said: \"Ultimately,...\", \"In conclusion,...\", \"At the end of the day,...\", \"In summary,...\". Rule: flag these closers and any final paragraph that adds no new information; a page section should end on the strongest concrete point, not a recap.",
 "source": "Reddit r/ChatGPT slop-phrase lists; The Guardian (via web search)",
 "topic": "EN summary-restatement closers"
}

{
 "rule": "Flag empty superlatives with no verifiable referent: seamless (experience/integration), robust, cutting-edge, world-class, state-of-the-art, unparalleled, effortless, transformative, innovative. Rule: any such adjective must be backed by a concrete fact (number, mechanism, guarantee) in the same sentence or be cut. Checkable: adjective-without-quantifier heuristic.",
 "source": "MarketingProfs banned-words threads; 'The AI Slop Lexicon'; HBR on AI-sounding brand writing (via web search)",
 "topic": "EN empty praise adjectives (marketing-specific)"
}

{
 "rule": "LLM prose over-hedges: \"can\", \"may\", \"potentially\", \"often\", \"in many cases\", \"it depends\", stacked 2-3 per sentence. Marketing copy hedging its own product reads as evasive and machine-flavored. Rule: flag sentences with 2+ hedge tokens; replace with a definite claim or a genuine conditional (\"if X, then Y\").",
 "source": "Synthesis of detection-vendor and writing-advice sources (Wired, Guardian, GPTZero blog) from web search",
 "topic": "EN hedging overuse"
}

{
 "rule": "LLM paragraphs are metronomic: near-uniform sentence lengths (low burstiness), every paragraph 3-4 sentences, every section the same shape. Human writing is bursty. Checkable: compute sentence-length standard deviation; stdev < ~5 words across a page of 20+ sentences = flag. Also flag every paragraph ending with a tidy wrap-up sentence.",
 "source": "Bengali/EN detection literature: burstiness and uniform rhythm are classifier features (BanglaBERT/mBERT detection papers, via web search); GPTZero burstiness metric",
 "topic": "Structural tell: uniform sentence rhythm and symmetric paragraph shapes"
}

{
 "rule": "AI Bangla reads as 'অনুবাদ ঘেঁষা' (translation-flavored): English idioms rendered literally, English clause order (long attributive modifiers before the noun), calqued compounds. Concrete calque examples to flag: \"গভীর ডাইভ/গভীরে ডুব দেওয়া\" (deep dive), \"গেম চেঞ্জার\", \"সিমলেস অভিজ্ঞতা\"-style transliterations, \"আপনার জার্নি শুরু করুন\" (journey), \"লক আনলক\" (unlock). Rule: prefer existing Bangla idioms and natural collocations; flag English compound calques that have established Bangla equivalents.",
 "source": "Bengali tech blogs and commentary on AI Bangla ('অনুবাদ ঘেঁষা', stiff register) via web search; Bangla LLM-detection papers noting unnatural collocations",
 "topic": "BN literal English calques (অনুবাদ ঘেঁষা)"
}

{
 "rule": "Mixing Sadhu verb forms (করিতেছি, হইয়াছে, করিয়াছেন) with Cholito forms (করছি, হয়েছে) in the same text — or the 19th-century 'মিশ্র রীতি' (Cholito nouns + Sadhu verbs) — is a non-standard marker that LLM Bangla drifts into, giving an over-formal bookish register. Rule: all finite verbs must follow চলিত রীতি consistently; flag any সাধু form (regex: িতেছ, িয়াছ, িতেন endings).",
 "source": "bn.wikipedia 'সাধু ভাষা ও চলিত ভাষা'; Bangla Academy grammar (ব্যাকরণ) and বানান রীতি pages, banan.banglaacademy.gov.bd",
 "topic": "BN সাধু-চলিত mixing (register break)"
}

{
 "rule": "Bangla AI slop leans on formulaic essay connectors: অতএব, ফলস্বরূপ, এছাড়াও, তবে, সুতরাং, উল্লেখ্য যে, বিশেষভাবে উল্লেখযোগ্য. Native marketing copy uses far fewer explicit connectors. Checkable: connector count per page above ~1 per 200 words = flag; never open consecutive paragraphs with the same connector.",
 "source": "Bengali commentary on AI Bangla (repetitive connectors তবে/এছাড়াও/অতএব) via web search; mirrors EN connector-chain tell",
 "topic": "BN connector-word chains"
}

{
 "rule": "Flag Bangla equivalents of the EN slop lexicon: \"বর্তমান বিশ্বে/বর্তমান যুগে\" (in today's world), \"দ্রুতগতির বিশ্বে\", \"গুরুত্বপূর্ণ ভূমিকা পালন করে\" (plays an important role), \"নতুন দিগন্ত উন্মোচন\" (unveiling new horizons), \"অভূতপূর্ব অগ্রগতি\", \"সমৃদ্ধ ঐতিহ্যের ধারাবাহিকতা\" (tapestry-equivalent), \"মসৃণ অভিজ্ঞতা\" (seamless). These are direct calques of the EN AI-slop phrases and read as machine-generated to native readers. Rule: regex blocklist + require concrete specifics instead.",
 "source": "Bengali commentary on unnatural AI Bangla via web search; direct calque mapping from EN slop lexicon (Guardian/GPTZero lists)",
 "topic": "BN stock slop phrases (direct Bangla equivalents of EN tells)"
}

{
 "rule": "LLM Bangla flatly deploys or misapplies বাগধারা/প্রবাদ (idioms/proverbs) — used as decoration, out of register, or slightly wrong — while human writing uses them idiosyncratically. Rule: every idiom used must fit the literal context and register; a page stuffed with one proverb per section = flag. Prefer plain accurate phrasing over forced idiom.",
 "source": "Bengali-language commentary on AI text (misuse/flat delivery of বাগধারা/প্রবাদ listed as recurring complaint) via web search",
 "topic": "BN idiom/proverb misuse (বাগধারা)"
}

{
 "rule": "AI Bangla produces unnatural word combinations (collocations) and slips with postpositions (অব্যয়/কারক) and verb aspect that native writers never make. Checkable: spot-check list of common errors — wrong ণ/ন and ষ/স spellings (ণ-ত্ব, ষ-ত্ব বিধান), হৃদয়/সৃষ্টি-class spelling slips, postposition mismatches. Rule: run a Bangla spelling/grammar pass against Bangla Academy প্রমিত rules before ship.",
 "source": "Bangla Academy বানান রীতি (banan.banglaacademy.gov.bd); প্রমিত বাংলা বানান (মোফাজ্জল হায়দার চৌধুরী); detection papers noting grammatical slips",
 "topic": "BN unnatural collocations and postposition/aspect errors"
}

{
 "rule": "Because single markers are weak evidence, score slop as density: (a) blocklist phrase count, (b) AI-lexicon count per 500 words, (c) structural counts (tricolons, \"not just...but\", em dashes, connectors) per page, (d) sentence-length variance. Suggested gate: any single hard blocklist hit on an opener/closer = fix; combined score above threshold = rewrite. Note: generic detectors (GPTZero, ZeroGPT) are unreliable for Bengali, so the gate must be rule-based + prompt-based for Bangla, not detector-API-based.",
 "source": "Vocabulary.com/writing-advice consensus that density+formula signals AI; Bengali detection papers showing generic detectors fail on Bengali while fine-tuned local models reach 85-95% (via web search)",
 "topic": "Machine-checkability: density thresholds, not single hits"
}

# RESULT 2

## Summary
Compiled 20 concrete, checkable copywriting-craft rules across audience research, sentence/claim discipline, specificity vs. weasel words, benefit framing, fact-checking/substantiation (FTC-backed), social-proof honesty, CTA clarity, reading level, headline scoring (4 U's), and an AI-slop phrase blocklist — each phrased so a validator (lexicon scans, regex, fact-sheet cross-checks) or a prompt-based review gate can verify an agent's own draft. Sources: Copyhackers, Copyblogger, Enchanting Marketing, AWAI/HubSpot headline rubrics, Nielsen Norman Group/plainlanguage.gov readability research, Unbounce CTA guidance, Wikipedia AI-writing-signs catalog, and FTC Endorsement Guides (16 CFR 255, 2023) / Reviews Rule (16 CFR 465, 2024).

## Findings
{
 "rule": "Before writing any page copy, the agent must produce (or be given) an audience snapshot: who the reader is, their top pain point, their desired outcome, and their stage of awareness. A draft with no audience record attached fails the gate. Checkable as: copy file must reference a message/audience doc (message-mining doc listing verbatim customer phrases, objections, desires mined from reviews/interviews/forums).",
 "source": "Copyhackers (Joanna Wiebe) voice-of-customer methodology — copyhackers.com; CXL talks on VoC data as foundation of conversion copywriting",
 "topic": "Audience-before-writing"
}

{
 "rule": "Headlines and body benefits must be built from verbatim or near-verbatim customer language (review quotes, testimonial phrases, survey answers), not invented marketing vocabulary. Checkable as: each headline/hero benefit maps to a quoted source phrase in the message-mining doc; untraceable 'creative' claims get flagged.",
 "source": "Copyhackers message-mining / swipe-file guides (copyhackers.com)",
 "topic": "Voice-of-customer language reuse"
}

{
 "rule": "Flag sentences above a length threshold (e.g. >25 words) and paragraphs above 3-4 sentences; each sentence should advance exactly one idea. Treat as a soft rule: short is the default, longer sentences allowed only when conversational flow demands it — but any sentence containing two separate claims joined by 'and' that could be split is flagged for review.",
 "source": "Copyhackers 'Copywriting Rules' (copyhackers.com/blog/copywriting-rules) — one-idea-per-sentence is a guideline, clarity is the hard rule; Copyblogger Copywriting 101",
 "topic": "One idea per sentence"
}

{
 "rule": "Every feature claim ('24/7 support', 'AI-powered', 'responsive design') must be paired with or framed as a customer outcome ('fix a flat tire at 2am without leaving your driveway'). Checkable as: scan feature-noun sentences; each must contain an outcome clause or sit adjacent to one. Features are facts; customers buy outcomes.",
 "source": "Copyhackers benefit-driven storytelling (copyhackers.com/blog/benefit-driven-story); Amazon Ads creative guidelines (ads.amazon.com/library/guidelines/creative-guidelines)",
 "topic": "Benefit-before-feature"
}

{
 "rule": "Detect vague quantifiers and hedge attributions: 'many', 'several', 'some say', 'experts say', 'studies show', 'it is believed', 'up to X%', 'industry-leading', 'world-class'. Each occurrence must either be replaced with a concrete, source-backed number/fact or deleted. Checkable as a regex/lexicon scan with a blocklist (many, several, experts say, studies show, some argue, virtually, remarkably) plus a requirement that every numeric claim cite a source in the copy's fact sheet.",
 "source": "Wikipedia 'Weasel word'; Grammarly weasel-words guide; Copyhackers on specificity ('Save 50%' vs 'Save up to 50%'); Verba detection checklist",
 "topic": "Specificity over vague claims (weasel-word ban)"
}

{
 "rule": "Concrete transformations beat abstractions: 'Offering the best customer service' -> 'Helping small business owners get paid in 24 hours'. Checkable as: flag abstract quality nouns in claims (best, quality, excellence, service, solution, innovation) that lack a concrete noun/number/verb within the same sentence.",
 "source": "Henneke Duistermaat, Enchanting Marketing (enchantingmarketing.com/copywriting-tips)",
 "topic": "Concrete nouns over abstractions"
}

{
 "rule": "Every statistic, percentage, date, or named-entity fact in copy must have an entry in a fact sheet with a real, verifiable source (URL, document, client record). If no source exists, the number is deleted — the agent never invents, extrapolates, or 'rounds up' figures. Checkable as: extract all numerals from the draft; each must appear in the approved fact sheet; numerals absent from the fact sheet fail the build.",
 "source": "FTC advertising substantiation doctrine — advertisers need competent and reliable evidence before making objective claims (FTC.gov Business Guidance); FTC Endorsement Guides 16 CFR Part 255 (2023 update, 88 FR 40949)",
 "topic": "No fabricated facts, numbers, or statistics"
}

{
 "rule": "'500+ clients', '10 years of experience', 'trusted by 1,000 businesses' — each social-proof count must trace to a real internal record (client list, invoice count, review platform). Checkable as: every 'N+' / 'N clients' / 'N projects' claim in copy must match the count in a referenced data file; mismatch or missing file = fail.",
 "source": "FTC Rule on the Use of Consumer Reviews and Testimonials, 16 CFR Part 465 (2024) — civil penalties for fake reviews and fabricated indicators; FTC Endorsement Guides",
 "topic": "No invented social proof counts"
}

{
 "rule": "Testimonials must be real: attributed to an identifiable real person with their consent, and any material connection to the business (payment, free product, employment, family, affiliate relationship) must be disclosed clearly and conspicuously in the same medium. Never write a testimonial on the customer's behalf. Checkable as: each testimonial has (a) a consent/source record, (b) a disclosure note if incentivized; unattributed or stock-photo testimonials fail.",
 "source": "FTC Endorsement Guides 2023 update, 16 CFR Part 255 — material connection disclosure, clear-and-conspicuous standard, fake review prohibitions (ftc.gov)",
 "topic": "Social-proof honesty (testimonials)"
}

{
 "rule": "If a testimonial or case study implies a performance result ('doubled revenue in 3 months'), the advertiser needs competent and reliable evidence for the implied claim, not just the quote. Checkable as: result-claims inside testimonials are extracted and run through the same fact-checking gate as body claims.",
 "source": "FTC Endorsement Guides 2023 — the endorsement itself can convey a deceptive performance claim requiring substantiation (ftc.gov; 88 FR 40949)",
 "topic": "Testimonial performance claims"
}

{
 "rule": "Each page has exactly one primary CTA; competing secondary actions must be visually and structurally subordinate. CTA copy is verb-first, benefit-second, first-person where natural ('Get my free quote', 'Start my 14-day trial'), never bare vague labels ('Submit', 'Click here', 'Learn more' as the only CTA). Checkable as: parse CTA/button strings; must start with an imperative verb, must not be a member of a vague-label blocklist (Submit, Click here, OK, Learn more alone); count of primary CTAs per page = 1.",
 "source": "Unbounce CTA guides (unbounce.com) — action verbs, first-person phrasing tests, anxiety-reducing microcopy; HubSpot/WordStream 'one page one goal'; NN/g button-label research",
 "topic": "CTA clarity — one primary action"
}

{
 "rule": "Urgency and scarcity ('Limited time', 'Only 5 spots left', countdown) are permitted only when a real deadline/limit exists and is recorded in the fact sheet. False urgency is a deceptive practice. Checkable as: urgency-phrase lexicon scan; each hit must map to a real constraint record or be removed.",
 "source": "AWAI 4 U's guidance — 'authenticity matters, false urgency destroys trust' (awai.com); FTC deception policy (ftc.gov)",
 "topic": "CTA urgency must be real"
}

{
 "rule": "Target roughly grade 6-8 reading level for general-audience web copy (grade 5-6 for health; grade 8 max for government-adjacent content), measured via Flesch-Kincaid or equivalent — but treat the score as a screening flag, not a pass/fail: simplicity of expression, short sentences, active voice, and scannability outrank the formula. Checkable as: compute readability score per page; flag pages above threshold for rewrite rather than auto-fail.",
 "source": "Nielsen Norman Group 'Keep Web Content Short' and plain-language research (nngroup.com); plainlanguage.gov (Plain Writing Act 2010); CDC Clear Communication Index",
 "topic": "Reading-level matching"
}

{
 "rule": "Front-load the key message (inverted pyramid), chunk with meaningful headings, bold sparingly, use bulleted lists for parallel items, keep active voice, address the reader as 'you'. Checkable as: heading text must be informative (not 'Introduction'/'Our Services' alone where a benefit phrasing is possible); passive-voice ratio flagged above threshold.",
 "source": "Nielsen Norman Group web usability research (nngroup.com); usablecontent.com plain-language checklist",
 "topic": "Scannable structure"
}

{
 "rule": "Score each headline against the 4 U's — Useful, Urgent, Unique, Ultra-specific — and require a minimum total (e.g. >=9/16) or a rewrite; 'Clear, Concise, Compelling, Credible' (4 C's) is the modernized variant. Do not force all four elements into one headline (clumsy). Ultra-specificity is the most machine-checkable: a headline with a concrete number, named outcome, or specific audience scores higher than a vague promise. Checkable as: headline must contain at least one specific element (number, audience noun, concrete outcome verb) — pure abstract hype headlines ('Transform your business today') fail.",
 "source": "Michael Masterson / AWAI 4 U's formula (awai.com); HubSpot 4 C's adaptation with scoring rubric (hubspot.com)",
 "topic": "Headline quality — 4 U's rubric"
}

{
 "rule": "Maintain an explicit blocklist of content-free AI-tell phrases and fail any draft containing them: 'in today's fast-paced world', 'in the ever-evolving landscape of', 'in the digital age', 'look no further', 'game-changer', 'revolutionize', 'unlock', 'unleash', 'elevate your', 'seamless', 'cutting-edge', 'delve into', 'navigate the landscape', 'tapestry', 'testament to', 'beacon of', 'double-edged sword', 'don't miss out', 'the secret to', 'it's not just X, it's Y', 'whether you're a ... or ...', 'in conclusion', 'ultimately'. Checkable as: lexicon scan (word-boundary regex, case-insensitive) against the blocklist; hits must be rewritten with subject-specific content.",
 "source": "Wikipedia 'Signs of AI writing' catalog; editor banned-phrase lists (Copyblogger, ProWritingAid, freelance editing guides)",
 "topic": "AI-slop phrase blocklist (robotic-copy ban)"
}

{
 "rule": "Flag mechanical AI patterns: rule-of-three triads in consecutive sentences ('innovation, efficiency, and growth' style), every paragraph the same length, excessive em-dashes, uniform sentence rhythm, and generic superlatives without referents ('the best', 'premier', 'world-class' with no comparison basis). Checkable as: n-gram/rhythm heuristics + superlative-without-basis scan; these are review flags, not hard fails.",
 "source": "Wikipedia 'Signs of AI writing'; Copyhackers on vague superlatives; UX Collective on weasel-word marketing",
 "topic": "Structural AI tells"
}

{
 "rule": "Distinguish puffery from objective claims: subjective non-measurable hype ('delicious', 'beautiful design', 'we love what we do') is legally tolerated, but any objective, measurable claim ('fastest', 'cheapest', '50% faster', 'clinically proven', 'certified') requires substantiation before it ships. Checkable as: a superlative/comparative lexicon ('fastest', 'best', 'cheapest', 'leading', 'certified', 'clinically proven', 'guaranteed') where each hit is either (a) marked as subjective opinion or (b) supplied with a substantiation source; unmarked objective claims fail.",
 "source": "FTC deception policy statement and substantiation doctrine — objective claims need competent and reliable evidence, puffery does not (ftc.gov Business Guidance)",
 "topic": "Puffery vs. measurable claim"
}

{
 "rule": "CTA and landing-page copy must match the traffic source's promise (message match): the headline a visitor clicked must be echoed on the page. Checkable as: ad/campaign phrase appears (or is paraphrased) in the page H1/hero; mismatch flagged.",
 "source": "Unbounce CTA and message-match guidance (unbounce.com)",
 "topic": "CTA message match"
}

{
 "rule": "Copy that promises specific outcomes ('get paid in 24 hours', 'pass the exam') must either be true as stated or hedged to what is actually typical; the 2023 Guides removed the old 'typical results' disclaimer loophole — a misleading implied performance claim is deceptive regardless of a disclaimer. Checkable as: outcome promises are extracted and verified against the fact sheet; unsupported outcome promises fail.",
 "source": "FTC Endorsement Guides 2023 update — removal of 'clearly and conspicuously' typical-results disclaimer safe harbor (ftc.gov; 88 FR 40949)",
 "topic": "Results claims — no disclaimers-as-loophole"
}

# RESULT 3

## Summary
BuildPilot gates follow a strict, fully observable pattern: an ALL-CAPS gate doc in skill/sps/ (PLAN-GATE.md is the structural template: The Gate with a STOP step, required contents, abort conditions, exceptions, memory), law registration as a numbered '**Bold Name.**' entry in SKILL.md's inlined hard-law core, machine enforcement via literal marker strings grepped by framework/sps2/tools/check_laws.py (inline VIOLATIONS blocks or standalone stdlib tools like check_product_proof.py, with seo_audit.py's advisory/deployment fail-closed mode as the audit-tool model), and wiring into CI (sps-ci.yml), the handoff battery (HANDOFF-CHECKPOINT steps 2/4b), the law-log/regression loop (sps-lawlog.sh + gen_law_test.py with --approved-by human gate), and the SKILL-ROUTER domain table. For a copy-quality gate specifically: sps-seo covers only technical SEO (metadata, canonical, sitemaps, JSON-LD, CWV) and has zero copy-quality content; DESIGN-GATE.md already owns marketing copy STRUCTURE/conversion laws (8 copy laws + anti-slop ban list, 4 of them machine-checked) — so a new COPY-GATE.md should cross-reference both and own only the missing layer: language quality, Bangla standard (প্রমিত বাংলা/চলিত রীতি), tone/humanization. Reuse: DESIGN-GATE copy laws, seo_audit.py, SECTION-DOD items 13-16 as the DoD anchor, fresh-context review + adversarial second opinion for prompt-only rules, MISTAKE-PROMOTION for repeat failures. Add: one SKILL.md hard law, skill/sps/COPY-GATE.md, a check_laws.py marker block plus a standalone copy checker (Unicode Bangla range, banned AI-slop phrase lists, mixed-script detection) with advisory/deployment modes, a SKILL-ROUTER row update demoting `copywriting` to enhancer, and the check_emoji.py exemption pattern for any text-scanning checker.

## Findings
{
 "rule": "A new gate lives as an ALL-CAPS-KEBAB.md file in skill/sps/ (e.g. skill/sps/COPY-GATE.md), alongside PLAN-GATE.md and DESIGN-GATE.md. PLAN-GATE.md is the structural template: (1) title '# <Name> Gate (hard law)', (2) '## The Gate' — numbered steps ending in a STOP point ('**Stop.** No code... until the user approves'), (3) '## What the plan must contain' (required contents), (4) '## Abort conditions' (numbered fail-closed triggers), (5) '## Exceptions' (Tier 1 quick-fix carve-out via APPROVAL-PACKETS.md, read-only Q&A), (6) '## Memory' (what to write to .sps/handoff.md + .sps/changelog-sps.md after approval). DESIGN-GATE.md shows the variant for evergreen law docs: '# <Name> Gate (portable source of truth)' + 'Specialist skills are enhancers only' clause + concrete checkable rules grouped under bold sub-headings.",
 "source": "skill/sps/PLAN-GATE.md; skill/sps/DESIGN-GATE.md",
 "topic": "Gate doc pattern: file naming and structure"
}

{
 "rule": "Hard laws are registered in skill/sps/SKILL.md 'Inlined Hard-Law Core' as a numbered list item in bold-name format: '**<Law Name>.** <one-line rule> ([DOC-NAME.md](DOC-NAME.md))'. check_laws.py enforces the core by literally searching SKILL.md for the string '**{law}' for each registered law name ('Task Queue', 'Write Confinement', 'Tool Consent', etc.) — so a new COPY law's bold name must exactly match the string the checker greps for, and the checker's law tuple must be extended in the same commit or the law is not actually registered.",
 "source": "skill/sps/SKILL.md lines 24-48; framework/sps2/tools/check_laws.py lines 109-117",
 "topic": "Law registration in SKILL.md hard-law core"
}

{
 "rule": "Gate docs are machine-checked via literal marker strings: check_laws.py reads the doc and asserts each marker text appears (for DESIGN-GATE.md it requires 'Copy laws', 'Above-the-fold sells', 'Benefits before features', 'No padded copy', 'tabular-nums', 'Anti-slop ban list', etc.). A COPY-GATE.md must ship with (a) a defined marker list in check_laws.py — pick stable, load-bearing phrases, one per law, since deleting a law from the doc must trip the checker; and (b) for SKILL-ROUTER wiring, literal strings the router check requires ('Tool Consent gate first', 'CONTEXT-BUDGET.md' are the current examples).",
 "source": "framework/sps2/tools/check_laws.py lines 100-107, 143-156",
 "topic": "Marker format for machine checks"
}

{
 "rule": "Two validator patterns exist, both stdlib-only, project-local, no network: (A) INLINE BLOCK in framework/sps2/tools/check_laws.py — code appends to the module-global VIOLATIONS list via v(f'check-id: target: detail'), violations print one per line on stderr, exit 0 all-hold / exit 1 violations, summary line '== LAW CHECK: N violation(s) =='. (B) STANDALONE TOOL in framework/sps2/tools/ (model: check_product_proof.py) — module-level CHECK_ID constant, same output/exit conventions ('Format and exit convention mirror check_generated_tests.py / check_laws.py'), invoked separately. seo_audit.py adds the two-mode pattern a copy auditor should copy: --mode advisory (report only, always exit 0, for development iteration) vs --mode deployment (fail-closed, exit 1 on any CRITICAL, the actual gate).",
 "source": "framework/sps2/tools/check_laws.py; framework/sps2/tools/check_product_proof.py header; framework/sps2/tools/seo_audit.py; skill/sps-seo/SKILL.md 'Fail-Closed Deployment Law'",
 "topic": "Validator hook-in: where checks run"
}

{
 "rule": "A new validator must be wired into: (1) CI — .github/workflows/sps-ci.yml runs check_laws.py (lines 35 and 310) and check_docs_drift.py (line 38); weekly-audit.yml line 70 also runs check_laws.py; (2) the handoff battery — HANDOFF-CHECKPOINT.md step 2 ('full local battery') and step 4b (agent runs check_laws.py + 'validators affected by the change' and ATTACHES output); (3) the law-log loop — scripts/sps-lawlog.sh wraps check_laws.py and logs each FAIL to .sps/law-rejections.jsonl, and after >=2 rejections of the same (check_id, target_file) gen_law_test.py proposes a subprocess-based regression test (copies repo to tempdir, replants violation, asserts checker FAILs with expected check id) which only writes with --approved-by (human gate, LESSONS.md).",
 "source": ".github/workflows/sps-ci.yml; .github/workflows/weekly-audit.yml; skill/sps/HANDOFF-CHECKPOINT.md steps 2/4b; framework/sps2/tools/gen_law_test.py header; skill/sps/SKILL.md Law Log mode",
 "topic": "CI and checkpoint wiring"
}

{
 "rule": "SKILL-ROUTER.md has a domain table (Domain | Primary | Secondary | Fallback if missing). Current row: 'Content / copy | copywriting (SPS drafts, user edits) | fact-check | copy in content-model.md'. A COPY gate follows the DESIGN-GATE precedent: SPS-owned gate doc becomes the source of truth, external specialist skills are 'enhancers only' — 'If a specialist skill is missing, still enforce this file.' The router row must be updated (primary = COPY-GATE.md, copywriting demoted to enhancer), and INSTALL-PROFILES.md / SKILL-GOVERNANCE.md list the same copywriting skill and need the matching edit. check_docs_drift.py additionally requires any /sps subcommand mentioned in docs to appear in SKILL.md Modes sections or METHOD-CARD, and any referenced script path to exist.",
 "source": "skill/sps/SKILL-ROUTER.md line 42-48, 134-137; skill/sps/DESIGN-GATE.md header; skill/sps/INSTALL-PROFILES.md line 55; skill/sps/SKILL-GOVERNANCE.md line 23; framework/sps2/tools/check_docs_drift.py",
 "topic": "Router and skill-governance registration"
}

{
 "rule": "Section comment markers are the only in-code marker format: '<!-- SPS:SECTION name=\"...\" -->', '<!-- SPS:CMS_FIELDS [...] -->', '<!-- SPS:READS_FROM ... -->', closed by '<!-- SPS:ENDSECTION -->' (// variants for TSX). SECTION-DOD item 18 requires them present. A copy gate that needs per-section copy evidence should hook into the DoD list (SECTION-DOD section 4 'Content & CMS Copy', items 13-16: SPS drafts/user edits, content inventory in content-model.md, copy loaded through CMS layer, empty/loading/error states) by adding a numbered item there rather than inventing a new marker family; check_laws.py already greps SECTION-DOD.md for audit-gap marker strings, so a new DoD item gets a marker in that list too.",
 "source": "skill/sps/SECTION-DOD.md sections 1 and 4, item 18; framework/sps2/tools/check_laws.py lines 128-141",
 "topic": "Section marker format (in shipped code)"
}

{
 "rule": "sps-seo is a TECHNICAL SEO standard only: metadata generation/validation (title/description length, duplication, never invent facts not in content), canonical law, robots.txt/sitemap.xml governance, schema.org JSON-LD (LocalBusiness/Product/Article/hreflang), heading hierarchy (single h1, no skips), link audit, image alt/filename SEO, Core Web Vitals, and a 19-dimension fail-closed deployment audit (seo_audit.py). It contains NOTHING about marketing copy quality, tone, humanization, language style, or Bangla — grep for copy/tone/readability/slop across sps-seo docs and seo_audit.py returns zero hits. The copy gate complements it: sps-seo owns 'is the content technically findable and truthful', the copy gate owns 'is the content well-written, human, and in standard Bangla'. The only overlap point is sps-seo's anti-hallucination rule 'metadata generated from real page content; never invent facts not present in the content' — the copy gate should reference, not restate, it.",
 "source": "skill/sps-seo/SKILL.md; skill/sps-seo/METHOD-CARD.md; framework/sps2/tools/seo_audit.py (grep: no copy/tone/readability/slop hits)",
 "topic": "What sps-seo already covers (do not duplicate)"
}

{
 "rule": "DESIGN-GATE.md already contains a '## Copy laws (marketing/landing copy)' section with 8 laws (above-the-fold sells in <=2 lines; one target buyer; benefits before features; social proof next to claims; handle objections before the CTA; CTAs start with action verb + outcome; scannable short sentences; no padded copy/generic openers) plus an anti-slop ban list (fake counters/review stars/invented metrics, Lorem ipsum, vague hero text, 'Made with AI' badges). These four markers ('Copy laws', 'Above-the-fold sells', 'Benefits before features', 'No padded copy') are already machine-enforced in check_laws.py. A COPY-GATE must NOT restate these — it should cross-reference DESIGN-GATE copy laws as the structure/conversion layer and cover only what they lack: language quality/grammar standard, Bangla-specific rules, tone/humanization, and AI-slop language patterns (as opposed to DESIGN-GATE's AI-slop visual patterns).",
 "source": "skill/sps/DESIGN-GATE.md lines 124-155; framework/sps2/tools/check_laws.py lines 143-156",
 "topic": "What DESIGN-GATE already covers for copy (do not duplicate)"
}

{
 "rule": "Copy delivery is already governed by: SECTION-DOD items 13-16 (drafted copy, content-model.md inventory, CMS-loaded copy, state handling); SKILL-ROUTER 'Content / copy' row (copywriting skill, fallback = copy in content-model.md); SUBAGENT-PLAYBOOK content-agent lane ('copy drafting (SPS voice), meta, structured data, alt text' -> content-model.md + copy files); sps-cms MULTI-LANGUAGE-I18N.md supports Bengali (Bangla) as a first-class CMS translation language (English -> Bangla, Gemini Flash auto-translation). None of these address writing QUALITY or the Bangla standard (প্রমিত বাংলা / চলিত রীতি) — the i18n doc is transport (fields, sync), not style. The copy gate should declare itself the quality layer on top of the existing content-agent lane and CMS i18n pipeline.",
 "source": "skill/sps/SECTION-DOD.md items 13-16; skill/sps/SKILL-ROUTER.md line 48; skill/sps/SUBAGENT-PLAYBOOK.md line 12; skill/sps-cms/MULTI-LANGUAGE-I18N.md line 21; skill/sps-cms/SKILL.md line 46",
 "topic": "Existing content pipeline the copy gate plugs into"
}

{
 "rule": "REUSE, do not add: (1) DESIGN-GATE copy laws + anti-slop ban list stay put and keep their existing check_laws.py markers — the copy gate references them; (2) seo_audit.py stays the technical gate — run it unchanged in deployment mode; (3) SECTION-DOD items 13-16 are the DoD anchor — extend item 13 or add one item ('copy passes the copy gate') rather than a parallel checklist; (4) non-machine-checkable Bangla rules (grammar, naturalness, প্রমিত vs চলিত usage) are prompt-based laws in COPY-GATE.md enforced by the existing human loops: SECTION-DOD #52 fresh-context review by an agent that did not author it, HANDOFF-CHECKPOINT step 4 adversarial second opinion, and the MISTAKE-PROMOTION/LESSONS loop for repeat failures; (5) the Tier 1 quick-fix exception in PLAN-GATE already covers 'copy edit' — the copy gate must define whether a copy-only change needs the full gate or just the 5-line packet.",
 "source": "skill/sps/DESIGN-GATE.md; framework/sps2/tools/seo_audit.py; skill/sps/SECTION-DOD.md items 13-16, 52; skill/sps/HANDOFF-CHECKPOINT.md step 4; skill/sps/PLAN-GATE.md Exceptions",
 "topic": "Which laws/checkers to REUSE for a COPY gate"
}

{
 "rule": "ADD: (1) one numbered hard law in SKILL.md core in the '**<Name>.**' bold format (e.g. '**Copy Quality Gate.**') + its name added to the hard-law tuple in check_laws.py; (2) skill/sps/COPY-GATE.md following the DESIGN-GATE 'portable source of truth' structure with a defined marker list; (3) a marker-list block in check_laws.py asserting those markers, plus structural checks that ARE machine-checkable: Bangla Unicode range validation (U+0980-U+09FF present when lang=bn declared), mixed-script contamination, banned AI-slop phrase lists (English + Bangla equivalents of 'In today's fast-paced world'), Lorem ipsum, invented-metric patterns — as a standalone tool (check_product_proof.py pattern) with advisory/deployment modes (seo_audit.py pattern) so it can gate without false-positive-blocking during drafting; (4) SKILL-ROUTER row update (copywriting becomes enhancer); (5) a regression-test path via sps-lawlog.sh + gen_law_test.py once the checker has real rejections. Caution: check_laws.py currently has a latent bug in its FILE-SPLITTING block (lines 120-126 reference an out-of-scope `law` variable) and a mislabeled comment ('LEGAL-COMPLIANCE' over the LESSONS.md block) — new blocks should not copy those patterns.",
 "source": "skill/sps/SKILL.md; framework/sps2/tools/check_laws.py lines 109-126, 168; skill/sps/SKILL-ROUTER.md; skill/sps/SKILL.md Law Log mode",
 "topic": "Which laws/checkers to ADD for a COPY gate"
}

{
 "rule": "If the copy gate produces user-facing gate messages (a pass/fail verdict shown to the user), and the project opts in with 'language: plain' in .sps/agent.md, the message must render via a plain template in framework/sps2/templates/plain-gates/ through plain_language.py render — 8th-grade vocabulary, one bolded 'What you're deciding:' line, {placeholders} filled. Unknown gates fail closed with PLAIN_GATE_MISSING (stderr, exit 1). A copy gate that only feeds section approval packets (which already have a plain template) inherits this for free; a NEW standalone gate message type would need its own template registered in the gate->template mapping table in PLAIN-LANGUAGE.md.",
 "source": "skill/sps/PLAIN-LANGUAGE.md; framework/sps2/tools/plain_language.py",
 "topic": "Plain-language mode interaction"
}

{
 "rule": "Bangla copy rules split cleanly: machine-checkable — script detection via Unicode Bangla block, banned-phrase lists, placeholder/filler detection, mixed-script and encoding checks, consistency of terminology across sections (grep-level); prompt-only — বাংলা একাডেমি প্রমিত বাংলা grammar compliance, চলিত রীতি register, naturalness/humanization judgments. The repo precedent for prompt-only rules is that they live in the gate doc as concrete numbered laws and get enforced by fresh-context review (SECTION-DOD #52) and the adversarial second opinion (HANDOFF-CHECKPOINT step 4), with repeat-failure promotion through MISTAKE-PROMOTION.md. Note: check_emoji.py demonstrates the exemption pattern any text-scanning checker needs — files that legitimately CONTAIN banned strings (the checker itself, the rule doc) must be explicitly exempted or the checker self-trips.",
 "source": "framework/sps2/tools/check_emoji.py (exemption pattern); skill/sps/SECTION-DOD.md item 52; skill/sps/HANDOFF-CHECKPOINT.md step 4; skill/sps/MISTAKE-PROMOTION.md",
 "topic": "Machine-checkability boundary for Bangla rules"
}

# RESULT 4

## Summary
Prior art for a BuildPilot humanized-copywriting gate: (1) Newsroom/editorial anti-AI guidance — AP Stylebook's 2024 AI chapter bans publishing unedited generative-AI content and requires attribution/verification; editors across newsrooms maintain banned-phrase lists ('delve into', 'in the ever-evolving landscape of', 'it's worth noting', 'testament to', 'tapestry'); the Princeton 'Delve' study (arXiv:2507.07510) gives the 'excess vocabulary' method — words statistically over-represented in LLM output — which is exactly how BuildPilot should build its own slop wordlists. (2) Bangladeshi media style — the authoritative public baseline is বাংলা একাডেমি's 'বানানের নিয়ম' (1976/2002/2013, free PDF) and 'প্রমিত বাংলা বানান অভিধান' (2018): চলিত রীতি only (no সাধু forms like তাহার/করিয়াছে), চন্দ্রবিন্দু and হসন্ত-বর্জন rules, bn-BD spellings (শ্রেণি, কারও, কোনো); BBC Bangla's ভাষা নীতিমালা and Prothom Alo practice follow the Academy standard plus transliteration rules but are internal/semi-public. (3) Bangla AI-detection research — arXiv:2502.19286 (41k Bangla sentences, RF on lexical+syntactic+semantic features, 91%) and HC-Bangla (18k sentences, ~90%+) identify the markers Bangla copy must avoid: uniform sentence length (low burstiness), low lexical diversity, GPT-typical function-word/punctuation patterns; GPTZero is unreliable for Bangla, Copyleaks claims Bengali support — so the gate should be statistical checks + prompt rubric + mandatory human pass, not a detector. (4) Localization guidance — Google's TLC Bengali style guide and Bengali (India) reviewer guide (public PDFs on storage.googleapis.com/transedpublic/) and Microsoft's ben-BD guide give checkable rules: দাঁড়ি '।' sentence ending, Bengali numerals ০১২৩৪৫৬৭৮৯ for bn-BD, আপনি as default for user-facing text (তুমি acceptable for friendly brand voice, decided per site, never mixed), keep product names in English, transliteration glossary. (5) Open-source anti-slop tooling — sam-paech/antislop-sampler (Apache-2.0, ICLR 2026 paper) is the most directly borrowable: slop_phrases.json + slop_words.json + slop_regexes.txt with phrase-weight entries (['testament to', 0.5]) and regex bans for structural clichés like 'not X, but Y'; it auto-builds lists from LLM-vs-human frequency ratios and advises curating your own per language. Key design lesson: pure wordlists are evadable (paraphrase attacks drop detector accuracy to ~5%) and false-positive-prone, so the BuildPilot gate should layer a wordlist/regex validator + burstiness/punctuation-variance checks + a prompt-based rubric + the SPS human manual check.

## Findings
{
 "rule": "AP Stylebook's 2024 AI chapter sets the machine-checkable floor: 'Avoid using generative AI tools to create publishable content'; AI output must never be presented as original reporter work; attribute and independently verify any AI-assisted research/transcription/translation. Borrow as a BuildPilot LAW: copy shipped to a client site must be human-edited, and any AI-assisted draft must pass an explicit humanization/edit pass before gate approval.",
 "source": "https://www.apstylebook.com/stylebook/entries/artificial-intelligence ; https://www.poynter.org/reporting-editing/2024/ap-stylebook-adds-guidance-on-generative-ai-for-journalists/ ; https://www.ap.org/ai/",
 "topic": "Newsroom AI-use policy (AP)"
}

{
 "rule": "Editors' publicly reported banned-phrase sets target: 'delve into', 'in the ever-evolving landscape/world of', 'it's worth noting that', 'it's important to note', 'navigate the complexities of', 'unlock the potential of', 'testament to', 'tapestry'. Borrow as seed entries for a BuildPilot ENGLISH_SLOP_PHRASES wordlist checked by check_laws.py (exact-match + regex over shipped copy).",
 "source": "Poynter/CJR/r/editors summaries surfaced via web search; https://www.poynter.org/reporting-editing/2024/ap-stylebook-adds-guidance-on-generative-ai-for-journalists/",
 "topic": "Editorial banned-phrase lists (newsrooms)"
}

{
 "rule": "The Princeton/Georgia Tech 'Delve' study (arXiv:2507.07510; 1.2M arXiv+PubMed papers) defines 'excess vocabulary' = words significantly over-represented in LLM output vs human text (delve, intricate, pivotal, realm, underscore, boast; ~17.5% of 2024 CS intros showed LLM signs). Prior work Liang et al. 'Monitoring AI-modified content at scale' coined the metric. Borrow the METHOD, not just the list: compute per-word frequency ratio (LLM-corpus vs human-corpus) and flag words above a threshold — BuildPilot can maintain its own excess-vocabulary list per language.",
 "source": "https://arxiv.org/abs/2507.07510",
 "topic": "Excess-vocabulary method (Princeton 'Delve' study)"
}

{
 "rule": "AntiSlop Sampler (github.com/sam-paech/antislop-sampler, Apache-2.0; ICLR 2026 paper arXiv:2510.15061) ships directly reusable artifacts: slop_phrases_*.json, slop_words_*.json, slop_regexes.txt (e.g. banning the 'not X, but Y' construction), and phrase+multiplier entries like ['testament to', 0.5]. Its lists were auto-built from words over-represented in LLM output. Borrow: the JSON wordlist schema (phrase, weight/regex), the regex-ban approach for structural clichés, and its advice to 'roll your own slop list' per language. Related: Koboldcpp v1.76+ ships antislop banning natively; exllamav2's banned_strings did the same.",
 "source": "https://github.com/sam-paech/antislop-sampler ; https://arxiv.org/abs/2510.15061",
 "topic": "Open-source anti-slop linter (AntiSlop Sampler) — most directly borrowable"
}

{
 "rule": "Deciphering Machine-Generated Text in Bangla (arXiv:2502.19286, Qatar Univ + Michigan Tech, Feb 2025): 41,000 Bangla sentences (human from IndicNLP vs GPT-3.5-turbo) across news/education/story/social-media/conversation; Random Forest on lexical (char/word frequency, hapax legomena, sentence length) + syntactic (POS, function words) + semantic features hit 91% accuracy, beating fine-tuned BanglaBERT. Borrow: the marker list IS the writing rulebook — Bangla copy must vary sentence length, avoid uniform function-word distribution, and not show GPT-typical hapax/char-frequency signatures; these are machine-checkable features for check_laws.py.",
 "source": "https://arxiv.org/abs/2502.19286",
 "topic": "Bangla AI-text detection markers (what writing must avoid) — key paper"
}

{
 "rule": "HC-Bangla: 18,000 Bangla sentences (9,000 human / 9,000 ChatGPT) across news, education, literature, social media; stylometric features (sentence length, lexical diversity, function words, punctuation patterns) + RF/SVM/LogReg reach ~90%+. Confirms the same four marker families. Borrow: punctuation-pattern uniformity and lexical-diversity (e.g. MATTR moving-average type-token ratio) as computable BuildPilot gate metrics — flag copy whose sentence-length variance is too low (low 'burstiness').",
 "source": "HC-Bangla benchmark dataset paper (arXiv, ~2506.xxxx), surfaced via web search; related HC3 lineage",
 "topic": "Bangla AI-text detection markers — HC-Bangla"
}

{
 "rule": "Detection literature (GPTZero methodology, 'The Human Puzzle' survey) converge on two statistical tells: low perplexity (over-predictable word choice) and low burstiness (uniform sentence length/structure). Caveat from same sources: heuristics with false positives, especially for non-native writers. Borrow: implement sentence-length-variance (burstiness) as a cheap deterministic check; treat perplexity as advisory only. Note GPTZero is English-centric and unreliable on Bangla; Copyleaks explicitly advertises Bengali support (30+ languages) — usable as an optional external second-opinion check, not the gate itself.",
 "source": "GPTZero methodology pages; arXiv 'The Human Puzzle' survey; https://www.copyleaks.com/ai-content-detector",
 "topic": "Burstiness + perplexity as gate metrics (with caveats)"
}

{
 "rule": "Widely cited AI tells: em-dash overuse, 'rule of three' triadic constructions, listicle-heavy formatting, 'overly polished and structured language'. The Verge's MTG piece and detector literature stress these are UNRELIABLE alone (humans use them too). Borrow as WARN-level (not FAIL) rules in the validator: cap em-dash density, flag repeated triadic parallel structures, flag every section having identical structure.",
 "source": "The Verge 'Marjorie Taylor Greene ChatGPT' piece; Wikipedia 'AI detector'; GPTZero 'Listicle Problem' blog — via web search",
 "topic": "Structural 'tells' — warn-level only, not hard bans"
}

{
 "rule": "Bangla Academy's 'বানানের নিয়ম' (first published 1976; revised 2002, 2013; PDF free on banglaacademy.org.bd) is the government standard, written on চলিত রীতি: rules for চন্দ্রবিন্দু (চাঁদ, পাঁচ, সাঁতার), হসন্ত-বর্জন (পরিষদ not পরিষৎ, বনাম, আয়াত), য-ফলা, রেফ, যুক্তবর্ণ. The 'প্রমিত বাংলা বানান অভিধান' (2018) lists ~50,000 standard spellings. Borrow as machine-checkable BD rules: শব্দান্তে ঈ নয় (শ্রেণি/দেশি not শ্রেণী/দেশী), প্রথম বর্গের বর্ণের পরে ঊ নয় (কুমার/গুরু), হ-এর পরে ঈ (হীরা, হীন), চন্দ্রবিন্দু usage — all regex/wordlist-checkable against the Academy list.",
 "source": "banglaacademy.org.bd বানানের নিয়ম PDF; প্রমিত বাংলা বানান অভিধান (2018); Wikipedia বাংলা বানান — via web search",
 "topic": "প্রমিত বাংলা spelling standard — বাংলা একাডেমি (Bangladesh baseline)"
}

{
 "rule": "চলিত রীতি (colloquial standard, based on Nadia colloquial speech) is the modern written norm: করিতেছি→করছি, করিয়াছে→করেছে, তাহার→তার, হইবে→হবে. Lineage: বিদ্যাসাগর → রবীন্দ্রনাথ/প্রমথ চৌধুরী → 1936 Calcutta University spelling committee → Bangla Academy adoption 1976. Dhaka vs Kolkata divergences to pin down for a bn-BD gate: অসম/আসাম, স্বরস্বতী/সরস্বতী, কোনো/কোনও, কারো/কারও, শ্রেণি/শ্রেণী (Dhaka follows বাংলা একাডেমি; Kolkata follows সুবলচন্দ্র মিত্র's বানান পরিচয়, De'জ). Borrow: hard rule — no সাধু forms (তাহার, করিয়াছে, হইবে) in marketing copy; maintain a sadhu→chalit mapping table; pin bn-BD (Dhaka) spellings explicitly.",
 "source": "Wikipedia সাধু ভাষা ও চলিত ভাষা; বাংলা একাডেমি নিয়ম-বই — via web search",
 "topic": "চলিত রীতি enforcement — no সাধু forms"
}

{
 "rule": "Bangla Academy's own editorial/observer guidance (e.g. পর্যবেক্ষক শব্দকোষ-style guidance) prescribes: (a) prefer the Bengali term when the English term has a well-established Bengali equivalent (চলিত, natural register); (b) don't mix সাধু and চলিত in one piece; (c) prefer the বিশেষ্য form of loanwords; (d) use standard Bangla spelling per the Academy dictionary; (e) don't apply English capitalization rules to Bangla; (f) for a term with no established equivalent, translate closely or transliterate per Academy rules. Borrow directly as prompt-level rules for the copy agent plus a terminology wordlist check.",
 "source": "Bangla Academy editorial guidance surfaced via web search (পর্যবেক্ষক/একাডেমি নীতিমালা summaries)",
 "topic": "Bangla Academy editorial language guidance (loanwords, register, capitalization)"
}

{
 "rule": "BBC Bangla maintains an internal ভাষা নীতিমালা following প্রমিত বানান (anchored on Bangla Academy's dictionary) with detailed phonetic transliteration rules for English/foreign names into Bengali script; the full guide is internal/semi-public, referenced as a benchmark by Bangla journalism schools. Prothom Alo follows Bangla Academy orthography as the de-facto house standard for Bangladeshi news. Borrow: transliteration consistency table (one approved Bengali rendering per foreign brand/term — critical for marketing copy naming products) as a BuildPilot glossary check; treat Prothom Alo/Bangla Academy spelling as the tiebreaker.",
 "source": "BBC Bangla ভাষা নীতিমালা (internal, via web search summaries); Prothom Alo practice — via web search",
 "topic": "BBC Bangla + Prothom Alo house practice (no fully public guide)"
}

{
 "rule": "Google's Bengali style guides are public PDFs: Google TLC Bengali style guide (storage.googleapis.com/transedpublic/Google_TLC_Bengali_style_guide.pdf) and Google Bengali (India) In-Country Reviewer Style Guide (…/Google_Bengali_India_In-Country-Reviewer_Style_Guide.pdf) covering punctuation (দাঁড়ি '।' as full stop; comma/colon/semicolon usage), transliteration of loanwords, abbreviations/acronyms, units. Microsoft's Bengali Language Style Guide (2004, download.microsoft.com/.../ben-BD.pdf) covers bn-BD conventions: Bengali numerals ০১২৩৪৫৬৭৮৯, formal আপনি for user-facing text, keep product names (Microsoft, Windows) in English. Meta's Bengali guide covers transliteration + formality (আপনি default). Borrow: danda check (Bangla sentences end with । not '.'), Bengali-numeral policy for bn-BD copy, আপনি default for customer-facing site copy, and a transliteration glossary.",
 "source": "https://storage.googleapis.com/transedpublic/Google_TLC_Bengali_style_guide.pdf ; https://storage.googleapis.com/transedpublic/Google_Bengali_India_In-Country-Reviewer_Style_Guide.pdf ; https://download.microsoft.com/download/8/8/0/880BCA75-32DD-467E-991C-82CA2B87E7B0/ben-BD.pdf",
 "topic": "Localization-industry Bangla style guides (public PDFs — directly borrowable)"
}

{
 "rule": "bn-BD vs bn-IN vocabulary differs: Indian Bengali absorbs more English loanwords; Bangladesh Bengali has more Arabic/Persian influence; numerals — Bengali numerals standard in Bangladesh, Latin numerals common in Indian Bengali. Politeness: আপনি is the everyday politeness default in Bangladesh service/customer contexts, তুমি is the friendlier advertising norm (brands use তুমি for approachability, আপনি for respectful positioning, তুই only for edgy youth campaigns); in West Bengal তুমি is the broader default. Borrow: BuildPilot gate pins locale bn-BD → Bengali numerals + আপনি/তুমি choice must be an explicit per-site tone decision recorded in the plan, never mixed within one page.",
 "source": "CSA Research bilingual style guide catalog (csa-research.com/Bilingual-Style-Guides); Quora/locale summaries — via web search; TranslationJournal.net 'Localization of Google Products into Bangla'",
 "topic": "bn-BD vs bn-IN split — machine-checkable locale rules"
}

{
 "rule": "No dedicated public Bangladeshi ad-agency copywriting style guide surfaced; best available signal is the pronoun-register norm above plus Prothom Alo/Bangla Academy orthography. CSA Research hosts 100+ community style guides for 85+ locales including Bengali (some behind registration). Borrow: for the Bangla marketing register, encode as prompt rules — চলিত রীতি only, concrete verbs over Bengali calques of English jargon (e.g. avoid untranslated 'ইউটিলাইজ', 'লেভারেজ' where a natural Bangla verb exists), and a human read-aloud pass, since no detector is trustworthy for Bangla (GPTZero unreliable; Copyleaks claims Bengali support but industry guidance still mandates human review).",
 "source": "CSA Research catalog; Copyleaks/GPTZero language-support pages — via web search",
 "topic": "Bangla advertising copy register (thin public guidance — gap finding)"
}

{
 "rule": "Academic paraphrase attacks (arXiv 'Evading AI-Generated Text Detection using Language Models') drop detector accuracy from 100% to ~5%, and Wired reports humanizer tools stripping em dashes etc. to evade. Conclusion for BuildPilot: a pure wordlist gate is gameable and false-positive-prone; pair it with (a) structural/statistical checks (burstiness, punctuation-pattern variance), (b) prompt-based rubric review (second-opinion agent reads copy for voice, specificity, concrete detail), and (c) mandatory human manual check — which the SPS workflow already requires per section.",
 "source": "arXiv 'Evading AI-Generated Text Detection using Language Models' (via web search); Wired 'Chatbots Got Big. Their Footprints Got Smaller.'",
 "topic": "Gate-design lesson — detectors are evadable; design for layered checks"
}

{
 "rule": "AntiSlop's default list was 'mostly auto-generated by finding words over-represented in LLM output compared to normal human writing' and the author recommends curating your own. Borrow the pipeline: for any language, build the BuildPilot slop list by diffing word/phrase frequencies between a corpus of the target model's Bangla output and human-written Bangla (e.g. Prothom Alo archives as human reference), then hand-curate. This gives a defensible, checkable, language-specific wordlist rather than an imported English one.",
 "source": "https://github.com/sam-paech/antislop-sampler README (via WebFetch)",
 "topic": "Roll-your-own-list guidance (calibrate per language/model)"
}

