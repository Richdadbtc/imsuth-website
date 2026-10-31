import {spawn} from 'node:child_process';
const child=spawn(process.execPath,['.next/standalone/server.js'],{stdio:'inherit',env:{...process.env,HOSTNAME:process.env.HOSTNAME||'127.0.0.1',PORT:process.env.PORT||'3000'}});
for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>child.kill(signal));
child.on('exit',code=>process.exit(code??1));
