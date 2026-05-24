import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    // ──────── PWA設定：オフライン対応・ホーム画面追加を有効にする ────────
    VitePWA({
      // registerTypeをauto-updateにするとビルド時に自動でService Workerが更新される
      registerType: "autoUpdate",
      // ビルド時にService Workerを生成する（開発環境では無効）
      devOptions: { enabled: false },
      manifest: {
        // アプリの名前（ホーム画面に追加した時に表示される）
        name: "BYB — Before You Broke",
        short_name: "BYB",
        description: "収支・ローンを管理するプライベート家計アプリ",
        // テーマカラー（ブラウザのアドレスバーの色）
        theme_color: "#070b14",
        background_color: "#070b14",
        display: "standalone",
        // ホーム画面から開いた時の最初の画面
        start_url: "/",
        // アプリのアイコン一覧
        icons: [
          { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
          { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
          { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
        ],
      },
      workbox: {
        // キャッシュするファイルの種類（JS・CSS・画像・フォント）
        globPatterns: ["**/*.{js,css,html,ico,png,svg,woff2}"],
      },
    }),
  ],
  build: {
    rollupOptions: {
      output: {
        // ──────── 手動チャンク分割：vendor をアプリコードと分離してキャッシュ効率を上げる ────────
        // recharts は重いので独立チャンクに。react はSWR的に長期キャッシュさせるため別出し
        manualChunks: {
          "vendor-react": ["react", "react-dom"],
          "vendor-recharts": ["recharts"],
        },
      },
    },
  },
  test: {
    // テスト環境をブラウザに近いjsdomに設定する
    environment: "jsdom",
    // テストファイルの読み込み前に必ずsetup.tsを実行する
    setupFiles: ["./src/test/setup.ts"],
    // describe / it / expect をimportなしで使えるようにする
    globals: true,
  },
});
