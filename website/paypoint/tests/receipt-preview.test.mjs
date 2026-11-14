import test from 'node:test';
import assert from 'node:assert/strict';
import {receiptPreviewPath} from '../features/receipt-preview.js';
test('receipt previews only use authenticated same-origin receipt print endpoints',()=>{
 const origin='https://www.imsuth.site',path='/paypoint/api/v1/receipts/1234-abcd/print/';
 assert.equal(receiptPreviewPath(path,origin),path);
 assert.equal(receiptPreviewPath(path+'?paper=thermal',origin),path+'?paper=thermal');
 for(const url of ['https://evil.example'+path,'/paypoint/api/v1/payments/','/paypoint/api/v1/receipts/1234-abcd/print/extra','javascript:alert(1)'])assert.equal(receiptPreviewPath(url,origin),null);
});
