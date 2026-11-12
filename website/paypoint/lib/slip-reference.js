export const SLIP_PATTERN='09FG[0-9]{16}[A-Z0-9]{5}';
export const SLIP_HELP='Enter the complete 25-character TRANS REF: 09FG, 16 digits, then 5 letters/numbers. Join wrapped lines.';
export const isSlipChannel=channel=>['pos','bank_transfer'].includes(channel);
export const normalizeSlipReference=value=>value.replace(/\s+/g,'').toUpperCase();
