"""
threads_posts.json に day151〜200 の投稿テキストを追加するスクリプト
テーマ：day151〜175=武士語録・名言 / day176〜200=自然・季節
（一回限りの実行スクリプト。実行後は削除する）
"""

import json
import os

POSTS_FILE = os.path.join(os.path.dirname(__file__), "threads_posts.json")

HASHTAGS_A = ["#JapaneseWisdom", "#Bushido", "#Mindset", "#Stoicism", "#Philosophy", "#RoninWords", "#Ronin"]
HASHTAGS_B = ["#DailyHabit", "#Discipline", "#Mastery", "#Growth", "#Action", "#RoninWords", "#Consistency"]
HASHTAGS_C = ["#Mindfulness", "#SelfAwareness", "#Courage", "#Resilience", "#RoninWords", "#Inspiration"]

new_posts = [
    # ===== 武士語録・名言 (day151〜175) =====
    {
        "day": 151,
        "morning": "Do not regret what you have done.\nRegret only what you have not done.\n\n我事において後悔せず\nWaga koto ni oite koukai sezu\n\n\"I have never regretted\nmy own actions.\"\n\nMiyamoto Musashi wrote this\nat the end of his life.\n\nNot arrogance.\nThe acceptance of full responsibility.\n\nWhen you own your decisions —\neven the ones that failed —\nyou cannot be a victim of them.\n\nThe person who regrets\nis still trying to change the past.\nThe one who owns their choices\nis building the future.\n\nOwn it. Learn. Move.\n\n#Musashi #Responsibility",
        "evening": "What decision today\ndo you fully own —\nregardless of outcome?\n\nOwnership is power.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 152,
        "morning": "The path is not found.\nIt is made.\n\n道は無し、歩むところに道は開ける\nMichi wa nashi, ayumu tokoro ni michi wa hirakeru\n\n\"There is no path.\nThe path opens where you walk.\"\n\nMatsuo Basho walked thousands of miles\nwriting poetry.\nNot following routes — making them.\n\nThe road you want\ndoesn't exist yet.\nIt emerges under your feet\nas you move.\n\nStop waiting for the path to appear.\nWalk. The path is what you leave behind.\n\n#Basho #Path",
        "evening": "What path did you begin making today\nthat didn't exist this morning?\n\nEvery step is the path.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 153,
        "morning": "Technique without heart\nis just mechanics.\n\n剣は心なり\nKen wa kokoro nari\n\n\"The sword is the mind.\"\n\nYagyu Munenori, master swordsman and strategist.\n\nThe sword reflects the state of the person holding it.\nA fearful person fights defensively.\nA proud person fights recklessly.\nA clear person fights precisely.\n\nThis is not just about swords.\nIt's about everything you create.\n\nYour work reflects your state of mind.\nYour communication reflects your inner clarity.\nYour results reflect who you are.\n\nImprove the person. The technique follows.\n\n#Yagyu #Mindset",
        "evening": "What did your work today\nreveal about your state of mind?\n\nTomorrow: start with the mind.\nThe hands will follow.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 154,
        "morning": "The mind that knows no enemy\nhas no enemy.\n\n敵なし\nTeki nashi\n\n\"The true warrior\nhas no enemy.\"\n\nYagyu Munenori again.\n\nThe master does not seek opponents.\nHe has transcended the need for them.\n\nNot passivity — mastery.\nThe one who has mastered himself\nhas nothing to prove\nand no need to fight.\n\nConflict is often ego seeking confirmation.\nMastery has no need for confirmation.\n\nWho are you fighting\nthat you could simply walk past?\n\n#Yagyu #Mastery",
        "evening": "What conflict today\nwas about ego\nnot about necessity?\n\nLeave those fights behind.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 155,
        "morning": "The body will follow the mind\nwhen the mind is decided.\n\n心頭滅却すれば火もまた涼し\nShinto mekkyaku sureba hi mo mata suzushi\n\n\"When the mind is extinguished,\neven fire is cool.\"\n\nFukushima Masanori, Zen monk-warrior.\nSaid to have been burned alive\nand remained in meditation.\n\nThe legend may be extreme.\nThe principle is real.\n\nThe body has far more endurance\nthan the mind usually allows.\nThe mind quits first.\n\nWhen the mind is clear and decided,\nthe body does remarkable things.\n\n#Mind #Endurance",
        "evening": "Where today did your mind quit\nbefore your body needed to?\n\nThe limit is usually mental.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 156,
        "morning": "The way of the warrior\nis more than fighting.\n\n武士道とは死ぬことと見つけたり\nBushido to wa shinu koto to mitsuketari\n\n\"The way of the warrior\nis to be found in dying.\"\n\nYamamoto Tsunetomo in Hagakure.\n\nMisread as glorifying death.\nActually about freedom.\n\nThe samurai who had already accepted death\nhad nothing left to fear.\nAnd a person with nothing to fear\nacts with complete commitment.\n\nFull presence. No hedging. No half-measures.\n\nWhat would you do today\nif you feared nothing?\n\n#Bushido #Courage",
        "evening": "What held you back today\nthat fear could be renamed\n'caution' to make it comfortable?\n\nName the fear. Then decide.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 157,
        "morning": "The one who hesitates\nhas already decided.\n\n迷わず行けよ、行けばわかるさ\nMayowazu yuke yo, yukeba wakaru sa\n\n\"Go without hesitation.\nYou'll understand once you move.\"\n\nAntonio Inoki, Japanese wrestler and philosopher.\n\nUnderstanding follows action.\nNot the reverse.\n\nYou will not understand the path\nby analyzing it from the starting line.\nYou understand it by walking it.\n\nThe hesitation that feels like preparation\nis often just fear with a respectable name.\n\nGo. Understand on the way.\n\n#Action #Courage",
        "evening": "What would you understand about your situation\nif you simply moved toward it\ninstead of analyzing it?\n\nGo tomorrow. Find out.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 158,
        "morning": "Seven times down.\nEight times up.\n\n七転び八起き\nNana korobi ya oki\n\n\"Fall seven times.\nRise eight.\"\n\nJapanese proverb.\nNot about being unaffected by failure.\nAbout getting up more times than you fall.\n\nThe successful person has failed more.\nNot less.\n\nThey fall. They rise. They fail again.\nThey rise again.\n\nThe ratio is simple:\nrise more than you fall.\n\nYou are currently at some fall or rise.\nWhichever it is — this is the count that matters.\n\n#Resilience #Persistence",
        "evening": "How many times have you gotten up\nthis year?\n\nEvery rise counts.\nKeep the ratio.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 159,
        "morning": "The sharpest weapon\nis one that has been used.\n\n鍛えた刃は折れない\nKitaeta ha wa orenai\n\n\"The blade that has been forged\ndoes not break.\"\n\nSamurai steel was folded thousands of times.\nEach fold removed impurities.\nEach fold increased strength.\n\nThe person who has faced difficulty\nand continued\nis folded steel.\n\nThe untested person is raw metal.\nBeautiful, perhaps.\nBut brittle.\n\nWhat is life folding into you right now?\nDon't resist the forge.\n\n#Resilience #Character",
        "evening": "What difficulty today\nwas the forge doing its work?\n\nThe fold makes you stronger.\nNot the comfortable days.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 160,
        "morning": "Mastery belongs to the one\nwho keeps going after everyone else stops.\n\n続けることが最強の武器\nTsuzukeru koto ga saikyo no buki\n\n\"Continuity is the most powerful weapon.\"\n\nNot talent. Not intelligence. Not connections.\n\nThe person who continues\nwhen it's no longer exciting,\nwhen results are not yet visible,\nwhen everyone around them has quit —\n\nthat person becomes the master.\n\nMastery is not a gift.\nIt is the compound interest\nof continued effort.\n\nAre you still going?\n\n#Persistence #Mastery",
        "evening": "What did you continue today\nthat you could have quit?\n\nThat continuation is the practice.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 161,
        "morning": "The warrior does not wait\nfor the right moment.\nHe makes the moment right.\n\n今この瞬間に全力を尽くせ\nIma kono shunkan ni zenryoku o tsukuse\n\n\"Give everything\nto this moment.\"\n\nBushi — warriors — were trained\nfor the moment of engagement.\n\nNot for the perfect moment.\nFor the moment that existed.\n\nThe warrior who waited for ideal conditions\ndied waiting.\nThe one who committed fully to what was —\nthat one made history.\n\nThis moment is what you have.\nGive it everything.\n\n#Commitment #Presence",
        "evening": "Did you give this day your full effort —\nor were you saving something\nfor a better moment?\n\nThis was the moment.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 162,
        "morning": "Loyalty is not blind obedience.\nIt is honest service.\n\n諫言は武士の誠\nKangen wa bushi no makoto\n\n\"Honest counsel\nis the samurai's true loyalty.\"\n\nThe samurai who told his lord only good news\nbetrayed him.\nThe one who delivered the difficult truth —\neven at risk to himself —\nserved him.\n\nTrue loyalty is honest.\n\nThe person who only tells you what you want to hear\nis not your ally.\nThe one who tells you what you need to hear\nis.\n\nAre you being that person for others?\n\n#Loyalty #Honesty",
        "evening": "Who needed honest counsel from you today\nthat you softened instead?\n\nHonest service is the truest loyalty.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 163,
        "morning": "The highest form of service\nis invisible service.\n\n縁の下の力持ち\nEn no shita no chikaramochi\n\n\"The strong man\nbeneath the floor.\"\n\nJapanese phrase: the unseen support.\nThe person who holds things up\nbut is never seen holding.\n\nThe greatest contributors to any organization\nare often not the most visible.\nThey are the ones who make others shine.\n\nThe floor holds you up.\nYou rarely think about the floor.\n\nWho is your floor?\nAnd are you someone else's?\n\n#Service #Humility",
        "evening": "Who supported you today\nwithout needing recognition?\n\nSee them.\nAnd consider how you support others.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 164,
        "morning": "The one who moves without thinking\nand the one who thinks without moving\nare both useless.\n\n文武両道\nBunbu ryodo\n\n\"The dual path:\nlearning and action.\"\n\nThe ideal samurai was both scholar and warrior.\nNeither pure intellect nor pure action.\n\nThe thinker who never acts becomes irrelevant.\nThe actor who never reflects becomes dangerous.\n\nLearning without action is entertainment.\nAction without learning is stumbling.\n\nBoth. Always both.\n\nWhat did you learn this week\nthat you have not yet acted on?\n\n#Learning #Action",
        "evening": "Learning that is not used\ndecays into trivia.\n\nWhat have you learned recently\nthat needs to become action?",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 165,
        "morning": "The man who wins alone\ndoes not go far.\n\n一人は万人のために、万人は一人のために\nHitori wa bannin no tame ni, bannin wa hitori no tame ni\n\n\"One for all.\nAll for one.\"\n\nNot Western — this principle runs deep in samurai culture.\nThe lord exists to serve the clan.\nThe clan exists to serve the lord.\n\nRadical individualism is a new invention.\nFor most of human history, we survived together.\n\nThe most successful people are those\nwho build something others can contribute to\nand benefit from.\n\nWho are you for?\n\n#Community #Leadership",
        "evening": "Who did your work today serve\nbeyond yourself?\n\nMeaning is usually found there.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 166,
        "morning": "Grace under pressure\nis not a gift.\nIt is training.\n\n泰然自若\nTaizen jijaku\n\n\"Unmoved by circumstance.\nCalm at the center.\"\n\nThe samurai trained for crisis\nso that in crisis, the training appeared.\n\nNot the performance of calm.\nActual calm — because the body had been here before.\n\nCalm under pressure is a practiced skill.\nNot a personality trait.\n\nWhat are you training for\nthat will require calm when it arrives?\n\n#Calm #Resilience",
        "evening": "How calm were you under pressure today?\n\nNot as a judgment —\nas data about what to practice next.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 167,
        "morning": "Your word is your bond.\nOr it is nothing.\n\n武士に二言なし\nBushi ni nigon nashi\n\n\"A samurai's word\nis spoken once.\"\n\nNot because the samurai was rigid.\nBecause his word meant something.\n\nThe person who commits and delivers\nbuilds trust compounding over decades.\nThe person who commits and hedges\nundermines every relationship.\n\nWord once spoken = reality.\nNot intention. Not approximation.\nReality.\n\nAre your commitments that reliable?\n\n#Integrity #Trust",
        "evening": "What did you commit to today?\n\nAnd is it a real commitment —\nor just an intention\nyou'll revise later?",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 168,
        "morning": "The enemy is often inside.\n\n己に勝つ\nOre ni katsu\n\n\"Conquer yourself.\"\n\nMiyamoto Musashi:\n'The most dangerous opponent\nis the one within.'\n\nThe laziness that is dressed as wisdom.\nThe fear that is dressed as caution.\nThe ego that is dressed as standards.\n\nExternal opponents can be studied and defeated.\nThe internal opponent shifts and disguises.\n\nThe person who has conquered themselves\nhas conquered more\nthan most armies ever have.\n\nWhich internal opponent\ndo you need to face today?\n\n#Musashi #SelfMastery",
        "evening": "What internal opponent showed up today?\n\nNamed: it has less power.\nUnnamed: it runs you.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 169,
        "morning": "The lesson is not what happened.\nThe lesson is what you do next.\n\n失敗は成功の母\nShippai wa seiko no haha\n\n\"Failure is the mother of success.\"\n\nJapanese proverb — and a universal truth.\n\nThe failure that produces learning\nis not failure.\nIt is tuition.\n\nThe failure that produces shame\nand no change\nis just loss.\n\nSame failure. Different response.\nCompletely different outcomes.\n\nWhat have your failures been teaching you\nthat you haven't yet learned?\n\n#Failure #Growth",
        "evening": "What failure from today\nare you going to convert to tuition?\n\nWrite the lesson down.\nThe lesson is the asset.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 170,
        "morning": "The wise man learns from others' mistakes.\nThe average man learns from his own.\nThe fool learns from neither.\n\n他山の石以って玉を攻むべし\nTazan no ishi motte tama o osamu beshi\n\n\"The stones of another mountain\ncan polish your own jade.\"\n\nChinese proverb, deeply embedded in Japanese wisdom.\n\nOther people's mistakes are cheap lessons.\nYour own mistakes are expensive ones.\nBoth are worth extracting from.\n\nWho around you is making mistakes\nyou could learn from\nwithout making them yourself?\n\n#Learning #Wisdom",
        "evening": "What did someone else's difficulty today\nteach you?\n\nThe lesson was free.\nDid you take it?",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 171,
        "morning": "Work without purpose\nis just motion.\n\n死ぬまで働け、死んでも働け\nShinu made hatarake, shinde mo hatarake\n\n\"Work until you die.\nWork even after you die.\"\n\nNot about exhaustion.\nAbout purpose that outlives you.\n\nThe work that continues after you\nare gone was work worth doing.\n\nThe samurai who built institutions,\nwho trained students,\nwho established traditions —\ntheir work still walks.\n\nWhat are you building\nthat will continue?\n\n#Purpose #Legacy",
        "evening": "What did you build today\nthat could outlast you?\n\nThat question separates\ntasks from purpose.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 172,
        "morning": "The strong are not those\nwho feel nothing.\nThey are those who feel everything\nand continue.\n\n男は泣かない\nOtoko wa nakanai\n\n\"A man does not cry.\"\n\nThe old phrase misunderstood.\n\nThe warrior cried. Musashi wept.\nThe bushi felt grief, loss, love.\n\nThe point was not suppression.\nIt was the continuation despite feeling.\n\nFeel the grief. Continue.\nFeel the fear. Continue.\nFeel the doubt. Continue.\n\nStrength is action in the presence of feeling.\nNot the absence of feeling.\n\n#Courage #Strength",
        "evening": "What did you feel today\nthat you moved through anyway?\n\nThat movement is strength.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 173,
        "morning": "The arrow that is not released\nkills no one.\n\n弓を引く者は射る\nYumi o hiku mono wa iru\n\n\"He who draws the bow\nmust release the arrow.\"\n\nNot cruelty — completion.\n\nThe archer who draws and holds forever\nachieves nothing.\nThe action must be completed.\n\nYour plan must become action.\nYour decision must become execution.\nYour intention must become behavior.\n\nThe draw is not the shot.\nOnly the release accomplishes anything.\n\nWhat have you drawn but not released?\n\n#Action #Completion",
        "evening": "What are you holding drawn\nthat needs to be released?\n\nRelease it tomorrow.\nThe holding is the waste.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 174,
        "morning": "The cup cannot be filled\nwhen it is already full.\n\n素直な心\nSunao na kokoro\n\n\"A straight and honest heart.\"\n\nMatsushita Konosuke — founder of Panasonic —\nspoke often of sunao.\n\nNot naivety. Openness.\nThe willingness to see what is\nrather than what you want to see.\n\nThe leader who couldn't be told bad news\nwas always surprised by it.\nThe one who stayed sunao\nheard the truth and adjusted.\n\nAre you open to what is actually true\nright now?\n\n#Openness #Leadership",
        "evening": "What truth are you resisting tonight\nbecause it's inconvenient?\n\nA straight heart sees it anyway.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 175,
        "morning": "The way of the warrior\nis the way of fully being alive.\n\n武士道は生きることと見つけたり\nBushido wa ikiru koto to mitsuketari\n\n\"The way of the warrior\nis to be found in living.\"\n\nThe counterpoint to Yamamoto's famous quote.\n\nDeath-acceptance is not death-seeking.\nIt is life-fully-living.\n\nThe samurai who had nothing to fear\nwas the one most alive —\nmost present,\nmost committed,\nmost engaged.\n\nFull life requires accepting its limits.\nThe finite makes the infinite precious.\n\nAre you living fully —\nor managing safely?\n\n#Bushido #Life",
        "evening": "What part of your life\nare you managing safely\nrather than living fully?\n\nToday: one step toward full.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    # ===== 自然・季節 (day176〜200) =====
    {
        "day": 176,
        "morning": "Look at what's around you.\nReally look.\n\n花鳥風月\nKacho fugetsu\n\n\"Flower, bird, wind, moon —\nthe beauty of nature.\"\n\nThe classical Japanese concept of aesthetic sensitivity.\nThe ability to be moved by the world.\n\nNot sentimentality.\nPerception.\n\nThe warrior who noticed beauty\nwas not distracted by it.\nHe was more awake because of it.\n\nThe person who walks past flowers without seeing them\nwalks past people without seeing them too.\n\nSensitivity to beauty\nis sensitivity to life.\n\nWhat did you almost walk past today?\n\n#Beauty #Nature",
        "evening": "One beautiful thing today.\n\nFlower, bird, wind, or moon —\nor the human equivalent.\n\nName it before you sleep.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 177,
        "morning": "You cannot rush the bloom.\n\n桜の時\nSakura no toki\n\n\"There is a time for the cherry blossom.\"\n\nThe sakura does not bloom in autumn.\nNo amount of wishing makes it so.\n\nEverything has its season.\nThe idea before the market is ready.\nThe relationship before both people are ready.\nThe success before the foundation is laid.\n\nTiming is not surrender.\nIt is intelligence.\n\nWhat are you forcing into bloom\nbefore the season is right?\nAnd what are you letting go dormant\nthat has its season right now?\n\n#Timing #Nature",
        "evening": "What is in season right now\nin your life?\n\nGive that thing your full attention.\nSeasons pass.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 178,
        "morning": "Even the strongest storm\nends in stillness.\n\n嵐の後の静けさ\nArashi no ato no shizukesa\n\n\"After the storm, stillness.\"\n\nThe Japanese coast has seen typhoons\nthat leveled forests.\nAnd the morning after:\nbirds. Light. The smell of cleared air.\n\nNo storm lasts forever.\nThis is not a platitude.\nIt is the physics of weather\nand the physics of difficulty.\n\nStorms end.\nWhat remains when yours clears\nis what you built in advance.\n\nWhat are you building before the storm?\n\n#Resilience #Hope",
        "evening": "If you are in the storm right now —\nit will end.\n\nIf you are in the stillness —\nbuild now, before the next one.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 179,
        "morning": "The ocean does not apologize\nfor being the ocean.\n\n海の如く\nUmi no gotoku\n\n\"Be as the ocean —\ndeep, vast, unhurried.\"\n\nThe ocean does not compare itself to the river.\nDoes not apologize for its salt.\nDoes not need to explain its depth.\n\nIt simply is what it is.\nFully. Without performance.\n\nThe person who has found their own nature\nhas the same quality.\nNot arrogance — groundedness.\n\nYou don't need to be the river or the lake.\nBe the thing you actually are.\nFully.\n\n#Nature #Authenticity",
        "evening": "What aspect of your nature\nhave you been apologizing for\nor hiding?\n\nIt's the ocean. Let it be.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 180,
        "morning": "The mountain does not argue\nwith the wind.\n\n山は動かず\nYama wa ugokazu\n\n\"The mountain does not move.\"\n\nThe wind howls. The mountain stands.\nThe rain pounds. The mountain stands.\nThe seasons change. The mountain stands.\n\nNot stubbornness — groundedness.\nThe mountain's stability is not resistance.\nIt is nature.\n\nWhat would it feel like\nto have your own mountain quality?\n\nNot immovable in thought —\nstable in identity.\nBent by nothing that doesn't need to bend you.\n\n#Stability #Character",
        "evening": "What tried to move you today\nthat you stood firm against?\n\nOr what needed to move you\nthat you resisted unnecessarily?\n\nThe mountain knows the difference.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 181,
        "morning": "The bamboo bends.\nAnd does not break.\n\n竹の節\nTake no fushi\n\n\"The bamboo has joints —\neach one a place it could break,\nbut doesn't.\"\n\nThe bamboo bends under snow\nuntil the snow falls off.\nThen it springs back.\n\nNot because it has no joints.\nBecause the joints are its strength.\n\nYour breaking points — the difficult relationships,\nthe failures, the humiliations —\nthese can be your joints.\n\nIf you bend instead of resist.\nIf you spring back instead of staying bent.\n\n#Resilience #Bamboo",
        "evening": "Where did you bend today\nrather than break?\n\nThe bend is the skill.\nNot the weakness.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 182,
        "morning": "The pine endures the winter.\n\n松の緑\nMatsu no midori\n\n\"The pine stays green\nthrough winter.\"\n\nDeciduous trees shed their leaves.\nThe pine does not.\n\nConstancy through adverse conditions\nis the pine's gift.\n\nThe person who shows up when it's hard —\nwho continues when motivation has left,\nwho maintains when others have abandoned —\n\nthat is pine quality.\n\nNot heroic effort in the spring.\nGreen through winter.\n\nWhat does your winter look like?\nAre you staying green?\n\n#Constancy #Discipline",
        "evening": "This might be your winter.\n\nGreen anyway.\nThe spring will come.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 183,
        "morning": "Rain does not ask\nbefore it falls.\n\n雨は降る\nAme wa furu\n\n\"The rain falls.\nAccept it.\"\n\nThe rain does not negotiate.\nIt falls where it falls, when it falls.\n\nThe farmer who cursed the rain\nstill got wet.\nThe one who prepared and worked with it\nhad a better harvest.\n\nSome things are not in your control.\nThe response always is.\n\nThe rain is falling. What are you building\nto work with what falls?\n\n#Acceptance #Adaptation",
        "evening": "What fell today that you didn't choose?\n\nYou chose the response.\nWas it the response you'd choose again?",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 184,
        "morning": "The fire does not ask\nif the wood is ready.\n\n火は燃える\nHi wa moeru\n\n\"Fire burns.\nBe the fire.\"\n\nFire does not wait for permission.\nIt does not ask if the conditions are ideal.\nIt simply burns — where it is, with what it has.\n\nThe person who burns\nwith purpose and commitment\nis not asking if the conditions are right.\nThey are creating the conditions.\n\nYou are the fire.\nNot the wood.\nNot the conditions.\n\nBurn.\n\n#Purpose #Energy",
        "evening": "Did you burn today —\nfully, with what you had,\nin the conditions that existed?\n\nOr did you wait for better wood?",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 185,
        "morning": "The river does not store water.\nIt gives it.\n\n川は流れる\nKawa wa nagareru\n\n\"The river flows —\ngiving all it has.\"\n\nThe river does not hoard.\nIt flows. Continuously. Without calculating.\n\nThe stagnant water becomes a swamp.\nThe flowing water stays clean and alive.\n\nGenerosity — of time, of knowledge, of attention —\ndoes not deplete the generous person.\nIt often replenishes them.\n\nWhere are you hoarding\nwhat could be flowing?\n\n#Generosity #Flow",
        "evening": "What could you give tomorrow\nthat you've been holding back?\n\nThe river stays clean by flowing.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 186,
        "morning": "The seed does not see the tree it will become.\nBut it grows anyway.\n\n種は知らずして育つ\nTane wa shirazu shite sodatsu\n\n\"The seed grows\nwithout knowing the tree.\"\n\nYou cannot see the full result of your efforts.\nNo one can.\n\nThe samurai planting a tree in his lord's garden\nknew he would not live to sit in its shade.\nHe planted anyway.\n\nWhat are you planting today\nthat you will not see fully grown?\n\nPlant it anyway.\nThe shade will benefit someone.\n\n#Legacy #Patience",
        "evening": "What did you plant today\nthat won't be ready for years?\n\nPlanting is the work.\nThe harvest is for later.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 187,
        "morning": "Even the moon\nhas its dark phase.\n\n月の満ち欠け\nTsuki no michikake\n\n\"The moon waxes and wanes.\"\n\nThe moon does not apologize for the new moon.\nThe darkness is part of the cycle.\n\nYour energy, motivation, and clarity\nhave phases too.\n\nThe low phase is not failure.\nIt is the cycle.\n\nYou cannot be full moon every day.\nThe waning is part of what makes the full moon\nso striking.\n\nWhat phase are you in?\nAnd can you be that phase without fighting it?\n\n#Rhythm #Acceptance",
        "evening": "What phase are you in right now?\n\nFull moon or new moon —\nboth are the same moon.\nBoth are needed.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 188,
        "morning": "The morning mist clears.\nThe path was always there.\n\n朝霧晴れて\nAsagiri harete\n\n\"When the morning mist clears,\nthe path appears.\"\n\nIn confusion, we think the path is missing.\nUsually, it is obscured.\n\nThe confusion will clear.\nThe urgency will settle.\nThe emotion will pass through.\n\nAnd the path — which was always there —\nwill be visible again.\n\nDo not make permanent decisions\nin temporary mist.\n\nWait for the morning to clear.\nThen walk.\n\n#Clarity #Patience",
        "evening": "What looked impossible in the morning\nthat became clearer by evening?\n\nThe mist moves.\nAlways.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 189,
        "morning": "The stone is patient.\nAnd it outlasts almost everything.\n\n石の如く\nIshi no gotoku\n\n\"Be as stone —\npatient, enduring.\"\n\nThe stone in the riverbed\nhas been smoothed by ten thousand years of water.\nNot by force.\nBy patience.\n\nThe sharp edges that once caused harm\nhave been worn smooth\nby the patient passing of experience.\n\nPatience is not passive.\nIt is the active choice to let time do its work.\n\nWhat in your life needs stone-patience\nrather than rushing?\n\n#Patience #Endurance",
        "evening": "What are you rushing\nthat would be better\ngiven to time?\n\nThe stone knows.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 190,
        "morning": "The wind moves without form.\nAnd changes everything it touches.\n\n風は形なし\nKaze wa katachi nashi\n\n\"The wind has no form.\nYet nothing escapes it.\"\n\nThe wind is invisible.\nBut you see what it moves.\nThe trees. The clouds. The sea surface.\n\nInfluence does not require visibility.\nImpact does not require presence.\n\nSome of the most powerful forces in your life\nhave been invisible — habits, ideas, relationships —\nthat moved everything else.\n\nWhat invisible force are you cultivating\nthat is moving the visible things?\n\n#Influence #Invisible",
        "evening": "What invisible thing —\nhabit, belief, or relationship —\nis shaping your visible life?\n\nSee it. Direct it.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 191,
        "morning": "Still water reflects clearly.\nThe moving surface distorts.\n\n静水明鏡\nSeisui meikyo\n\n\"Still water reflects like a clear mirror.\"\n\nThe Zen saying: the still pond shows the moon.\nThe disturbed pond shows fragments.\n\nThe still mind sees clearly.\nThe agitated mind sees distortion.\n\nMost poor decisions are made\nfrom a disturbed surface.\n\nNot stupidity — agitation.\nThe same mind, stilled,\nwould have seen it differently.\n\nStill the surface before deciding.\n\n#Clarity #Stillness",
        "evening": "What decision today\nwould have been clearer\nif you had stilled first?\n\nStill before deciding tomorrow.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 192,
        "morning": "The forest survives by diversity.\nNot uniformity.\n\n森の知恵\nMori no chie\n\n\"The wisdom of the forest:\ndiversity creates resilience.\"\n\nA monoculture forest is efficient.\nOne disease can erase it entirely.\n\nThe diverse forest loses trees —\nbut the forest itself endures.\n\nThe person who has only one skill,\none income, one relationship type —\nis a monoculture.\n\nDiversity of skill, perspective, and relationship\nis not inefficiency.\nIt is resilience.\n\nWhere are you a monoculture\nthat could use more diversity?\n\n#Resilience #Diversity",
        "evening": "What single point of failure\nexists in your life?\n\nThe forest knows:\ndiversity is protection.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 193,
        "morning": "The horizon is not the end of the world.\nIt is the invitation to continue.\n\n地平線の向こう\nChiheisen no muko\n\n\"Beyond the horizon —\nsomething is there.\"\n\nThe ancient sailors knew:\nthe horizon is not a wall.\nIt is a threshold.\n\nWhat looks like an edge\nis actually a beginning.\n\nThe limit of your current vision\nis not the limit of what exists.\n\nWhere are you treating a horizon\nas if it were a wall?\n\nSail toward it.\nSee what's on the other side.\n\n#Vision #Exploration",
        "evening": "What did you stop at today\nthat was actually an invitation to continue?\n\nThe horizon moves as you move toward it.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 194,
        "morning": "The tree does not negotiate\nwith the season.\n\n木は季節に従う\nKi wa kisetsu ni shitagau\n\n\"The tree follows the season.\"\n\nIn autumn, the tree releases its leaves.\nNot reluctantly. Not with grief.\nSimply — because it is autumn.\n\nIn spring, it grows again.\nNot because it forced it.\nBecause the season called for it.\n\nThe tree in harmony with its season\nsurvives centuries.\n\nWhat season are you actually in?\nAnd are you doing what that season requires —\nor fighting it?\n\n#Seasons #Acceptance",
        "evening": "What season are you in?\nSpring, summer, autumn, or winter?\n\nAnd what does that season require?\nDo that.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 195,
        "morning": "Look at the sky.\nIt has held everything\nwithout holding on.\n\n大空の如く\nOozora no gotoku\n\n\"Be as the great sky —\nvast, open, containing all.\"\n\nThe sky holds clouds without becoming cloud.\nHolds storms without becoming storm.\nHolds darkness without becoming dark.\n\nThe sky is not affected by what passes through it.\nIt remains sky.\n\nCan you be that open?\nHolding difficulty without becoming difficult.\nHolding uncertainty without becoming uncertain.\n\nYou are the sky.\nNot the weather.\n\n#Openness #Equanimity",
        "evening": "What weather passed through you today?\n\nYou are the sky.\nThe weather was passing through.\nAre you still sky?",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 196,
        "morning": "The river finds the sea\nby following its nature.\n\n水は低きに就く\nMizu wa hikuki ni tsuku\n\n\"Water seeks the lowest place.\"\n\nTao Te Ching. Deeply embedded in Japanese thought.\n\nWater does not climb.\nIt descends. Takes the humble path.\nAnd in doing so, it feeds everything below\nand reaches the sea.\n\nThe humble path — the low road —\nis not the path of the defeated.\nIt is the path of the wise.\n\nWhat would the low path look like\nin your current situation?\n\n#Humility #WuWei",
        "evening": "Where did pride block\nthe humble path today?\n\nThe water finds the sea\nby going low.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 197,
        "morning": "The night is not the enemy of the day.\nIt is its partner.\n\n昼と夜\nHiru to yoru\n\n\"Day and night —\neach needs the other.\"\n\nWithout darkness, the stars are invisible.\nWithout rest, the effort is unsustainable.\nWithout winter, the spring means nothing.\n\nThe obsession with constant productivity\nis the refusal to accept night.\n\nBut the warrior who never rested\nfought poorly.\nThe mind that never stopped\nthought shallowly.\n\nHonor the night.\nIt makes the day possible.\n\n#Rest #Balance",
        "evening": "The night is beginning.\n\nHonor it.\nSleep is not wasted time.\nIt is what makes tomorrow possible.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 198,
        "morning": "The crane lives long\nbecause it knows how to be still.\n\n鶴の一声\nTsuru no hitokoe\n\n\"The crane speaks once.\nAnd is heard.\"\n\nThe crane does not chatter.\nWhen it speaks, it speaks with weight.\n\nThe person who speaks constantly\ndilutes every word.\nThe one who speaks selectively\nmakes each word land.\n\nAnd the crane lives long\nbecause it is never wasteful —\nnot of movement, not of sound.\n\nWhat would fewer, better words\ndo for you?\n\n#Communication #Stillness",
        "evening": "How many words did you use today\nthat could have been fewer?\n\nThe crane speaks once.\nAnd is heard.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 199,
        "morning": "The wave rises and falls.\nThe ocean continues.\n\n波は来ては返す\nNami wa kite wa kaesu\n\n\"Waves come and go.\nThe ocean remains.\"\n\nYour successes are waves.\nYour failures are waves.\nYour emotions, moods, circumstances —\nwaves.\n\nYou are not the wave.\nYou are the ocean.\n\nThe wave that crashes\ndoes not destroy the ocean.\nIt is returned to it.\n\nWhat wave are you over-identified with\nright now — success or failure —\nthat is not the whole of you?\n\n#Identity #Resilience",
        "evening": "You are not your last wave.\n\nNot your best day.\nNot your worst.\nYou are the ocean.\n\nRest in that.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 200,
        "morning": "The path does not end.\nIt changes form.\n\n道は続く\nMichi wa tsuzuku\n\n\"The path continues.\nKeep walking.\"\n\n200 days of walking.\n\nNot because you have arrived.\nBecause the walking is the point.\n\nThe samurai who thought he had mastered\nthe sword stopped growing.\nThe one who remained a student\nuntil death — that one mastered.\n\nMastery is not a destination.\nIt is the daily return to the path.\n\nThe path continues.\nYou continue.\n\nKeep walking.\n\n#Path #Mastery",
        "evening": "200 days.\n\nYou are not finished.\nThe path continues.\n\nWhere does it lead next?\n\nKeep walking.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    }
]


def main():
    # threads_posts.jsonを読み込む
    with open(POSTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 既存のday番号を集める（重複チェック用）
    existing_days = {p["day"] for p in data["posts"]}
    print(f"現在の投稿数: {len(data['posts'])}件 (day: {min(existing_days)}〜{max(existing_days)})")

    added = 0
    for post in new_posts:
        if post["day"] not in existing_days:
            data["posts"].append(post)
            added += 1
        else:
            print(f"  スキップ: day{post['day']} は既に存在します")

    # day順にソートして保存
    data["posts"].sort(key=lambda p: p["day"])

    with open(POSTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ {added}件を追加しました")
    print(f"現在の投稿数: {len(data['posts'])}件 (day: {data['posts'][0]['day']}〜{data['posts'][-1]['day']})")


if __name__ == "__main__":
    main()
