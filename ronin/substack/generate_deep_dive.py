#!/usr/bin/env python3
# deep-dive記事100本分のJSONを生成するスクリプト
import json

articles = []

# ── Day 1 ──────────────────────────────────────────────
articles.append({
    "day": 1,
    "japanese": "七転び八起き",
    "romanji": "Nana korobi ya oki",
    "title": "The Arithmetic of Rising",
    "subtitle": "Fall seven times. Rise eight. The math doesn't add up — and that's the whole point.",
    "body_html": """<h2>The Numbers That Shouldn't Work</h2>
<p>Imagine a fighter on the mat. He has fallen seven times. The crowd has gone quiet. His corner men are already reaching for the towel. By any reasonable calculation, the fight is over.</p>
<p>Then he rises.</p>
<p>This is the moment the Japanese proverb <em>nana korobi ya oki</em> describes — not as an exceptional act of heroism, but as the only logical response to being alive. The numbers are strange: seven falls, eight risings. Where does that extra rise come from? You cannot rise before you fall. You cannot have eight risings without eight falls. So the proverb is describing something that has not happened yet.</p>
<p>That eighth rising is always in the future. It is always still possible. That is the arithmetic this phrase is really teaching.</p>

<h2>The Extra Rise</h2>
<p>Most resilience frameworks count what you survived. <em>Nana korobi ya oki</em> counts what you have left. There is a profound difference. Survivors look backward — I made it through that. The proverb looks forward — I can still rise again.</p>
<p>The asymmetry is not a mistake. In the original Japanese worldview, falling is expected. Life is a series of setbacks, failures, and losses. The question was never whether you would fall. The question was whether you would have one more rising in you than the number of times life knocked you down.</p>
<p>This reframes failure entirely. A fall is not evidence of weakness. It is simply a position from which you have not yet risen. The moment you stand up, the count resets. You are now someone who has risen eight times — and you are capable of rising nine.</p>

<h2>One More Rising</h2>
<p>The practical power of this proverb is its refusal to ask how many times you have fallen. It does not matter. What matters is the single question: can you rise one more time?</p>
<p>Not forever. Not infinitely. Just once more than the last fall. That is all the proverb asks. It makes the enormous task of resilience into the smallest possible act: stand up, this once, right now.</p>
<p>When you feel crushed by the accumulation of failures, do not count the falls. Count only the risings. However many times you have been knocked down, you have risen every single time so far. Your record of rising is perfect. That record is what <em>nana korobi ya oki</em> is asking you to extend.</p>

<hr>
<p><em>Enjoyed this? Paid subscribers go deeper every week — into the Japanese philosophies that change how you work, speak, and think. <a href='#'>Subscribe to read →</a></em></p>"""
})

# ── Day 2 ──────────────────────────────────────────────
articles.append({
    "day": 2,
    "japanese": "一期一会",
    "romanji": "Ichi go ichi e",
    "title": "This Moment Will Never Return",
    "subtitle": "Every encounter happens exactly once. Japanese tea masters knew this. Most of us have forgotten.",
    "body_html": """<h2>The Tea That Cannot Be Repeated</h2>
<p>In the tea ceremony tradition, the host prepares for weeks before guests arrive. They select the scroll in the alcove, arrange the flowers, choose the bowl. On the morning of the gathering, they light the charcoal and begin to heat the water. By the time the guests are seated, hours of preparation have converged into a single moment.</p>
<p>The tea master Sen no Rikyu taught his students: treat every gathering as if it will never happen again. Not as a polite fiction, but as a literal truth. Because it will not. Not this combination of people, this weather, this bowl, this silence. This tea is being drunk for the first and last time in history.</p>
<p>The phrase <em>ichi go ichi e</em> — one time, one meeting — emerged from this practice. It was a reminder whispered in the tearoom and later written on scrolls: pay attention. This is all there is, and it will not return.</p>

<h2>The Weight of Impermanence</h2>
<p>Western culture often treats impermanence as a problem to be solved. We photograph every meal, archive every conversation, build systems to preserve what we love. The anxiety beneath all of it is the same: this will end, and we are not ready.</p>
<p><em>Ichi go ichi e</em> takes the opposite approach. It does not try to preserve the moment. It asks you to be fully present in it — precisely because it cannot be preserved. The impermanence is not the tragedy. The impermanence is what makes the moment matter at all.</p>
<p>A cherry blossom that bloomed forever would not be beautiful in the Japanese sense. It is the brief, complete flowering — and then the falling — that creates <em>aware</em>, the bittersweet ache that is the deepest register of beauty. Knowing this is the last time is not sad. It is what makes the tea taste like tea.</p>

<h2>Treating Every Meeting as the Last</h2>
<p>You have had a thousand conversations with your closest friends. You can predict their stories, their opinions, the way they laugh. Familiarity has made you efficient but not present. You know how these encounters go, so you stop arriving fully.</p>
<p><em>Ichi go ichi e</em> asks a harder question: what if this is the last time? Not as a morbid thought experiment, but as a corrective to the assumption of continuity. The people you love will change. You will change. This particular version of this particular evening together has never happened before and will never happen again.</p>
<p>Put down the phone. Stop half-listening while composing your reply. Let the moment be exactly what it is. That cup of coffee, that conversation, that person sitting across from you — it is happening exactly once. The tea ceremony teaches that the appropriate response to something irreplaceable is full attention.</p>

<hr>
<p><em>Enjoyed this? Paid subscribers go deeper every week — into the Japanese philosophies that change how you work, speak, and think. <a href='#'>Subscribe to read →</a></em></p>"""
})

# ── Day 3 ──────────────────────────────────────────────
articles.append({
    "day": 3,
    "japanese": "花は桜木、人は武士",
    "romanji": "Hana wa sakuragi, hito wa bushi",
    "title": "The Standard That Changes Everything",
    "subtitle": "Among flowers, the cherry blossom. Among people, the warrior. Choose your standard carefully.",
    "body_html": """<h2>The Best Among the Best</h2>
<p>Japan has no shortage of beautiful flowers. Plum blossoms appear in February, fragrant and early. Chrysanthemums are the imperial symbol. Peonies, irises, wisteria — the list of revered blooms is long. And yet, if you ask a Japanese person to name the flower, the answer is almost always the same: <em>sakura</em>. The cherry blossom.</p>
<p>Why? Not because it is the most fragrant, or the most durable, or the most colorful. The cherry blossom blooms brilliantly for days, then falls completely, without clinging. It lives at full intensity and releases without resistance. In Japanese aesthetics, this is not just beauty — it is character.</p>
<p>The proverb pairs this with the warrior: among people, the ideal is the <em>bushi</em>, the samurai. The comparison is not about violence. It is about a person who holds to a code even when it costs them, who faces uncertainty without flinching, whose character holds under pressure the way the cherry blossom holds its color in wind and rain — until it is time to let go entirely.</p>

<h2>What Choosing a Standard Actually Does</h2>
<p>The deeper teaching of this proverb is about orientation. When you name your highest standard, you are not just describing an ideal — you are creating a direction. Every decision you make can now be measured against it. Not "what do I want right now?" but "what would the standard require here?"</p>
<p>This is what ethics actually is, before it becomes academic: a chosen standard that guides you when personal interest points the other way. The samurai code, <em>bushido</em>, was not a list of restrictions. It was a compass. A warrior who had truly internalized it did not need to calculate each situation from scratch. The standard had already done that work.</p>
<p>Most people today live without a chosen standard. They have preferences, habits, and social expectations — but no deliberate north star. The proverb suggests this is a significant loss. Not because you need to be a warrior, but because the clarity of a named ideal changes how you move through each day.</p>

<h2>Name Your Sakura</h2>
<p>The exercise this proverb invites is simple and surprisingly difficult: what is your cherry blossom? Not what you think you should say. Not what sounds good. What actual quality, when you see it embodied, makes you feel something pull inside you — recognition, aspiration, the quiet ache of seeing what you want to become?</p>
<p>For some it is precision — the craftsperson who never cuts corners even when no one is watching. For others it is warmth — the person who makes everyone in the room feel seen. For others still it is courage — the willingness to say the true thing at the wrong time.</p>
<p>Once you name it, you have a standard. And once you have a standard, you have a way to read every moment of your life: am I growing toward this, or drifting away from it? The cherry blossom does not wonder whether to bloom. It blooms completely, then falls. That clarity — that commitment to its own nature — is the whole point.</p>

<hr>
<p><em>Enjoyed this? Paid subscribers go deeper every week — into the Japanese philosophies that change how you work, speak, and think. <a href='#'>Subscribe to read →</a></em></p>"""
})

# ── Day 4 ──────────────────────────────────────────────
articles.append({
    "day": 4,
    "japanese": "雨降って地固まる",
    "romanji": "Ame futte ji katamaru",
    "title": "The Ground After the Rain",
    "subtitle": "After rain, the earth becomes harder. After hardship, the foundation becomes stronger.",
    "body_html": """<h2>What Rain Actually Does</h2>
<p>Before a storm, the ground is often loose — dry soil that scatters with a footstep, dust that rises in the wind. Then the rain comes. It is uncomfortable, inconvenient, sometimes violent. And when it passes, if you walk on the same ground, you find something different beneath your feet. Compact. Firm. Able to bear weight it could not hold before.</p>
<p>This is not metaphor. It is the physical mechanism that Japanese farmers and laborers noticed for centuries, and that gave rise to the proverb <em>ame futte ji katamaru</em>. The rain does not damage the ground. It consolidates it. What seemed like disruption was actually transformation.</p>
<p>The leap to human experience is not forced. We have all lived through storms — broken relationships, public failures, periods of illness or loss — that felt, while they were happening, like pure destruction. The question is what we find when we test the ground afterward. Is it looser than before, or firmer?</p>

<h2>The Mechanism of Strengthening</h2>
<p>Not every crisis strengthens. The proverb is describing a specific outcome, not a guarantee. What determines whether rain consolidates the ground or floods it away? The composition of what is already there. Ground with good structure — the right mix of minerals and organic matter — responds to rain differently than loose sand.</p>
<p>The same principle applies to people. Adversity reveals character structure. If a person has built slowly — through honest self-examination, through commitment kept even when difficult, through small actions aligned with their values — then hardship compresses and refines that structure. The crisis passes, and they are more themselves than before.</p>
<p>This is why the proverb is not naive optimism. It is not claiming that all storms lead to strengthening. It is pointing to a process and asking: are you building the kind of ground that rain hardens rather than erodes? The preparation happens before the storm.</p>

<h2>Testing the Ground You Stand On</h2>
<p>After a period of difficulty — whatever yours has been — there is an important question to ask. Not "what did I lose?" but "what did the difficulty reveal that I did not know was there?"</p>
<p>Every crisis is a geological survey. It shows you where the bedrock is, and where you have been standing on loose soil without realizing it. The relationship that fell apart under pressure: was it weak from the beginning, or did external stress expose a solvable problem? The project that collapsed: was there a flaw in the foundation, or was the execution simply under-resourced?</p>
<p>The ground after the rain is harder because the water has filled the spaces between particles and bound them together. After your hardship, what has been bound together that was separate before? What do you know now — about yourself, about what matters — that the easier seasons would never have shown you? That knowledge is the hardened ground. That is where you build what comes next.</p>

<hr>
<p><em>Enjoyed this? Paid subscribers go deeper every week — into the Japanese philosophies that change how you work, speak, and think. <a href='#'>Subscribe to read →</a></em></p>"""
})

# ── Day 5 ──────────────────────────────────────────────
articles.append({
    "day": 5,
    "japanese": "禍福は糾える縄の如し",
    "romanji": "Kafuku wa azanaeru nawa no gotoshi",
    "title": "The Rope of Fortune",
    "subtitle": "Misfortune and blessing are twisted together like strands in a rope. You cannot have one without the other.",
    "body_html": """<h2>The Rope in Your Hands</h2>
<p>Hold a length of traditional Japanese rope. Look closely at how it is made. Individual fibers are twisted into threads, threads are twisted into strands, strands are twisted together into the rope itself — each twist going in the opposite direction from the last, so the tensions hold each other and the whole becomes strong.</p>
<p>You cannot separate good fortune from misfortune in this rope. They are structurally the same material, twisted into each other. Pull one out and the other collapses. This is what the ancient Chinese tale that underlies this proverb was teaching: a farmer loses his horse (misfortune) → the horse returns with wild horses (fortune) → his son breaks his leg taming a wild horse (misfortune) → the son cannot be drafted into a war in which most young men die (fortune). The story does not end. Each turn contains the seed of its opposite.</p>
<p><em>Kafuku wa azanaeru nawa no gotoshi</em> is not about accepting bad luck with a shrug. It is a structural observation about how fortune actually works — not as discrete events but as a continuous, intertwined process that cannot be evaluated in real time.</p>

<h2>The Evaluation Problem</h2>
<p>We are constantly grading our experiences: this is good, this is bad, this development is fortunate, that one is a disaster. We do this automatically, instantly, and with great confidence. The proverb suggests this grading is almost always premature.</p>
<p>The job you did not get was a disaster — until it freed you for the opportunity that changed your life. The relationship that ended was devastating — until the solitude forced a self-understanding that made every subsequent relationship more honest. The business failure was catastrophic — until the lessons it deposited became the foundation for something that actually worked.</p>
<p>This is not to say that misfortune always converts to fortune, or that suffering is secretly wonderful. It is to say that you almost never have enough context, in the moment, to accurately evaluate what is happening to you. The rope keeps being twisted. What looks like pure disaster from inside the disaster often looks different from two years later.</p>

<h2>The Practice of Suspension</h2>
<p>What the proverb offers, practically, is permission to suspend final judgment. Not to feel nothing — feelings are appropriate, and the proverb is not teaching stoic numbness. But to hold your evaluation loosely. To say: this is difficult now, and I do not yet know what this will have been.</p>
<p>There is a phrase in Japanese: <em>ma</em> — the space between events, the pause before the next thing. The proverb is inviting you into that space. Before you decide that the setback is final, before you conclude that the windfall has solved everything, wait. Watch the rope being twisted. Notice how the strands interact.</p>
<p>The practical benefit is not philosophical detachment. It is resilience. When you deeply understand that misfortune and fortune are twisted together — that neither state is permanent, that each contains the energy of its opposite — you become harder to destroy by bad luck and harder to corrupt by good luck. You hold both more lightly. And holding them lightly is the only way to keep making clear decisions while the rope of your life continues to twist.</p>

<hr>
<p><em>Enjoyed this? Paid subscribers go deeper every week — into the Japanese philosophies that change how you work, speak, and think. <a href='#'>Subscribe to read →</a></em></p>"""
})

# ── Day 6 ──────────────────────────────────────────────
articles.append({
    "day": 6,
    "japanese": "人生意気に感ず",
    "romanji": "Jinsei iki ni kanzu",
    "title": "The Unreasonable Life",
    "subtitle": "We are moved by spirit, not calculation. The things worth doing rarely make rational sense.",
    "body_html": """<h2>The Thing That Cannot Be Explained</h2>
<p>Someone asks you why you are doing this — spending years on something uncertain, investing in a person others have written off, defending a position that costs you socially. You try to explain. The reasons you find sound thin even to you. Not because there are no reasons, but because the real reason is not rational.</p>
<p>You are moved by something. A quality in the person, a rightness in the cause, something you recognize without being able to fully name. This is what <em>iki</em> describes — spirit, vital energy, the quality of being fully, authentically alive in a particular moment or commitment. And <em>jinsei iki ni kanzu</em> says: this is how life should be lived. Moved by spirit.</p>
<p>The samurai who followed a lord who had lost everything did not do it because the calculations favored loyalty. The craftsperson who spent thirty years mastering a technique that no one would pay properly for did not do it because of a sound business plan. They were moved by something the spreadsheet cannot capture.</p>

<h2>What Spirit Actually Is</h2>
<p><em>Iki</em> in Japanese culture is a complex aesthetic concept — it implies a kind of refined, unselfconscious aliveness. Not flashy, not performative, but genuinely present and engaged. A person with <em>iki</em> is not trying to look passionate; they simply are. Their commitment has a quality of naturalness, of inevitability.</p>
<p>This is the opposite of the modern optimization mindset, which approaches major life decisions the same way it approaches which toothpaste to buy: gather data, compare options, calculate expected value. The optimization mindset is useful for many things. But applied to questions of how to spend a life, it produces a peculiar paralysis — because the things that genuinely matter are not the things with the clearest data.</p>
<p>The proverb is not anti-rational. It is not saying ignore consequences, leap without looking. It is saying that the animating force of a meaningful life is not reason. Reason is the servant, not the master. First you are moved by spirit. Then reason helps you figure out how to answer that call.</p>

<h2>Finding What Moves You</h2>
<p>The diagnostic question this proverb offers is: what moves you? Not what should move you, not what would look good if it moved you. What actually, in practice, pulls you forward without requiring constant self-persuasion?</p>
<p>Most people can answer this with a little honesty. There are domains where motivation feels effortless, where you lose track of time, where you find yourself curious beyond what the external rewards would justify. This is not accidental. It is information about what your particular <em>iki</em> is responding to.</p>
<p>The proverb suggests that building your life toward what moves you is not self-indulgence. It is alignment. A person acting from genuine <em>iki</em> — from authentic inner movement — brings a quality of presence and commitment that cannot be manufactured by any incentive structure. They do not need to be reminded why they care. They are already moved. That quality is rare and unmistakable, and it is what the proverb is asking you to cultivate in yourself.</p>

<hr>
<p><em>Enjoyed this? Paid subscribers go deeper every week — into the Japanese philosophies that change how you work, speak, and think. <a href='#'>Subscribe to read →</a></em></p>"""
})

# ── Day 7 ──────────────────────────────────────────────
articles.append({
    "day": 7,
    "japanese": "明日は明日の風が吹く",
    "romanji": "Ashita wa ashita no kaze ga fuku",
    "title": "Tomorrow's Wind",
    "subtitle": "Tomorrow, tomorrow's wind will blow. Why exhaust yourself today preparing for weather that hasn't arrived?",
    "body_html": """<h2>The Forecast You Cannot Make</h2>
<p>You have been awake at 3am, running the scenarios. What if this fails? What if that person reacts badly? What if the project collapses, the money runs out, the relationship changes, the opportunity disappears? The mind, given silence and darkness, becomes a probability engine running catastrophe calculations.</p>
<p>This is not irrational. Future threats are real. Planning matters. But there is a version of this that is not planning — it is suffering in advance for things that have not happened and may never happen. The Japanese have a name for the corrective: <em>ashita wa ashita no kaze ga fuku</em>. Tomorrow, tomorrow's wind will blow.</p>
<p>The image is precise. Wind is real, wind matters, wind changes what is possible. But tomorrow's wind is unknowable from today. You cannot feel it yet, cannot lean into it or shelter from it, because it does not exist yet. To spend today's energy bracing against tomorrow's unknown wind is to exhaust yourself before the weather even arrives.</p>

<h2>Worry as a Misuse of Imagination</h2>
<p>Worry is imagination applied to the future without the constraint of what is actually known. It takes the real uncertainties of life and populates them with specific negative outcomes — not because those outcomes are most likely, but because the mind prefers a terrible known scenario to a genuinely open unknown.</p>
<p>The proverb does not say the future is fine. It says the future will bring its own conditions, and those conditions will require responses that you cannot fully prepare in advance. The samurai who spent the night before battle in anxious rehearsal of every possible wound was not better prepared than the one who slept deeply and arrived rested. The battle would bring what it brought. Clear eyes and a rested body were the actual asset.</p>
<p>This is not fatalism or passivity. It is a precise insight about where preparation ends and where anxiety begins. Preparation asks: what can I do today that will genuinely help? Anxiety asks: what disaster can I imagine that I cannot yet solve? One is useful. The other burns tomorrow's wind before it has arrived.</p>

<h2>What Today's Wind Actually Requires</h2>
<p>The implicit second half of this proverb is: today's wind is blowing right now. That is the weather you can actually feel, lean into, navigate. The question of what tomorrow holds is less urgent than the question of whether you are fully present to what today requires.</p>
<p>Most chronic anxiety is a form of temporal displacement — living in a simulated future instead of the actual present. The meetings you are dreading have not started. The conversation you are rehearsing has not been had. The crisis you are bracing for has not arrived. Meanwhile, the actual day — the one with real people and real opportunities and real small decisions that compound into a life — passes in a blur of pre-suffering.</p>
<p>Tomorrow, tomorrow's wind will blow. And when it does, you will respond to it with whatever resources today has left you. The best way to prepare for that unknown wind is not to worry about it now. It is to show up fully for the wind that is blowing today — to make the decisions, do the work, be present with the people in front of you. That is what builds the capacity to handle whatever comes next.</p>

<hr>
<p><em>Enjoyed this? Paid subscribers go deeper every week — into the Japanese philosophies that change how you work, speak, and think. <a href='#'>Subscribe to read →</a></em></p>"""
})

# ── Day 8 ──────────────────────────────────────────────
articles.append({
    "day": 8,
    "japanese": "成せば成る",
    "romanji": "Naseba naru",
    "title": "The Power of True Commitment",
    "subtitle": "If you do it, it will be done. Three words that collapse the distance between intention and reality.",
    "body_html": """<h2>The Three Words That Change Everything</h2>
<p>Japanese has a remarkable capacity for compression. Three syllables — <em>na-se-ba na-ru</em> — carry a logic so tight it borders on mathematical. If you do, it becomes. If you act, it is achieved. The conditional is everything: not "if you try," not "if you hope," not "if circumstances cooperate." If you <em>do</em>.</p>
<p>This proverb belongs to a cluster of Japanese sayings about the relationship between will and outcome. But it is the most minimal, the most uncompromising. It removes all the hedges. It does not say "if you work hard." It does not say "if you persist." It says: if you do the thing, the thing gets done. The causation is absolute and the logic is circular in the best possible way — action creates the result that action aimed at.</p>
<p>The warlord Uesugi Yozan, who saved his domain from bankruptcy through extraordinary discipline and personal sacrifice, had this proverb inscribed as a guiding principle. It was not an inspiration poster. It was a governing philosophy. If it must be done, do it. If you do it, it will be done.</p>

<h2>The Doing That Most People Skip</h2>
<p>The problem <em>naseba naru</em> solves is not a motivational problem. Most people are motivated. They want to write the book, build the business, repair the relationship, develop the skill. The deficit is not desire.</p>
<p>The deficit is in the transition from wanting to doing — the moment where the abstract aspiration must become a specific action in real time. This transition is harder than it looks, because desire can exist indefinitely without producing action, and we have learned to mistake thinking about the thing for doing the thing. We research the project extensively and feel like we have worked on it. We draft plans in our heads and feel like we have begun.</p>
<p><em>Naseba naru</em> is a blade that cuts through all of this. It asks: have you actually done the thing, or have you done everything adjacent to the thing? Wanting is not doing. Planning is not doing. Talking about doing is not doing. The proverb has no room for any of it. Only the act itself counts.</p>

<h2>Starting Where You Are</h2>
<p>The most useful application of <em>naseba naru</em> is in the moment when you have been circling a task — knowing you need to do it, finding reasons to delay, waiting for the right conditions or the right mood or more information or a better plan. The proverb cuts the loop: do it now, with what you have.</p>
<p>The conditions will never be perfect. The mood will rarely arrive without the action. The information will keep multiplying. The plan will keep being revised. These are not prerequisites for action — they are the ways the mind extends the gap between intention and the actual doing.</p>
<p>Three syllables: <em>naseba naru</em>. If you do it, it will be done. The smallest concrete action toward your real goal — not a preparation for the action, not a plan about the action, the action itself — is worth more than any amount of perfect readiness. The readiness comes from the doing. That is what the proverb has been trying to tell us all along.</p>

<hr>
<p><em>Enjoyed this? Paid subscribers go deeper every week — into the Japanese philosophies that change how you work, speak, and think. <a href='#'>Subscribe to read →</a></em></p>"""
})

# ── Day 9 ──────────────────────────────────────────────
articles.append({
    "day": 9,
    "japanese": "為せば成る、為さねば成らぬ何事も",
    "romanji": "Naseba naru, nasaneba naranu nanigoto mo",
    "title": "The Willing Heart",
    "subtitle": "Do, and it becomes. Don't, and it never will. Nothing in this world is exempt from this law.",
    "body_html": """<h2>The Complete Law</h2>
<p>The short form, <em>naseba naru</em>, is a promise. This longer version is something more demanding: a complete law, stated in both its positive and negative forms, then sealed with the absolute — <em>nanigoto mo</em>, in all things, with no exceptions.</p>
<p>Do, and it becomes. Do not, and it never will. In all things.</p>
<p>The full proverb comes from Uesugi Yozan, a feudal lord who inherited a domain on the edge of collapse. His full declaration continues: "Not doing is due to the lack of a willing heart, not to a lack of ability." This final line is the philosophical payload. The obstacle to great achievement is almost never incapacity. It is the unwilling heart — the heart that wants the outcome without embracing the doing.</p>

<h2>The Difference Between Ability and Will</h2>
<p>We have become sophisticated at attributing inaction to inability. I am not a creative person. I do not have that kind of mind. I was not born with the talent for this. Some people can, I cannot. These statements are often sincere — and almost always incorrect.</p>
<p>The research on skill development has spent decades documenting what Japanese wisdom encoded centuries ago: almost every domain of meaningful performance is learnable, and the main variable is not raw talent but sustained, effortful practice. The people who become exceptional at things are not, in most cases, the most naturally gifted. They are the people whose hearts were willing enough to do the work when it was hard, when it was boring, when progress was invisible.</p>
<p>Uesugi's addition — the unwilling heart — is not a condemnation. It is a clarification. When you say "I can't," you are usually saying "I haven't decided that this matters enough to do." That is useful information. It means the question is not about ability. It is about what you actually want, at the level beneath the stated goal.</p>

<h2>Making Your Heart Willing</h2>
<p>The practical work this proverb points to is not skill development. It is motivation — but a particular kind, not the shallow variety that surges and fades. It is the cultivation of genuine commitment: deciding that the thing matters, that the doing is worth doing, that the outcome you want is worth the cost of the process.</p>
<p>This decision cannot be manufactured by willpower alone. It comes from clarity about why. When you understand why the work matters — not abstractly, but in terms of what you actually care about — the heart becomes willing not because you force it but because it genuinely wants to.</p>
<p><em>Naseba naru, nasaneba naranu nanigoto mo.</em> In all things, without exception: do and it becomes, don't and it never will. The law is simple. What remains is the question of your heart. What is it willing to do? The answer to that question is the outline of your actual life — not the life you imagine for yourself, but the life you are building, one willing action at a time.</p>

<hr>
<p><em>Enjoyed this? Paid subscribers go deeper every week — into the Japanese philosophies that change how you work, speak, and think. <a href='#'>Subscribe to read →</a></em></p>"""
})

# ── Day 10 ──────────────────────────────────────────────
articles.append({
    "day": 10,
    "japanese": "時は金なり",
    "romanji": "Toki wa kane nari",
    "title": "Richer Than Money",
    "subtitle": "Time is money — but the Japanese understanding of this equation is far deeper than the Western version.",
    "body_html": """<h2>Benjamin Franklin's Version and the Other One</h2>
<p>You know this phrase. It comes to us through Benjamin Franklin, the archetype of Protestant work ethic and rational self-improvement. In his version, time is a resource to be optimized, invested, and not wasted. Idle hours are squandered capital. The implication is efficiency: every hour should earn its return.</p>
<p>The Japanese phrase <em>toki wa kane nari</em> is a direct translation and shares the same surface logic. But in the context of Japanese thought about time — shaped by Buddhist impermanence, Zen presence, and the aesthetic of <em>mono no aware</em> — the phrase carries a different weight. Not "time is money, so don't waste it on unproductive things." More like: "time is as precious as gold, and gold, once spent, is gone."</p>
<p>The difference is subtle but important. Franklin's version tells you to work harder. The Japanese context whispers something more uncomfortable: every hour of your life is a form of wealth you are spending, whether you notice it or not. The question is not only productivity. The question is what you are buying with this irreplaceable resource.</p>

<h2>The Asymmetry of Time</h2>
<p>Money has a property that makes the comparison instructive even beyond the cliché: it can be earned back. You can spend and replenish. You can borrow from the future and pay back later. Time does not work this way. Time spent is gone. There is no earning it back, no borrowing from a future hour to compensate for a wasted past one.</p>
<p>This asymmetry gives time a different character than any financial asset. It makes every hour a one-way door. The hour you are in right now will never be available again. Not for regret, not for different decisions, not for the conversation you chose not to have. It will simply have been — and what it will have been is determined entirely by what you do with it while it is present.</p>
<p>Japanese culture has a particular sensitivity to this. The tea ceremony, the haiku, the spare Zen garden — all of these traditions are structured around the acute appreciation of a specific moment, because the moment is understood to be finite and unreturnable. <em>Ichi go ichi e</em>: one time, one meeting. The same awareness underlies <em>toki wa kane nari</em>.</p>

<h2>What Are You Buying?</h2>
<p>If time is gold, the interesting question is not how to avoid spending it. The question is: what are you purchasing with it? You are going to spend every hour you have. The only choice is what those hours build.</p>
<p>Some hours buy experiences that become part of who you are. Some buy skills that compound over decades. Some buy relationships that sustain you in ways you cannot predict. Some buy regret. Some simply pass without leaving a trace.</p>
<p>The proverb is not telling you to be busy. It is telling you to be awake to the transaction that is always occurring. You are spending gold right now — this minute, this hour, this year. The gold is finite and non-renewable. What it purchases is entirely up to you. Make sure the exchange rate is worth it.</p>

<hr>
<p><em>Enjoyed this? Paid subscribers go deeper every week — into the Japanese philosophies that change how you work, speak, and think. <a href='#'>Subscribe to read →</a></em></p>"""
})

print(f"Days 1-10 loaded: {len(articles)} articles so far")
