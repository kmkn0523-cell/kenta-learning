// ────────── ローン計算・金利テーブル ──────────

// 完済計算の結果の形
interface IntResult {
  interest: number; // 総利息額（円）
  months: number;   // 完済までの月数
}

// 今月の利息額を計算する（残債 × 年利 / 12）
export function calculateMonthlyInterest(rem: number | string, rate: number | string): number {
  return Math.round(Number(rem) * (Number(rate) / 100 / 12));
}

// 毎月の返済額で完済するまでの月数と総利息を計算する（元利均等返済の逆算）
export function calculateTotalInterest(rem: number | string, rate: number | string, mo: number | string): IntResult | null {
  const r = Number(rate)/100/12, m = Number(mo), rv = Number(rem);
  if (!rv || !m) return null;
  if (r === 0) return { interest: 0, months: Math.ceil(rv/m) };
  if (m <= rv*r) return null; // 毎月返済額が利息以下なら永遠に完済できない
  const months = Math.ceil(-Math.log(1-(rv*r)/m) / Math.log(1+r));
  return { interest: Math.round(m*months-rv), months };
}

// 何ヶ月後の年と月を返す（完済予定日表示用）
export function calculateCompletionDate(months: number | null | undefined): { y: number; m: number } | null {
  if (!months) return null;
  const d = new Date(); d.setMonth(d.getMonth() + months);
  return { y: d.getFullYear(), m: d.getMonth()+1 };
}

// ────────── 消費者金融・カードローンの金利テーブル ──────────
// 各ブランドの「借入額帯ごとの上限金利(%)」をまとめたもの
// [上限金額(円), 金利%] を金額の小さい順に並べる
// ※あくまで各社公表の最高金利の目安。実際の契約金利は審査で決まるため上書きOK
const RATE_TABLES: Record<string, [number, number][]> = {
  // 大手消費者金融
  "アコム":         [[1000000,18.0],[3000000,15.0],[5000000,12.0],[8000000,9.0],[Infinity,7.7]],
  "プロミス":        [[1000000,17.8],[3000000,15.0],[5000000,12.0],[Infinity,6.3]],
  "アイフル":        [[1000000,18.0],[2000000,15.0],[3000000,13.0],[5000000,12.0],[Infinity,7.5]],
  "レイク":          [[1000000,18.0],[2000000,15.0],[3000000,12.0],[5000000,9.0],[Infinity,4.5]],
  "SMBCモビット":    [[1000000,18.0],[2000000,15.0],[5000000,12.0],[Infinity,7.7]],
  // 中堅消費者金融
  "フクホー":        [[1000000,20.0],[Infinity,18.0]],
  "セントラル":      [[1000000,18.0],[Infinity,15.0]],
  "ライフティ":      [[1000000,20.0],[Infinity,17.95]],
  "フタバ":          [[500000,19.94],[Infinity,17.95]],
  "アロー":          [[1000000,19.94],[Infinity,15.0]],
  "エニー":          [[1000000,19.94],[Infinity,17.95]],
  // 銀行カードローン
  "三菱UFJ銀行 バンクイック":   [[1000000,14.6],[2000000,12.6],[3000000,9.6],[4000000,8.1],[5000000,7.1],[Infinity,1.8]],
  "三井住友銀行カードローン":   [[1000000,14.5],[2000000,12.0],[3000000,10.0],[5000000,8.0],[Infinity,4.0]],
  "みずほ銀行カードローン":     [[1000000,14.0],[2000000,12.0],[3000000,9.0],[5000000,7.0],[Infinity,2.0]],
  "楽天銀行スーパーローン":     [[1000000,14.5],[3000000,9.6],[5000000,7.8],[8000000,6.6],[Infinity,1.9]],
  "オリックス銀行カードローン": [[1000000,17.8],[1500000,14.8],[3000000,12.8],[5000000,9.8],[8000000,5.0],[Infinity,1.7]],
  "auじぶん銀行カードローン":   [[1000000,17.4],[2000000,12.6],[3000000,9.5],[5000000,7.0],[Infinity,2.2]],
  "PayPay銀行カードローン":     [[1000000,18.0],[3000000,13.5],[5000000,9.5],[8000000,5.5],[Infinity,1.59]],
  "SBI新生銀行カードローン":    [[1000000,14.8],[2000000,12.0],[3000000,9.8],[5000000,7.0],[Infinity,4.5]],
  // 信販系カードローン
  "オリコ CREST":          [[1000000,18.0],[Infinity,15.0]],
  "セディナ カードローン": [[1000000,18.0],[Infinity,15.0]],
  "JCB FAITH":             [[Infinity,12.5]],
  "三菱UFJニコス":         [[1000000,17.8],[Infinity,14.6]],
  "アプラス カードローン": [[1000000,18.0],[Infinity,15.0]],
};

// 消費者金融タブで選べるブランド一覧
export const BRANDS_CF=["アコム","プロミス","アイフル","レイク","SMBCモビット","フクホー","セントラル","ライフティ","フタバ","アロー","エニー"];

// 銀行/リボ・信販タブで選べるブランド一覧
export const BRANDS_BL=["三菱UFJ銀行 バンクイック","三井住友銀行カードローン","みずほ銀行カードローン","楽天銀行スーパーローン","オリックス銀行カードローン","auじぶん銀行カードローン","PayPay銀行カードローン","SBI新生銀行カードローン","オリコ CREST","セディナ カードローン","JCB FAITH","三菱UFJニコス","アプラス カードローン"];

// ブランド一覧で「自分で名前を入力する」を選ぶときの目印
export const FREE="（自由入力）";

// 借入額(円)とブランド名から、自動で当てはまる金利(%)を返す関数
// テーブルに無いブランドや借入額0のときは null を返す（金利を勝手に書き換えない）
export function findRate(brand: string, amount: number | string): number | null {
  const t=RATE_TABLES[brand]; if(!t) return null;
  const a=Number(amount)||0; if(!a) return null;
  for(const [cap,rate] of t){ if(a<=cap) return rate; }
  return t[t.length-1][1];
}
