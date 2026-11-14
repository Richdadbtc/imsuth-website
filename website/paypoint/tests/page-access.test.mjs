import test from 'node:test';
import assert from 'node:assert/strict';
import {canAccessPage,firstAccessiblePage} from '../lib/navigation.js';
test('page selections narrow navigation and cover direct aliases',()=>{
 const user={allowed_pages:['dashboard-record-payment','my-profile','admin-departments']};
 assert.equal(canAccessPage(user,'dashboard-record-payment'),true);
 assert.equal(canAccessPage(user,'reports'),false);
 assert.equal(canAccessPage(user,'department-management'),true);
 assert.equal(canAccessPage(user,'admin-settings'),false);
 assert.equal(firstAccessiblePage(user),'dashboard-record-payment');
 assert.equal(firstAccessiblePage({allowed_pages:['my-profile']}),'my-profile');
});
