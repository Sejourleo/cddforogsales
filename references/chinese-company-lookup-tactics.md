# Chinese ToB Customer Lookup Tactics

Use this reference when a customer background check involves a small/private Chinese company with sparse official marketing footprint.

## Search sequence

1. Start broad with exact company name in quotes and variants with/without Chinese parentheses:
   - `"中发国兴（杭州）人工智能科技有限公司"`
   - `"中发国兴(杭州)人工智能科技有限公司"`
   - `"中发国兴" "杭州" "人工智能"`
2. Use DuckDuckGo/Bing-style result pages to discover stable URLs, but do not trust snippets alone.
3. Prefer public registry pages that render SEO HTML:
   - 爱企查 `company_shares_<pid>` often exposes header facts + shareholder table even when `company_detail_<pid>` redirects to anti-bot/captcha.
   - 爱企查 `company_annual_<pid>` often exposes annual-report index and company header facts.
   - QCC may return WAF/anti-bot payloads; treat it as discovery unless content is readable.
4. Extract not only the target company but also controlling shareholder / parent company PIDs. A new local subsidiary often makes sense only through the parent.
5. Search for exact names excluding registry sites to detect real operating footprint:
   - `"公司全称" -企查查 -爱企查`
   - `公司简称 官网`
   - `公司简称 招聘`
   - `法人名 公司简称`
6. Cross-check industry context separately from company facts: local government policy, industry association/news, and subsidy notices are useful for pain hypotheses but should not be presented as company-specific facts.
7. For Nuxt/Vue company sites with sparse rendered HTML, inspect bundled JS for API bases and routes:
   - Fetch homepage, list `/_nuxt/*.js` scripts, then search bundles for strings like `/f/`, `baseURL`, `jsonp`, `tCase`, `contact`, `position`, `projecttype`.
   - Many Chinese SME sites expose JSONP endpoints directly (example pattern: `http://site/gw-ht/f/...` returning `null([...])`). Strip the JSONP wrapper and parse JSON.
   - Useful endpoints often include company/about text, project categories, case lists/details, contact locations, and open positions; these are high-signal for sales hypotheses.
   - Treat old case/position timestamps as historical capability signals, not proof of current active hiring or current product focus.

## Useful fields to capture

- Company status, incorporation/registration time, registered capital, legal representative, address, official website presence.
- Shareholder table: shareholder name, holding ratio, subscribed capital, actual paid capital if shown.
- Parent company: incorporation date, registered capital, legal representative, address, shareholders.
- Risk counts if shown, but caveat strongly for new companies: low/no risk can simply mean insufficient operating history.
- Whether independent website, recruiting, product pages, news, patents/software copyrights, or customer cases are publicly visible.

## Interpretation pattern

For a newly established subsidiary, frame the sales hypothesis as:

> This may be a regional/project/business-carrier entity under an older parent, not yet a mature standalone operating company. The meeting should first verify why this entity was created, where decision rights sit, and whether budget comes from the subsidiary or parent.

## Pitfalls

- Do not infer mature product lines from an AI-themed company name alone.
- Do not treat DBC/top-list/news mentions as proof of the target company unless the exact target name appears.
- Do not over-personalize legal-representative research; if public material is only registry-level, say personal profile information is insufficient.
- Do not lead with a fixed product pitch. For early/new entities, first validate: strategic purpose, team, customer stage, project/budget ownership, and near-term business direction.
