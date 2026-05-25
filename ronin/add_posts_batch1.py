"""
threads_posts.json に day61〜100 の投稿テキストを追加するスクリプト
（一回限りの実行スクリプト。実行後は削除する）
"""

import json
import os

# ファイルパスを設定する
POSTS_FILE = os.path.join(os.path.dirname(__file__), "threads_posts.json")

# ハッシュタグ（全dayで共通）
HASHTAGS_A = ["#JapaneseWisdom", "#Bushido", "#Mindset", "#Stoicism", "#Philosophy", "#RoninWords", "#Ronin"]
HASHTAGS_B = ["#DailyHabit", "#Discipline", "#Mastery", "#Growth", "#Action", "#RoninWords", "#Consistency"]
HASHTAGS_C = ["#Mindfulness", "#SelfAwareness", "#Courage", "#Resilience", "#RoninWords", "#Inspiration"]

# day61〜100 の投稿テキストを定義する
new_posts = [
    {
        "day": 61,
        "morning": "What you leave out\noften matters more than\nwhat you put in.\n\n間\nMa\n\n\"The power of the space between.\"\n\nIn Japanese music, the pause is not silence.\nIt is tension.\nExpectation.\nBreath.\n\nIn conversation, the space before your answer\nreveals more than the answer itself.\n\nIn design, emptiness guides the eye.\nIn a room, the gap between people\nis where honesty lives.\n\nMost people rush to fill the space.\nThe master knows:\nthe space is where everything happens.\n\n#Presence #Silence",
        "evening": "You don't need to fill every silence.\nSome spaces are not empty.\n\nThey are where the truth waits.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 62,
        "morning": "You won't find it.\nYou walk it.\n\n道\nDo\n\n\"The Way. A lifelong path of becoming.\"\n\nThe word 道 appears in everything:\nKendo. Judo. Chado. Bushido.\n\nNot because all things are the same.\nBecause all mastery\nshares the same quality:\n\nIt never ends.\n\nThe craftsman who thinks he's finished\nhas left the path.\nThe one who knows there is always further\nhas already arrived.\n\nWhat is your Way?\nAnd are you actually walking it?\n\n#ThePath #Mastery",
        "evening": "The destination is not the point.\nThe walking is.\n\nBecome the kind of person\nwho keeps walking.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 63,
        "morning": "Comfort never made anyone great.\n\n七難八苦を乗り越えてこそ\nShichinin hakku o norikoete koso\n\n\"Only through great trials\ndoes greatness emerge.\"\n\nSeven difficulties. Eight pains.\nThat is the old formula for a life well-forged.\n\nThe warrior who only trained in comfort\nshattered under pressure.\nThe one who had been tested —\nwho had lost, failed, stood back up —\nheld together when it mattered.\n\nYour hardest seasons\nare not interruptions.\nThey are the forge.\n\n#Resilience #Trials",
        "evening": "The years that broke you\nmade you what you are.\n\nDon't waste them\nby pretending they didn't happen.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 64,
        "morning": "Results are slow.\nThat's the point.\n\n辛抱する木に金がなる\nShinbo suru ki ni kane ga naru\n\n\"The tree that endures\nbears golden fruit.\"\n\nA tree does not panic in winter.\nIt does not demand fruit before its season.\nIt roots deeper. Waits longer.\n\nThe people we admire most\nlook like overnight successes.\nThey were not.\n\nThey were trees in winter.\nWaiting with the patience\nmost people never develop.\n\nWhat are you growing\nthat just needs more time?\n\n#Patience #LongGame",
        "evening": "The fruit comes after the roots.\nThe roots come before anyone notices.\n\nKeep going in the dark.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 65,
        "morning": "The worst days are building something.\n\n苦は楽の種\nKu wa raku no tane\n\n\"Suffering is the seed of joy.\"\n\nEvery craft has a phase\nwhere it only takes from you.\nEnergy. Time. Confidence.\n\nYou give and give\nand nothing grows.\n\nThis is not failure.\nThis is the seed stage.\n\nBeneath the surface,\nroots are forming.\nFoundations hardening.\n\nThe gardener who digs up the seed\nto check if it's growing\nkills it.\n\nTrust the process.\nThe suffering is the seed.\n\n#GrowthMindset #Trust",
        "evening": "Tomorrow's ease\nis built from today's effort.\n\nPlant something tonight\nyou'll be grateful for later.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 66,
        "morning": "Bend. But never break.\n\n百折不撓\nHyakusetsu futo\n\n\"Bend a hundred times,\nbut never break.\"\n\nThe bamboo survives the storm\nnot because it is rigid —\nbut because it bends completely\nand returns.\n\nRigid trees fall.\nBamboo survives.\n\nStrength is not about refusing to move.\nIt is about moving —\nfully, dramatically —\nand coming back.\n\nHow many times have you already bent\nand returned?\nThat is your real strength.\n\n#Perseverance #Adaptability",
        "evening": "You have bent before.\nYou came back.\n\nThis time is no different.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 67,
        "morning": "The moment you think you've won,\nyou've already started losing.\n\n高慢は損気\nKoman wa sonki\n\n\"Arrogance invites loss.\"\n\nEvery great defeat in history\nhas arrogance somewhere in its story.\n\nThe general who underestimated.\nThe champion who stopped training.\nThe business that mocked the upstart.\n\nHumility is not weakness.\nIt is information processing.\nIt keeps you learning\nwhen pride would shut you down.\n\nStay hungry.\nStay curious.\nStay a student.\n\n#Humility #Mindset",
        "evening": "The one who thinks they've arrived\nis usually the one\nbeing passed right now.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 68,
        "morning": "Talking about what you know\nshows the edge of it.\n\n自慢は知恵の行き止まり\nJiman wa chie no yukidomari\n\n\"Boasting is where wisdom ends.\"\n\nThe truly wise rarely announce themselves.\nThey're too busy learning.\n\nBoasting requires certainty.\nCertainty closes curiosity.\nClosed curiosity stops growth.\n\nThe person loudest about their expertise\nis usually the one\nmost threatened by new information.\n\nKnow what you know.\nKnow what you don't.\nLet the work speak.\n\n#Wisdom #Humility",
        "evening": "Wisdom grows in silence.\nBoasting shrinks it.\n\nLet your actions\nspeak first.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 69,
        "morning": "Gratitude is a strategy.\n\n不足を言うな、有余を言え\nFusoku o iu na, yuyo o ie\n\n\"Don't speak of what's missing.\nSpeak of what you have.\"\n\nComplaining is easy.\nInventorying what you lack\ntakes no skill.\n\nBut what do you actually have?\nCapability. Relationships. Time.\nExperience. Options.\n\nThe warrior who could only see\nwhat he didn't have\nwas already defeated.\n\nThe one who saw what he had\nbuilt his strategy from there.\n\nWhat are your real assets?\nStart there.\n\n#Gratitude #Perspective",
        "evening": "You have more than you realize.\n\nCount it.\nAll of it.\nThen move.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 70,
        "morning": "Wanting less is not poverty.\nIt's a different kind of wealth.\n\n小欲知足\nShoyoku chisoku\n\n\"Small desires,\ndeep contentment.\"\n\nThe pursuit of more\nhas no natural stopping point.\nYou reach what you wanted.\nAnd immediately recalibrate upward.\n\nThis is not ambition.\nThis is a treadmill.\n\nThe samurai who had enough\nfought without desperation.\nHis clarity was his advantage.\n\nWhat if enough is\ncloser than you think?\n\n#Contentment #Minimalism",
        "evening": "Enough is not a limit.\nIt's a foundation.\n\nBuild from there.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 71,
        "morning": "The hungriest person in the room\nis not always the most powerful.\n\n無欲は大欲に勝る\nMuyoku wa taiyoku ni masaru\n\n\"Wanting nothing\nis greater than wanting everything.\"\n\nDesire is leverage over you.\nWhoever knows what you want\ncontrols you.\n\nThe negotiator who needs the deal\nalready lost.\nThe one who can walk away\nholds all the power.\n\nWanting nothing is not emptiness.\nIt is freedom.\nAnd freedom is the highest form of strength.\n\n#Freedom #Detachment",
        "evening": "He who needs nothing\ncan give everything.\n\nRelease what you're gripping.\nFeel what opens.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 72,
        "morning": "Feel everything.\nThink clearly.\nAct.\n\n熱い心、冷静な頭\nAtsui kokoro, reisei na atama\n\n\"A burning heart,\na cool head.\"\n\nPassion without clarity is chaos.\nClarity without passion is calculation.\n\nThe great warriors were not cold.\nThey burned.\n\nBut they had learned to let the fire\npower the engine\nwithout burning the house down.\n\nEmotional intelligence\nis not suppressing feeling.\nIt is directing it.\n\nWhat are you passionate about?\nHow clearly are you thinking about it?\n\n#EmotionalIntelligence #Balance",
        "evening": "The heart knows what matters.\nThe head knows how to get there.\n\nYou need both.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 73,
        "morning": "Small goals produce small people.\n\n志高く\nKokorozashi takaku\n\n\"Aim high.\"\n\nNot because you'll always hit the mark.\nBut because the trajectory matters.\n\nThe archer aimed at the moon\nfar surpassed the one\naimed at the nearby tree.\n\nYour ceiling shapes your effort.\nLow expectations produce low energy.\nHigh aims pull something extraordinary\nout of ordinary days.\n\nAim somewhere that makes you\nslightly uncomfortable.\n\nThat discomfort is information.\nYou're pointing at something real.\n\n#Ambition #Vision",
        "evening": "Aim small.\nGet small.\n\nAim beyond what you think you deserve.\nSee what happens.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 74,
        "morning": "The dream without the action\nis just a story you tell yourself.\n\n夢は大きく、行動は今\nYume wa okiku, kodo wa ima\n\n\"Dream big,\nact now.\"\n\nTwo failures, not one:\n\nThe one who dreams but never moves —\nprotecting the vision from the test of reality.\n\nThe one who moves but never dreams —\nbusy, but aimed at nothing.\n\nThe combination is rare:\nA vision that pulls you forward.\nAction taken before you're ready.\n\nWhat are you waiting for?\nThe dream is already there.\nThe action is the only missing piece.\n\n#Action #DreamBig",
        "evening": "The dream lives in the future.\nThe action lives right now.\n\nDo one thing tonight\nfor the version of yourself\nyou're trying to become.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 75,
        "morning": "What breaks you\ncan also be the weapon.\n\n弱さも強さになる\nYowasa mo tsuyosa ni naru\n\n\"Even weakness\ncan become strength.\"\n\nThe warrior born small\nmastered speed.\nThe one born slow\nmastered patience.\nThe one born with fear\nmastered courage.\n\nYour limitation is a prompt.\nA direction.\nA question mark demanding an answer.\n\nThe people who have most transformed their weaknesses\nare often the most dangerous —\nbecause they had the most reason\nto change.\n\n#Strength #GrowthMindset",
        "evening": "Your weakness points\nto your next growth.\n\nDon't avoid it.\nWalk toward it.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 76,
        "morning": "The wall is not the end.\nIt's a door that doesn't look like one yet.\n\n窮すれば通ず\nKyu sureba tsuzu\n\n\"When cornered,\na way opens.\"\n\nDesperation has produced\nmore innovation than comfort ever has.\n\nWhen you have no good options,\nyou find options that weren't visible before.\nWhen retreat is impossible,\ncreativity activates.\n\nThe greatest breakthroughs in your life\nprobably came from moments\nwhen you had no choice but to find a way.\n\nThe corner is a gift.\nYou just can't see it yet.\n\n#Resourcefulness #Breakthrough",
        "evening": "You've been here before.\nCornered. Out of options.\n\nAnd you found a way.\nThis is no different.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 77,
        "morning": "The cracks are not the damage.\nThey're the story.\n\n金継ぎ\nKintsugi\n\n\"Repair with gold.\nThe break becomes beauty.\"\n\nKintsugi is the Japanese art\nof repairing broken pottery with gold.\n\nNot hiding the damage.\nHighlighting it.\n\nThe philosophy: what has been broken\nand repaired\nis more beautiful than what was never broken.\n\nYour failures, losses, and setbacks\nare not blemishes to hide.\nThey are the gold lines\nthat make you who you are.\n\nWear your history.\n\n#Kintsugi #Resilience",
        "evening": "The repaired piece\nholds the memory of breaking\nand the proof of recovery.\n\nSo do you.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 78,
        "morning": "Commitment is when retreat\nis no longer an option.\n\n背水の陣\nHaisui no jin\n\n\"No retreat —\nor you drown.\"\n\nThe ancient general burned the boats.\nNot to be dramatic.\nTo be clear.\n\nWhen retreat is possible,\npart of the mind always considers it.\nWhen it isn't —\nthat energy becomes forward momentum.\n\nWhat in your life needs the boats burned?\nWhat would change\nif you fully committed\nwith no exit strategy?\n\nNot every goal needs this.\nBut the right ones do.\n\n#Commitment #AllIn",
        "evening": "Half-commitment produces\nhalf-results.\n\nDecide fully.\nOr don't decide at all.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 79,
        "morning": "Where are you\nright now?\n\n一所懸命\nIsshoukenmei\n\n\"Be fully here.\nOr not at all.\"\n\nOne place. One life.\nThat is the literal meaning.\n\nThe samurai fought with everything\nbecause the alternative was death.\nHalf-presence was half-commitment.\nHalf-commitment was losing.\n\nYou are not fighting for your life.\nBut you are spending it.\n\nThe meeting you're half-attending.\nThe conversation you're barely in.\nThe work you're doing distracted.\n\nBe here.\nFully.\nOr be somewhere else fully.\n\n#Presence #Focus",
        "evening": "What are you only half-present for?\n\nBe there fully.\nOr leave it.\nBoth are honest.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 80,
        "morning": "The flower falls.\nThe tree stands.\n\n桜散る、されど根は残る\nSakura chiru, saredo ne wa nokoru\n\n\"The cherry blossom falls,\nbut the roots remain.\"\n\nEverything visible ends.\nPeaks fade. Seasons turn.\nWhat looked permanent wasn't.\n\nBut beneath?\nThe roots hold.\n\nYour reputation — built slowly.\nYour relationships — tended over years.\nYour character — forged through difficulty.\n\nThese are roots.\nThey outlast every season.\n\nBuild what lasts underground\nand the blossoms will return.\n\n#Roots #Longevity",
        "evening": "Let the season end.\nLet the blossom fall.\n\nWhat is rooted in you\ncannot be taken.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 81,
        "morning": "Good preparation\nmakes extraordinary things ordinary.\n\n鬼に金棒\nOni ni kanabo\n\n\"The strong,\nmade even stronger.\"\n\nA demon with an iron club.\nAlready fearsome. Now unstoppable.\n\nThe principle: advantage compounds.\nStrength built on strength.\nSkill layered on skill.\n\nYou don't need to be exceptional at everything.\nYou need your strengths\nreinforcing each other.\n\nWhat is your iron club?\nAnd how are you sharpening it?\n\n#Compounding #Strengths",
        "evening": "Your edge, sharpened daily,\nbecomes something others\ncannot compete with.\n\nSharpen tonight.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 82,
        "morning": "Stop waiting\nfor the right season.\n\n春夏秋冬、それぞれに美しい\nShunkashuto, sorezore ni utsukushii\n\n\"Every season\nhas its own beauty.\"\n\nSpring is not better than winter.\nSummer is not better than autumn.\n\nEach is complete. Each is enough.\n\nYou are in a season right now.\nMaybe it's not the season you planned.\nMaybe it's harder, slower, quieter\nthan you hoped.\n\nBut it has its own beauty.\nIts own lessons.\nIts own gifts.\n\nStop waiting for the next season\nto start living.\n\n#Seasons #Presence",
        "evening": "This season —\nwhatever it is —\nwon't come again.\n\nFind what's beautiful in it.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 83,
        "morning": "Everything ends.\nThat is not the tragedy.\nHow you hold it is.\n\n形あるものはいつか壊れる\nKatachi aru mono wa itsuka kowareru\n\n\"Everything that has form\nwill one day break.\"\n\nThe company. The relationship.\nThe body. The city. The civilization.\n\nKnowing this is not pessimism.\nIt's clarity.\n\nWhen you know something will end,\nyou stop taking it for granted.\nYou hold it with open hands.\nYou are present for it.\n\nImpermanence is not the enemy.\nClinging to permanence is.\n\n#Impermanence #Acceptance",
        "evening": "What would you do differently today\nif you truly knew\nit could be the last time?\n\nAct on that answer.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 84,
        "morning": "Don't calculate.\nFeel. Then move.\n\n人生意気に感ず\nJinsei iki ni kanzu\n\n\"Live by passion,\nnot by calculation.\"\n\nCalculation is necessary.\nBut a life run entirely on spreadsheets\nis a life half-lived.\n\nThe moments you remember most\nwere probably not optimized.\nThey were felt.\nResponded to.\nJumped at.\n\nPassion is not recklessness.\nIt is responding to what is alive in you\nbefore you talk yourself out of it.\n\nWhat are you talking yourself out of\nthat your gut already approved?\n\n#Passion #Authenticity",
        "evening": "What did you do today\nthat came from the gut,\nnot the spreadsheet?\n\nDo more of that.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 85,
        "morning": "At their peak, both are brief.\nBoth are beautiful.\nBoth are worth everything.\n\n花は桜木、人は武士\nHana wa sakuragi, hito wa bushi\n\n\"Among flowers, the cherry blossom.\nAmong men, the warrior.\"\n\nThe cherry blossom is prized\nnot despite its brevity —\nbut because of it.\n\nThe warrior lived by the same code.\nFull commitment. Short arc.\nBlazing and then gone.\n\nYou don't have to be a warrior.\nBut you can ask:\nWhat would it mean to live fully,\nknowing it ends?\n\n#LivingFully #Bushido",
        "evening": "Short and fully lived\nbeats long and half-present.\n\nDon't waste the season\nyou're in right now.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 86,
        "morning": "Good luck and bad luck\nare the same rope.\n\n禍福は糾える縄の如し\nKafuku wa azanaeru nawa no gotoshi\n\n\"Fortune and misfortune\nare twisted like rope.\"\n\nThe threads cannot be separated.\nYour greatest disaster\ncreated the conditions for your greatest breakthrough.\nYour biggest win\ncontained the seeds of your next test.\n\nThis is not pessimism.\nIt is pattern recognition.\n\nYou stop celebrating wins as final.\nYou stop mourning losses as permanent.\nYou ride the rope.\n\nWhat loss became a gift?\nWhat win became a warning?\n\n#Duality #Perspective",
        "evening": "The bad thing that happened\nmight be the good thing\nyou haven't recognized yet.\n\nGive it time.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 87,
        "morning": "The hard times are not interruptions.\nThey are the ground hardening beneath you.\n\n雨降って地固まる\nAme futte ji katamaru\n\n\"After the rain,\nthe ground grows harder.\"\n\nRain makes things difficult.\nMud. Cold. Slow progress.\n\nBut the ground that has been rained on\nis more solid than the dry dust.\nMore able to support weight.\nMore resistant to erosion.\n\nYour difficult period\nis compressing and solidifying something in you.\n\nWhen the sun returns,\nyou will stand on ground\nyou couldn't have stood on before.\n\n#Hardship #Perseverance",
        "evening": "The storm passes.\nThe ground remains —\nfirmer than before.\n\nYou will too.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 88,
        "morning": "Say less.\nMean it completely.\n\n男子の一言、金鉄の如し\nDanshi no ichigon, kintetsu no gotoshi\n\n\"A person's word is iron.\"\n\nIn a world of notifications and noise,\nwords have become cheap.\nPromises are hedged.\nCommitments are soft.\n\nThe samurai's word was binding.\nNot legally. Personally.\nViolating it was worse than death.\n\nYou don't have to be a samurai.\nBut what if you treated your word\nas iron?\n\nWho would trust you more?\nHow much more would you accomplish?\n\n#Integrity #WordIsLaw",
        "evening": "Mean what you say.\nSay only what you mean.\n\nThis alone\nsets you apart.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 89,
        "morning": "The name outlasts the body.\nBuild one worth outlasting you.\n\n死して不朽の名を残せ\nShishite fukyu no na o nokose\n\n\"Die and leave a name\nthat never fades.\"\n\nReputation is not vanity.\nIt is the echo you leave behind.\n\nThe teacher remembered decades later.\nThe leader whose principle still runs the team.\nThe parent whose voice still guides the child.\n\nYou are building something\nthat will outlive you.\nAre you building it deliberately?\n\nYour name — how it's spoken,\nby whom, after you're gone —\nthat is the measure.\n\n#Legacy #Reputation",
        "evening": "What will people say\nwhen you're not in the room?\n\nThat is your real reputation.\nBuild it intentionally.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 90,
        "morning": "You act more carefully\nwhen you remember\nyou could be wrong for the last time.\n\n事に臨んでは死を思え\nKoto ni nozonde wa shi o omoe\n\n\"Think of death —\nand act without hesitation.\"\n\nThis sounds grim.\nIt is the opposite.\n\nThe samurai who held death in mind\nwas freed from petty fear.\nNothing trivial could paralyze him.\nThe permanent end made the moment vivid.\n\nMemento mori — remember death —\nis not despair.\nIt is focus.\n\nIf today were your last opportunity,\nwhat would deserve your full attention?\n\n#MementoMori #Presence",
        "evening": "The awareness of ending\nmakes the moment matter.\n\nBe here.\nFully.\nWhile you can.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 91,
        "morning": "Before you begin,\nbe already at peace with all outcomes.\n\n覚悟\nKakugo\n\n\"Accept all consequences\nbefore you begin.\"\n\nFear is usually future-facing.\nWhat if this fails?\nWhat if I'm wrong?\nWhat if I lose everything?\n\nKakugo is the answer:\naccept all of it now.\nAll the bad outcomes. All the losses.\nAll the embarrassment.\n\nAccept them completely\nbefore you take the first step.\n\nThen move without the weight of fear.\nYou've already grieved what might happen.\nNow you can act.\n\n#Kakugo #Courage",
        "evening": "Prepare for the worst.\nHope for the best.\nAct as if the outcome is already settled.\n\nThat is freedom.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 92,
        "morning": "There is a code.\nMost people haven't written theirs.\n\n武士道\nBushido\n\n\"The Way of the Warrior.\"\n\nBushido was not a law.\nIt was an internal commitment\nto live by something larger than appetite.\n\nHonesty when no one is watching.\nCompassion without softness.\nCourage without recklessness.\nLoyalty without blind obedience.\n\nYou don't need the sword.\nBut the code?\n\nEvery serious person\nhas one — written or unwritten.\n\nWhat is yours?\n\n#Bushido #Code",
        "evening": "What do you stand for\nwhen no one is watching?\n\nThat is your real code.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 93,
        "morning": "Doing the right thing\nis not a feeling.\nIt's a choice.\n\n義\nGi — Rectitude\n\n\"Do what is right,\neven when it is hard.\"\n\nRectitude is the core of Bushido.\nNot courage. Not honor. Rectitude.\n\nBecause without the compass of right action,\ncourage becomes violence,\nhonor becomes pride,\nloyalty becomes complicity.\n\nDo what is right.\nNot because it's easy.\nNot because anyone will see it.\nBecause you are the kind of person\nwho does.\n\n#Gi #Integrity",
        "evening": "At the end of the day:\ndid you do what was right?\n\nNot what was easy.\nNot what was praised.\nWhat was right.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 94,
        "morning": "Strength without compassion\nis just violence with better posture.\n\n仁\nJin — Benevolence\n\n\"Compassion,\neven for your enemies.\"\n\nThe warrior who could not feel\nwas not strong — he was broken.\n\nJin requires more than strength:\nit requires the capacity to feel another's pain\nand respond to it.\n\nCompassion is not softness.\nThe surgeon's hands must be firm.\nThe leader's decision must be clear.\n\nBut the heart that cannot be moved\ncannot lead.\n\nFeel. And act from that feeling.\n\n#Jin #Compassion",
        "evening": "Who needs something from you\nthat you've been withholding?\n\nCompassion costs less\nthan you think.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 95,
        "morning": "Courage is not\nthe absence of fear.\n\n勇\nYu — Courage\n\n\"Fear acknowledged.\nAction taken anyway.\"\n\nEvery brave person was afraid.\nCourage is not the warrior\nwho felt nothing.\n\nIt is the warrior who stood there,\nknowing exactly what could go wrong,\nand moved anyway.\n\nFear is information.\nIt points to what matters.\nCourage is the decision\nto act despite the signal.\n\nWhat are you afraid of\nthat you need to walk toward today?\n\n#Yu #Courage",
        "evening": "You don't need the fear to stop.\nYou need to move\nbefore it talks you out of it.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 96,
        "morning": "How you treat people\nwho can do nothing for you\nis who you actually are.\n\n礼\nRei — Respect\n\n\"Every person\nis worthy of dignity.\"\n\nRespect in Bushido was not earned.\nIt was given.\n\nNot because everyone deserved honor —\nbut because the warrior's dignity\ndid not depend on yours.\n\nHow you treat the powerless\nis the truest measure of character.\nNot how you treat your superiors.\nNot how you treat your peers.\n\nThe difficult person.\nThe stranger.\nThe one who can't repay you.\n\n#Rei #Respect",
        "evening": "Every person you meet today\nis carrying something you don't know about.\n\nRespect that.\nAlways.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 97,
        "morning": "The first person you lie to\nis always yourself.\n\n誠\nMakoto — Honesty\n\n\"No deception.\nNot even to yourself.\"\n\nExternal honesty is table stakes.\nSelf-honesty is where it gets hard.\n\nThe story you're telling yourself\nabout why things are the way they are.\nThe blame you're directing outward\nthat belongs closer to home.\nThe problem you're framing\nas someone else's.\n\nMakoto starts inside.\nRadical honesty with yourself\nbefore anyone else.\n\nWhat are you lying to yourself about?\n\n#Makoto #SelfHonesty",
        "evening": "What did you tell yourself today\nthat you know isn't quite true?\n\nBe honest about that.\nThat is where growth starts.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 98,
        "morning": "You are the one\nwho has to live with it.\n\n名誉\nMeiyo — Honor\n\n\"You are your own judge.\"\n\nReputation is what others think.\nHonor is what you know.\n\nThe applauded decision you know was wrong.\nThe quiet choice no one saw\nthat you know was right.\n\nHonor is internal accounting.\nNo amount of external approval\ncan zero out internal debt.\nNo external criticism\ncan take away internal credit.\n\nAt the end of the day,\nyou sit alone with what you did.\n\nMake it something you can live with.\n\n#Meiyo #Honor",
        "evening": "The verdict that matters most\nis the one you give yourself\nin the quiet before sleep.\n\nWhat is your verdict tonight?",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 99,
        "morning": "Loyalty is a choice\nyou keep making.\n\n忠義\nChugi — Loyalty\n\n\"Chosen commitment,\nfully kept.\"\n\nThe samurai's loyalty was not blind.\nIt was a decision — made with eyes open.\n\nAnd then kept. Through difficulty.\nThrough doubt. Through the moments\nwhen breaking it would have been easier.\n\nModern loyalty is the same.\nThe commitment to the team.\nThe relationship. The craft. The self.\n\nNot because it's always convenient.\nBecause you decided it mattered.\nAnd decisions mean something.\n\n#Chugi #Loyalty",
        "evening": "What commitment did you keep today\nthat it would have been easy to break?\n\nThat is character.\nBuilt one day at a time.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 100,
        "morning": "100 days.\nOne truth:\nThe path never ends.\n\n武士道百訓\nBushido hyakukun\n\n\"100 days.\nOne truth.\nThe Way continues.\"\n\nYou've been here 100 days.\nIf the words landed even once —\nif one morning you moved differently\nbecause of something you read here —\n\nThe path worked.\n\nBut the path doesn't end at 100.\nIt deepens.\nEvery day another chance\nto practice what you understand.\n\nThank you for walking with me.\n\nThe Way continues.\n\n⚔️ Day 100. @RoninWords\n\n#Bushido #100Days",
        "evening": "100 days of wisdom.\nAnd still:\nthe most important lesson\nis to begin again tomorrow.\n\nSee you on day 101.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    }
]


def main():
    """threads_posts.json に day61〜100 の投稿を追加する"""

    # 現在のデータを読み込む
    with open(POSTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 既存のday番号を確認する
    existing_days = {p["day"] for p in data["posts"]}
    print(f"現在の投稿数: {len(data['posts'])}件 (day: {min(existing_days)}〜{max(existing_days)})")

    # 重複しないように追加する
    added = 0
    for post in new_posts:
        if post["day"] not in existing_days:
            data["posts"].append(post)
            added += 1
        else:
            print(f"  スキップ: day{post['day']} は既に存在します")

    # dayの順番に並べ直す
    data["posts"].sort(key=lambda p: p["day"])

    # ファイルに保存する
    with open(POSTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ {added}件を追加しました")
    print(f"現在の投稿数: {len(data['posts'])}件 (day: {data['posts'][0]['day']}〜{data['posts'][-1]['day']})")


if __name__ == "__main__":
    main()
