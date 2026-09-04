# Content-completeness checklists (per activity type)

Score = (fields present / fields expected) × 100. Default threshold: **70%**.
Below threshold → verdict `CONTENT_INCOMPLETE` (always record the score, e.g. "score 4/7 = 57%").
Field presence is judged from the page text/snippet; when the snippet is not
enough, fetch the full page (WebFetch or in-app browser).

## guest post / article (7 fields)
1. Page title present and topical (not "Untitled"/domain default)
2. Body ≥ 300 words
3. Target link placed **inside the article body** (not footer/sidebar/comment)
4. Anchor text sensible (matches sheet's Anchor Text column if given)
5. At least 1 image
6. Author/byline or publish date visible
7. Content readable & on-topic (not gibberish/spun)

## business listing (7 fields)
1. Business name correct
2. Description present (≥ 50 words)
3. Website field = target URL
4. Category selected
5. **Address present in content (NAP)** — also gates verdict `ADDRESS_MISSING`
6. Phone number present
7. Logo/image uploaded

## profile / bio link (5 fields)
1. Display name / business name set
2. Bio/description present (≥ 30 words)
3. Website/target link placed
4. Avatar/logo uploaded
5. Profile public (visible logged-out — implied by Gate 1 pass)

## social bookmark / directory (4 fields)
1. Title present
2. Description ≥ 30 words
3. Target link placed
4. Correct category/tag

## unknown activity type
Use guest-post list minus fields that don't apply; note assumption in Reason.
