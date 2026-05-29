/// <reference types="vite/client" />

// CSS ファイルを TypeScript から import できるようにする型宣言
declare module "*.css" {
  const content: Record<string, string>;
  export default content;
}
