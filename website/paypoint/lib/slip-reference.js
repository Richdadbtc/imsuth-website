export const SLIP_PATTERN='[A-Z0-9]{4}/[A-Z0-9]{5}';
export const SLIP_HELP='Enter the first 4 and last 5 characters of the transfer reference. The slash is added automatically (example: 09FG/CY0W7).';
export const isSlipChannel=channel=>['pos','bank_transfer'].includes(channel);
export const normalizeSlipReference=value=>value.replace(/\s+/g,'').toUpperCase();
export const referenceRule=channel=>channel==='pos'
  ? {pattern:'[0-9]{12}',placeholder:'12-digit card Reference Number',help:'Enter the 12-digit Reference Number printed on the card slip, not the STAN or Auth Code.'}
  : {pattern:SLIP_PATTERN,placeholder:'0000/00000',help:SLIP_HELP};

export const formatTransferReference=value=>{
  const normalized=normalizeSlipReference(value);
  if(/^09FG[0-9]{16}[A-Z0-9]{5}$/.test(normalized))return normalized.slice(0,4)+'/'+normalized.slice(-5);
  const characters=normalized.replace(/\//g,'');
  if(!/^[A-Z0-9]*$/.test(characters)||characters.length>9)return normalized;
  return characters.length>4?characters.slice(0,4)+'/'+characters.slice(4):characters;
};
