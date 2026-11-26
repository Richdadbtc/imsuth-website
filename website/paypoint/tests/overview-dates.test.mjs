import test from 'node:test';
import assert from 'node:assert/strict';
import {defaultOverviewDates,overviewDateQuery} from '../lib/overview-dates.js';
test('overview calendar defaults use Lagos date with an inclusive 30-day window',()=>{
 assert.deepEqual(defaultOverviewDates(new Date('2026-11-25T23:30:00Z')),{date_from:'2026-10-28',date_to:'2026-11-26'});
});
test('calendar filter preserves exact dates and rejects missing or reversed dates',()=>{
 assert.equal(overviewDateQuery({date_from:'2026-11-25',date_to:'2026-11-26'}).toString(),'period=custom&date_from=2026-11-25&date_to=2026-11-26');
 for(const dates of [{date_from:'',date_to:'2026-11-26'},{date_from:'2026-11-27',date_to:'2026-11-26'},{date_from:'2026-02-30',date_to:'2026-11-26'}])assert.throws(()=>overviewDateQuery(dates));
});
