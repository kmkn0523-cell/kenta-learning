// ────────── パスワード認証画面 ──────────
// アプリ起動時に最初に表示される認証ゲート
// 初回：パスワード設定画面 → 設定済み：ログイン画面
// ログイン成功後は CryptoKeyContext に AES-GCM 鍵をセットして children（本体）を描画する

import { useState, useRef } from "react";
import CryptoKeyContext from "../contexts/CryptoKeyContext";
import {
  simpleHash, makeNewHash, verifyNewHash, isLegacyHash,
  deriveEncryptionKey, getOrCreateEncSalt,
} from "../utils/crypto";
import { PasswordInput } from "./ui";

import { ReactNode } from "react";

export default function PasswordGate({ children }: { children: ReactNode }) {
  // sessionStorage = ブラウザを閉じると消えるので毎回ログインが必要
  const [ok, setOk] = useState(() => sessionStorage.getItem("ff_auth") === "1");
  // localStorage にパスワードのハッシュが保存されているか確認
  // 保存されていない = 初回アクセス → パスワード設定画面を出す
  const [savedHash, setSavedHash] = useState(() => { try { return localStorage.getItem("kk_pw_hash") || ""; } catch(_){ return ""; } });
  const [pw, setPw] = useState("");
  const [pw2, setPw2] = useState(""); // パスワード設定時の確認用（2回入力）
  const [err, setErr] = useState("");
  const [showReset, setShowReset] = useState(false); // リセット確認ダイアログの表示フラグ
  const [busy, setBusy] = useState(false); // ハッシュ計算中フラグ（ボタン連打防止）
  // AES-GCM の暗号化鍵（CryptoKey オブジェクト）。ログイン成功時に派生してメモリだけに保持
  const [cryptoKey, setCryptoKey] = useState<CryptoKey | null>(null);
  // ブルートフォース対策：失敗回数とロック解除時刻（エポックms）をsessionStorageで管理
  // sessionStorageなのでブラウザを閉じればリセットされる（厳しすぎないユーザー体験）
  const failCount = useRef<number>(Number(sessionStorage.getItem("ff_fail") || "0")); // JSXで使わないのでrefで管理
  const lockUntil = useRef<number>(Number(sessionStorage.getItem("ff_lock") || "0")); // 同上

  function showErr(msg){ setErr(msg); setTimeout(()=>setErr(""),2000); }

  // ── パスワードリセット処理（データは消さずにパスワードだけ削除） ──
  function resetPw(){ try{ localStorage.removeItem("kk_pw_hash"); }catch(error){ console.warn("[PasswordGate] removeItem failed", error); } setSavedHash(""); setShowReset(false); setPw(""); setPw2(""); }

  // ── ログイン処理 ──
  // 旧形式（simpleHashの8桁hex）も受け付け、合っていたら新形式（PBKDF2+salt）に自動アップグレードする
  async function login() {
    if (busy) return; // すでに処理中なら何もしない
    // ロック中チェック：5回連続失敗後は30秒間ログイン試行を拒否する
    const now = Date.now();
    if (now < lockUntil.current) {
      const remaining = Math.ceil((lockUntil.current - now) / 1000);
      showErr(`${remaining}秒後に再試行できます`);
      return;
    }
    setBusy(true);
    try {
      let success = false;
      if (isLegacyHash(savedHash)) {
        // 旧形式 → simpleHashで照合
        if (simpleHash(pw) === savedHash) {
          success = true;
          // 新形式へ静かにアップグレード（失敗してもログインは進める）
          try {
            const newHash = await makeNewHash(pw);
            localStorage.setItem("kk_pw_hash", newHash);
            setSavedHash(newHash);
          } catch (error) { console.warn("[PasswordGate] hash upgrade failed", error); }
        }
      } else {
        // 新形式 → PBKDF2で照合
        try {
          success = await verifyNewHash(pw, savedHash);
        } catch (_) {
          success = false;
        }
      }
      if (success) {
        // ログイン成功 → 失敗カウントをリセット
        failCount.current = 0;
        lockUntil.current = 0;
        sessionStorage.removeItem("ff_fail");
        sessionStorage.removeItem("ff_lock");
        // パスワードからAES-GCM鍵を派生してメモリにだけ持つ（鍵の保存はしない）
        try {
          const key = await deriveEncryptionKey(pw, getOrCreateEncSalt());
          setCryptoKey(key);
        } catch (_) {
          showErr("鍵の準備に失敗しました");
          return;
        }
        sessionStorage.setItem("ff_auth", "1");
        setOk(true);
      } else {
        // ログイン失敗 → カウントを増やし、5回目でロックをかける
        const newCount = failCount.current + 1;
        failCount.current = newCount;
        sessionStorage.setItem("ff_fail", String(newCount));
        if (newCount >= 5) {
          const until = Date.now() + 30 * 1000; // 30秒ロック
          lockUntil.current = until;
          sessionStorage.setItem("ff_lock", String(until));
          setPw("");
          showErr("30秒間ロックされました");
        } else {
          setPw("");
          showErr(`パスワードが違います（あと${5 - newCount}回）`);
        }
      }
    } finally {
      setBusy(false);
    }
  }

  // ── 初回パスワード設定処理 ──
  async function setup() {
    if (busy) return;
    if (pw.length < 8) { showErr("8文字以上で設定してください"); return; }
    if (pw !== pw2)    { showErr("パスワードが一致しません"); setPw2(""); return; }
    setBusy(true);
    try {
      const h = await makeNewHash(pw);
      try { localStorage.setItem("kk_pw_hash", h); } catch(error){ console.warn("[PasswordGate] setItem failed", error); }
      setSavedHash(h);
      // 新規パスワード設定と同時に暗号化鍵も派生してメモリへ
      try {
        const key = await deriveEncryptionKey(pw, getOrCreateEncSalt());
        setCryptoKey(key);
      } catch (_) {
        showErr("鍵の準備に失敗しました");
        return;
      }
      sessionStorage.setItem("ff_auth", "1");
      setOk(true);
    } catch (_) {
      showErr("設定に失敗しました");
    } finally {
      setBusy(false);
    }
  }

  // ok（セッション認証済み）かつ cryptoKey（暗号化鍵あり）が揃ったら本体を描画
  // リロードや別タブ復元時は ok=true でも cryptoKey=null になるのでログイン画面が出る
  if (ok && cryptoKey) return <CryptoKeyContext.Provider value={cryptoKey}>{children}</CryptoKeyContext.Provider>;

  const btnStyle = {border:"none",borderRadius:10,padding:"13px 0",cursor: busy ? "wait" : "pointer",fontSize:15,fontWeight:700,background:"#818cf8",color:"#0a0a0c",width:"100%",fontFamily:"inherit",opacity: busy ? 0.6 : 1};
  const wrap = {minHeight:"100vh",display:"flex",alignItems:"center",justifyContent:"center",background:"#0a0a0c",padding:20};
  const inner = {width:"100%",maxWidth:320,textAlign:"center" as const};

  // ── パスワード未設定（初回）→ ランディングページ＋設定画面 ──
  // 初訪者向けにアプリの特徴を訴求してからパスワード設定フォームへ
  if (!savedHash) return (
    <div style={{minHeight:"100vh",background:"#0a0a0c",padding:"24px 16px 48px",overflowY:"auto"}}>
      <div style={{maxWidth:520,margin:"0 auto",color:"#f5f5f7"}}>
        {/* ヒーロー */}
        <div style={{textAlign:"center",marginBottom:36,paddingTop:20}}>
          <div style={{fontSize:60,marginBottom:14,filter:"drop-shadow(0 0 24px rgba(129,140,248,0.5))"}}>💰</div>
          <div style={{fontSize:10,letterSpacing:"3px",color:"#818cf8",textTransform:"uppercase",fontWeight:600,marginBottom:8}}>Family Finance</div>
          <h1 style={{fontSize:28,fontWeight:700,marginBottom:10,letterSpacing:"-1px",lineHeight:1.3,margin:"0 0 10px"}}>
            家計を、見える化。<br/>暗号化で、安心。
          </h1>
          <p style={{fontSize:14,color:"#9a9aa3",lineHeight:1.7,maxWidth:420,margin:"0 auto"}}>
            収入・支出・ローン・貯金目標を一画面で。<br/>
            グラフで家計の流れが一目でわかる、無料の家計管理アプリ。
          </p>
        </div>

        {/* 主要機能カード（3つの特徴） */}
        <div style={{display:"grid",gap:10,marginBottom:32}}>
          {[
            {icon:"📊",title:"自動で家計診断",desc:"貯蓄率・返済比率・緊急資金を A〜E で評価。改善ポイントが一目で分かる"},
            {icon:"🎯",title:"目標貯金と返済シミュ",desc:"「100万円貯める」「繰り上げ返済で何ヶ月早まる？」をリアルタイム試算"},
            {icon:"🔒",title:"パスワード暗号化",desc:"データは端末内に暗号化保存。クラウドに送らないからプライバシー完全保護"},
          ].map(f=>(
            <div key={f.title} style={{background:"rgba(255,255,255,0.03)",border:"1px solid rgba(255,255,255,0.06)",borderRadius:14,padding:"14px 16px",display:"flex",gap:14,alignItems:"flex-start"}}>
              <div style={{fontSize:24,flexShrink:0,lineHeight:1}}>{f.icon}</div>
              <div>
                <div style={{fontSize:14,fontWeight:700,marginBottom:4}}>{f.title}</div>
                <div style={{fontSize:12,color:"#9a9aa3",lineHeight:1.6}}>{f.desc}</div>
              </div>
            </div>
          ))}
        </div>

        {/* セキュリティアピール */}
        <div style={{background:"rgba(52,211,153,0.06)",border:"1px solid rgba(52,211,153,0.25)",borderRadius:14,padding:"14px 16px",marginBottom:32}}>
          <div style={{fontSize:11,fontWeight:700,color:"#34d399",letterSpacing:"1px",textTransform:"uppercase",marginBottom:8}}>🛡 プライバシーへのこだわり</div>
          <ul style={{fontSize:12,color:"#9a9aa3",lineHeight:1.7,paddingLeft:18,margin:0}}>
            <li>AES-GCM 暗号化（パスワード派生鍵・PBKDF2）</li>
            <li>サーバには何も保存しない（端末内のみ）</li>
            <li>JSONバックアップで簡単引っ越し</li>
          </ul>
        </div>

        {/* CTA：パスワード設定フォーム */}
        <div style={{background:"rgba(129,140,248,0.06)",border:"1px solid rgba(129,140,248,0.3)",borderRadius:16,padding:"20px 18px",textAlign:"center"}}>
          <div style={{fontSize:22,marginBottom:6}}>🔑</div>
          <div style={{fontSize:16,fontWeight:700,marginBottom:6}}>パスワードを決めて、はじめよう</div>
          <div style={{fontSize:11,color:"#9a9aa3",marginBottom:16,lineHeight:1.6}}>
            このアプリで使うパスワードを設定します（8文字以上）<br/>
            ※ 紛失すると復元できません。安全な場所にメモしてください
          </div>
          <PasswordInput value={pw}  onChange={setPw}  placeholder="パスワード（8文字以上）" err={!!err}/>
          <PasswordInput value={pw2} onChange={setPw2} onEnter={setup} placeholder="もう一度入力" err={!!err}/>
          {err && <div style={{color:"#f87171",fontSize:13,marginBottom:10}}>{err}</div>}
          <button onClick={setup} disabled={busy} style={btnStyle}>{busy ? "処理中..." : "✓ 設定してはじめる"}</button>
        </div>

        {/* フッター */}
        <div style={{textAlign:"center",fontSize:10,color:"#5a5a63",marginTop:32,lineHeight:1.6}}>
          v1.2.2 / © 2026 kmkn0523<br/>
          PWA対応{" — "}ホーム画面に追加してアプリのように使えます
        </div>
      </div>
    </div>
  );

  // ── パスワード設定済み → ログイン画面 ──
  return (
    <div style={wrap}><div style={inner}>
      <div style={{fontSize:44,marginBottom:16}}>🔒</div>
      <div style={{fontSize:20,fontWeight:700,color:"#f5f5f7",marginBottom:6}}>家計管理</div>
      <div style={{fontSize:13,color:"#9a9aa3",marginBottom:28}}>パスワードを入力してください</div>
      <PasswordInput value={pw} onChange={setPw} onEnter={login} placeholder="パスワード" err={!!err}/>
      {err && <div style={{color:"#f87171",fontSize:13,marginBottom:10}}>{err}</div>}
      <button onClick={login} disabled={busy} style={btnStyle}>{busy ? "確認中..." : "ログイン"}</button>
      {/* パスワードを忘れた場合のリンク */}
      <button onClick={()=>setShowReset(true)} style={{background:"none",border:"none",color:"#5a5a63",fontSize:12,cursor:"pointer",marginTop:20,fontFamily:"inherit",textDecoration:"underline"}}>パスワードを忘れた場合</button>
      {/* リセット確認ダイアログ */}
      {showReset&&<div onClick={()=>setShowReset(false)} style={{position:"fixed",inset:0,background:"rgba(0,0,0,0.72)",zIndex:200,display:"flex",alignItems:"center",justifyContent:"center",padding:20}}>
        <div onClick={e=>e.stopPropagation()} style={{background:"#18181f",border:"1px solid rgba(255,255,255,0.08)",borderRadius:20,padding:24,width:"100%",maxWidth:320,textAlign:"left" as const}}>
          <div style={{fontSize:15,fontWeight:700,color:"#f5f5f7",marginBottom:8}}>パスワードをリセット</div>
          <div style={{fontSize:13,color:"#9a9aa3",marginBottom:4,lineHeight:1.7}}>パスワードをリセットして、新しく設定し直します。</div>
          <div style={{fontSize:13,color:"#f87171",marginBottom:20,lineHeight:1.7}}>⚠ 新しいパスワードでは既存の家計データを読み込めなくなります。事前にバックアップを取ってください。</div>
          <div style={{display:"flex",gap:10}}>
            <button onClick={()=>setShowReset(false)} style={{flex:1,background:"transparent",border:"1px solid rgba(255,255,255,0.08)",borderRadius:10,padding:"12px 0",cursor:"pointer",fontSize:13,color:"#9a9aa3",fontFamily:"inherit",minHeight:44}}>キャンセル</button>
            <button onClick={resetPw} style={{flex:1,border:"none",borderRadius:10,padding:"12px 0",cursor:"pointer",fontSize:13,fontWeight:700,background:"#f87171",color:"#0a0a0c",fontFamily:"inherit",minHeight:44}}>リセットする</button>
          </div>
        </div>
      </div>}
    </div></div>
  );
}
