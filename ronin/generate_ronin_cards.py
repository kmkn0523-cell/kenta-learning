# generate_ronin_cards.py
# @RoninWords用の書道カード画像を自動生成するスクリプト
# Reactコンポーネント（ronin_words.jsx）のデザインに合わせた版
# 使い方: python3 generate_ronin_cards.py

from PIL import Image, ImageDraw, ImageFont
import os
import math

# カードのサイズ（正方形 1080×1080）
W, H = 1080, 1080

# 和紙風の背景色（Reactと同じ配列）
PAPERS = ["#f0e6d0", "#ede0c8", "#f3e9d5", "#e8ddc8", "#f1e7d2"]

# ブランドカラー（赤）
RED    = (158, 30, 14)
INK    = (18, 10, 4)      # 墨色（ほぼ黒）
SEPIA  = (80, 50, 20)     # セピア（ローマ字・英語テキスト用）

# フォントのパス
FONT_JP    = "/home/kenta_kamijyo/fonts/YujiSyuku.ttf"           # 筆書き風かな漢字
FONT_ROMAN = "/home/kenta_kamijyo/fonts/CormorantGaramond-Italic.ttf"  # エレガントな欧文
FONT_SERIF = "/home/kenta_kamijyo/fonts/NotoSerifJP.otf"          # バックアップ

# レイアウト定数（全て1080×1080基準）
MARGIN      = 54   # 外側余白
SEAL_SIZE   = 120  # 右上のRWシールのサイズ
SEAL_PAD    = 54   # シールの端からの距離
TOP_RULE_Y  = 160  # 上の区切り線のY座標
BOT_RULE_Y  = 860  # 下の区切り線のY座標
RULE_PAD    = 94   # 区切り線の左右余白

# 格言データ（Day01〜Day100）
proverbs = [
    {"day":  1, "jp": "一期一会",                   "roma": "Ichi go ichi e",                        "en": "This moment will never come again."},
    {"day":  2, "jp": "能ある鷹は爪を隠す",          "roma": "No aru taka wa tsume o kakusu",         "en": "A skilled hawk hides its talons."},
    {"day":  3, "jp": "七転び八起き",               "roma": "Nana korobi ya oki",                    "en": "Fall seven times. Rise eight."},
    {"day":  4, "jp": "背水の陣",                   "roma": "Haisui no jin",                         "en": "Fight with your back to the river."},
    {"day":  5, "jp": "諸行無常",                   "roma": "Shogyo mujo",                           "en": "Nothing in this world stays the same."},
    {"day":  6, "jp": "石の上にも三年",              "roma": "Ishi no ue ni mo san nen",              "en": "Even a cold stone warms."},
    {"day":  7, "jp": "虎穴に入らずんば虎子を得ず",  "roma": "Koketsu ni irazunba koji o ezu",        "en": "No reward without entering the den."},
    {"day":  8, "jp": "覚悟を決めた者は強い",        "roma": "Kakugo o kimeta mono wa tsuyoi",        "en": "One who has decided is unbreakable."},
    {"day":  9, "jp": "足るを知る",                 "roma": "Taru o shiru",                          "en": "Know when enough is enough."},
    {"day": 10, "jp": "実るほど頭を垂れる稲穂かな",  "roma": "Minoru hodo atama o tareru inaho kana", "en": "The richer the rice, the lower it bows."},
    {"day": 11, "jp": "初志貫徹",                   "roma": "Shoshi kantetsu",                       "en": "Stay true to what you set out to do."},
    {"day": 12, "jp": "急がば回れ",                 "roma": "Isogaba maware",                        "en": "The long way is often the shortest."},
    {"day": 13, "jp": "沈黙は金",                   "roma": "Chinmoku wa kin",                       "en": "Silence is gold."},
    {"day": 14, "jp": "継続は力なり",               "roma": "Keizoku wa chikara nari",               "en": "Consistency is strength."},
    {"day": 15, "jp": "以心伝心",                   "roma": "Ishin denshin",                         "en": "Heart speaks to heart without words."},
    {"day": 16, "jp": "千里の道も一歩から",          "roma": "Senri no michi mo ippo kara",           "en": "A thousand miles begins with one step."},
    {"day": 17, "jp": "出る杭は打たれる",            "roma": "Deru kui wa utareru",                   "en": "The nail that sticks up gets hammered."},
    {"day": 18, "jp": "好きこそものの上手なれ",      "roma": "Suki koso mono no jozu nare",           "en": "What you love, you'll master."},
    {"day": 19, "jp": "艱難汝を玉にす",             "roma": "Kannan nanji o tama ni su",             "en": "Hardship polishes you into a gem."},
    {"day": 20, "jp": "負けるが勝ち",               "roma": "Makeru ga kachi",                       "en": "Losing can be winning."},
    {"day": 21, "jp": "柔よく剛を制す",             "roma": "Ju yoku go o seisu",                    "en": "Softness overcomes hardness."},
    {"day": 22, "jp": "禍を転じて福となす",          "roma": "Wazawai o tenjite fuku to nasu",        "en": "Turn disaster into fortune."},
    {"day": 23, "jp": "窮すれば通ず",               "roma": "Kyu sureba tsuzu",                      "en": "When cornered, a way opens."},
    {"day": 24, "jp": "当たって砕けろ",              "roma": "Atatte kudakero",                       "en": "Charge in, even if you shatter."},
    {"day": 25, "jp": "情けは人の為ならず",          "roma": "Nasake wa hito no tame narazu",         "en": "Kindness to others is kindness to yourself."},
    {"day": 26, "jp": "型があるから型を破れる",      "roma": "Kata ga aru kara kata o yabureru",      "en": "Master the form, then break free."},
    {"day": 27, "jp": "一所懸命",                   "roma": "Isshoukenmei",                          "en": "Give everything to this one moment."},
    {"day": 28, "jp": "道を極めるには終わりがない",  "roma": "Michi o kiwameru ni wa owari ga nai",   "en": "The mastery of a path has no end."},
    {"day": 29, "jp": "武士は食わねど高楊枝",        "roma": "Bushi wa kuwanedo takayoji",            "en": "Dignity over comfort."},
    {"day": 30, "jp": "生き死に一如",               "roma": "Ikishi ni ichinyo",                     "en": "Life and death are one."},
    {"day": 31, "jp": "聞くは一時の恥",             "roma": "Kiku wa ichiji no haji",                "en": "The shame of asking lasts a moment."},
    {"day": 32, "jp": "千里の道も一歩から",           "roma": "Senri no michi mo ippo kara",           "en": "Even a journey of a thousand miles begins with one step."},
    {"day": 33, "jp": "継続は力なり",               "roma": "Keizoku wa chikara nari",               "en": "Consistency is strength."},
    {"day": 34, "jp": "塵も積もれば山となる",        "roma": "Chiri mo tsumoreba yama to naru",        "en": "Dust, piled up, becomes a mountain."},
    {"day": 35, "jp": "袖振り合うも他生の縁",        "roma": "Sode furi au mo tasho no en",           "en": "Even a brush of sleeves is a bond from a past life."},
    {"day": 36, "jp": "以心伝心",                   "roma": "Ishin denshin",                         "en": "Heart speaks to heart without words."},
    {"day": 37, "jp": "花鳥風月",                   "roma": "Kacho fugetsu",                         "en": "Flowers. Birds. Wind. Moon."},
    {"day": 38, "jp": "物の哀れ",                   "roma": "Mono no aware",                         "en": "The gentle sadness of things passing."},
    {"day": 39, "jp": "月に叢雲、花に風",           "roma": "Tsuki ni murakumo, hana ni kaze",       "en": "Clouds gather around the moon. Wind scatters the flowers."},
    {"day": 40, "jp": "足るを知る",                 "roma": "Taru o shiru",                          "en": "Know when enough is enough."},
    {"day": 41, "jp": "実るほど頭を垂れる稲穂かな",  "roma": "Minoru hodo atama o tareru inaho kana", "en": "The richer the rice, the lower it bows."},
    {"day": 42, "jp": "志高く",                     "roma": "Kokorozashi takaku",                    "en": "Aim high."},
    {"day": 43, "jp": "好きこそものの上手なれ",      "roma": "Suki koso mono no jozu nare",           "en": "What you love, you'll master."},
    {"day": 44, "jp": "一芸は身を助ける",            "roma": "Ichigei wa mi o tasukeru",              "en": "One skill can save your life."},
    {"day": 45, "jp": "魂を込めて作れ",             "roma": "Tamashii o komete tsukure",             "en": "Pour your soul into what you make."},
    {"day": 46, "jp": "損して得取れ",               "roma": "Son shite toku tore",                   "en": "Take the loss now. Claim the gain later."},
    {"day": 47, "jp": "急いては事を仕損じる",        "roma": "Seite wa koto o shissonjiru",           "en": "Haste makes waste."},
    {"day": 48, "jp": "弱さも強さになる",            "roma": "Yowasa mo tsuyosa ni naru",             "en": "Even weakness can become strength."},
    {"day": 49, "jp": "捨てる神あれば拾う神あり",    "roma": "Suteru kami areba hirou kami ari",      "en": "A god who abandons you — a god who picks you up."},
    {"day": 50, "jp": "怪我の功名",                 "roma": "Kega no komyo",                         "en": "A lucky break born from a blunder."},
    {"day": 51, "jp": "雨降って地固まる",            "roma": "Ame futte ji katamaru",                 "en": "After the rain, the ground grows harder."},
    {"day": 52, "jp": "禍福は糾える縄の如し",        "roma": "Kafuku wa azanaeru nawa no gotoshi",    "en": "Fortune and misfortune are twisted together like rope."},
    {"day": 53, "jp": "出る杭は打たれる",            "roma": "Deru kui wa utareru",                   "en": "The nail that sticks up gets hammered down."},
    {"day": 54, "jp": "三人寄れば文殊の知恵",        "roma": "Sannin yoreba monju no chie",           "en": "Three heads together hold the wisdom of a god."},
    {"day": 55, "jp": "転ばぬ先の杖",               "roma": "Korobanu saki no tsue",                 "en": "Better to have a walking stick before you fall."},
    {"day": 56, "jp": "急がば回れ",                 "roma": "Isogaba maware",                        "en": "If you're in a hurry, take the long way around."},
    {"day": 57, "jp": "沈黙は金",                   "roma": "Chinmoku wa kin",                       "en": "Silence is gold."},
    {"day": 58, "jp": "覚悟を決めた者は強い",        "roma": "Kakugo o kimeta mono wa tsuyoi",        "en": "One who has truly made up their mind is unbreakable."},
    {"day": 59, "jp": "後悔先に立たず",             "roma": "Kokai saki ni tatazu",                  "en": "Regret never arrives early."},
    {"day": 60, "jp": "高慢は損気",                 "roma": "Koman wa sonki",                        "en": "Arrogance invites loss."},
    {"day": 61, "jp": "間",                         "roma": "Ma",                                    "en": "The power of the space between."},
    {"day": 62, "jp": "道",                         "roma": "Do",                                    "en": "The Way. A lifelong path of becoming."},
    {"day": 63, "jp": "七難八苦を乗り越えてこそ",    "roma": "Shichinin hakku o norikoete koso",      "en": "Only through great trials does greatness emerge."},
    {"day": 64, "jp": "辛抱する木に金がなる",        "roma": "Shinbo suru ki ni kane ga naru",        "en": "The tree that endures bears golden fruit."},
    {"day": 65, "jp": "苦は楽の種",                 "roma": "Ku wa raku no tane",                    "en": "Suffering is the seed of joy."},
    {"day": 66, "jp": "百折不撓",                   "roma": "Hyakusetsu futo",                       "en": "Bend a hundred times, but never break."},
    {"day": 67, "jp": "高慢は損気",                 "roma": "Koman wa sonki",                        "en": "Arrogance invites loss."},
    {"day": 68, "jp": "自慢は知恵の行き止まり",      "roma": "Jiman wa chie no yukidomari",           "en": "Boasting is where wisdom ends."},
    {"day": 69, "jp": "不足を言うな、有余を言え",    "roma": "Fusoku o iu na, yuyo o ie",             "en": "Don't complain about what's missing."},
    {"day": 70, "jp": "小欲知足",                   "roma": "Shoyoku chisoku",                       "en": "Small desires, deep contentment."},
    {"day": 71, "jp": "無欲は大欲に勝る",            "roma": "Muyoku wa taiyoku ni masaru",           "en": "Wanting nothing is greater than wanting everything."},
    {"day": 72, "jp": "熱い心、冷静な頭",           "roma": "Atsui kokoro, reisei na atama",         "en": "A burning heart, a cool head."},
    {"day": 73, "jp": "志高く",                     "roma": "Kokorozashi takaku",                    "en": "Aim high."},
    {"day": 74, "jp": "夢は大きく、行動は今",        "roma": "Yume wa okiku, kodo wa ima",            "en": "Dream big, act now."},
    {"day": 75, "jp": "弱さも強さになる",            "roma": "Yowasa mo tsuyosa ni naru",             "en": "Even weakness can become strength."},
    {"day": 76, "jp": "窮すれば通ず",               "roma": "Kyu sureba tsuzu",                      "en": "When cornered, a way opens."},
    {"day": 77, "jp": "金継ぎ",                     "roma": "Kintsugi",                              "en": "Repair with gold. The break becomes beauty."},
    {"day": 78, "jp": "背水の陣",                   "roma": "Haisui no jin",                         "en": "No retreat — or you drown."},
    {"day": 79, "jp": "一所懸命",                   "roma": "Isshoukenmei",                          "en": "Be fully here. Or not at all."},
    {"day": 80, "jp": "桜散る、されど根は残る",      "roma": "Sakura chiru, saredo ne wa nokoru",     "en": "The cherry blossom falls, but the roots remain."},
    {"day": 81, "jp": "鬼に金棒",                   "roma": "Oni ni kanabo",                         "en": "The strong, made even stronger."},
    {"day": 82, "jp": "春夏秋冬、それぞれに美しい",  "roma": "Shunkashuto, sorezore ni utsukushii",   "en": "Every season has its own beauty."},
    {"day": 83, "jp": "形あるものはいつか壊れる",    "roma": "Katachi aru mono wa itsuka kowareru",   "en": "Everything that has form will one day break."},
    {"day": 84, "jp": "人生意気に感ず",             "roma": "Jinsei iki ni kanzu",                   "en": "Live by passion, not by calculation."},
    {"day": 85, "jp": "花は桜木、人は武士",          "roma": "Hana wa sakuragi, hito wa bushi",       "en": "Among flowers the cherry blossom. Among men the warrior."},
    {"day": 86, "jp": "禍福は糾える縄の如し",        "roma": "Kafuku wa azanaeru nawa no gotoshi",    "en": "Fortune and misfortune are twisted like rope."},
    {"day": 87, "jp": "雨降って地固まる",            "roma": "Ame futte ji katamaru",                 "en": "After the rain, the ground grows harder."},
    {"day": 88, "jp": "男子の一言、金鉄の如し",      "roma": "Danshi no ichigon, kintetsu no gotoshi","en": "A person's word is iron."},
    {"day": 89, "jp": "死して不朽の名を残せ",        "roma": "Shishite fukyu no na o nokose",         "en": "Die and leave a name that never fades."},
    {"day": 90, "jp": "事に臨んでは死を思え",        "roma": "Koto ni nozonde wa shi o omoe",         "en": "Think of death — and act without hesitation."},
    {"day": 91, "jp": "覚悟",                       "roma": "Kakugo",                                "en": "Accept all consequences before you begin."},
    {"day": 92, "jp": "武士道",                     "roma": "Bushido",                               "en": "The Way of the Warrior."},
    {"day": 93, "jp": "義",                         "roma": "Gi — Rectitude",                        "en": "Do what is right, even when it is hard."},
    {"day": 94, "jp": "仁",                         "roma": "Jin — Benevolence",                     "en": "Compassion, even for your enemies."},
    {"day": 95, "jp": "勇",                         "roma": "Yu — Courage",                          "en": "Fear acknowledged. Action taken anyway."},
    {"day": 96, "jp": "礼",                         "roma": "Rei — Respect",                         "en": "Every person is worthy of dignity."},
    {"day": 97, "jp": "誠",                         "roma": "Makoto — Honesty",                      "en": "No deception. Not even to yourself."},
    {"day": 98, "jp": "名誉",                       "roma": "Meiyo — Honor",                         "en": "You are your own judge."},
    {"day": 99, "jp": "忠義",                       "roma": "Chugi — Loyalty",                       "en": "Chosen commitment, fully kept."},
    {"day":100, "jp": "武士道百訓",                  "roma": "Bushido hyakukun",                      "en": "100 days. One truth. The Way continues."},

    # ── 禅・仏教の言葉（Day101〜125）──────────────────────────────
    {"day":101, "jp": "一切皆苦",             "roma": "Issai kaiku",              "en": "All of life involves suffering. Accept it."},
    {"day":102, "jp": "刹那",                "roma": "Setsuna",                  "en": "This single moment is all you have."},
    {"day":103, "jp": "無我",                "roma": "Muga",                     "en": "Release the self. You are larger than your ego."},
    {"day":104, "jp": "空",                  "roma": "Ku",                       "en": "Form is emptiness. Emptiness is form."},
    {"day":105, "jp": "慈悲",               "roma": "Jihi",                     "en": "Compassion for all living things."},
    {"day":106, "jp": "無心",               "roma": "Mushin",                   "en": "An empty mind moves without resistance."},
    {"day":107, "jp": "悟り",               "roma": "Satori",                   "en": "Awakening is not found. It is recognized."},
    {"day":108, "jp": "平常心",              "roma": "Heijoshin",                "en": "The ordinary mind is the Way."},
    {"day":109, "jp": "只管打坐",            "roma": "Shikantaza",               "en": "Just sit. Nothing else is needed."},
    {"day":110, "jp": "不立文字",            "roma": "Furyu monji",              "en": "Truth cannot be captured in words."},
    {"day":111, "jp": "生死事大",            "roma": "Shoji jidai",              "en": "Life and death — this is the great matter."},
    {"day":112, "jp": "自灯明",              "roma": "Ji tomyo",                 "en": "Be a lamp unto yourself."},
    {"day":113, "jp": "万物流転",            "roma": "Banbutsu ruten",           "en": "All things are in constant flow."},
    {"day":114, "jp": "行雲流水",            "roma": "Koun ryusui",              "en": "Move like clouds. Flow like water."},
    {"day":115, "jp": "因果応報",            "roma": "Inga oho",                 "en": "What you sow, you will reap."},
    {"day":116, "jp": "身心一如",            "roma": "Shinshin ichinyo",         "en": "Body and mind are one."},
    {"day":117, "jp": "大死一番",            "roma": "Daishi ichiban",           "en": "Die the great death — and truly live."},
    {"day":118, "jp": "随所作主",            "roma": "Zuisho sa shu",            "en": "Wherever you stand, be the master."},
    {"day":119, "jp": "喫茶去",              "roma": "Kissako",                  "en": "Have a cup of tea. Be present."},
    {"day":120, "jp": "本来無一物",          "roma": "Honrai mu ichimotsu",      "en": "Originally, there is nothing. And that is everything."},
    {"day":121, "jp": "花は花",              "roma": "Hana wa hana",             "en": "A flower is simply a flower."},
    {"day":122, "jp": "此処が道場",          "roma": "Koko ga dojo",             "en": "Here, now — this is your training ground."},
    {"day":123, "jp": "直指人心",            "roma": "Jikishi ninshin",          "en": "Point directly to the human heart."},
    {"day":124, "jp": "不生不滅",            "roma": "Fusho fumetsu",            "en": "Neither born nor destroyed."},
    {"day":125, "jp": "無常観",              "roma": "Mujokan",                  "en": "All things pass — and that is beautiful."},

    # ── 戦略・兵法の言葉（Day126〜150）──────────────────────────────
    {"day":126, "jp": "知彼知己",            "roma": "Chi hi chi ki",            "en": "Know your enemy. Know yourself."},
    {"day":127, "jp": "兵は詭道なり",        "roma": "Hei wa kido nari",         "en": "All warfare is based on deception."},
    {"day":128, "jp": "速戦即決",            "roma": "Sokusen sokketsu",         "en": "Strike fast. Decide fast."},
    {"day":129, "jp": "機を見るに敏",        "roma": "Ki o miru ni bin",         "en": "Read the moment. Act without delay."},
    {"day":130, "jp": "先手必勝",            "roma": "Sente hissho",             "en": "The first to move has the advantage."},
    {"day":131, "jp": "迂直の計",            "roma": "Ucho no kei",              "en": "The indirect path is often the fastest."},
    {"day":132, "jp": "後手必敗",            "roma": "Kote hipai",               "en": "He who only responds always loses."},
    {"day":133, "jp": "形勢逆転",            "roma": "Keisei gyakuten",          "en": "The tide can always turn."},
    {"day":134, "jp": "捨石",               "roma": "Sutego",                   "en": "Sacrifice a piece to win the game."},
    {"day":135, "jp": "一網打尽",            "roma": "Ichimo dajin",             "en": "One net. One sweep. No escape."},
    {"day":136, "jp": "天の時、地の利、人の和", "roma": "Ten no toki, chi no ri, hito no wa", "en": "Timing, terrain, unity — these three win wars."},
    {"day":137, "jp": "死地に生を求めよ",    "roma": "Shichi ni sei o motomeyo", "en": "Seek life in the place of death."},
    {"day":138, "jp": "呉越同舟",            "roma": "Go etsu doshu",            "en": "Even enemies must cooperate when survival demands it."},
    {"day":139, "jp": "不戦而勝",            "roma": "Fusen ni shite katsu",     "en": "The greatest victory is one never fought."},
    {"day":140, "jp": "軍は神速を貴ぶ",      "roma": "Gun wa shinsoku o tatttobu","en": "An army prizes swiftness above all."},
    {"day":141, "jp": "寡をもって衆を制す",  "roma": "Ka o motte shu o seisu",   "en": "With few, master the many."},
    {"day":142, "jp": "奇正相生",            "roma": "Ki sei sojo",              "en": "Order and surprise — each gives birth to the other."},
    {"day":143, "jp": "後発先至",            "roma": "Kohatsu senshi",           "en": "Leave late — arrive first."},
    {"day":144, "jp": "虚実相交",            "roma": "Kyojitsu soko",            "en": "Use both deception and truth."},
    {"day":145, "jp": "謀深ければ行い遠し",  "roma": "Hakarigoto fukaku, okonai toshi", "en": "Deep planning enables far-reaching action."},
    {"day":146, "jp": "兵は速きを尊ぶ",      "roma": "Hei wa hayaki o tatttobu", "en": "In war, speed is everything."},
    {"day":147, "jp": "攻は守なり",          "roma": "Ko wa mamori nari",        "en": "The best defense is offense."},
    {"day":148, "jp": "無為にして為さざるなし","roma": "Mui ni shite nasazaru nashi","en": "Do nothing — and nothing remains undone."},
    {"day":149, "jp": "勝負は時の運",        "roma": "Shobu wa toki no un",      "en": "Victory and defeat both depend on timing."},
    {"day":150, "jp": "百戦百勝",            "roma": "Hyakusen hyakusho",        "en": "Win every battle — by knowing when not to fight."},

    # ── 武士語録・名言（Day151〜175）─────────────────────────────────
    {"day":151, "jp": "我事において後悔せず",  "roma": "Wagakoto ni oite kokai sezu",  "en": "I do not regret what I have done."},
    {"day":152, "jp": "今日の我に昨日の我を斬れ", "roma": "Kyo no ware ni kino no ware o kire", "en": "Cut down yesterday's self with today's blade."},
    {"day":153, "jp": "剣は心なり",           "roma": "Ken wa kokoro nari",           "en": "The sword is the mind."},
    {"day":154, "jp": "風林火山",             "roma": "Fu-rin-ka-zan",                "en": "Swift as wind. Silent as forest. Fierce as fire. Immovable as mountain."},
    {"day":155, "jp": "死ぬ事と見つけたり",   "roma": "Shinu koto to mitsuke tari",   "en": "I have found the way — it is to die fully."},
    {"day":156, "jp": "鋼も鍛えずば剣とならず","roma": "Hagane mo kitaezuba ken to narazu","en": "Even steel must be forged to become a sword."},
    {"day":157, "jp": "武士は食わねど高楊枝", "roma": "Bushi wa kuwanedo takayoji",    "en": "A samurai bears hunger with dignity."},
    {"day":158, "jp": "七生報国",             "roma": "Shichisho hokoku",             "en": "Seven lives — all devoted to what matters."},
    {"day":159, "jp": "重荷を負うて遠き道",   "roma": "Omoni o oute toki michi",      "en": "Carry the weight. Walk the long road."},
    {"day":160, "jp": "功は急がず",           "roma": "Ko wa isogazu",                "en": "Achievement cannot be rushed."},
    {"day":161, "jp": "一騎当千",             "roma": "Ikki tosen",                   "en": "One warrior worth a thousand."},
    {"day":162, "jp": "義を見てせざるは勇なきなり","roma": "Gi o mite sezaru wa yu naki nari","en": "To see what is right and not do it — that is cowardice."},
    {"day":163, "jp": "生は重く死は軽し",     "roma": "Sei wa omoku shi wa karushi",   "en": "Life is heavy. Death is light."},
    {"day":164, "jp": "己を磨け",             "roma": "Onore o migake",               "en": "Polish yourself."},
    {"day":165, "jp": "身を捨ててこそ",       "roma": "Mi o sutete koso",             "en": "Only by letting go do you find what holds you."},
    {"day":166, "jp": "天知る地知る我知る",   "roma": "Ten shiru, chi shiru, ware shiru","en": "Heaven knows. Earth knows. You know."},
    {"day":167, "jp": "一剣に天地を截断す",   "roma": "Ikken ni tenchi o setsudan su", "en": "One sword cuts through heaven and earth."},
    {"day":168, "jp": "信は力なり",           "roma": "Shin wa chikara nari",          "en": "Belief is power."},
    {"day":169, "jp": "問わず語りは無用",     "roma": "Towazu gatari wa muyo",         "en": "Words unasked for are rarely needed."},
    {"day":170, "jp": "何事も一人前になれ",   "roma": "Nani goto mo ichininmae ni nare","en": "In all things, master your craft fully."},
    {"day":171, "jp": "生ある限り、鍛えよ",   "roma": "Sei aru kagiri, kitaeyo",       "en": "As long as there is life, forge yourself."},
    {"day":172, "jp": "一瞬の刃",             "roma": "Isshun no yaiba",              "en": "The edge of a single moment."},
    {"day":173, "jp": "弓矢も心の先から出でたり","roma": "Yumi ya mo kokoro no saki kara idetari","en": "Every arrow begins with the mind."},
    {"day":174, "jp": "黙して語らず",         "roma": "Mokushite katarazu",           "en": "Silence speaks what words cannot."},
    {"day":175, "jp": "武士道は死ぬことと見つけたり","roma": "Bushido wa shinu koto to mitsuke tari","en": "The way of the warrior is found in death."},

    # ── 自然・季節の言葉（Day176〜200）───────────────────────────────
    {"day":176, "jp": "花鳥風月",             "roma": "Kacho fugetsu",            "en": "Flower, bird, wind, moon — beauty in all things."},
    {"day":177, "jp": "雪月花",               "roma": "Setsu getsu ka",           "en": "Snow, moon, blossom — the three beauties."},
    {"day":178, "jp": "物の哀れ",             "roma": "Mono no aware",            "en": "The gentle sorrow of passing things."},
    {"day":179, "jp": "侘び寂び",             "roma": "Wabi-sabi",                "en": "Beauty in imperfection. Peace in impermanence."},
    {"day":180, "jp": "木漏れ日",             "roma": "Komorebi",                 "en": "The light that filters through leaves."},
    {"day":181, "jp": "木枯らし",             "roma": "Kogarashi",                "en": "The first cold wind that strips the trees bare."},
    {"day":182, "jp": "初雪",                 "roma": "Hatsuyuki",                "en": "The first snow. Everything begins again."},
    {"day":183, "jp": "春暁",                 "roma": "Shungyo",                  "en": "Dawn in spring — the world barely awake."},
    {"day":184, "jp": "夏の終わり",           "roma": "Natsu no owari",           "en": "The end of summer — bittersweet and vast."},
    {"day":185, "jp": "秋の空",               "roma": "Aki no sora",              "en": "The autumn sky — endlessly, piercingly clear."},
    {"day":186, "jp": "冬枯れ",               "roma": "Fuyugare",                 "en": "Winter bareness — the beauty of what remains."},
    {"day":187, "jp": "朝露",                 "roma": "Asatsuyu",                 "en": "Morning dew — gone before you notice it."},
    {"day":188, "jp": "夕焼け",               "roma": "Yuyake",                   "en": "The evening sky burns — and then it is dark."},
    {"day":189, "jp": "山は静かなり",         "roma": "Yama wa shizuka nari",     "en": "The mountain is silent. It does not explain itself."},
    {"day":190, "jp": "川の流れのように",     "roma": "Kawa no nagare no yo ni",  "en": "Like the flow of a river — always moving, never forced."},
    {"day":191, "jp": "大地は語らず",         "roma": "Daichi wa katarazu",       "en": "The earth does not speak. Yet everything grows from it."},
    {"day":192, "jp": "風は見えず",           "roma": "Kaze wa miezu",            "en": "You cannot see the wind. But you know when it has passed."},
    {"day":193, "jp": "桜散る",               "roma": "Sakura chiru",             "en": "The cherry blossoms fall — and we love them more for it."},
    {"day":194, "jp": "月夜に佇む",           "roma": "Tsukiyo ni tatazumu",      "en": "Standing still in the moonlight."},
    {"day":195, "jp": "霧の中",               "roma": "Kiri no naka",             "en": "In the mist — you see only what is right before you."},
    {"day":196, "jp": "波は繰り返す",         "roma": "Nami wa kurikaesu",        "en": "The waves return — again and again, without complaint."},
    {"day":197, "jp": "天地自然",             "roma": "Tenchi shizen",            "en": "Heaven, earth, and nature — the great teacher."},
    {"day":198, "jp": "一粒万倍",             "roma": "Ichiryu manbai",           "en": "One seed becomes ten thousand."},
    {"day":199, "jp": "草木も眠る",           "roma": "Kusaki mo nemuru",         "en": "Even the grass and trees fall asleep."},
    {"day":200, "jp": "道は続く",             "roma": "Michi wa tsuzuku",         "en": "The path continues. Keep walking."},
]


# ==================================================
# ユーティリティ関数
# ==================================================

def hex_to_rgb(hex_color):
    """16進数カラーコードをRGBに変換する"""
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def blend_color(base, overlay_rgb, alpha):
    """2色をalphaで合成する（0.0〜1.0）"""
    return tuple(int(b * (1 - alpha) + o * alpha) for b, o in zip(base, overlay_rgb))


def add_vignette(img):
    """
    画像の端を少し暗くするビネット効果を加える
    Reactのradial-gradientによるビネットを再現する
    """
    vignette = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(vignette)

    # 端から内側へのグラデーション矩形を重ねて端を暗くする
    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    layers = 40
    for i in range(layers):
        depth = i / layers        # 0（端）→1（内側）
        alpha = int(28 * (1 - depth) ** 1.8)  # 端ほど暗く
        ov_draw.rectangle([i * 2, i * 2, W - i * 2 - 1, H - i * 2 - 1],
                          outline=(90, 55, 15, alpha), width=3)

    return Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')


def draw_rw_seal(draw, x_center, y_center, size, font_r, font_w):
    """
    RWシール（右上の印章）を描画する
    Reactの SVG シールを PIL で再現する
    """
    half = size // 2
    x0 = x_center - half
    y0 = y_center - half
    x1 = x_center + half
    y1 = y_center + half

    lw = max(2, size // 54)  # 線の太さ（サイズに比例）

    # 外枠（赤い正方形）
    draw.rectangle([x0, y0, x1, y1], outline=RED, width=lw)

    # 対角線（左下→右上、Reactのlineと同じ方向）
    draw.line([(x0 + size // 6, y1 - size // 6),
               (x1 - size // 6, y0 + size // 6)],
              fill=RED, width=lw)

    # "R" — 左下エリアに大きく
    try:
        r_bbox = draw.textbbox((0, 0), "R", font=font_r)
        r_w = r_bbox[2] - r_bbox[0]
        r_h = r_bbox[3] - r_bbox[1]
        draw.text((x0 + size // 8, y0 + size // 2 - r_h // 2 + size // 10),
                  "R", font=font_r, fill=INK)
    except Exception:
        pass

    # "W" — 右下エリアに少し薄く
    try:
        w_bbox = draw.textbbox((0, 0), "W", font=font_w)
        w_h = w_bbox[3] - w_bbox[1]
        draw.text((x0 + size // 2, y0 + size // 2 - w_h // 2 + size // 10),
                  "W", font=font_w, fill=(*INK, 100))
    except Exception:
        pass


def draw_h_rule(draw, y, x0=RULE_PAD, x1=W - RULE_PAD, alpha=0.10):
    """
    水平の区切り線を描く（端が透明になるグラデーション風）
    """
    steps = 80
    for i in range(steps):
        # 中央が最も濃く、端が透明（三角波形）
        ratio = 1 - abs(i / steps * 2 - 1)  # 0→1→0 の三角関数
        a = int(255 * alpha * ratio)
        xi = int(x0 + (x1 - x0) * i / steps)
        draw.line([(xi, y), (xi + (x1 - x0) // steps + 1, y)],
                  fill=(*SEPIA, a), width=1)


def calc_jp_font_size(text):
    """漢字のフォントサイズを文字数に応じて決める"""
    n = len(text)
    # 使える縦スペース（上下ルール間）
    area = BOT_RULE_Y - TOP_RULE_Y - 60
    # 1文字あたりの高さ = area / 文字数（間隔込み）
    per_char = area / max(n, 1)
    size = int(per_char * 0.82)
    return max(60, min(180, size))


def draw_vertical_kanji(img, draw, text, font_jp, x_center):
    """
    漢字を縦書きで描画する
    文字数に応じてフォントサイズを調整し、テキストエリアの中央に配置する
    戻り値: 漢字列の左端X座標（ローマ字の配置に使う）
    """
    n = len(text)
    font_size = calc_jp_font_size(text)
    font = ImageFont.truetype(FONT_JP, font_size)

    char_heights = []
    char_widths  = []
    for ch in text:
        bb = draw.textbbox((0, 0), ch, font=font)
        char_heights.append(bb[3] - bb[1])
        char_widths.append(bb[2] - bb[0])

    spacing = max(6, font_size // 8)
    total_h = sum(char_heights) + spacing * (n - 1)

    text_area_center = (TOP_RULE_Y + BOT_RULE_Y) // 2
    start_y = text_area_center - total_h // 2

    # 最大文字幅を使って左端X座標を求める（ローマ字配置に渡す）
    max_w = max(char_widths) if char_widths else 0
    kanji_left_x = x_center - max_w // 2

    current_y = start_y
    for i, ch in enumerate(text):
        ch_w = char_widths[i]
        ch_h = char_heights[i]
        x = x_center - ch_w // 2
        draw.text((x, current_y), ch, font=font, fill=INK)
        current_y += ch_h + spacing

    return kanji_left_x


def draw_vertical_romaji(img, roma, kanji_left_x):
    """
    ローマ字を縦書き（90°回転）で描画する
    CSS の writing-mode:vertical-rl に相当する見た目を再現する
    kanji_left_x: 漢字列の左端X座標
    """
    font_size = 50
    try:
        font = ImageFont.truetype(FONT_ROMAN, font_size)
    except Exception:
        return

    # 一時画像にローマ字を横書きで描いてから90°回転させる
    tmp_draw = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    bb = tmp_draw.textbbox((0, 0), roma, font=font)
    text_w = bb[2] - bb[0]
    text_h = bb[3] - bb[1]

    pad = 6
    tmp = Image.new('RGBA', (text_w + pad * 2, text_h + pad * 2), (0, 0, 0, 0))
    tmp_d = ImageDraw.Draw(tmp)
    tmp_d.text((pad, pad), roma, font=font, fill=(60, 35, 12, 200))

    # 90°反時計回りに回転（縦書きにする）
    rotated = tmp.rotate(90, expand=True)

    # 漢字の左端から40px空けて配置
    gap = 40
    paste_x = kanji_left_x - rotated.width - gap

    # はみ出し防止
    paste_x = max(MARGIN, paste_x)

    # Y位置：テキストエリアの中央に
    text_area_center = (TOP_RULE_Y + BOT_RULE_Y) // 2
    paste_y = text_area_center - rotated.height // 2

    img.paste(rotated, (paste_x, paste_y), rotated)


def draw_english_quote(draw, text, font):
    """
    英語の引用文を画像下部の中央に描画する
    長い場合は複数行に折り返す
    """
    quote = f'"{text}"'
    max_w = W - RULE_PAD * 2 - 40

    # 文字列を複数行に分割する
    words = quote.split(' ')
    lines = []
    current = ''
    for word in words:
        test = (current + ' ' + word).strip()
        bb = draw.textbbox((0, 0), test, font=font)
        if bb[2] - bb[0] <= max_w:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    # 行の高さを計算して縦中央に収める
    line_h = 48
    total_h = line_h * len(lines)
    quote_area_center = (BOT_RULE_Y + H - MARGIN) // 2
    start_y = quote_area_center - total_h // 2

    for i, line in enumerate(lines):
        bb = draw.textbbox((0, 0), line, font=font)
        lw = bb[2] - bb[0]
        draw.text(((W - lw) // 2, start_y + i * line_h),
                  line, font=font, fill=(*SEPIA, 210))


# ==================================================
# カード生成メイン関数
# ==================================================

def generate_card(proverb, output_dir):
    """1枚の書道カード画像を生成する（Reactデザインに合わせた版）"""
    day  = proverb["day"]
    paper_color = hex_to_rgb(PAPERS[(day - 1) % len(PAPERS)])

    # ---- 1. ベース画像（和紙色の背景）----
    img  = Image.new('RGB', (W, H), paper_color)
    draw = ImageDraw.Draw(img)

    # ---- 2. 和紙の端に微かな影（テクスチャは入れない）----
    # 和紙の自然な色だけで十分なので、線は入れない

    # ---- 3. 上下の細い境界線（グラデーション風）----
    for yi in range(3):
        a = [40, 20, 8][yi]
        draw.line([(0, yi), (W, yi)], fill=(*SEPIA, a), width=1)
        draw.line([(0, H - 1 - yi), (W, H - 1 - yi)], fill=(*SEPIA, a), width=1)

    # ---- 4. フォントを読み込む ----
    try:
        seal_font_r = ImageFont.truetype(FONT_ROMAN, int(SEAL_SIZE * 0.46))
        seal_font_w = ImageFont.truetype(FONT_ROMAN, int(SEAL_SIZE * 0.36))
        font_en     = ImageFont.truetype(FONT_ROMAN, 42)
    except Exception as e:
        print(f"  フォントエラー: {e}")
        return

    # ---- 5. RW シール（右上）----
    seal_cx = W - SEAL_PAD - SEAL_SIZE // 2
    seal_cy = SEAL_PAD + SEAL_SIZE // 2
    draw_rw_seal(draw, seal_cx, seal_cy, SEAL_SIZE, seal_font_r, seal_font_w)

    # ---- 6. 上の区切り線 ----
    draw_h_rule(draw, y=TOP_RULE_Y)

    # ---- 7. 漢字（縦書き）----
    # 中央より少し右に配置（ローマ字のスペースを左に確保）
    kanji_x_center = W // 2 + 60
    kanji_left_x = draw_vertical_kanji(img, draw, proverb["jp"],
                                       font_jp=FONT_JP, x_center=kanji_x_center)

    # ---- 8. ローマ字（縦書き・漢字の左隣）----
    draw_vertical_romaji(img, proverb["roma"], kanji_left_x=kanji_left_x)

    # draw オブジェクトを再取得（img にペーストした後なので）
    draw = ImageDraw.Draw(img)

    # ---- 9. 下の区切り線 ----
    draw_h_rule(draw, y=BOT_RULE_Y)

    # ---- 10. 英語の引用文 ----
    draw_english_quote(draw, proverb["en"], font_en)

    # ---- 11. ビネット効果 ----
    img = add_vignette(img)

    # ---- 12. 保存 ----
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"day{day:02d}.png")
    img.save(output_path, "PNG")
    print(f"✅ Day{day:02d} 生成完了: {output_path}")


def main():
    output_dir = "/home/kenta_kamijyo/ronin/ronin_images"

    # 新規追加分のみ生成するかどうか（既存ファイルはスキップ）
    skip_existing = True

    # 生成が必要な格言だけを抽出する
    targets = []
    for proverb in proverbs:
        day = proverb["day"]
        output_path = os.path.join(output_dir, f"day{day:02d}.png")
        if skip_existing and os.path.exists(output_path):
            # すでに画像がある場合はスキップ
            pass
        else:
            targets.append(proverb)

    if not targets:
        print("新規生成が必要なカードはありません（すべて既存）。")
        return

    print(f"書道カード画像を生成します（{len(targets)}枚 / 全{len(proverbs)}枚中）...\n")
    for proverb in targets:
        generate_card(proverb, output_dir)
    print(f"\n🎉 {len(targets)}枚の生成が完了しました！")
    print(f"保存先: {output_dir}/")


if __name__ == "__main__":
    main()
