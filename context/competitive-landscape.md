# Competitive Landscape

**LAST UPDATED:** March 22, 2026
**NEXT REVIEW:** June 2026

This file maps the competitive landscape per ICP. Read it before executing Skill 04 (Account Research) to produce consistent, account-specific competitive analysis in every research output.

---

## ICP A: Workspace Security — Who We Compete Against

### The Big Picture

Most companies have **email security** (Proofpoint, Mimecast, or Microsoft Defender) and **endpoint/XDR** (CrowdStrike, SentinelOne). A few have **DLP for collaboration** (Polymer, Zscaler). Almost nobody has **phishing and social engineering detection across Slack, Zoom, Teams, and beyond**. That's Cyvore's open field.

Two vendors have recently started moving into collaboration security: Proofpoint (Messaging Protection) and Abnormal Security. Both are URL-centric — they scan for malicious links, not for social engineering in message text, visual phishing, or cross-identity correlation. This is the critical distinction.

### Competitor Map

#### Proofpoint (incl. Messaging Protection / Collaboration Security Prime)

| | |
|---|---|
| **What they do** | Market leader in email security. Recently launched "Messaging Protection" covering Slack, Teams, Zoom, and social platforms. Part of their Collaboration Security Prime bundle. |
| **Strengths** | Dominant email security brand (80+ Fortune 100). Massive URL intelligence (20T URLs analyzed/year). Native integration across their stack. Gartner Leader. |
| **Weaknesses (Cyvore's angle)** | Messaging Protection is **URL-only** — it inspects links in collaboration messages. It does NOT analyze message text for social engineering (DAN), visual elements for phishing (OPR), or do cross-identity correlation. It misses attacks with no malicious URL (pure social engineering, deepfakes, impersonation via text). |
| **Pricing** | $25-$70/user/year for email. Messaging Protection pricing is add-on, not public. Enterprise bundles exceed $100K+/year. |
| **Typical buyer** | CISO at enterprise with 1,000+ employees. |
| **Trap question** | "Does your Proofpoint deployment detect a phishing message in Slack that contains no URL — just social engineering text or a fake screenshot? What about a deepfake on Zoom?" |
| **How we position** | "Proofpoint catches malicious URLs in Slack. We catch the attacks that don't have URLs — social engineering, impersonation, visual phishing. We're the content-level layer Proofpoint doesn't provide." |

#### Abnormal Security

| | |
|---|---|
| **What they do** | AI-powered email security (behavioral AI for BEC, account takeover). Recently added Slack and Teams coverage for URL and file inspection with automated remediation. |
| **Strengths** | Strong behavioral AI for email. Growing fast ($285M ARR as of 2025). Covers email + Slack + Teams in one platform. Good automation (AI Security Mailbox, AI Phishing Coach). |
| **Weaknesses (Cyvore's angle)** | Slack/Teams coverage is still **URL and file inspection** — same paradigm as email security extended to collaboration. No visual phishing recognition (OPR), no NLU-based social engineering detection (DAN), no cross-identity correlation, no WhatsApp/CRM/Jira coverage. Doesn't analyze video calls (Zoom/Meet). |
| **Pricing** | $15-$35/user/year. Median deal ~$39K/year. Min contracts $25K-$50K. |
| **Typical buyer** | CISO at mid-market SaaS/tech companies. |
| **Trap question** | "Does Abnormal detect social engineering in Slack messages where there's no malicious URL or file — just manipulation in the text? Does it cover Zoom, WhatsApp Business, or CRM?" |
| **How we position** | "Abnormal extended email security to Slack/Teams — great for URLs and files. We analyze the actual message content: NLU for social engineering, visual recognition for fake screenshots and brand impersonation, and cross-identity correlation linking personal account compromises to corporate risk. Different detection layer." |

#### Mimecast (incl. Aware)

| | |
|---|---|
| **What they do** | Email security platform. Acquired Aware (collaboration governance/compliance tool) for Teams, SharePoint, OneDrive monitoring. Covers archiving, eDiscovery, DLP, and some threat detection. |
| **Strengths** | Strong email security with encryption, DLP, archiving. Aware adds governance and compliance for collaboration tools. Gartner Leader for email. |
| **Weaknesses (Cyvore's angle)** | Aware is primarily **governance and compliance** (data retention, eDiscovery, policy violations) — not phishing detection. URL/file scanning exists but not deep content analysis for social engineering. No Slack coverage (Teams, SharePoint, OneDrive only). No Zoom/video analysis. No cross-identity correlation. |
| **Pricing** | $42-$120/user/year depending on tier. Aware pricing is custom (add-on). |
| **Typical buyer** | Compliance-driven organizations (financial, healthcare, legal). |
| **Trap question** | "Does Mimecast/Aware detect a social engineering message in Teams, or is it focused on compliance and data governance? Does it cover Slack?" |
| **How we position** | "Mimecast + Aware solves compliance and archiving. We solve active threat detection — phishing, impersonation, social engineering — across all collaboration channels including Slack and Zoom, which Aware doesn't cover." |

#### Polymer DLP

| | |
|---|---|
| **What they do** | AI-powered DLP for Slack, Teams, Google Drive, OneDrive, GitHub. Detects and remediates sensitive data exposure (PII, PHI) in messages and files. |
| **Strengths** | Purpose-built for Slack/Teams DLP. 150+ data detection elements. Real-time remediation (redact/delete). Affordable ($5/user/month). |
| **Weaknesses (Cyvore's angle)** | Polymer is **DLP, not threat detection**. It finds sensitive data leaking in messages — it does NOT detect phishing, social engineering, impersonation, or malicious content. Completely different use case. |
| **Pricing** | $5/user/month (Standard), from $33K/year (Enterprise). |
| **Trap question** | N/A — Polymer is not a competitor. It's complementary (they protect data, we detect threats). Only relevant if a prospect conflates DLP with phishing detection. |
| **How we position** | "Polymer stops your employees from accidentally sharing sensitive data in Slack. We stop attackers from phishing your employees in Slack. Different problem, different solution. You probably need both." |

#### Microsoft Defender for Office 365 / Google Workspace Security

| | |
|---|---|
| **What they do** | Native email/collaboration security built into Microsoft 365 and Google Workspace. Basic anti-phishing, anti-spam, Safe Links, Safe Attachments. |
| **Strengths** | Free with the platform (no incremental cost). Always on. Good for commodity threats. |
| **Weaknesses (Cyvore's angle)** | Covers only their own ecosystem (Microsoft or Google, not both). Basic detection — misses sophisticated phishing, social engineering, and zero-day attacks. No cross-platform visibility. No cross-identity correlation. No WhatsApp/CRM/Jira. |
| **Pricing** | Included in Microsoft 365 E3/E5 or Google Workspace Enterprise. |
| **Trap question** | "What catches a phishing message that comes through Slack (not email), contains no URL, and uses a fake screenshot to impersonate your CEO? Does Microsoft Defender see that?" |
| **How we position** | "Native security catches the basics. We catch what gets through — and across all the channels native security doesn't cover." |

### Cyvore's Unique Positioning in ICP A

| Capability | Cyvore | Proofpoint | Abnormal | Mimecast | Polymer |
|---|---|---|---|---|---|
| Email phishing detection | Yes | Yes (leader) | Yes | Yes | No |
| Slack phishing detection | Yes | Yes (URL only) | Yes (URL/file only) | No | No (DLP only) |
| Teams phishing detection | Yes | Yes (URL only) | Yes (URL/file only) | Partial (Aware) | No (DLP only) |
| Zoom/video call analysis | Yes | No | No | No | No |
| WhatsApp Business | Yes | No | No | No | No |
| CRM / Jira | Yes | No | No | No | No |
| Visual phishing recognition (OPR) | Yes | No | No | No | No |
| NLU social engineering detection (DAN) | Yes | No | No | No | No |
| Cross-identity correlation | Yes | No | No | No | No |
| Active investigation / attack chains | Yes | Partial | Partial | No | No |

**Bottom line:** Proofpoint and Abnormal are the closest competitors in ICP A, but both extend the email security paradigm (URLs, files, sender analysis) into collaboration. Cyvore analyzes the **content** (text, visuals, behavior) — a fundamentally different detection layer. They complement more than they compete, but the buyer may see them as overlapping.

---

## ICP B: Threat Intelligence — Who We Compete Against

### The Big Picture

Enterprise threat intelligence is a mature market. Premium feeds cost $100K+/year (Recorded Future, Mandiant). Mid-tier options run $20K-$75K. Israeli specialists (KELA, Cybersixgill) focus on dark web. Cyvore's TIAO feed at $20K/year is priced at the low end but offers a unique capability: **cross-identity correlation** linking personal account compromises to corporate exposure. No other feed does this.

### Competitor Map

#### Recorded Future

| | |
|---|---|
| **What they do** | Premium threat intelligence platform. Aggregates data from open web, dark web, and technical sources. AI-powered analysis and risk scoring. Acquired by Mastercard (2024). |
| **Strengths** | Broadest coverage (1M+ sources). AI-driven analysis. Strong brand. Gartner Leader. Deep integration ecosystem. |
| **Weaknesses (Cyvore's angle)** | Expensive ($100K+/year for enterprise). Broad but not deep on cross-identity correlation. Doesn't link personal account compromises to corporate identities — focuses on IOCs, vulnerability intelligence, brand monitoring. |
| **Pricing** | Custom, typically $100K-$300K+/year for enterprise. |
| **Trap question** | "When an employee's personal Gmail credentials appear on the dark web, does Recorded Future automatically link that to their corporate identity and alert your SOC?" |
| **How we position** | "Recorded Future gives you macro intelligence — IOCs, vulnerability data, brand mentions. TIAO gives you micro intelligence — which of YOUR employees' personal accounts are compromised and how that maps to corporate risk. Different layer, 1/5th the price." |

#### IBM X-Force

| | |
|---|---|
| **What they do** | Threat intelligence feeds, incident response, penetration testing. Part of IBM Security. |
| **Strengths** | Strong brand. Broad coverage. Integration with QRadar SIEM. Research team reputation. |
| **Weaknesses (Cyvore's angle)** | Expensive ($20K-$150K/year). IBM sales cycles are long. Feed is broad, not focused on phishing/social engineering or cross-identity. Legacy feel — slower innovation than specialists. |
| **Pricing** | $20K-$150K/year for enterprise. |
| **Trap question** | "Does X-Force correlate dark web credential dumps with your specific employee identities — personal and corporate?" |
| **How we position** | "X-Force is a broad intelligence platform. TIAO is a focused, high-signal feed for credential exposure and cross-identity correlation. Complementary, not competing." |

#### KELA (Israeli dark web specialist)

| | |
|---|---|
| **What they do** | Israeli cybercrime intelligence. Monitors dark web forums, markets, messaging channels. Modules: Monitor, Investigate, Identity Guard, Threat Actors, Threat Landscape. |
| **Strengths** | Deep dark web coverage. Israeli company (easy relationship for Israeli buyers). Identity Guard module covers compromised account detection. Strong in financial services and government. |
| **Weaknesses (Cyvore's angle)** | Pricing likely higher than $20K (enterprise-tier). No **cross-identity correlation** linking personal accounts to corporate identities — Identity Guard monitors for compromised credentials but doesn't do the personal→corporate linkage that's unique to TIAO. Broader platform, less focused on the phishing/social engineering intelligence layer. |
| **Pricing** | Custom, not public. Likely $50K-$150K+ for enterprise. |
| **Trap question** | "Does KELA automatically link an employee's compromised personal email to their corporate identity and alert your SOC before an attacker exploits the connection?" |
| **How we position** | "KELA is excellent for dark web monitoring and threat actor profiling. We add a specific layer they don't: cross-identity correlation that links personal account exposure to corporate risk. At $20K/year, we're a supplementary feed, not a replacement." |

#### Cybersixgill (now Bitsight)

| | |
|---|---|
| **What they do** | Israeli dark web intelligence. Acquired by Bitsight (Nov 2024). Focuses on dark web forums, underground markets, threat actor profiling. |
| **Strengths** | Deep dark web collection (back to 1990s). AI-driven profiling. Now part of Bitsight (broader risk management platform). Israeli heritage. |
| **Weaknesses (Cyvore's angle)** | Same gap as KELA — no cross-identity correlation. Bitsight acquisition may shift focus toward third-party risk scoring and away from standalone threat intel. Pricing not public. |
| **Pricing** | Custom, not public. |
| **Trap question** | Same as KELA: "Does Cybersixgill link personal credential exposure to corporate identity?" |
| **How we position** | Same as KELA: supplementary feed for cross-identity correlation. |

#### CrowdStrike Falcon Intelligence

| | |
|---|---|
| **What they do** | Threat intelligence module within CrowdStrike's endpoint platform. IOC feeds, adversary profiles, malware analysis. |
| **Strengths** | Tightly integrated with Falcon endpoint platform. If the org runs CrowdStrike, adding intelligence is frictionless. Strong adversary tracking. |
| **Weaknesses (Cyvore's angle)** | Intelligence is primarily **endpoint and malware focused** — IOCs, file hashes, adversary TTPs. Not focused on phishing campaign intelligence, dark web credential monitoring, or cross-identity correlation. Expensive when buying the full Falcon stack. |
| **Pricing** | Starts at $59.99/endpoint/month (Falcon Go). Intelligence module is add-on to enterprise plans. |
| **Trap question** | "Does CrowdStrike Intelligence monitor the dark web for your employees' personal credential exposure, or is it focused on endpoint IOCs and adversary tracking?" |
| **How we position** | "CrowdStrike Intelligence is great for endpoint-level threat data. TIAO covers a different layer: dark web credential exposure with cross-identity correlation. Feeds directly into your SIEM alongside CrowdStrike's data." |

### Cyvore's Unique Positioning in ICP B

| Capability | Cyvore TIAO | Recorded Future | KELA | Cybersixgill | CrowdStrike Intel |
|---|---|---|---|---|---|
| Dark web credential monitoring | Yes | Yes | Yes | Yes | Partial |
| Cross-identity correlation (personal → corporate) | **Yes (unique)** | No | No | No | No |
| IOC feeds (hashes, IPs, domains) | Partial | Yes (leader) | Yes | Yes | Yes |
| Threat actor profiling | No | Yes | Yes | Yes (leader) | Yes |
| SIEM integration via syslog | Yes | Yes | Yes | Yes | Yes |
| Price point | $20K/year | $100K+ | $50K-$150K+ | Not public | Add-on to endpoint |

**Bottom line:** TIAO doesn't compete head-to-head with Recorded Future or KELA on breadth. It wins on one specific, unique capability (cross-identity correlation) at a fraction of the price. Position as a supplementary feed, not a replacement.

---

## ICP C: Marketplace Chat Protection — Who We Compete Against

### The Big Picture

There is no established "marketplace messaging security" category. Platforms typically choose between: (1) building in-house with keyword filters + manual T&S review, (2) using content moderation APIs (Hive, ActiveFence/Alice), or (3) using fraud platforms (Sift, Unit21) that focus on transactions, not chat content. None of these detect phishing, social engineering, or visual impersonation in user-to-user messaging. Cyvore is pioneering this space.

### Competitor Map

#### In-House Keyword Filters + Manual Review (the default)

| | |
|---|---|
| **What they do** | Most marketplaces build basic content filters (regex, keyword matching, blocklists) and staff T&S teams for manual review. User reports drive most enforcement. |
| **Strengths** | Custom to the platform. No vendor dependency. T&S teams understand their specific fraud patterns. |
| **Weaknesses (Cyvore's angle)** | Keyword filters catch ~10-20% of sophisticated scams. Miss AI-generated social engineering, visual phishing (fake screenshots, brand impersonation), and zero-day attack patterns. Manual review doesn't scale. Reactive (waits for user reports), not proactive. |
| **Pricing** | T&S headcount cost: $80K-$150K per analyst/year. A 10-person T&S team = $800K-$1.5M/year. |
| **Trap question** | "What percentage of fraud in your platform messaging is detected proactively vs. through user reports? What does your detection rate look like for messages with no suspicious keywords — just social engineering?" |
| **How we position** | "Your keyword filters catch the obvious stuff. Our AI engines catch what they miss: visual phishing, NLU-detected social engineering, and patterns from threat intelligence. We make your T&S team 10x more effective, not replace them." |

#### ActiveFence / Alice (Content Moderation)

| | |
|---|---|
| **What they do** | Content moderation and trust & safety platform. Detects hate speech, violent extremism, CSAM, disinformation, coordinated inauthentic behavior. Rebranded as Alice with AI security focus (WonderSuite). |
| **Strengths** | Deep content moderation across 120+ languages. 3B+ users protected. Strong in policy enforcement and regulatory compliance. New AI security suite (WonderBuild, WonderFence, WonderCheck). |
| **Weaknesses (Cyvore's angle)** | ActiveFence/Alice focuses on **content policy violations** (hate speech, extremism, CSAM) — not phishing, fraud, or social engineering in user messaging. Different problem entirely. They moderate what users say; we detect when users are being attacked. |
| **Pricing** | Custom, not public. Enterprise-tier. |
| **Trap question** | "Does ActiveFence detect when a buyer is sending a phishing link to a seller in your platform chat? Or when a fake support message uses social engineering to steal credentials?" |
| **How we position** | "ActiveFence catches bad content (hate speech, extremism). We catch bad actors (phishing, fraud, social engineering). You probably need both — one protects your community, the other protects your users from scams." |

#### Hive Moderation (API-based)

| | |
|---|---|
| **What they do** | Content moderation APIs. Visual and text moderation at scale. Detects NSFW, violence, drugs, spam in images and text. Used for real-time chat moderation. |
| **Strengths** | Fast API (real-time). Cheap ($0.50/1K text requests). Easy to integrate. Good for high-volume moderation. |
| **Weaknesses (Cyvore's angle)** | Hive is a **content classification API** — it categorizes content (toxic, spam, NSFW) but doesn't detect phishing, social engineering, impersonation, or fraud schemes. No threat intelligence layer. No cross-identity correlation. No visual phishing recognition (they detect NSFW images, not fake brand screenshots). |
| **Pricing** | $0.50/1K text requests. $3/1K visual requests. Enterprise: custom. |
| **Trap question** | "Does Hive detect a message that contains a fake PayPal screenshot designed to trick a seller into sending a refund? Or a social engineering script that mimics platform support?" |
| **How we position** | "Hive classifies content (is this spam? is this NSFW?). We detect attacks (is this phishing? is this social engineering? is this visual impersonation?). Different detection engine for a different problem." |

#### Sift / Unit21 (Fraud Platforms)

| | |
|---|---|
| **What they do** | Digital trust and safety platforms focused on transaction-level fraud: payment fraud, account takeover, fake accounts, chargebacks. Sift processes 1T+ events/year. |
| **Strengths** | Strong transaction fraud detection. Large consortium data. Real-time risk scoring. Proven in e-commerce and marketplaces. |
| **Weaknesses (Cyvore's angle)** | Transaction-focused, not messaging-focused. They detect fraudulent payments, chargebacks, and fake accounts — but they don't scan the actual user-to-user chat messages for phishing, social engineering, or visual impersonation. The fraud that happens INSIDE conversations is their blind spot. |
| **Pricing** | Sift: usage-based, starting $0.06/event. Custom enterprise pricing. |
| **Trap question** | "Does Sift scan the actual message text between buyers and sellers for phishing and social engineering — or does it score the transaction after the fact?" |
| **How we position** | "Sift catches fraudulent transactions. We catch the fraudulent conversations that lead to those transactions — before the money moves. Upstream detection." |

### Cyvore's Unique Positioning in ICP C

| Capability | Cyvore | In-House Filters | ActiveFence | Hive | Sift |
|---|---|---|---|---|---|
| Phishing detection in user messaging | **Yes** | Partial (keyword) | No | No | No |
| Social engineering detection (NLU) | **Yes** | No | No | No | No |
| Visual phishing recognition | **Yes** | No | No | No (NSFW only) | No |
| Content policy moderation | No | Yes | Yes (leader) | Yes | No |
| Transaction fraud detection | No | No | No | No | Yes (leader) |
| Threat intelligence integration | **Yes** | No | Partial | No | Partial |

**Bottom line:** Cyvore is creating a new category in ICP C: messaging security for marketplaces. Existing tools handle content moderation (ActiveFence) or transaction fraud (Sift) — nobody detects phishing, social engineering, and visual impersonation inside user-to-user chat. The Fiverr deal at $40K/year validates this is a real, distinct budget line.

---

## ICP D: Telecom SMS Filtering — Who We Compete Against

### The Big Picture

Carrier-level SMS security is dominated by two incumbents: Proofpoint/Cloudmark and Enea/Adaptive Mobile. Both analyze sender reputation, metadata, and URLs. Neither analyzes **message content** for social engineering (NLU) or **visual elements** for phishing (OPR). As smishing evolves beyond malicious URLs toward pure social engineering and fake screenshots, content-level AI detection becomes essential — and that's Cyvore's differentiation.

### Competitor Map

#### Proofpoint / Cloudmark

| | |
|---|---|
| **What they do** | Carrier-grade SMS/MMS/RCS security. Content filtering, flow control, policy compliance. Deployed at major carriers globally. Ranked #1 SMS firewall by Juniper Research. |
| **Strengths** | Market leader in carrier SMS security. Massive install base. URL intelligence (20T+ URLs/year). Flexible deployment (on-prem, cloud, hybrid). |
| **Weaknesses (Cyvore's angle)** | Detection is based on **URL analysis, sender reputation, and known signatures**. Does NOT analyze message text for social engineering or visual elements for brand impersonation. Misses zero-day smishing with no malicious URL — like the March 2026 Hamas campaign that used a fake Red Alert app screenshot. |
| **Pricing** | Custom, carrier-scale. Not public. |
| **Trap question** | "Does Cloudmark catch a smishing message that contains no malicious URL — just a fake emergency app screenshot and social engineering text?" |
| **How we position** | "Cloudmark catches URL-based smishing. We catch the next generation: AI-generated social engineering, visual brand impersonation, and zero-day attacks with no malicious links. Supplementary layer, not replacement." |

#### Enea / Adaptive Mobile

| | |
|---|---|
| **What they do** | AI-driven messaging firewall for carriers and CPaaS providers. Real-time URL classification, SMS spam/scam protection, grey route fraud blocking. |
| **Strengths** | AI-powered URL classification (real-time, zero-day URLs). Very low false positive rate (<1 in 3B messages). Supports SMS, MMS, RCS. Containerized deployment. Strong A2P monetization features. |
| **Weaknesses (Cyvore's angle)** | Same paradigm as Cloudmark: **URL and sender analysis**. Real-time URL classification is advanced, but still URL-centric. Does not analyze message text (NLU) or visual content (OPR). "Restricted Image Detection" exists for MMS/RCS but is focused on prohibited content (NSFW), not brand impersonation or fake app screenshots. |
| **Pricing** | Custom, carrier-scale. Not public. |
| **Trap question** | "Does Enea's firewall detect social engineering in the message text when there's no URL — just a convincing impersonation of a bank or government agency? Does it catch fake app screenshots in MMS?" |
| **How we position** | "Enea is excellent at URL classification. We add the content layer: NLU analysis of the actual message text and visual recognition of brand impersonation. Together, you get full-spectrum detection." |

#### NetNumber

| | |
|---|---|
| **What they do** | Phone number intelligence and fraud registry. TITAN platform for signaling security, number portability, and routing. |
| **Strengths** | Deep number intelligence. Good for caller ID verification and fraud registry lookups. |
| **Weaknesses (Cyvore's angle)** | **Sender-focused, not content-focused.** Analyzes who is sending, not what they're sending. Can't catch smishing from legitimate-looking numbers that carry malicious content. |
| **Pricing** | Custom. |
| **Trap question** | "NetNumber tells you about the sender. Who tells you about the content? If a legitimate number sends a phishing message, does NetNumber catch it?" |
| **How we position** | "NetNumber validates the sender. We analyze the content. Different layer — and you need both as smishing from legitimate-looking numbers increases." |

### Cyvore's Unique Positioning in ICP D

| Capability | Cyvore | Cloudmark | Enea | NetNumber |
|---|---|---|---|---|
| URL-based smishing detection | Via TIAO | Yes (leader) | Yes (leader) | No |
| Sender reputation analysis | Via TIAO | Yes | Yes | Yes (leader) |
| Message text NLU analysis | **Yes (DAN)** | No | No | No |
| Visual phishing recognition | **Yes (OPR)** | No | No | No |
| Threat intelligence correlation | **Yes (TIAO)** | Yes | Partial | Partial |
| Carrier-scale throughput | Proven at 5K events/min | Yes (carrier-grade) | Yes (carrier-grade) | Yes |

**Bottom line:** Cyvore doesn't replace Cloudmark or Enea — it's the **content-level detection layer** that sits alongside them. As smishing evolves beyond URLs toward social engineering and visual impersonation, this layer becomes essential. Position as supplementary, propose a pilot, and prove the incremental detection rate.

---

## Cross-ICP Discovery Questions

Use these in discovery calls across any ICP to expose the competitive gap:

1. **"What covers your Slack and Zoom for phishing?"** — Most will say "nothing" or "Proofpoint" (which only covers URLs). Either answer opens the door.
2. **"If an employee's personal Gmail gets compromised, does your security team know before the attacker uses it to reach their corporate account?"** — Tests cross-identity correlation. Nobody else does this.
3. **"When was the last phishing attempt that came through a non-email channel?"** — If they have an answer, it proves the pain. If they don't, it might mean they're not detecting them.
4. **"What percentage of threats in your collaboration tools are detected proactively vs. reported by users?"** — Exposes the reactive vs. proactive gap.
5. **"Does your current stack detect a phishing message with no malicious URL — just social engineering in the text?"** — This is the key differentiator question for all ICPs.
