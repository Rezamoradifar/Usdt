import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import {execFile} from "node:child_process";
const snapshotPlugin = {name:"read-only-token-api", configureServer(server){
 let cache={contract:"TRpMNouAARgEA5KjtRjbb6f3n1FvmLoL4x",events:null,status:"loading"}, busy=false,last=0;
 function refresh(){if(busy || Date.now()-last<30000)return;busy=true;execFile("python3",["api.py","--snapshot"],{timeout:60000,maxBuffer:2000000},(err,out)=>{last=Date.now();busy=false;try{if(err)throw err;const next=JSON.parse(out);cache=next.status==="unavailable"&&cache.updatedAt?{...cache,status:"stale"}:next;}catch{cache={...cache,status:cache.updatedAt?"stale":"unavailable"}}});}
 server.middlewares.use("/api/token",(req,res)=>{refresh();res.setHeader("Content-Type","application/json");res.setHeader("Cache-Control","no-store");res.end(JSON.stringify(cache));});refresh();
}};

export default defineConfig({
  build: {
    outDir: "dist/client",
  },
  optimizeDeps: {
    include: ["react", "react-dom/client"],
  },
  server: {
    host: "0.0.0.0",
    allowedHosts: ["terminal.local"],
    warmup: {
      clientFiles: ["./src/main.jsx"],
    },
  },
  plugins: [react(),snapshotPlugin],
});
