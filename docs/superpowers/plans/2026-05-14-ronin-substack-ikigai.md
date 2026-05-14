# Ikigai Substack Article Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Write a 2,000–2,500 word paid Substack article for @RoninWords that reframes the Western misinterpretation of Ikigai and delivers practical self-discovery questions.

**Architecture:** Write each section of the article independently as a Markdown file in `ronin/substack/`, then assemble into the final article. Each section is self-contained and reviewable before assembly.

**Tech Stack:** Plain Markdown, saved to `ronin/substack/ikigai_article.md`

**Spec:** `docs/superpowers/specs/2026-05-14-ronin-substack-ikigai-design.md`

---

### Task 1: Hook（200語）

**Files:**
- Create: `ronin/substack/ikigai_article.md`

- [ ] **Step 1: Hook セクションを書く**

以下の内容を `ronin/substack/ikigai_article.md` に書く：

```markdown
# The Ikigai Lie: What the West Got Wrong — and the Ancient Truth That Actually Changes Lives

---

The Ikigai diagram you've seen everywhere — the four overlapping circles, the neat quadrants of passion, mission, vocation, and profession — was not created by a Japanese person.

It was made in 2014 by a British blogger named Marc Winn, who stitched together two unrelated concepts and posted it on his website. Within months, it went viral. Within years, it had been reprinted in bestselling books, Fortune 500 keynotes, and TEDx slides worldwide.

The Japanese concept of 生き甲斐 (*ikigai*) is over a thousand years old. Marc Winn's diagram is eleven.

And yet, most people in the West think they mean the same thing.

They don't.

This distinction matters more than you might expect — because the version you were sold comes with a hidden cost. It quietly convinces you that you must find *one perfect answer* to the question of your life. That unless you've located the precise intersection of what you love, what you're good at, what the world needs, and what you can be paid for, you haven't really figured out how to live.

That pressure is not Japanese. It's not even philosophical. It's Western productivity culture wearing a kimono.

What the Japanese actually mean by *ikigai* is something older, quieter, and far more useful. And once you understand it, you won't need a diagram at all.
```

- [ ] **Step 2: 語数・トーンを確認する**

語数が180〜220語の範囲にあること、フック（逆張り主張）が冒頭2文以内に来ていることを確認する。

- [ ] **Step 3: コミット**

```bash
git add ronin/substack/ikigai_article.md
git commit -m "feat: Ikigai記事 Hook セクションを追加"
```

---

### Task 2: The Western Distortion（400語）

**Files:**
- Modify: `ronin/substack/ikigai_article.md`

- [ ] **Step 1: Section 2 を追記する**

`ronin/substack/ikigai_article.md` のHookの後に以下を追記する：

```markdown
---

## The Map That Wasn't the Territory

Marc Winn didn't set out to mislead anyone. In 2014, he was writing a blog post about purpose and came across a diagram by Spanish author Andrés Zuzunaga — a Venn diagram about finding *purpose* that had nothing to do with Japan. At the same time, he'd been reading about the Japanese island of Okinawa and its unusually high number of centenarians, whose longevity was often attributed to having a sense of *ikigai*.

He combined the two ideas, labeled Zuzunaga's circles with the word *ikigai*, and posted it. It spread.

The result is a concept that sounds Japanese, looks systematic, and feels profound — but is actually a Western framework for career optimization dressed in Eastern clothes.

The real word, 生き甲斐, breaks down like this:

- **生き** (*iki*) — to live, to be alive
- **甲斐** (*gai*) — worth, effect, result, benefit

Together: *the worth of being alive*. Or more simply: *a reason to get up in the morning*.

That's it. There is no diagram. There are no four circles. There is no optimization exercise.

In Japan, *ikigai* is used in ordinary conversation. A grandmother talks about her *ikigai* when she describes tending her garden. A retired engineer finds his *ikigai* in teaching neighborhood kids origami on weekends. A fisherman's *ikigai* is the ritual of preparing his boat before dawn.

None of these people are at the intersection of passion, mission, vocation, and profession. They haven't been paid to do what they love. They haven't found their life's calling in any grand sense.

They've simply found something that makes being alive feel worthwhile.

The Western diagram turned this humble, daily orientation toward life into an achievement to unlock. It made *ikigai* into a destination rather than a practice. And in doing so, it made it much, much harder to find — because it made the criteria impossibly high.

You can't find your *ikigai* if you're looking for something that justifies your entire existence. But you can notice it in almost any ordinary moment, if you know what you're looking for.
```

- [ ] **Step 2: 流れを確認する**

HookからSection 2への接続が自然であること、Winn/Zuzunagaの事実が正確に書かれていることを確認する。

- [ ] **Step 3: コミット**

```bash
git add ronin/substack/ikigai_article.md
git commit -m "feat: Ikigai記事 Western Distortion セクションを追加"
```

---

### Task 3: What Ikigai Actually Means（400語）

**Files:**
- Modify: `ronin/substack/ikigai_article.md`

- [ ] **Step 1: Section 3 を追記する**

```markdown
---

## What Okinawa Actually Taught Us

The centenarians of Okinawa — the real inspiration behind the modern *ikigai* conversation — were studied by researcher Dan Buettner as part of his Blue Zones project. What he found was not a population of people who had discovered their perfect life purpose. He found people who had woven small, consistent sources of meaning into the fabric of daily life.

Their *ikigai* was not a career. It was a *moai* — a small social group that met regularly and supported one another for decades. It was the act of growing bitter melon in a garden you've tended for fifty years. It was the habit of moving your body, eating slowly, and sitting with neighbors in the evening sun.

Researchers Michiko Kumano and Akihiro Hasegawa, who have spent careers studying *ikigai* in Japanese populations, describe it not as a purpose to find but as a *subjective wellbeing* — a felt sense of life's worth that arises from engagement, connection, and presence.

The scale they use to measure it asks questions like:

- *Do you feel that your daily life is fulfilling?*
- *Do you feel that your life has meaning?*
- *Are you satisfied with your life?*

Notice what's absent: questions about career fit, marketable skills, or world-changing missions.

Japanese psychiatrist Mieko Kamiya, who wrote the foundational text on *ikigai* in 1966, described it as having seven components: life satisfaction, meaning and worth, existence, freedom, self-actualization, change and growth, and the future. It is a constellation, not a single star.

This is the crucial difference. The Western version asks you to find *the thing*. The Japanese original asks you to cultivate *a way of living*.

One is a treasure hunt with no guaranteed ending. The other is a daily practice available to anyone, starting today.

The Okinawan elders didn't wake up each morning because they had found the perfect intersection of passion and income. They woke up because there were people who needed them, plants that needed watering, and a bowl of miso soup that wouldn't make itself.

That, it turns out, is enough.
```

- [ ] **Step 2: 確認する**

沖縄・Blue Zonesの言及が具体的かつ正確であること、Section 2からの論理的な流れがあることを確認する。

- [ ] **Step 3: コミット**

```bash
git add ronin/substack/ikigai_article.md
git commit -m "feat: Ikigai記事 What Ikigai Actually Means セクションを追加"
```

---

### Task 4: Why This Matters for You（400語）

**Files:**
- Modify: `ronin/substack/ikigai_article.md`

- [ ] **Step 1: Section 4 を追記する**

```markdown
---

## The Tyranny of the Perfect Purpose

Here is what the Western *ikigai* framework quietly does to you.

It tells you that your life has a *correct answer* — and that until you've found it, you're living incorrectly. It says your work should be your passion. Your passion should serve the world. The world should pay you for it. And you should be good at it too, or it doesn't count.

By those standards, most people on earth have no *ikigai*. The fisherman doesn't qualify. The grandmother doesn't qualify. The retired engineer teaching origami doesn't qualify.

This framework doesn't liberate you. It paralyzes you.

There's a phenomenon psychologist Barry Schwartz called *the paradox of choice* — the finding that more options don't make people happier, they make them more anxious, more prone to regret, and less able to choose. The Western *ikigai* diagram applies this paradox directly to the question of meaning: it turns the open landscape of a good life into a high-stakes optimization problem.

The result? People who spend their thirties anxious about whether they've found their "true calling." People who leave perfectly meaningful jobs because they don't also qualify as passions. People who feel like failures because their *ikigai* diagram doesn't produce a clean answer.

This is not a Japanese problem. Japan consistently ranks among the highest in the world for sense of life meaning in elderly populations — precisely because the culture doesn't demand that meaning come from one dramatic source.

Your *ikigai* is allowed to be small. It's allowed to be multiple things. It's allowed to change as you change. It doesn't need to make you money. It doesn't need to save the world.

It just needs to make you feel that being alive today is worth something.

Maybe that's your craft. Maybe it's a relationship. Maybe it's a physical practice, a creative habit, or the quiet ritual of a morning you've built for yourself.

The Samurai understood this. A warrior whose *ikigai* was only combat was a warrior without an inner life — brittle, purposeless in peacetime, and dangerous to himself. The great ones cultivated multiple sources of meaning: poetry, calligraphy, the tea ceremony, loyalty to a lord, love of a craft.

They didn't find purpose. They built it, piece by piece, day by day.
```

- [ ] **Step 2: 確認する**

「武士・サムライ」の言及が@RoninWordsブランドに自然に接続されていることを確認する。読者への語りかけ（"you"）が一貫していることを確認する。

- [ ] **Step 3: コミット**

```bash
git add ronin/substack/ikigai_article.md
git commit -m "feat: Ikigai記事 Why This Matters セクションを追加"
```

---

### Task 5: The 7 Questions（400語）

**Files:**
- Modify: `ronin/substack/ikigai_article.md`

- [ ] **Step 1: Section 5 を追記する**

```markdown
---

## The 7 Questions That Find What the Diagram Can't

The following questions are not a framework. They're not a system. They're an invitation to pay attention to what's already there.

Take these to a journal. Give each one ten minutes. Don't aim for a final answer — aim for honesty.

---

**1. What did you do this week that made time disappear?**

Not what you were proud of or what someone else praised. What made an hour feel like ten minutes? Flow states are one of the clearest signals the body gives about genuine engagement. Note it, even if it seems trivial.

**2. What would you do even if no one paid you or praised you for it?**

Strip away the audience. Strip away the income. What would remain? This isn't about finding a career — it's about locating desire that isn't borrowed from other people's expectations.

**3. What small moment this week made you feel most alive?**

Not happy, necessarily. *Alive*. Present, engaged, real. It might have been a difficult conversation, a physical effort, a moment of beauty. Where did life feel most concentrated?

**4. What skill do you have that feels natural to you but effortful to others?**

Not what you've been trained for — what you're wired for. The thing you do without thinking that others find impressive or mysterious. This is often closer to your *ikigai* than any passion you can name.

**5. What do people thank you for, without you asking?**

The specific way you show up that others notice. Not your job title. Not your achievements. The quality of your presence, your listening, your way of solving a problem or holding a difficult moment.

**6. What would you regret not doing at the end of your life?**

Not what you want to achieve. What you would regret *not having been*. This question usually bypasses the ego's ambitions and goes straight to what actually matters.

**7. What would the 80-year-old version of you say to you right now?**

Not to comfort you. To tell the truth. The older self has survived the urgency, the comparison, the fear of missing out. What do they see from that vantage point that you can't see yet?

---

You don't need all seven answers to change anything. One honest answer — really honest — is enough to shift your orientation. *Ikigai* is not a destination you reach. It's a direction you practice pointing toward.
```

- [ ] **Step 2: 確認する**

7つの質問がそれぞれ独立して使えること、各質問の補足説明が50〜70語であることを確認する。

- [ ] **Step 3: コミット**

```bash
git add ronin/substack/ikigai_article.md
git commit -m "feat: Ikigai記事 The 7 Questions セクションを追加"
```

---

### Task 6: Closing + CTA（150語）

**Files:**
- Modify: `ronin/substack/ikigai_article.md`

- [ ] **Step 1: Closing セクションを追記する**

```markdown
---

## The Ronin's *Ikigai*

A ronin — a samurai without a master — had no lord to define his purpose for him. No mission handed down from above. No framework to tell him where his passion met his market.

He had only the question every free person eventually faces: *what do I live for, now that I must decide for myself?*

The ones who answered that question well didn't find one perfect answer. They built a life with many small answers. They practiced their craft not because it would make them famous, but because the practice itself was worth doing.

That's *ikigai*. Not a discovery. Not a diagram. A daily decision to notice what makes being alive worthwhile — and to keep showing up for it.

---

*If this article shifted something for you, share it with someone who's been stuck looking for "the answer." Sometimes the most useful thing we can do for the people we care about is hand them a different question.*

*Next week: the Japanese concept of* **Wabi-Sabi** *— and why imperfection might be the most radical act of self-respect you can practice.*
```

- [ ] **Step 2: 記事全体を通読する**

冒頭からClosingまで通して読み、以下を確認する：
- 語数が2,000〜2,500語の範囲にあること
- @RoninWordsのブランドトーン（直接的・詩的・文化的根拠あり）が一貫していること
- 有料コンテンツとして完結感があること
- 次回記事へのCTAが自然な形で入っていること

- [ ] **Step 3: 最終コミット**

```bash
git add ronin/substack/ikigai_article.md
git commit -m "feat: Ikigai記事 Closing + CTA セクションを追加（記事完成）"
```

---

## 完成ファイル

`ronin/substack/ikigai_article.md` — Substack にそのままコピー&ペーストできる状態の完成記事。

## Substack投稿時の設定

| 項目 | 値 |
|------|-----|
| Title | The Ikigai Lie: What the West Got Wrong — and the Ancient Truth That Actually Changes Lives |
| Subtitle | The diagram you've seen everywhere wasn't made by a Japanese person. Here's what was. |
| Access | Paid subscribers only |
| Section | — |
| Tags | Japanese Wisdom, Philosophy, Self-Development |
