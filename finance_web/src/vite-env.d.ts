/// <reference types="vite/client" />

// CSS ファイルを TypeScript から import できるようにする型宣言
declare module "*.css" {
  const content: Record<string, string>;
  export default content;
}

// vite.config.js の define で注入されるアプリバージョン（package.json の version と常に一致）
declare const __APP_VERSION__: string;
