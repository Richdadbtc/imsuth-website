export const SLIP_PATTERN='09FG[0-9]{16}[A-Z0-9]{5}';
export const SLIP_HELP='Enter the complete 25-character TRANS REF: 09FG, 16 digits, then 5 letters/numbers. Join wrapped lines.';
export const isSlipChannel=channel=>['pos','bank_transfer'].includes(channel);
export const normalizeSlipReference=value=>value.replace(/\s+/g,'').toUpperCase();
export const referenceRule=channel=>channel==='pos'
  ? {pattern:'[0-9]{12}',placeholder:'12-digit card Reference Number',help:'Enter the 12-digit Reference Number printed on the card slip, not the STAN or Auth Code.'}
  : {pattern:SLIP_PATTERN,placeholder:'25-character TRANS REF',help:SLIP_HELP};
