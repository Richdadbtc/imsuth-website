import {cp,mkdir} from 'node:fs/promises';
const destination=new URL('../.next/standalone/',import.meta.url);
await mkdir(new URL('.next/',destination),{recursive:true});
await cp(new URL('../public/',import.meta.url),new URL('public/',destination),{recursive:true});
await cp(new URL('../.next/static/',import.meta.url),new URL('.next/static/',destination),{recursive:true});
console.log('Standalone server assets prepared.');
