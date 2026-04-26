import { useState, useEffect } from "react";

const RED    = "#9e1e0e";
const PAPERS = ["#f0e6d0","#ede0c8","#f3e9d5","#e8ddc8","#f1e7d2"];
const SEALS  = ["武","道","心","刀","侍","禅","義","仁","勇","礼"];

const proverbs = [
  { day:1,  jp:"一期一会",                   roma:"Ichi go ichi e",                         en:"This moment will never come again." },
  { day:2,  jp:"能ある鷹は爪を隠す",          roma:"Nō aru taka wa tsume o kakusu",          en:"A skilled hawk hides its talons." },
  { day:3,  jp:"七転び八起き",               roma:"Nana korobi ya oki",                     en:"Fall seven times. Rise eight." },
  { day:4,  jp:"背水の陣",                   roma:"Haisui no jin",                          en:"Fight with your back to the river." },
  { day:5,  jp:"諸行無常",                   roma:"Shogyō mujō",                            en:"Nothing in this world stays the same." },
  { day:6,  jp:"石の上にも三年",              roma:"Ishi no ue ni mo san nen",               en:"Even a cold stone warms." },
  { day:7,  jp:"虎穴に入らずんば虎子を得ず",  roma:"Koketsu ni irazunba koji o ezu",         en:"No reward without entering the den." },
  { day:8,  jp:"覚悟を決めた者は強い",        roma:"Kakugo o kimeta mono wa tsuyoi",         en:"One who has decided is unbreakable." },
  { day:9,  jp:"足るを知る",                 roma:"Taru o shiru",                           en:"Know when enough is enough." },
  { day:10, jp:"実るほど頭を垂れる稲穂かな",  roma:"Minoru hodo atama o tareru inaho kana",  en:"The richer the rice, the lower it bows." },
  { day:11, jp:"初志貫徹",                   roma:"Shoshi kantetsu",                        en:"Stay true to what you set out to do." },
  { day:12, jp:"急がば回れ",                 roma:"Isogaba maware",                         en:"The long way is often the shortest." },
  { day:13, jp:"沈黙は金",                   roma:"Chinmoku wa kin",                        en:"Silence is gold." },
  { day:14, jp:"継続は力なり",               roma:"Keizoku wa chikara nari",                en:"Consistency is strength." },
  { day:15, jp:"以心伝心",                   roma:"Ishin denshin",                          en:"Heart speaks to heart without words." },
  { day:16, jp:"千里の道も一歩から",          roma:"Senri no michi mo ippo kara",            en:"A thousand miles begins with one step." },
  { day:17, jp:"出る杭は打たれる",            roma:"Deru kui wa utareru",                    en:"The nail that sticks up gets hammered." },
  { day:18, jp:"好きこそものの上手なれ",      roma:"Suki koso mono no jōzu nare",            en:"What you love, you'll master." },
  { day:19, jp:"艱難汝を玉にす",             roma:"Kannan nanji o tama ni su",              en:"Hardship polishes you into a gem." },
  { day:20, jp:"負けるが勝ち",               roma:"Makeru ga kachi",                        en:"Losing can be winning." },
  { day:21, jp:"柔よく剛を制す",             roma:"Jū yoku gō o seisu",                    en:"Softness overcomes hardness." },
  { day:22, jp:"禍を転じて福となす",          roma:"Wazawai o tenjite fuku to nasu",         en:"Turn disaster into fortune." },
  { day:23, jp:"窮すれば通ず",               roma:"Kyū sureba tsūzu",                      en:"When cornered, a way opens." },
  { day:24, jp:"当たって砕けろ",              roma:"Atatte kudakero",                        en:"Charge in, even if you shatter." },
  { day:25, jp:"情けは人の為ならず",          roma:"Nasake wa hito no tame narazu",          en:"Kindness to others is kindness to yourself." },
  { day:26, jp:"型があるから型を破れる",      roma:"Kata ga aru kara kata o yabureru",       en:"Master the form, then break free." },
  { day:27, jp:"一所懸命",                   roma:"Isshōkenmei",                            en:"Give everything to this one moment." },
  { day:28, jp:"道を極めるには終わりがない",  roma:"Michi o kiwameru ni wa owari ga nai",    en:"The mastery of a path has no end." },
  { day:29, jp:"武士は食わねど高楊枝",        roma:"Bushi wa kuwanedo takayōji",             en:"Dignity over comfort." },
  { day:30, jp:"生き死に一如",               roma:"Ikishi ni ichinyo",                      en:"Life and death are one." },
  { day:31, jp:"聞くは一時の恥",             roma:"Kiku wa ichiji no haji",                 en:"The shame of asking lasts a moment." },
  { day:32, jp:"知らぬが仏",                 roma:"Shiranu ga hotoke",                      en:"What you don't know can't hurt you." },
  { day:33, jp:"三人寄れば文殊の知恵",        roma:"Sannin yoreba monju no chie",            en:"Three heads hold the wisdom of a god." },
  { day:34, jp:"転ばぬ先の杖",               roma:"Korobanu saki no tsue",                  en:"Better a walking stick before you fall." },
  { day:35, jp:"備えあれば憂いなし",          roma:"Sonae areba urei nashi",                 en:"Prepare, and you'll have nothing to fear." },
  { day:36, jp:"後悔先に立たず",             roma:"Kōkai saki ni tatazu",                   en:"Regret never arrives early." },
  { day:37, jp:"類は友を呼ぶ",               roma:"Rui wa tomo o yobu",                     en:"Like attracts like." },
  { day:38, jp:"遠くの親戚より近くの他人",    roma:"Tōku no shinseki yori chikaku no tanin", en:"A neighbor nearby beats a relative far away." },
  { day:39, jp:"人の振り見て我が振り直せ",    roma:"Hito no furi mite waga furi naose",      en:"Watch others, fix your own ways." },
  { day:40, jp:"魚心あれば水心",             roma:"Uogokoro areba mizugokoro",              en:"Goodwill invites goodwill." },
  { day:41, jp:"目は口ほどに物を言う",        roma:"Me wa kuchi hodo ni mono o iu",          en:"Eyes speak as loudly as words." },
  { day:42, jp:"花鳥風月",                   roma:"Kachō fūgetsu",                          en:"Flowers, birds, wind, moon." },
  { day:43, jp:"物の哀れ",                   roma:"Mono no aware",                          en:"The gentle sadness of things passing." },
  { day:44, jp:"水は低きに流れる",            roma:"Mizu wa hikuki ni nagareru",             en:"Water flows to the lowest place." },
  { day:45, jp:"一葉落ちて天下の秋を知る",    roma:"Ichiyō ochite tenka no aki o shiru",     en:"One falling leaf tells you autumn has come." },
  { day:46, jp:"天網恢恢、疎にして漏らさず",  roma:"Tenmō kaikaku, so ni shite morasa zu",   en:"Heaven's net — nothing escapes it." },
  { day:47, jp:"月に叢雲、花に風",           roma:"Tsuki ni murakumo, hana ni kaze",        en:"Beauty is always fleeting." },
  { day:48, jp:"損して得取れ",               roma:"Son shite toku tore",                    en:"Take the loss now, claim the gain later." },
  { day:49, jp:"回り道が一番の近道",          roma:"Mawari michi ga ichiban no chikamichi",  en:"The long way round is often the shortest." },
  { day:50, jp:"嘘から出た誠",               roma:"Uso kara deta makoto",                   en:"A lie that accidentally became the truth." },
  { day:51, jp:"捨てる神あれば拾う神あり",    roma:"Suteru kami areba hirou kami ari",       en:"When one door closes, another opens." },
  { day:52, jp:"怪我の功名",                 roma:"Kega no kōmyō",                          en:"A lucky break born from a blunder." },
  { day:53, jp:"侘び寂び",                   roma:"Wabi sabi",                              en:"Beauty in the imperfect and impermanent." },
  { day:54, jp:"一芸は身を助ける",            roma:"Ichigei wa mi o tasukeru",               en:"One skill can save your life." },
  { day:55, jp:"大志を抱け",                 roma:"Taishi o idake",                         en:"Dare to have great ambitions." },
  { day:56, jp:"魂を込めて作れ",             roma:"Tamashii o komete tsukure",              en:"Pour your soul into what you make." },
  { day:57, jp:"匠の心",                     roma:"Takumi no kokoro",                       en:"The craftsman who never stops refining." },
  { day:58, jp:"もったいない",               roma:"Mottainai",                              en:"Too precious to waste." },
  { day:59, jp:"お互い様",                   roma:"Otagai sama",                            en:"We're all in the same boat." },
  { day:60, jp:"粋",                         roma:"Iki",                                    en:"Effortless cool. Knowing when not to try." },
  { day:61, jp:"間",                         roma:"Ma",                                     en:"The power of the space between." },
  { day:62, jp:"道",                         roma:"Dō",                                     en:"The Way. A lifelong path of becoming." },
  { day:63, jp:"七難八苦を乗り越えてこそ",    roma:"Shichinin hakku o norikoete koso",       en:"Only through great trials does greatness emerge." },
  { day:64, jp:"辛抱する木に金がなる",        roma:"Shinbō suru ki ni kane ga naru",         en:"The tree that endures bears golden fruit." },
  { day:65, jp:"苦は楽の種",                 roma:"Ku wa raku no tane",                     en:"Suffering is the seed of joy." },
  { day:66, jp:"百折不撓",                   roma:"Hyakusetsu futō",                        en:"Bend a hundred times, but never break." },
  { day:67, jp:"高慢は損気",                 roma:"Kōman wa sonki",                         en:"Arrogance invites loss." },
  { day:68, jp:"自慢は知恵の行き止まり",      roma:"Jiman wa chie no yukidomari",            en:"Boasting is where wisdom ends." },
  { day:69, jp:"不足を言うな、有余を言え",    roma:"Fusoku o iu na, yūyo o ie",              en:"Don't complain about what's missing." },
  { day:70, jp:"小欲知足",                   roma:"Shōyoku chisoku",                        en:"Small desires, deep contentment." },
  { day:71, jp:"無欲は大欲に勝る",            roma:"Muyoku wa taiyoku ni masaru",            en:"Wanting nothing is greater than wanting everything." },
  { day:72, jp:"熱い心、冷静な頭",           roma:"Atsui kokoro, reisei na atama",          en:"A burning heart, a cool head." },
  { day:73, jp:"志高く",                     roma:"Kokorozashi takaku",                     en:"Aim high." },
  { day:74, jp:"夢は大きく、行動は今",        roma:"Yume wa ōkiku, kōdō wa ima",             en:"Dream big, act now." },
  { day:75, jp:"弱さも強さになる",            roma:"Yowasa mo tsuyosa ni naru",              en:"Even weakness can become strength." },
  { day:76, jp:"窮すれば通ず",               roma:"Kyū sureba tsūzu",                      en:"When cornered, a way opens." },
  { day:77, jp:"金継ぎ",                     roma:"Kintsugi",                               en:"Repair with gold. The break becomes beauty." },
  { day:78, jp:"背水の陣",                   roma:"Haisui no jin",                          en:"No retreat — or you drown." },
  { day:79, jp:"一所懸命",                   roma:"Isshōkenmei",                            en:"Be fully here. Or not at all." },
  { day:80, jp:"桜散る、されど根は残る",      roma:"Sakura chiru, saredo ne wa nokoru",      en:"The cherry blossom falls, but the roots remain." },
  { day:81, jp:"鬼に金棒",                   roma:"Oni ni kanabō",                          en:"The strong, made even stronger." },
  { day:82, jp:"春夏秋冬、それぞれに美しい",  roma:"Shunkashūtō, sorezore ni utsukushii",   en:"Every season has its own beauty." },
  { day:83, jp:"形あるものはいつか壊れる",    roma:"Katachi aru mono wa itsuka kowareru",    en:"Everything that has form will one day break." },
  { day:84, jp:"人生意気に感ず",             roma:"Jinsei iki ni kanzu",                    en:"Live by passion, not by calculation." },
  { day:85, jp:"花は桜木、人は武士",          roma:"Hana wa sakuragi, hito wa bushi",        en:"Among flowers the cherry blossom. Among men the warrior." },
  { day:86, jp:"禍福は糾える縄の如し",        roma:"Kafuku wa azanaeru nawa no gotoshi",     en:"Fortune and misfortune are twisted like rope." },
  { day:87, jp:"雨降って地固まる",            roma:"Ame futte ji katamaru",                  en:"After the rain, the ground grows harder." },
  { day:88, jp:"男子の一言、金鉄の如し",      roma:"Danshi no ichigon, kintetsu no gotoshi", en:"A person's word is iron." },
  { day:89, jp:"死して不朽の名を残せ",        roma:"Shishite fukyū no na o nokose",          en:"Die and leave a name that never fades." },
  { day:90, jp:"事に臨んでは死を思え",        roma:"Koto ni nozonde wa shi o omoe",          en:"Think of death — and act without hesitation." },
  { day:91, jp:"覚悟",                       roma:"Kakugo",                                 en:"Accept all consequences before you begin." },
  { day:92, jp:"武士道",                     roma:"Bushido",                                en:"The Way of the Warrior." },
  { day:93, jp:"義",                         roma:"Gi — Rectitude",                         en:"Do what is right, even when it is hard." },
  { day:94, jp:"仁",                         roma:"Jin — Benevolence",                      en:"Compassion, even for your enemies." },
  { day:95, jp:"勇",                         roma:"Yū — Courage",                           en:"Fear acknowledged. Action taken anyway." },
  { day:96, jp:"礼",                         roma:"Rei — Respect",                          en:"Every person is worthy of dignity." },
  { day:97, jp:"誠",                         roma:"Makoto — Honesty",                       en:"No deception. Not even to yourself." },
  { day:98, jp:"名誉",                       roma:"Meiyo — Honor",                          en:"You are your own judge." },
  { day:99, jp:"忠義",                       roma:"Chūgi — Loyalty",                        en:"Chosen commitment, fully kept." },
  { day:100,jp:"武士道百訓",                  roma:"Bushido hyakukun",                       en:"100 days. One truth. The Way continues." },
];

// Font size: fill one vertical column
function calcFz(text, large) {
  const avail = large ? 390 : 168;
  const ratio = 1.26;
  const v = Math.floor(avail / (text.length * ratio));
  return Math.min(large ? 68 : 32, Math.max(large ? 20 : 10, v));
}

// Single card — pure CSS, matches calligraphy.jsx exactly
function Card({ p, large = false, onClick }) {
  const [hovered, setHovered] = useState(false);
  const W     = large ? 400 : 172;
  const H     = large ? 560 : 244;
  const padH  = large ? 22  : 10;
  const padV  = large ? 18  : 9;
  const sealSz= large ? 42  : 21;
  const enFz  = large ? 13  : 8;
  const mainFz= calcFz(p.jp, large);
  const romaFz= large ? 10  : 6;
  const paper = PAPERS[p.day % PAPERS.length];
  const seal  = SEALS[p.day % SEALS.length];

  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        width:W, height:H,
        background: paper,
        borderRadius:2,
        position:"relative",
        overflow:"hidden",
        cursor: onClick ? "pointer" : "default",
        display:"flex", flexDirection:"column",
        boxShadow: hovered
          ? "0 22px 52px rgba(0,0,0,0.34), 0 0 0 1px rgba(20,12,4,0.14), 5px 5px 0 rgba(0,0,0,0.07)"
          : "0 5px 18px rgba(0,0,0,0.16), 0 0 0 1px rgba(20,12,4,0.08), 3px 3px 0 rgba(0,0,0,0.05)",
        transform: hovered && onClick ? "translateY(-5px)" : "none",
        transition:"all 0.3s ease",
        flexShrink:0,
      }}
    >
      {/* Washi fiber */}
      <div style={{
        position:"absolute", inset:0, pointerEvents:"none", zIndex:0,
        backgroundImage:`
          repeating-linear-gradient(0deg,transparent,transparent 3px,rgba(130,90,40,0.045) 3px,rgba(130,90,40,0.045) 4px),
          repeating-linear-gradient(90deg,transparent,transparent 9px,rgba(150,110,50,0.022) 9px,rgba(150,110,50,0.022) 10px)
        `,
      }}/>
      {/* Vignette */}
      <div style={{
        position:"absolute", inset:0, pointerEvents:"none", zIndex:0,
        background:"radial-gradient(ellipse at 50% 50%, transparent 52%, rgba(90,55,15,0.12) 100%)",
      }}/>
      {/* Top border */}
      <div style={{
        position:"absolute", top:0, left:0, right:0, height: large?3:2,
        background:"linear-gradient(to right, transparent, rgba(100,60,20,0.2), transparent)",
        zIndex:2,
      }}/>
      {/* Bottom border */}
      <div style={{
        position:"absolute", bottom:0, left:0, right:0, height: large?3:2,
        background:"linear-gradient(to right, transparent, rgba(100,60,20,0.18), transparent)",
        zIndex:2,
      }}/>

      {/* Seal — top right */}
      <div style={{
        position:"absolute", top: large?16:8, right: large?16:8, zIndex:3,
        width:sealSz, height:sealSz,
        border:`${large?2:1.5}px solid ${RED}`,
        display:"flex", alignItems:"center", justifyContent:"center",
      }}>
        {/* Logo B SVG */}
        <svg width={sealSz} height={sealSz} viewBox="0 0 100 100">
          <rect x="3" y="3" width="94" height="94" fill="none" stroke={RED} strokeWidth="5"/>
          <line x1="16" y1="84" x2="84" y2="16" stroke={RED} strokeWidth="5" strokeLinecap="round"/>
          <text x="13" y="72" style={{ fontFamily:"Georgia,serif", fontSize:46, fontWeight:700, fill:"#0e0804" }}>R</text>
          <text x="49" y="72" style={{ fontFamily:"Georgia,serif", fontSize:36, fontWeight:400, fill:"#0e0804", opacity:0.45 }}>W</text>
        </svg>
      </div>

      {/* Top rule */}
      <div style={{
        margin:`${large?52:26}px ${padH}px ${large?6:3}px`,
        height:1,
        background:"linear-gradient(to right, transparent, rgba(20,12,4,0.1), transparent)",
        flexShrink:0, zIndex:2, position:"relative",
      }}/>

      {/* Text area — kanji + romaji vertical */}
      <div style={{
        flex:1, display:"flex", alignItems:"center", justifyContent:"center",
        gap: large?14:6,
        padding:`${large?4:2}px ${padH + (large?6:3)}px`,
        position:"relative", zIndex:2, overflow:"hidden",
      }}>
        {/* Romaji */}
        <div style={{
          writingMode:"vertical-rl",
          textOrientation:"mixed",
          fontFamily:"'Cormorant Garamond', Georgia, serif",
          fontSize: romaFz,
          fontStyle:"italic",
          color:"rgba(50,28,8,0.62)",
          letterSpacing:"0.2em",
          whiteSpace:"nowrap",
          alignSelf:"center",
          flexShrink:0,
          userSelect:"none",
        }}>{p.roma}</div>

        {/* Kanji */}
        <div style={{
          writingMode:"vertical-rl",
          textOrientation:"mixed",
          fontFamily:"'Yuji Syuku', serif",
          fontSize: mainFz,
          fontWeight:400,
          color:"#120a04",
          lineHeight:1.08,
          letterSpacing:"0.16em",
          whiteSpace:"nowrap",
          userSelect:"none",
          filter:`drop-shadow(0.8px 0.8px 0px rgba(0,0,0,0.22)) drop-shadow(0px 0px ${large?1.5:0.8}px rgba(0,0,0,0.08))`,
        }}>{p.jp}</div>
      </div>

      {/* Bottom rule */}
      <div style={{
        margin:`${large?6:3}px ${padH}px ${large?8:4}px`,
        height:1,
        background:"linear-gradient(to right, transparent, rgba(20,12,4,0.09), transparent)",
        flexShrink:0, zIndex:2, position:"relative",
      }}/>

      {/* English */}
      <div style={{
        padding:`0 ${padH}px ${padV}px`,
        position:"relative", zIndex:2, flexShrink:0,
      }}>
        <div style={{
          fontFamily:"'Cormorant Garamond', Georgia, serif",
          fontSize: enFz,
          color:"rgba(18,8,2,0.68)",
          lineHeight:1.55,
          fontStyle:"italic",
        }}>"{p.en}"</div>
      </div>
    </div>
  );
}

// Fullscreen modal for screenshotting
function Modal({ p, onClose, onPrev, onNext }) {
  useEffect(() => {
    const fn = (e) => {
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowLeft")  onPrev();
      if (e.key === "ArrowRight") onNext();
    };
    window.addEventListener("keydown", fn);
    return () => window.removeEventListener("keydown", fn);
  }, [onClose, onPrev, onNext]);

  if (!p) return null;
  return (
    <div onClick={onClose} style={{
      position:"fixed", inset:0, zIndex:400,
      background:"rgba(4,2,1,0.95)",
      display:"flex", flexDirection:"column",
      alignItems:"center", justifyContent:"center",
      padding:24,
    }}>
      <div onClick={e => e.stopPropagation()} style={{ display:"flex", flexDirection:"column", alignItems:"center", gap:16 }}>
        <Card p={p} large/>
        <div style={{ display:"flex", gap:12 }}>
          <button onClick={onPrev} style={{ background:"none", border:`1px solid rgba(158,30,14,0.3)`, color:"rgba(232,216,180,0.5)", fontFamily:"Georgia,serif", fontSize:11, letterSpacing:2, padding:"8px 20px", cursor:"pointer" }}>← PREV</button>
          <button onClick={onClose} style={{ background:"none", border:`1px solid rgba(255,255,255,0.1)`, color:"rgba(232,216,180,0.3)", fontFamily:"Georgia,serif", fontSize:11, letterSpacing:2, padding:"8px 20px", cursor:"pointer" }}>ESC</button>
          <button onClick={onNext} style={{ background:"none", border:`1px solid rgba(158,30,14,0.3)`, color:"rgba(232,216,180,0.5)", fontFamily:"Georgia,serif", fontSize:11, letterSpacing:2, padding:"8px 20px", cursor:"pointer" }}>NEXT →</button>
        </div>
        <div style={{ fontSize:10, letterSpacing:3, color:"rgba(232,216,180,0.18)", fontStyle:"italic" }}>
          📱 長押し → 写真に保存　　💻 スクリーンショット
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [ready,    setReady]    = useState(false);
  const [selected, setSelected] = useState(null);
  const [filter,   setFilter]   = useState("all");

  useEffect(() => {
    const link = document.createElement("link");
    link.rel  = "stylesheet";
    link.href = "https://fonts.googleapis.com/css2?family=Yuji+Syuku&family=Cormorant+Garamond:ital,wght@0,400;1,400&display=swap";
    link.onload = () => setReady(true);
    document.head.appendChild(link);
    setTimeout(() => setReady(true), 2500);
  }, []);

  const ranges = [
    { label:"全100枚", val:"all" },
    { label:"Day 01–30", val:"1-30" },
    { label:"Day 31–60", val:"31-60" },
    { label:"Day 61–100", val:"61-100" },
  ];

  const filtered = proverbs.filter(p => {
    if (filter==="all")    return true;
    if (filter==="1-30")   return p.day <= 30;
    if (filter==="31-60")  return p.day >= 31 && p.day <= 60;
    if (filter==="61-100") return p.day >= 61;
    return true;
  });

  const selIdx = selected ? proverbs.findIndex(p => p.day === selected.day) : -1;
  const goPrev = () => selIdx > 0                    && setSelected(proverbs[selIdx-1]);
  const goNext = () => selIdx < proverbs.length-1    && setSelected(proverbs[selIdx+1]);

  return (
    <div style={{ minHeight:"100vh", background:"#080604", padding:"36px 14px 60px", fontFamily:"Georgia,serif" }}>

      {/* Header */}
      <div style={{ textAlign:"center", marginBottom:32 }}>
        <div style={{ fontSize:10, letterSpacing:6, color:"rgba(232,216,180,0.2)", textTransform:"uppercase", marginBottom:10 }}>
          ⚔ @RoninWords ⚔
        </div>
        <h1 style={{ fontSize:20, fontWeight:400, color:"#e8d8b4", letterSpacing:2, margin:0 }}>
          書道カード — 全100枚
        </h1>
        <div style={{ width:40, height:1, background:`linear-gradient(to right,transparent,${RED},transparent)`, margin:"12px auto 14px" }}/>
        <p style={{ fontSize:11, fontStyle:"italic", color:"rgba(232,216,180,0.22)", lineHeight:2, margin:0 }}>
          カードをタップ → 大きく表示<br/>
          📱 大きい画像を<strong style={{color:"rgba(158,30,14,0.6)"}}>長押し → 写真に保存</strong><br/>
          💻 大きい画像が出たら<strong style={{color:"rgba(158,30,14,0.6)"}}>スクリーンショット</strong>
        </p>
      </div>

      {/* Filter */}
      <div style={{ display:"flex", justifyContent:"center", gap:8, marginBottom:28, flexWrap:"wrap" }}>
        {ranges.map(r => (
          <button key={r.val} onClick={() => setFilter(r.val)} style={{
            background: filter===r.val ? RED : "rgba(255,255,255,0.04)",
            border:`1px solid ${filter===r.val ? RED : "rgba(255,255,255,0.1)"}`,
            color: filter===r.val ? "#fff" : "rgba(232,216,180,0.4)",
            fontFamily:"Georgia,serif", fontSize:11, letterSpacing:1,
            padding:"7px 18px", cursor:"pointer", transition:"all 0.2s",
          }}>{r.label}</button>
        ))}
      </div>

      {/* Grid */}
      <div style={{
        display:"flex", flexWrap:"wrap", gap:14,
        justifyContent:"center", maxWidth:1200, margin:"0 auto",
        opacity: ready ? 1 : 0,
        transition:"opacity 0.6s ease",
      }}>
        {filtered.map(p => (
          <Card key={p.day} p={p} onClick={() => setSelected(p)}/>
        ))}
      </div>

      <Modal p={selected} onClose={() => setSelected(null)} onPrev={goPrev} onNext={goNext}/>
    </div>
  );
}
