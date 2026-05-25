"""
threads_posts.json に day101〜150 の投稿テキストを追加するスクリプト
テーマ：day101〜125=禅・仏教 / day126〜150=戦略・兵法
（一回限りの実行スクリプト。実行後は削除する）
"""

import json
import os

POSTS_FILE = os.path.join(os.path.dirname(__file__), "threads_posts.json")

HASHTAGS_A = ["#JapaneseWisdom", "#Bushido", "#Mindset", "#Stoicism", "#Philosophy", "#RoninWords", "#Ronin"]
HASHTAGS_B = ["#DailyHabit", "#Discipline", "#Mastery", "#Growth", "#Action", "#RoninWords", "#Consistency"]
HASHTAGS_C = ["#Mindfulness", "#SelfAwareness", "#Courage", "#Resilience", "#RoninWords", "#Inspiration"]

new_posts = [
    # ===== 禅・仏教 (day101〜125) =====
    {
        "day": 101,
        "morning": "You have been fighting\nsomething that was always true.\n\n一切皆苦\nIssai kaiku\n\n\"All of life involves suffering.\nAccept it.\"\n\nThe Buddha did not say life is bad.\nHe said suffering is inevitable —\nand that fighting the inevitable\nis where the real suffering begins.\n\nThe unexpected bill. The difficult relationship.\nThe body that breaks down.\nThe plan that doesn't survive contact with reality.\n\nAcceptance is not defeat.\nIt is the beginning of clear action.\n\nAccept what is.\nThen decide what to do next.\n\n#Buddhism #Acceptance",
        "evening": "Stop fighting what is already true.\n\nAccept it.\nThen choose your next move\nfrom that ground.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 102,
        "morning": "The past is gone.\nThe future isn't here.\nThis moment is all you actually have.\n\n刹那\nSetsuna\n\n\"This single moment\nis all you have.\"\n\nSetsuna — a Sanskrit concept in Japanese.\nOne snap of a finger.\nThe smallest unit of time.\n\nAnd yet — it's where everything happens.\n\nThe decision made.\nThe word spoken.\nThe action taken.\n\nAll of it happens in setsuna.\nRight here. Right now.\n\nAre you actually present for it?\n\n#Presence #Zen",
        "evening": "This moment won't come again.\n\nBe in it.\nFully.\nNot planning the next one —\nthis one.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 103,
        "morning": "The self you're protecting\nmight be the thing in the way.\n\n無我\nMuga\n\n\"Release the self.\nYou are larger than your ego.\"\n\nThe ego curates. Defends. Performs.\nIt is exhausting.\n\nMuga — no-self — is not oblivion.\nIt is relief.\n\nWhen you're not defending a self-image,\nyou can simply respond.\nWhen you're not protecting a story,\nyou can simply see.\n\nThe samurai who forgot himself in battle\nwas the most dangerous.\nThe one performing bravery was already losing.\n\nLet go of the curator.\nJust act.\n\n#Muga #Ego",
        "evening": "What would you do today\nif you weren't worried about\nhow it looks?\n\nThat answer is who you actually are.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 104,
        "morning": "The thing you're clinging to\nis made of the same stuff\nas the space around it.\n\n空\nKu\n\n\"Form is emptiness.\nEmptiness is form.\"\n\nThis is the Heart Sutra.\nSix characters that took monks lifetimes.\n\nSolid things are mostly space.\nYour most fixed beliefs are constructs.\nYour clearest categories blur at the edges.\n\nThis is not nihilism.\nIt is freedom.\n\nWhen you know form is empty,\nyou hold it more lightly.\nYou're less destroyed when it changes.\nMore open to what comes next.\n\n#Ku #Zen",
        "evening": "The thing you thought was solid —\nwhat if it's more flexible\nthan you believed?\n\nHold it a little more lightly tonight.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 105,
        "morning": "Compassion is not a feeling.\nIt's a practice.\n\n慈悲\nJihi\n\n\"Compassion\nfor all living things.\"\n\nJi — loving kindness.\nHi — the wish to relieve suffering.\n\nNot just the people you like.\nNot just the people who are easy.\nAll living things.\n\nThe Buddhist knew:\nthe difficult person is suffering too.\nThe enemy is in pain too.\n\nCompassion does not mean agreeing.\nIt means seeing the human in front of you\nbefore seeing the obstacle.\n\nWho do you need to see more fully today?\n\n#Jihi #Compassion",
        "evening": "The person who frustrated you today\nwas struggling with something.\n\nYou don't need to know what.\nJust know it.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 106,
        "morning": "The cluttered mind\nfights itself.\n\n無心\nMushin\n\n\"An empty mind\nmoves without resistance.\"\n\nMushin — no mind — is the state\nwhere action flows without internal commentary.\n\nThe master swordsman didn't think about cutting.\nThe musician doesn't think about the notes.\nThe athlete in the zone has no narrator.\n\nThe mind that is too full of strategy\ncannot respond to what is actually happening.\n\nEmpty the cup.\nRespond to what's in front of you.\nNot what you planned to encounter.\n\n#Mushin #Flow",
        "evening": "You were overthinking today.\n\nEmptied of plans,\nwhat would you simply do?\n\nTry that tomorrow.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 107,
        "morning": "Awakening is not\nsomething you achieve.\nIt's something you stop covering up.\n\n悟り\nSatori\n\n\"Awakening is not found.\nIt is recognized.\"\n\nThe Zen tradition says:\nbefore enlightenment, chop wood, carry water.\nAfter enlightenment, chop wood, carry water.\n\nNothing changes.\nThe seeing changes.\n\nSatori is not a destination.\nIt is the moment you stop\nlooking away from what's already here.\n\nWhat are you looking away from?\nWhat would you see if you looked directly?\n\n#Satori #Zen",
        "evening": "The insight you're seeking\nmight already be available.\n\nStop looking for it.\nLook at what's in front of you.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 108,
        "morning": "Greatness might look\nlike ordinary days.\n\n平常心\nHeijoshin\n\n\"The ordinary mind\nis the Way.\"\n\nWhen asked what Zen was,\nthe master said: 'When hungry, eat.\nWhen tired, sleep.'\n\nThe student expected mystery.\nHe got radical simplicity.\n\nHeijoshin is not laziness.\nIt is the absence of performance.\nNo forcing the transcendent.\nNo manufacturing the profound.\n\nJust this moment. This task. This person.\nFully. Without drama.\n\nThat is the practice.\n\n#Heijoshin #Zen",
        "evening": "The most important moment\nis the one happening right now.\n\nNo ceremony required.\nJust attention.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 109,
        "morning": "Stop trying to get somewhere.\nBe where you are.\n\n只管打坐\nShikantaza\n\n\"Just sit.\nNothing else is needed.\"\n\nShikantaza is the Soto Zen practice\nof sitting without goal.\n\nNot sitting to become enlightened.\nNot sitting to calm down.\nJust sitting.\n\nIn a world obsessed with output,\nthis is radical.\n\nSometimes the most productive thing\nis to stop producing.\nTo stop optimizing.\nTo stop performing.\n\nAnd simply be present\nto what is already here.\n\n#Meditation #Presence",
        "evening": "Five minutes.\nNo phone. No agenda.\nJust sitting.\n\nThat's the whole practice.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 110,
        "morning": "The deepest truths\ndon't survive translation.\n\n不立文字\nFuryu monji\n\n\"Truth cannot be\ncaptured in words.\"\n\nZen was transmitted mind to mind.\nNot text to text.\n\nThe finger pointing at the moon\nis not the moon.\n\nWords are fingers.\nThey point. They gesture.\nBut the thing itself\ncannot be handed over in sentences.\n\nThis is not anti-intellectual.\nIt's a reminder:\nKnowing the words is not knowing the thing.\nReading about courage is not being courageous.\nUnderstanding compassion and practicing it\nare not the same.\n\n#Zen #Words",
        "evening": "What do you know in words\nthat you haven't yet put into practice?\n\nThat gap is the work.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 111,
        "morning": "Everything else\nis secondary to this.\n\n生死事大\nShoji jidai\n\n\"Life and death —\nthis is the great matter.\"\n\nThe Zen monks hung this phrase\nin their practice halls.\n\nNot to create anxiety.\nBut to create clarity.\n\nWhen you remember that life ends —\nthat this project has a deadline,\nthat this relationship has limits,\nthat this body has an expiration —\n\nThe trivial falls away.\nWhat matters becomes obvious.\n\nWhat is the great matter in your life right now?\nIs what you're doing today connected to it?\n\n#LifeAndDeath #Clarity",
        "evening": "What mattered today?\nNot what was urgent —\nwhat actually mattered.\n\nAnd did you give it your time?",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 112,
        "morning": "You are the authority\non your own experience.\n\n自灯明\nJi tomyo\n\n\"Be a lamp\nunto yourself.\"\n\nThe Buddha's last words.\n\nAfter forty years of teaching,\nhis final instruction was:\ndon't follow me. Don't follow anyone.\n\nTest everything against your own experience.\nObserve. Verify. Question.\n\nNot rebellion for its own sake.\nBut the commitment to see clearly\nrather than to believe conveniently.\n\nWhat have you accepted without testing?\nWhat would you see if you looked directly?\n\n#SelfReliance #Truth",
        "evening": "What did you believe today\nbecause it was easy —\nnot because you'd tested it?\n\nStart there tomorrow.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 113,
        "morning": "Nothing stands still.\nEverything is becoming.\n\n万物流転\nBanbutsu ruten\n\n\"All things\nare in constant flow.\"\n\nHeraclitus said you can't step in the same river twice.\nThe Buddhist said the same thing\nwith more detail.\n\nNot just rivers. Everything.\nYour body. Your relationships. Your beliefs.\nYour organization. Your certainties.\n\nAll of it in constant motion.\n\nWhen you resist this, you suffer.\nWhen you move with it —\nyou discover the fluidity\nthat was always available.\n\n#Impermanence #Flow",
        "evening": "What changed today\nthat you were pretending was permanent?\n\nLet it move.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 114,
        "morning": "Move without forcing.\nFlow without stopping.\n\n行雲流水\nKoun ryusui\n\n\"Move like clouds.\nFlow like water.\"\n\nClouds don't announce their movement.\nThey simply shift.\n\nWater doesn't argue with the rock.\nIt finds the way around.\n\nThe person who flows\nis not weak — they are efficient.\nNo energy wasted on resistance.\nNo ego defending the original plan.\n\nAdapt. Move. Continue.\n\nThat is the way of water.\n\n#Adaptability #Flow",
        "evening": "Where did you resist today\nwhat could have been flowed through?\n\nWater doesn't lose\nby going around.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 115,
        "morning": "The consequences are already in motion.\n\n因果応報\nInga oho\n\n\"What you sow,\nyou will reap.\"\n\nKarma is not mystical.\nIt is cause and effect.\n\nThe relationships you neglect will cool.\nThe skills you build will compound.\nThe choices you make today\nare shaping the person you will be tomorrow.\n\nThis is not pessimism.\nIt is the most powerful insight available:\n\nYou are building your future right now.\nWith every choice.\nEvery habit.\nEvery act of character or compromise.\n\n#Karma #Consequences",
        "evening": "What did you plant today?\n\nSomething worth growing —\nor something worth pulling out\nbefore it takes root?",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 116,
        "morning": "The division between mind and body\nis the problem.\n\n身心一如\nShinshin ichinyo\n\n\"Body and mind\nare one.\"\n\nWestern thought split them.\nZen never did.\n\nThe posture shapes the mood.\nThe breath changes the thought.\nThe thought tightens the shoulder.\nThe exercise clears the mind.\n\nYou cannot tend to one\nwithout affecting the other.\n\nThe warrior who neglected the body\nhad a dull mind.\nThe scholar who neglected the body\nhad fragile ideas.\n\nWhat does your body need today?\n\n#MindBody #Holistic",
        "evening": "Your body has been carrying\nyour mind's burdens all day.\n\nGive it something in return tonight.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 117,
        "morning": "Let something die\nso something real can live.\n\n大死一番\nDaishi ichiban\n\n\"Die the great death —\nand truly live.\"\n\nThe great death is not physical.\nIt is the death of the limited self.\n\nThe identity that was holding you back.\nThe story that was keeping you small.\nThe comfort that was blocking the next level.\n\nDying to what you were\nis the only way\nto become what you need to be.\n\nWhat version of yourself\nneeds to be released?\n\n#Transformation #Zen",
        "evening": "What died in you this year\nthat needed to?\n\nHonor it.\nAnd move forward.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 118,
        "morning": "Wherever you are —\nown it completely.\n\n随所作主\nZuisho sa shu\n\n\"Wherever you stand,\nbe the master.\"\n\nThe Zen teacher Linji said this.\nNot arrogance — presence.\n\nIn the difficult meeting:\nyou are the master.\nIn the mundane task:\nyou are the master.\nIn the unexpected situation:\nyou are the master.\n\nNot controlling everything.\nResponding fully to whatever arises.\n\nThe master is not the one\nwho controls the room.\nThe master is the one\nfully present in it.\n\n#Presence #Mastery",
        "evening": "Were you the master of your situation today —\nor were you reacting\nwithout presence?\n\nTomorrow: choose presence first.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 119,
        "morning": "The most profound invitation\nis the simplest one.\n\n喫茶去\nKissako\n\n\"Have a cup of tea.\nBe present.\"\n\nA Zen master's answer to every deep question:\n'Have you had your morning tea?'\n\nNot a dismissal. A teaching.\n\nThe deepest practice is not found\nin the extraordinary moment.\nIt's found in the cup of tea.\nIn the ordinary morning.\nIn the unremarkable Tuesday.\n\nBe fully present for this cup.\nNot the next one.\nThis one.\n\n#Zen #Ordinary",
        "evening": "What ordinary moment today\ndeserved more attention\nthan you gave it?\n\nTomorrow, give one ordinary thing\nyour full presence.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 120,
        "morning": "You started with nothing.\nYou still have everything.\n\n本来無一物\nHonrai mu ichimotsu\n\n\"Originally, there is nothing.\nAnd that is everything.\"\n\nHuineng, the Sixth Patriarch, wrote:\n\"Originally there is not a single thing.\"\n\nThe mirror of the mind needs no polishing.\nBecause it was never dirty.\n\nYour original nature is not something to be built.\nIt is something to stop covering up.\n\nAll the striving, performing, accumulating —\ncovering something that was always whole.\n\nYou started whole.\nYou still are.\n\n#Zen #OriginalNature",
        "evening": "Beneath the striving,\nbeneath the performance —\nyou were always enough.\n\nRest in that tonight.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 121,
        "morning": "The label obscures the thing.\n\n花は花\nHana wa hana\n\n\"A flower\nis simply a flower.\"\n\nBefore you learned the word 'flower',\nyou saw it directly.\nThe color. The shape. The fragrance.\n\nAfter the word, you see the category.\nNot the flower.\n\nThis is how we lose the world.\nOne label at a time.\n\nZen practice reverses this.\nLook at the thing before the word.\nAt the person before the role.\nAt the moment before the judgment.\n\nJust this. Just here. Just now.\n\n#DirectExperience #Zen",
        "evening": "See one thing tonight\nbefore you name it.\n\nA face.\nA light.\nA texture.\n\nJust see it.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 122,
        "morning": "You're already in the right place.\n\n此処が道場\nKoko ga dojo\n\n\"Here, now —\nthis is your training ground.\"\n\nThe dojo is not a special place.\nThe dojo is wherever you are.\n\nThe difficult conversation: dojo.\nThe frustrating task: dojo.\nThe person who tests your patience: dojo.\n\nYou don't need ideal conditions to practice.\nThe imperfect conditions are the practice.\n\nStop waiting for the right moment.\nThe right moment is always now.\nThe right place is always here.\n\n#Dojo #Practice",
        "evening": "What trained you today\nthat didn't look like training?\n\nEvery difficult moment\nis the dojo.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 123,
        "morning": "Bypass the system.\nGo straight to the source.\n\n直指人心\nJikishi ninshin\n\n\"Point directly\nto the human heart.\"\n\nBodhidharma's transmission:\nnot scripture, not ritual.\nDirect pointing.\n\nThe best teachers skip the apparatus.\nThey point at the thing itself.\n\nThe coach who sees exactly what's wrong.\nThe mentor who says the uncomfortable truth.\nThe friend who skips the small talk.\n\nDirect pointing is a gift.\nSometimes it lands. Sometimes it stings.\nBut it respects the person enough\nto tell them the truth.\n\n#DirectCommunication #Truth",
        "evening": "Who in your life\nis willing to point directly at what's true?\n\nAnd are you willing to hear it?",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 124,
        "morning": "You are not a temporary blip.\nYou are what has always been.\n\n不生不滅\nFusho fumetsu\n\n\"Neither born nor destroyed.\"\n\nThe Heart Sutra:\nform is emptiness.\nEmptiness is form.\n\nThe energy that animates you\nwas not created at your birth.\nIt will not be destroyed at your death.\n\nThis is not theology.\nIt is physics: energy transforms, never disappears.\n\nYou are a form that the universe\nis temporarily wearing.\n\nThat changes how you hold\nboth your gains and your losses.\n\n#Impermanence #Eternity",
        "evening": "Something in you has always been.\nAnd always will be.\n\nRest in that.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 125,
        "morning": "The cherry blossoms fall.\nAnd that is why they are beautiful.\n\n無常観\nMujokan\n\n\"All things pass —\nand that is beautiful.\"\n\nThe Japanese built an entire aesthetic\naround impermanence.\n\nThe blossom is treasured because it falls.\nThe sunset is beautiful because it ends.\nThe moment is precious because it passes.\n\nPermanent things are taken for granted.\nThe temporary is the treasure.\n\nWhat in your life right now\nis temporary — and more beautiful for it?\n\n#Mujokan #Impermanence",
        "evening": "This day is ending.\nYou will not have it again.\n\nWhat was beautiful about it\nthat you almost missed?",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    # ===== 戦略・兵法 (day126〜150) =====
    {
        "day": 126,
        "morning": "The one who wins the most battles\nis not always the greatest strategist.\n\n知彼知己\nChi hi chi ki\n\n\"Know your enemy.\nKnow yourself.\"\n\nSun Tzu: in a hundred battles,\nknow both — you will not lose.\nKnow one — you may win or lose.\nKnow neither — you will lose every time.\n\nSelf-knowledge is strategy.\nUnderstanding your weaknesses before your opponent does.\nKnowing your patterns before they're exploited.\n\nAnd the enemy you underestimate\nis the one who surprises you.\n\nKnow both. Win before fighting.\n\n#SunTzu #Strategy",
        "evening": "What do you know about yourself\nthat your opponent doesn't?\n\nWhat do they know about you\nthat you don't?",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 127,
        "morning": "The most honest people\nare the most easily deceived.\n\n兵は詭道なり\nHei wa kido nari\n\n\"All warfare\nis based on deception.\"\n\nSun Tzu's most famous line.\nAnd the most misunderstood.\n\nNot a license for dishonesty in daily life.\nA warning about the nature of competition.\n\nWhen capable, appear incapable.\nWhen active, appear inactive.\nWhen near, appear far.\n\nThe negotiator who shows all their cards loses.\nThe competitor who reveals their strategy gets countered.\n\nProtect your process.\nReveal your results.\n\n#SunTzu #Negotiation",
        "evening": "Where are you being too transparent\nabout your strategy?\n\nAnd where are you being deceived\nbecause you're not looking clearly?",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 128,
        "morning": "Speed is not just movement.\nSpeed is decision.\n\n速戦即決\nSokusen sokketsu\n\n\"Strike fast.\nDecide fast.\"\n\nMost opportunities have a window.\nThe window closes.\n\nAnalysis paralysis is not caution.\nIt is a decision — the decision to do nothing —\nmade slowly and expensively.\n\nThe best decision made now\nbeats the perfect decision made too late.\n\nTrain your judgment.\nTrust it.\nAct before the window closes.\n\n#Speed #Decision",
        "evening": "What did you delay today\nthat should have been decided?\n\nDecide it now.\nOr decide to let it go.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 129,
        "morning": "The moment is speaking.\nAre you listening?\n\n機を見るに敏\nKi o miru ni bin\n\n\"Read the moment.\nAct without delay.\"\n\nKi — the opportune moment.\nBin — the sharpness to see and seize it.\n\nOpportunity doesn't announce itself.\nIt appears in disguise.\nAs a problem. A gap. A brief opening.\n\nThe strategist who saw ki\ndid not wait for permission.\nDid not wait for more information.\nRead the moment. Moved.\n\nSharpening ki-reading is a practice.\nPay attention to what's shifting.\n\n#Opportunity #Timing",
        "evening": "Did you notice the moment today\nthat was asking to be seized?\n\nWhere did you hesitate\nwhen moving would have served you?",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 130,
        "morning": "Initiative is not aggression.\nIt is the refusal\nto let others write your story.\n\n先手必勝\nSente hissho\n\n\"The first to move\nhas the advantage.\"\n\nIn chess, in negotiation, in business —\nthe one who sets the frame\ncontrols the game.\n\nReaction is always playing catch-up.\nAction sets the terms.\n\nThis doesn't mean recklessness.\nIt means: where in your life are you\nwaiting to respond\nwhen you could be leading?\n\nMove first. Set the agenda.\nLet others respond to you.\n\n#Initiative #Leadership",
        "evening": "Tomorrow: one area\nwhere you will move first\ninstead of waiting.\n\nDecide now what that is.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 131,
        "morning": "The shortcut is often\nthe longest way.\n\n迂直の計\nUcho no kei\n\n\"The indirect path\nis often the fastest.\"\n\nSun Tzu called it the Detour Advantage.\n\nThe army that marched directly to the enemy\nwas expected. Met. Stopped.\n\nThe one that took the longer path\narrived unexpected.\nFrom a direction that had no defense.\n\nIn your work:\nthe direct approach is often the obvious one.\nEveryone is doing it.\nIt's crowded and defended.\n\nWhere is the indirect path\nno one else is taking?\n\n#Strategy #IndirectPath",
        "evening": "What's the unconventional approach\nyou've been avoiding\nbecause it looked harder?\n\nIt might be the fastest way.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 132,
        "morning": "Reactive people never lead.\nThey follow.\n\n後手必敗\nKote hipai\n\n\"He who only responds\nalways loses.\"\n\nWaiting to see what others do.\nAdjusting. Reacting. Catching up.\n\nThis is the posture of the permanently second.\n\nLeaders are not always smarter.\nThey are earlier.\nThey see what's coming\nand move before it arrives.\n\nIn your field — what's coming?\nAnd are you moving toward it\nor waiting to see how it lands?\n\n#Proactive #Leadership",
        "evening": "Where are you one step behind\nbecause you waited\ninstead of moved?\n\nWhat would getting ahead look like?",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 133,
        "morning": "It's not over when you're losing.\nIt's over when you stop.\n\n形勢逆転\nKeisei gyakuten\n\n\"The tide can always turn.\"\n\nEvery dramatic comeback\nbegan at a moment when winning looked impossible.\n\nThe team down by twenty.\nThe negotiation that seemed dead.\nThe career that looked finished.\n\nThe tide turned because someone\nkept working when the outcome looked decided.\n\nNobody comes back who gives up at halftime.\n\nAre you at halftime right now,\ntempted to call it?\n\nThe tide is always capable of turning.\n\n#Comeback #Persistence",
        "evening": "What looked decided today\nthat actually isn't?\n\nThe tide has not gone out forever.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 134,
        "morning": "Sacrifice is not loss.\nIt's investment.\n\n捨石\nSutego\n\n\"Sacrifice a piece\nto win the game.\"\n\nIn Go, the sacrificed stone is called sutego.\nGiven up deliberately.\nNot lost — spent.\n\nThe master can sacrifice a piece\nbecause they see ten moves ahead.\n\nWhat are you refusing to give up\nthat is blocking a larger win?\n\nThe sunk cost you're defending.\nThe position you're protecting.\nThe small win you're holding\ninstead of the bigger move.\n\nSome losses are purchases.\n\n#Strategy #Sacrifice",
        "evening": "What do you need to let go\nto make the larger move?\n\nName it. Then decide.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 135,
        "morning": "Scattered effort.\nScattered results.\n\n一網打尽\nIchimo dajin\n\n\"One net.\nOne sweep.\nNo escape.\"\n\nThe master strategist does not fight on ten fronts.\nHe chooses the right moment,\nsets the net,\nand sweeps once.\n\nFocus is the net.\nTiming is the sweep.\n\nYour attention is your most valuable resource.\nWhere it goes, results follow.\nWhere it scatters, nothing grows.\n\nWhat deserves your one net right now?\nWhat would you catch\nif you focused fully?\n\n#Focus #Strategy",
        "evening": "Where did your attention scatter today?\n\nTomorrow: one net.\nThrow it deliberately.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 136,
        "morning": "Three advantages.\nAll three, or lose.\n\n天の時、地の利、人の和\nTen no toki, chi no ri, hito no wa\n\n\"Timing, terrain, unity —\nthese three win wars.\"\n\nTiming: is now the right moment?\nTerrain: are conditions favorable?\nUnity: is the team aligned?\n\nMost failures can be traced\nto one of the three being wrong.\n\nThe right idea at the wrong time fails.\nThe right timing with the wrong team fails.\nPerfect alignment on the wrong terrain fails.\n\nCheck all three before you move.\n\n#Strategy #Leadership",
        "evening": "For your biggest current challenge:\nhow is your timing?\nYour conditions?\nYour alignment?\n\nFix the weakest one.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 137,
        "morning": "Desperation, correctly channeled,\nis the most powerful fuel available.\n\n死地に生を求めよ\nShichi ni sei o motomeyo\n\n\"Seek life\nin the place of death.\"\n\nSun Tzu: place your soldiers in deadly ground,\nand they will fight to survive.\n\nComfort produces mediocrity.\nDanger produces clarity.\n\nThe person with nothing to lose\nhas everything to gain.\n\nWhat is your deadly ground right now?\nThe deadline. The debt. The relationship at stake.\n\nUse the pressure.\nDon't be crushed by it.\n\n#Pressure #Motivation",
        "evening": "What pressure today\ncould have been fuel\nbut you spent as anxiety?\n\nConvert it tomorrow.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 138,
        "morning": "Shared danger\ncreates unlikely alliances.\n\n呉越同舟\nGo etsu doshu\n\n\"Even enemies must cooperate\nwhen survival demands it.\"\n\nWu and Yue were bitter rivals.\nBut in the same storm-tossed boat,\nthey rowed together.\n\nThe principle: common threat\noverrides historic conflict.\n\nIn your world — where are you\nstaying in opposition\nwhen cooperation would serve everyone?\n\nWhere could you row with someone\nyou don't entirely like\nto reach a destination you both need?\n\n#Cooperation #Alliance",
        "evening": "Who could you cooperate with\nthat you've been avoiding\nbecause of past friction?\n\nThe boat needs rowers.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 139,
        "morning": "The best fight\nis the one never fought.\n\n不戦而勝\nFusen ni shite katsu\n\n\"The greatest victory\nis one never fought.\"\n\nSun Tzu's highest principle.\nDefeating the enemy without engaging.\n\nThrough positioning so strong\nthey choose not to attack.\nThrough relationships that make conflict unnecessary.\nThrough strategy so clear\nthe outcome is obvious before it begins.\n\nThe warrior who fights every battle\nis eventually exhausted.\nThe one who doesn't need to fight\nhas mastered the deeper art.\n\nWhere can you win without war?\n\n#SunTzu #Strategy",
        "evening": "What conflict could you dissolve\nbefore it becomes one?\n\nThe best victory is preventive.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 140,
        "morning": "Speed is a weapon.\nDeliberation is expensive.\n\n軍は神速を貴ぶ\nGun wa shinsoku o tatttobu\n\n\"An army prizes\nswiftness above all.\"\n\nSun Tzu again.\nBecause it cannot be repeated enough.\n\nDeliberation has value. Preparation has value.\nBut at some point, the window closes.\nThe opportunity moves on.\nThe gap closes.\n\nThe general who paused to be perfect\narrived at a defended position.\nThe one who moved swiftly\narrived before the defense was ready.\n\nMove. Learn. Adjust.\nFaster than the opposition can respond.\n\n#Speed #Action",
        "evening": "What needed to move faster today?\n\nWhat would you do differently\nif you valued speed more than perfection?",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 141,
        "morning": "Numbers are not destiny.\nStrategy is.\n\n寡をもって衆を制す\nKa o motte shu o seisu\n\n\"With few,\nmaster the many.\"\n\nEvery underdog story\nis a story of superior positioning.\n\nThe small team that outmaneuvers the large one.\nThe startup that outmaneuvers the corporation.\nThe individual who changes the conversation.\n\nYou don't need the biggest army.\nYou need the clearest strategy.\nAnd the willingness to commit to it fully.\n\nWhere are you thinking\nyou need more resources\nwhen you need better positioning?\n\n#Strategy #Underdog",
        "evening": "You don't have every advantage.\nNobody does.\n\nWhat advantage do you have\nthat you're not fully using?",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 142,
        "morning": "Predictability is vulnerability.\n\n奇正相生\nKi sei sojo\n\n\"Order and surprise —\neach gives birth to the other.\"\n\nThe orthodox move sets up the unorthodox.\nThe pattern makes the deviation surprising.\nThe expected creates the unexpected.\n\nThe brilliant general used both:\nconventional enough to be legible,\nunpredictable enough to be lethal.\n\nIn your work:\nwhere are you purely conventional?\nWhere can surprise create advantage?\n\nAnd where does surprise need the safety of order first?\n\n#Creativity #Strategy",
        "evening": "What expected move\nsets up your unexpected one?\n\nPlan the surprise\nfrom the inside out.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 143,
        "morning": "The slow path can arrive first.\n\n後発先至\nKohatsu senshi\n\n\"Leave late —\narrive first.\"\n\nNot a paradox. A skill.\n\nThe army that departed last\nbut chose better roads arrived first.\n\nIn modern terms: start late, but start sharp.\nBetter preparation, clearer route, fewer wrong turns.\n\nThe person who spends more time planning\nsometimes outpaces the one who started first\nbut stumbled.\n\nWhen is late-with-clarity\nbetter than early-with-confusion?\n\n#Planning #Strategy",
        "evening": "Where would fewer wrong turns\nhave saved you time today?\n\nWhat's the smarter road\nyou haven't taken yet?",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 144,
        "morning": "Truth and misdirection\nboth belong in the toolkit.\n\n虚実相交\nKyojitsu soko\n\n\"Use both deception\nand truth.\"\n\nNot a license to lie.\nA map of how attention works.\n\nThe magician uses both hands.\nOne distracts. One acts.\n\nIn communication:\nwhere you direct attention\nshapes what is seen and missed.\n\nThe leader who says everything\nleaves nothing for emphasis.\nStrategic emphasis — truth with selection —\nis not dishonesty.\n\nIt is clarity about what matters most.\n\n#Communication #Strategy",
        "evening": "Where did you emphasize the right thing today?\n\nAnd where did noise\ncrowd out what mattered?",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 145,
        "morning": "Shallow plans produce\nsurprise at every turn.\n\n謀深ければ行い遠し\nHakarigoto fukaku, okonai toshi\n\n\"Deep planning enables\nfar-reaching action.\"\n\nThe general who planned three moves ahead\nmoved with freedom at each step.\nThe one who planned one move ahead\nwas always improvising.\n\nDeep planning is not rigidity.\nIt's the opposite: because you've thought through\nmore scenarios, you adapt faster.\n\nYou're not surprised — you prepared for this.\nYou're not lost — you mapped this terrain.\n\nWhat are you underprepared for?\n\n#Planning #Foresight",
        "evening": "What scenario did you not plan for today\nthat caught you off guard?\n\nPlan for it now.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 146,
        "morning": "In competition,\nmomentum is everything.\n\n兵は速きを尊ぶ\nHei wa hayaki o tatttobu\n\n\"In war,\nspeed is everything.\"\n\nThe slow-moving opportunity\nbecomes a defended position.\nThe gradual conversation\nbecomes an entrenched disagreement.\nThe delayed decision\nbecomes someone else's.\n\nSpeed is not recklessness.\nIt is the refusal to let opportunity expire.\n\nTrain the habit of fast decision.\nClear data. Clear criteria. Move.\n\nPerfect is the enemy of timely.\n\n#Speed #Momentum",
        "evening": "What decision do you need to make\nthat has been waiting for perfect information?\n\nMake it with what you have.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 147,
        "morning": "Waiting to be attacked\nis already losing ground.\n\n攻は守なり\nKo wa mamori nari\n\n\"The best defense\nis offense.\"\n\nThe passive defense becomes the slow contraction.\nBorder after border defended.\nNone of them held forever.\n\nThe active defense —\ncontinually expanding, testing, probing —\nforced the opponent to respond rather than press.\n\nIn your field:\nwhere are you defending territory\nwhen you could be creating it?\n\nThe best protection\nis being too busy moving forward\nto be caught standing still.\n\n#Offense #Initiative",
        "evening": "Where are you defending\nwhen you could be building?\n\nDefense can be exhausting.\nOffense can be energizing.\nChoose one area to push tomorrow.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 148,
        "morning": "The most efficient action\nlooks like no action.\n\n無為にして為さざるなし\nMui ni shite nasazaru nashi\n\n\"Do nothing —\nand nothing remains undone.\"\n\nThis is Wu Wei from the Tao Te Ching.\nNot laziness. Not passivity.\n\nAction in harmony with the natural flow of events.\nNo forcing. No fighting the current.\nMoving with what is, not against it.\n\nThe leader who controls by force\nbecomes exhausted.\nThe one who creates conditions\nand allows results\nseems to do nothing\nwhile everything gets done.\n\n#WuWei #Leadership",
        "evening": "Where did you force today\nwhat could have flowed?\n\nWhat would effortless action\nlook like in that situation?",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 149,
        "morning": "The prepared are rarely lucky.\nThey're usually ready.\n\n勝負は時の運\nShobu wa toki no un\n\n\"Victory and defeat\nboth depend on timing.\"\n\nTiming cannot be fully controlled.\nBut it can be prepared for.\n\nThe general who had trained his army\nwas ready when the moment came.\nThe one who waited for the moment to train\nwas always behind.\n\nLuck is when preparation\nmeets opportunity.\n\nAre you preparing\nfor the timing you need?\n\n#Timing #Preparation",
        "evening": "What are you preparing for\nthat hasn't arrived yet?\n\nKeep preparing.\nThe timing will come.",
        "hashtags_set_A": HASHTAGS_A,
        "hashtags_set_B": HASHTAGS_B,
        "hashtags_set_C": HASHTAGS_C
    },
    {
        "day": 150,
        "morning": "Winning every battle\nmight mean losing the war.\n\n百戦百勝\nHyakusen hyakusho\n\n\"Win every battle —\nby knowing when not to fight.\"\n\nSun Tzu's counterintuitive truth:\n100 victories in 100 battles\nis not supreme excellence.\n\nSupreme excellence:\nsubduing the enemy without fighting.\n\nEvery battle costs.\nEven won battles drain resources.\nThe strategist who fights only necessary battles\narrivals fresh to the ones that matter.\n\nWhich fights are you taking\nthat aren't worth winning?\n\n#SunTzu #Strategy",
        "evening": "Which conflict today\nwasn't worth the energy you spent?\n\nName it. And let it go.",
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
