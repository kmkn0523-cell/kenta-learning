# ronin_comment_templates.py
# @RoninWords リプ巡回ツール用の「英語の下書きテンプレ集」
# 他アカウントの投稿に残すコメントの候補。武士道/禅トーンで、短く・売り込まず・相手を立てる。
# ronin_reply_hunter.py から読み込まれる（純粋データのみ）。

# 6カテゴリ。各 "1"〜"6" に {name: 表示名, comments: 下書きリスト(3案以上)} を持つ。
# キーワード→カテゴリの対応は ronin_reply_hunter.py の KEYWORD_MAP 側で定義する。
COMMENT_TEMPLATES = {
    "1": {
        "name": "Discipline / habits（規律・習慣）",
        "comments": [
            "Discipline isn't punishment. It's the kindest thing you can do for your future self.",
            "The habit you keep on the hard days is the only one that counts. Respect.",
            "Motivation gets you to the door. Discipline is what walks you through it. Good words.",
            "Small reps, repeated past the point of boredom. That's where it's forged.",
            "Consistency is just discipline that stopped needing applause. Well said.",
            "The bushido way: the standard doesn't move on the days you don't feel like it.",
            "What's the one habit you refuse to skip, even on your worst days?",
            "Curious how you made discipline stick after the motivation wore off?",
        ],
    },
    "2": {
        "name": "Resilience / adversity（逆境・打たれ強さ）",
        "comments": [
            "The blade is sharpened by what resists it. This setback is doing quiet work on you.",
            "Falling isn't failing. Staying down is. Glad you got back up.",
            "The rice stalk bows in the storm and rises after. Bending isn't breaking.",
            "Scars are proof the lesson landed. Carry it, don't hide it.",
            "Seven times down, eight times up — nana korobi ya oki. You're living it.",
            "Hard seasons don't ask permission. They just sharpen whoever stays standing.",
            "What got you back on your feet the last time you were knocked down?",
            "How do you tell the difference between bending and breaking?",
        ],
    },
    "3": {
        "name": "Focus / distraction（集中・誘惑）",
        "comments": [
            "A divided mind cuts nothing. Picking one thing today is the whole battle.",
            "The empty cup pays attention. Hard to fill a mind that's already full of noise.",
            "Depth beats speed. The river that goes deep runs quiet. Strong reminder.",
            "Most 'busy' is just fear wearing a costume. Choosing one cut is courage.",
            "Distraction is a thousand small surrenders. One focused hour answers them all.",
            "Single-task like a swordsman: one target, one breath, one strike.",
            "What's the one thing you're cutting everything else for right now?",
            "How do you guard your attention when the noise gets loud?",
        ],
    },
    "4": {
        "name": "Stoic / mindset（ストイック・心の在り方）",
        "comments": [
            "Control the grip, not the storm. You're pointing at the only thing that's yours.",
            "Calm isn't the absence of the fight. It's refusing to be moved inside it.",
            "Fear shrinks the moment you name it and step toward it. Good to see you naming it.",
            "The mind is the dojo. What you rehearse there, you become out here.",
            "You can't still the waves, but you can stop being surprised by them. Wisdom.",
            "Mono no aware — feel it fully, then let it pass. Holding on is the only suffering.",
            "What helped you find calm in the middle of it?",
            "How do you remind yourself to control the grip, not the storm?",
        ],
    },
    "5": {
        "name": "Mastery / craft（熟達・鍛錬）",
        "comments": [
            "Mastery is a thousand quiet repetitions nobody saw. This is the work.",
            "The whetstone takes a little metal every pass. That's the price of an edge.",
            "Amateurs chase the trick. Masters polish the basics until the basics shine.",
            "Shu-ha-ri: keep the form, break the form, become the form. You're on the path.",
            "The craft doesn't reward the loud. It rewards the one who shows up again.",
            "Skill is just patience that refused to quit. Keep grinding the stone.",
            "What basic did you polish longest before it finally clicked?",
            "How many quiet reps in before you felt the edge sharpen?",
        ],
    },
    "6": {
        "name": "Purpose / meaning（目的・意味）",
        "comments": [
            "A sword without a cause is just sharp metal. The 'why' is what aims the blade.",
            "Ikigai isn't found. It's forged by what you keep choosing on ordinary days.",
            "Direction beats speed. A man who knows his 'why' never wastes a step.",
            "The empty path is the loud one. The chosen path is quiet and yours.",
            "Live like ichi-go ichi-e — this moment won't return. Spend it on what matters.",
            "Purpose isn't a feeling you wait for. It's a decision you keep making. Well put.",
            "What's the 'why' that aims your blade these days?",
            "How did you find the direction you keep choosing?",
        ],
    },
}

# どのカテゴリにも当てはまらなかった時の汎用テンプレ（取りこぼしゼロ用・3案以上）
GENERIC_TEMPLATES = [
    "Strong words. This is the kind of thing a man rereads on a hard morning.",
    "Saved this. Quiet truth, no noise. Respect.",
    "There's a whole discipline hidden in this one line. Thanks for sharing it.",
    "This lands. Simple, true, and hard to live — the best kind.",
    "Needed this today. The path is clearer for the reminder.",
    "Said plainly, which is the hardest way to say something true. Well done.",
]
