// 全JS/CSSを1つのHTMLに同梱したビルド。
// 出力: dist-single/index.html （これ1ファイルでアプリが動く）
import { build } from 'vite';
import react from '@vitejs/plugin-react';
import { viteSingleFile } from 'vite-plugin-singlefile';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import { copyFileSync, existsSync } from 'fs';

const __dirname = dirname(fileURLToPath(import.meta.url));

await build({
  configFile: false,
  root: __dirname,
  base: './',
  plugins: [react(), viteSingleFile()],
  build: {
    outDir: resolve(__dirname, 'dist-single'),
    emptyOutDir: true,
    cssCodeSplit: false,
    assetsInlineLimit: 100_000_000,
    rollupOptions: {
      output: { inlineDynamicImports: true },
    },
  },
});

// 分かりやすいファイル名のコピーも作る
const src = resolve(__dirname, 'dist-single', 'index.html');
const dst = resolve(__dirname, 'dist-single', 'DailyInquiryLog.html');
if (existsSync(src)) copyFileSync(src, dst);

console.log('\n単一ファイルビルド完了: dist-single/DailyInquiryLog.html\n');
