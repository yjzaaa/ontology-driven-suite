import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// 构建为单文件静态 bundle，供 engine.cjs serve（注入 __SCHEMA_JSON__）
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../engine/renderer-dist',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        entryFileNames: 'renderer.js',
        chunkFileNames: '[name].js',
        assetFileNames: '[name][extname]',
      },
    },
  },
})