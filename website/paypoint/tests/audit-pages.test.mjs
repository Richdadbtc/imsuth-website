import test from 'node:test';
import assert from 'node:assert/strict';
import {loadAuditPage} from '../lib/audit-pages.js';
test('audit loading makes one bounded request even with thousands of older pages',async()=>{
 const calls=[];const result=await loadAuditPage(async path=>{calls.push(path);return {count:20000,next:'https://example.invalid/page2',previous:null,results:[{id:'one'}]};});
 assert.deepEqual(calls,['audit-logs/?period=30&page=1&page_size=10']);assert.equal(result.count,20000);assert.equal(result.next,true);assert.equal(result.rows.length,1);
});
test('browsing an audit page retains server date filters instead of downloading all logs',async()=>{
 let path;await loadAuditPage(async value=>{path=value;return {results:[],count:0};},{period:'1',page:3,pageSize:25});
 assert.equal(path,'audit-logs/?period=today&page=3&page_size=25');
});
test('a server outage rejects only the explicitly requested audit page without retries',async()=>{
 let attempts=0;const error=new Error('Temporarily unavailable');error.status=503;
 await assert.rejects(loadAuditPage(async()=>{attempts++;throw error;}),error);assert.equal(attempts,1);
});
