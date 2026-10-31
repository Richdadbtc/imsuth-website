import {mountHospitalCatalogueSetup} from './catalogue-setup.js';
import {createLivePages} from './live-pages.js';
import {refreshOverview,watchPaymentStatus,mountTariffProposals,mountCashEvidence,mountOverviewTransactions,mountDepartmentDirectory} from './revenue-live.js';
import {api as request} from '../lib/api.js';
import {navigationPage} from '../lib/navigation.js';

export function mountWorkspace(content, {user,navigate,onSignedOut,onProfileSaved,onUnreadCount}) {
const abort = new AbortController();
const api = (path, options={}) => request(path, {...options, signal:abort.signal});
const session = {authenticated:true,user:{...user,permissions:{...user.permissions}}};
let activeRows=[];
const chartAttributes = {'data-chart-background':'background','data-chart-colour':'--department-colour','data-chart-width':'width','data-chart-height':'height'};
const applyChartStyles = root => {
  if (!(root instanceof Element)) return;
  for (const [attribute, property] of Object.entries(chartAttributes)) {
    const nodes = [...(root.hasAttribute(attribute) ? [root] : []), ...root.querySelectorAll(`[${attribute}]`)];
    for (const node of nodes) {
      node.style.setProperty(property, node.getAttribute(attribute));
      node.removeAttribute(attribute);
    }
  }
};
const observer = new MutationObserver(records => records.forEach(record => record.addedNodes.forEach(applyChartStyles)));
observer.observe(content, {childList:true, subtree:true});

const dashboardModes = {
  management: {
    label: "Management Dashboard",
    description: "Overview of hospital revenue, transactions and key activities"
  },
  front_desk: {
    label: "Front Desk Dashboard",
    description: "Patient registration, appointments and front-desk activity"
  },
  cashier: {
    label: "Cashier Dashboard",
    description: "Collections, payment verification and receipt activity"
  },
  finance: {
    label: "Finance Dashboard",
    description: "Revenue, approvals, reconciliation and financial controls"
  },
  daily: {
    label: "Daily Activity Overview",
    description: "Today’s operational activity across IMSUTH PayPoint"
  }
};
let dashboardMode = localStorage.getItem("imsuth-paypoint-dashboard") || "management";
if (!dashboardModes[dashboardMode]) dashboardMode = "management";
const escapeHtml = value => String(value ?? "").replace(/[&<>'"]/g, character => ({
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  "'": "&#39;",
  '"': "&quot;"
})[character]);
const money = (value, currency = "NGN") => `${currency === "NGN" ? "₦" : `${currency} `}${Number(value || 0).toLocaleString("en-NG", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2
})}`;
const moneyWhole = (value, currency = "NGN") => `${currency === "NGN" ? "₦" : `${currency} `}${Number(value || 0).toLocaleString("en-NG", {
  maximumFractionDigits: 0
})}`;
const list = payload => Array.isArray(payload) ? payload : payload?.results || [];
const title = text => `<div class="page-toolbar"><div><p class="eyebrow">IMSUTH PayPoint</p><h1>${escapeHtml(text)}</h1></div><button class="button button-secondary" type="button" data-refresh>Refresh</button></div>`;
const status = value => `<span class="status status-${escapeHtml(value)}">${escapeHtml(String(value || "unknown").replaceAll("_", " "))}</span>`;
const empty = message => `<div class="empty-state">${escapeHtml(message)}</div>`;
function setBusy(label = "Loading authorised data…") {
  content.innerHTML = `<div class="loading-state" role="status">${escapeHtml(label)}</div>`;
}
function showError(error) {
  if (error.status === 401 || error.status === 403) {
    content.innerHTML = `<div class="api-error"><h2>Access unavailable</h2><p>${escapeHtml(error.message)}</p></div>`;
    return;
  }
  content.innerHTML = `<div class="api-error"><h2>Unable to load this page</h2><p>${escapeHtml(error.message)}</p></div>`;
}
function table(headers, rows) {
  if (!rows.length) return empty("No authorised records are available.");
  activeRows = rows.map(row => row.map(cell => String(cell.text ?? cell)));
  return `<div class="table-wrap"><table class="data-table"><thead><tr>${headers.map(header => `<th>${escapeHtml(header)}</th>`).join("")}</tr></thead><tbody>${rows.map(row => `<tr>${row.map((cell, index) => `<td data-label="${escapeHtml(headers[index])}">${cell.html ?? escapeHtml(cell.text ?? cell)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
}
const livePages = createLivePages({
  content,
  getUser: () => session.user,
  escapeHtml,
  money,
  table,
  onSignedOut,
  onProfileSaved: values => {
    Object.assign(session.user, values);
    onProfileSaved(values);
  }
});
async function dashboard(reports = false) {
  return reports ? livePages.reportsDashboard() : overviewDashboardPreview();
}
async function patients() {
  return livePages.patients();
}
async function patientRegistration() {
  return livePages.patientRegistration();
}
async function patientProfile() {
  return livePages.patients();
}
async function createInvoice() {
  return livePages.createInvoice();
}
async function invoiceDetails() {
  return livePages.billing();
}
async function processPayment() {
  return livePages.billing();
}
async function verifyPayment() {
  return livePages.payments();
}
const pendingPayments = () => paymentDirectory(false);
const verifiedPayments = () => paymentDirectory(true);
async function paymentDirectory(verified = false) {
  return livePages.payments(verified ? 'confirmed' : ['pending','awaiting_offline_verification','review_required']);
}
async function failedPayments() {
  return livePages.payments(['failed','expired']);
}
async function receipts() {
  return livePages.receipts();
}
async function receiptVerification() {
  return livePages.receiptVerification();
}
async function billing() {
  return livePages.billing();
}
async function payments() {
  return livePages.payments();
}
async function financeOverview() {
  return livePages.report('revenue', 'Finance Overview');
}
async function revenueCollections() {
  return livePages.report('collections', 'Revenue Collections');
}
async function dailySettlement() {
  return livePages.settlements();
}
async function receiptReprints() {
  return livePages.receiptReprints();
}
async function bankReconciliation() {
  return livePages.bankReconciliation();
}
async function reconciliationDiscrepancies() {
  return livePages.discrepancies();
}
async function reportsDashboard() {
  return livePages.reportsDashboard();
}
async function refundRequests() {
  return livePages.financialRequests('refunds');
}
async function reversalRequests() {
  return livePages.financialRequests('reversals');
}
async function approvalQueue() {
  return livePages.approvalQueue();
}
async function finance() {
  return financeOverview();
}
async function staffManagement(adding = false) {
  return usersAndAudit();
}
async function addStaffMember() {
  await usersAndAudit();
  content.querySelector('[data-ua-add]')?.click();
}
async function rolesPermissions() {
  return livePages.roles();
}
async function hospitalCatalogueSetup() {return mountHospitalCatalogueSetup(content,{api,user,escapeHtml});}
async function departmentsManagement() {
  return revenueDepartments();
}
async function servicesManagement() {
  return servicesAndPrices();
}
async function tariffManagement() {
  return livePages.tariffs();
}
async function notificationsManagement() {
  return livePages.notifications();
}
async function systemSettings() {
  return livePages.settings();
}
async function revenueReports() {
  return livePages.report('revenue', 'Revenue Reports');
}
async function dailyCollectionReport() {
  return livePages.report('collections', 'Daily Collection Report');
}
async function departmentRevenueReport() {
  return livePages.report('departments', 'Department Revenue Report');
}
async function cashierCollectionReport() {
  return livePages.report('cashiers', 'Cashier Collection Report');
}
async function paymentChannelReport() {
  return livePages.report('channels', 'Payment Channel Report');
}
async function outstandingInvoicesReport() {
  return livePages.report('outstanding', 'Outstanding Invoices Report');
}
async function settlementReport() {
  return livePages.report('settlements', 'Settlement Report');
}
async function reconciliationReport() {
  return livePages.report('reconciliation', 'Reconciliation Report');
}
async function auditTrailReport() {
  return livePages.report('audit', 'Audit Trail Report');
}
async function patientRegistrationReport() {
  return livePages.report('patients', 'Patient Registration Report');
}
async function systemActivityReport() {
  return livePages.report('activity', 'System Activity Report');
}
async function userAccountSettings() {
  return livePages.profile();
}
async function helpSupport() {
  return livePages.help();
}
async function overviewDashboardPreview() {
  content.innerHTML=`<div class="overview-preview-page imported-overview"><header class="source-overview-header"><div><h1>IMSUTH Central Pay Point</h1><small>Imo State Teaching Hospital, Orlu: all payments in one place</small></div><label>Period <select data-overview-period><option value="1">Today</option><option value="7">Last 7 days</option><option value="30" selected>Last 30 days</option><option value="all">All records</option></select></label></header><nav class="source-overview-nav" aria-label="Revenue control sections"><a href="#dashboard-overview-preview" aria-current="page">Overview</a><a href="#dashboard-record-payment">Record payment</a><a href="#patients">Department desk</a><a href="#admin-departments">Departments</a><a href="#admin-services">Services and prices</a><a href="#cash-points">Cash points and orders</a><a href="#alerts">Alerts <b data-overview-alert-count></b></a><a href="#users-audit">Users and audit</a></nav><div class="source-overview-body"><section class="source-overview-kpis" data-overview-kpis aria-label="Collection summary"><p>Loading collection summary…</p></section><div class="source-overview-grid"><section class="source-overview-card"><h2>Daily collections by channel</h2><div data-overview-daily aria-label="Daily confirmed NGN collections"></div></section><section class="source-overview-card"><h2>Channel split</h2><div data-overview-channels></div></section><section class="source-overview-card"><h2>Top departments</h2><div data-overview-departments></div></section><section class="source-overview-card"><h2>Reconciliation with bank and POS settlement</h2><div data-overview-reconciliation></div><a class="source-overview-report" href="#reports-reconciliation">View reconciliation report</a></section></div><p class="overview-preview-note">Confirmed NGN collections for the selected period. Pending attempts are excluded. Reconciliation counts imported statement rows.</p></div></div>`;
  await refreshOverview(content.querySelector('.imported-overview'),escapeHtml,moneyWhole);
}
// During rolling upgrades, retain the existing operational screens until the
// new backend capture endpoint and its migration are deployed. Never fall back
// on authorization, network, or server failures.
async function recordPaymentPreview() {
  let capture;
  try {capture=await api('record-payment/');}
  catch(error){if(error.status!==404)throw error;await legacyRecordPaymentPreview();return;}
  await enhancedRecordPaymentPreview(capture);
}
async function departmentDesk() {
  try {await api('record-payment/');}
  catch(error){if(error.status!==404)throw error;await legacyDepartmentDesk();return;}
  await enhancedDepartmentDesk();
}

async function enhancedRecordPaymentPreview(capture) {
  const fetchAll = async name => {
    let data = await api(`${name}/?page_size=100`),
      items = [...list(data)];
    for (let page = 2; data.next; page++) {
      data = await api(`${name}/?page_size=100&page=${page}`);
      items.push(...list(data));
    }
    return items;
  };
  const [patients, departments, services, tariffs, payments] = await Promise.all([Promise.resolve([]), ...['departments', 'services', 'tariffs'].map(fetchAll), Promise.resolve([])]);
  let cataloguePreview=null,catalogueUnavailable=false;
  if(user.role==='super_admin'){
    try{cataloguePreview=await api('catalogue-setup/');}
    catch{catalogueUnavailable=true;}
  }
  const inactiveDepartments=departments.filter(d=>d.is_active===false);
  const proposedDepartments=(cataloguePreview?.rows||[]).filter(r=>r.kind==='department'&&!r.id);
  const departmentOptions=()=>`<option value="">Select department</option>${departments.filter(d=>d.is_active!==false).map(d=>`<option value="${escapeHtml(d.id)}">${escapeHtml(d.name)}</option>`).join('')}${inactiveDepartments.length?`<optgroup label="Inactive — approval required">${inactiveDepartments.map(d=>`<option disabled>${escapeHtml(d.name)} — inactive</option>`).join('')}</optgroup>`:''}${proposedDepartments.length?`<optgroup label="Proposed placeholders — setup required">${proposedDepartments.map(d=>`<option disabled>${escapeHtml(d.name)} — ${d.comparison_status==='conflict'?'review conflict':'not imported'}</option>`).join('')}</optgroup>`:''}`;
  const catalogueNotice=`<p role="status">${departments.some(d=>d.is_active!==false)?'Select an active department to load its configured services.':'No active departments are available for payment.'} ${inactiveDepartments.length?inactiveDepartments.length+' inactive departments await approval. ':''}${proposedDepartments.length?proposedDepartments.length+' proposed department placeholders are listed below but cannot accept payments yet. ':''}${catalogueUnavailable?'Catalogue setup could not be loaded. Refresh or contact an administrator. ':''}Services need an approved price before payment.${user.role==='super_admin'?' <a href="#admin-catalogue-setup">Review / import departments and categories</a> · <a href="#admin-services">Configure services and prices</a>':''}</p>${cataloguePreview?`<details><summary>Department-linked category placeholders (${cataloguePreview.rows.filter(r=>r.kind==='category').length})</summary><ul>${cataloguePreview.rows.filter(r=>r.kind==='category').map(r=>`<li>${escapeHtml(r.department_code)}: ${escapeHtml(r.name)} — ${r.id?(r.is_active?'active':'inactive'):'proposed, not imported'}</li>`).join('')}</ul><p>These are service categories, not billable services or patient categories.</p></details>`:''}`;
  let patient = null,
    service = null,
    unit = null,
    drafts = [],
    receipt = null;
  const fullName = i => i.full_name || [i.first_name, i.middle_name, i.last_name].filter(Boolean).join(' '),
    options = (items, label) => `<option value="">${label}</option>${items.map(i => `<option value="${escapeHtml(i.id)}">${escapeHtml(i.name)}</option>`).join('')}`,
    field = (label, name, type = 'text', attrs = '') => `<label>${label}<input type="${type}" name="${name}" ${attrs}></label>`,
    now = new Date(),
    localDate = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
  content.innerHTML = `<div class="record-payment-preview compact-record-payment"><header class="overview-preview-brand"><img src="/paypoint/images/hospital%20logo.png" alt="IMSUTH crest"><div><h1>IMSUTH Central Pay Point</h1><p>Imo State Teaching Hospital, Orlu: all payments in one place</p></div><span class="record-preview-label">Record Payment</span></header><nav class="overview-preview-tabs" aria-label="Revenue control shortcuts"><a href="#dashboard-overview-preview">Overview</a><a href="#dashboard-record-payment" aria-current="page">Record payment</a><a href="#patients">Department desk</a><a href="#admin-departments">Departments</a><a href="#admin-services">Services and prices</a><a href="#cash-points">Cash points and orders</a><a href="#alerts">Alerts</a><a href="#users-audit">Users and audit</a></nav><div class="compact-record-layout"><form class="finance-card record-preview-form" data-rp-form><h2>Record a payment and issue a receipt</h2><div class="compact-record-grid"><label>Cash point<select name="cash_point" required>${options(capture.cash_points,'Select cash point')}</select></label><label>Department paid for<select name="department" required>${departmentOptions()}</select></label><label>Service paid for<select name="service" required disabled><option value="">Select department first</option></select></label><label>Patient name<input name="patient_query" required autocomplete="off" placeholder="Search registered patient" aria-describedby="patient-selection-status"><span id="patient-selection-status" data-rp-selection-status>Type at least 2 characters, then select a patient.</span><span data-rp-results aria-live="polite"></span></label><label>Patient type<select name="category"><option value="self_pay">Regular (full price)</option><option disabled>NHIS — approved tariff not configured</option><option disabled>IMSHIA — approved tariff not configured</option></select></label><label>Amount to pay (₦)<input name="paid" type="number" min="0.01" step="0.01" required placeholder="Select service for approved price"></label><label>Reason, if the amount differs from the price list<textarea name="override_reason" maxlength="500"></textarea></label><label>Payment channel<select name="channel"><option value="pos">POS/card</option><option value="bank_transfer">Bank transfer</option><option value="online">Online payment</option><option value="cash">Cash</option></select></label><label>Reference (card slip, transfer, bank teller or USSD)<input name="reference" required maxlength="120"></label><label>Cash standing order (cash only)<select name="cash_order" disabled><option value="">None</option></select></label><button type="submit" class="pending-verify compact-record-submit" ${capture.can_record?'':'disabled'}>Issue receipt</button></div><p class="compact-record-note">The amount fills in from the approved price list. Changing it requires a reason and raises a review flag. An official receipt is issued after payment verification. Insurance discounts require approved tariffs.</p><p data-rp-message role="status"></p><details class="compact-record-setup"><summary>Department and category setup status</summary>${catalogueNotice}</details><input type="hidden" name="quantity" value="1"><input type="hidden" name="occurred" value="${localDate}"><input type="hidden" name="remarks" value="">${['patient_name','phone','dob','gender','address','next_of_kin','kin_phone'].map(name=>`<input type="hidden" name="${name}">`).join('')}<div hidden><span data-rp-total></span><span data-rp-fees></span><span data-rp-service></span><span data-rp-service-line></span><span data-rp-patient></span><button type="button" data-rp-search>Search</button></div></form><aside class="finance-card" data-rp-receipt-card><h2>Receipt</h2><div data-rp-receipt>The receipt appears here after verification.</div></aside></div><section class="finance-card"><h2>Latest receipts</h2><div data-rp-recent></div></section></div>`;
  const root = content.querySelector('.record-payment-preview'),
    form = content.querySelector('[data-rp-form]'),
    el = name => form.elements.namedItem(name),
    details = entries => `<dl class="record-detail-list">${entries.map(([label, value]) => `<div><dt>${label}</dt><dd>${escapeHtml(value || 'Not supplied')}</dd></div>`).join('')}</dl>`,
    total = () => unit === null ? 0 : Math.round(unit * Number(el('quantity').value || 0) * 100) / 100;
  const fees = () => {
    const amount = total();
    content.querySelector('[data-rp-total]').textContent = moneyWhole(Number(el('paid').value||amount));
    content.querySelector('[data-rp-fees]').innerHTML = details([['Service Amount', unit === null ? 'Not supplied' : moneyWhole(unit)], ['Quantity', el('quantity').value], ['Subtotal', moneyWhole(amount)], ['Entered Amount',moneyWhole(Number(el('paid').value||amount))], ['Price Difference',moneyWhole(Number(el('paid').value||amount)-amount)]]);
  };
  let latestReceipts=capture.receipts;
  const recent = () => {
    content.querySelector('[data-rp-recent]').innerHTML = `<div class="table-wrap"><table class="data-table finance-data-table record-recent-table"><thead><tr><th>Receipt</th><th>Patient</th><th>Service</th><th>Department</th><th>Amount paid</th><th>Service status</th><th>Actions</th></tr></thead><tbody>${latestReceipts.map(i=>`<tr><td>${escapeHtml(i.receipt_number)}</td><td>${escapeHtml(i.patient_name)}</td><td>${escapeHtml(i.service)}</td><td>${escapeHtml(i.department)}</td><td>${moneyWhole(i.amount)}</td><td>${escapeHtml(i.payment_status==='confirmed'?i.service_status:i.payment_status)}</td><td>${i.payment_status==='confirmed'?`<a class="pending-outline" target="_blank" rel="noopener" href="/paypoint/api/v1/receipts/${encodeURIComponent(i.id)}/print/">Print receipt</a>`:'Receipt unavailable'}</td></tr>`).join('')||'<tr><td colspan="7">No official receipts issued yet.</td></tr>'}</tbody></table></div>`;
  };

  const clearReceipt = () => {
    receipt = null;
    content.querySelector('[data-rp-receipt-card]').hidden = false;
    content.querySelector('[data-rp-receipt]').textContent='The receipt appears here after verification.';
  };
  const pickPatient = index => {
    patient = patients[index];
    el('patient_name').value = fullName(patient);
    el('phone').value = patient.phone || '';
    el('dob').value = patient.date_of_birth || '';
    el('gender').value = patient.sex || '';
    el('address').value = patient.address || '';
    el('next_of_kin').value = patient.emergency_contact || '';
    el('kin_phone').value = patient.next_of_kin_phone || '';
    el('patient_query').value = fullName(patient);
    content.querySelector('[data-rp-selection-status]').textContent='Selected: '+fullName(patient)+' · '+patient.patient_id;
    content.querySelector('[data-rp-results]').innerHTML = '';
    content.querySelector('[data-rp-patient]').innerHTML = details([['Patient ID', patient.patient_id], ['Full Name', fullName(patient)], ['Gender', patient.sex], ['Date of Birth', patient.date_of_birth], ['Phone Number', patient.phone], ['Address', patient.address], ['Emergency Contact', patient.emergency_contact], ['Next of Kin Phone', patient.next_of_kin_phone]]);
    clearReceipt();
  };
  const chooseService = () => {
    service = services.find(i => String(i.id) === el('service').value) || null;
    const time = Date.now(),
      matches = tariffs.filter(t => service && String(t.service) === String(service.id) && t.is_approved && t.currency === 'NGN' && Date.parse(t.effective_from) <= time && (!t.effective_until || Date.parse(t.effective_until) > time)).sort((a, b) => Date.parse(b.effective_from) - Date.parse(a.effective_from));
    unit = matches.length ? Number(matches[0].amount) : null;
    content.querySelector('[data-rp-service]').innerHTML = service ? details([['Service Name', service.name], ['Service Code', service.code], ['Unit Price', unit === null ? 'No single approved current NGN tariff' : moneyWhole(unit)], ['Patient Category', 'Self Pay']]) : '<p class="finance-empty">No service selected.</p>';
    content.querySelector('[data-rp-service-line]').textContent = service ? `${service.name} · ${unit === null ? 'Approved pricing unavailable' : moneyWhole(unit) + ' per unit'} · Self Pay · No discount` : 'No service selected';
    el('paid').value=unit===null?'':total().toFixed(2);
    el('override_reason').value='';
    el('override_reason').required=false;
    fees();
    clearReceipt();
  };
  let patientSearchSequence=0;
  root.addEventListener('click', async event => {
    if (event.target.closest('[data-rp-search]')) {
      const query=el('patient_query').value.trim(),sequence=++patientSearchSequence;
      if(!query){content.querySelector('[data-rp-results]').textContent='Enter a patient ID, name or phone number.';return;}
      content.querySelector('[data-rp-results]').textContent='Searching permitted patients…';
      try {
        const result=await api('patients/?page_size=20&search='+encodeURIComponent(query));
        if(sequence!==patientSearchSequence||!root.isConnected)return;
        patients.splice(0,patients.length,...list(result));
        content.querySelector('[data-rp-results]').innerHTML=patients.map((p,k)=>`<button type="button" class="pending-outline" data-rp-patient-index="${k}">${escapeHtml(p.patient_id)} · ${escapeHtml(fullName(p))}</button>`).join('')||'No matching patients found.';
      }catch(error){if(root.isConnected)content.querySelector('[data-rp-results]').textContent=error.message;}
    }
    const pick = event.target.closest('[data-rp-patient-index]');
    if (pick) pickPatient(Number(pick.dataset.rpPatientIndex));
  });
  form.addEventListener('input', () => {
    delete form.dataset.requestKey;
    delete form.dataset.lastPayment;
    clearReceipt();
  });
  el('department').addEventListener('change', () => {
    const availableServices=services.filter(i => String(i.department) === el('department').value && i.is_active !== false);
    el('service').innerHTML = options(availableServices, !el('department').value?'Select department first':availableServices.length?'Select service':'No active services configured');
    el('service').disabled = !el('department').value||!availableServices.length;
    el('service').value = '';
    chooseService();
  });
  el('service').addEventListener('change', chooseService);
  el('quantity').addEventListener('input', () => {
    el('paid').value=unit===null?'':total().toFixed(2);
    el('override_reason').required=false;
    fees();
    clearReceipt();
  });
  let patientSearchTimer;
  el('patient_query').addEventListener('input', () => {
    patient=null;
    content.querySelector('[data-rp-selection-status]').textContent='Select a registered patient from the search results.';
    content.querySelector('[data-rp-results]').innerHTML='';
    patientSearchSequence++;
    clearReceipt();clearTimeout(patientSearchTimer);
    if(el('patient_query').value.trim().length>=2)patientSearchTimer=setTimeout(()=>{if(root.isConnected)root.querySelector('[data-rp-search]').click();},300);
  });
  const updateOrders=()=>{
    const enabled=el('channel').value==='cash'&&!!el('cash_point').value;
    el('cash_order').disabled=!enabled;
    el('cash_order').innerHTML='<option value="">None</option>'+(enabled?capture.cash_orders.filter(o=>String(o.cash_point)===el('cash_point').value).map(o=>`<option value="${escapeHtml(o.id)}">${escapeHtml(o.purpose)} · ${moneyWhole(o.amount)}</option>`).join(''):'');
  };
  el('cash_point').addEventListener('change',updateOrders);el('channel').addEventListener('change',updateOrders);
  el('paid').addEventListener('input',()=>{fees();el('override_reason').required=Math.round(Number(el('paid').value)*100)!==Math.round(total()*100);clearReceipt();});
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const message = content.querySelector('[data-rp-message]'),
      amount = total(),
      quantity = Number(el('quantity').value),
      paid = Number(el('paid').value),
      reference = el('reference').value.trim();
    if (!patient || !service || unit === null || !Number.isInteger(quantity) || quantity < 1 || quantity > 100 || !reference || !el('cash_point').value || !Number.isFinite(paid) || paid<=0 || (Math.round(paid * 100) !== Math.round(amount * 100) && el('override_reason').value.trim().length<5)) {
      message.textContent = 'Select a cash point, patient and approved service, enter a reference and positive amount, and provide a reason of at least five characters for any price change.';
      return;
    }
    if (!el('occurred').value || !Number.isFinite(Date.parse(el('occurred').value)) || Date.parse(el('occurred').value) > Date.now() + 60000) {
      message.textContent = 'Enter a valid payment date and time that is not in the future.';
      return;
    }
    {
      const button = form.querySelector('[type=submit]');
      if (button) button.disabled = true;
      try {
        el('occurred').value=new Date(Date.now()-new Date().getTimezoneOffset()*60000).toISOString().slice(0,16);
        const key = form.dataset.requestKey || (form.dataset.requestKey = crypto.randomUUID());
        const recorded=await api('record-payment/',{method:'POST',body:JSON.stringify({
          patient:patient.id,department:el('department').value,service:service.id,quantity,
          cash_point:el('cash_point').value,cash_order:el('cash_order').value||null,
          amount:paid.toFixed(2),override_reason:el('override_reason').value.trim(),channel:el('channel').value,
          submitted_reference:reference,reported_paid_at:new Date(el('occurred').value).toISOString(),
          remarks:el('remarks').value.trim(),idempotency_key:key
        })});
        const {invoice,payment}=recorded;
        content.querySelector('[data-rp-receipt]').innerHTML=details([['Invoice',invoice.invoice_number],['Patient',fullName(patient)],['Department',departments.find(d=>String(d.id)===el('department').value)?.name],['Service',service.name],['Amount',moneyWhole(payment.amount)],['Payment status',payment.status]])+'<p>Payment recorded. An official receipt has not been issued; verification is pending.</p>';
        message.textContent = `Payment attempt ${payment.reference} recorded. Status: ${payment.status}. Amount due: ${moneyWhole(invoice.outstanding_balance)}. Reference submission does not verify payment; no paid receipt has been issued.`;
        payments.unshift(payment);
        if(recorded.price_changed)message.textContent+=' The price change has been flagged for review.';
        form.dataset.lastPayment = String(payment.id);
        recent();
        let statusControls = root.querySelector('[data-rp-status-controls]');
        if (!statusControls) {
          statusControls = document.createElement('div');
          statusControls.dataset.rpStatusControls = '';
          message.after(statusControls);
        }
        watchPaymentStatus(payment.id, () => root.isConnected && form.dataset.lastPayment === String(payment.id), async result => {
          if (result.error) {
            message.textContent = `Status check unavailable: ${result.error}. Refresh Transactions to check this payment.`;
            return;
          }
          payment.status = result.status;
          recent();
          message.textContent = `Payment ${payment.reference}: ${result.status}. Reference submission is not verification.`;
          if (result.status === 'confirmed') {
            const response = await api(`receipts/?payment=${encodeURIComponent(payment.id)}`),
              official = list(response)[0];
            if (official) {
              content.querySelector('[data-rp-receipt-card]').hidden = false;
              content.querySelector('[data-rp-receipt]').innerHTML = details([['Receipt',official.receipt_number],['Patient',payment.patient_name],['Department',payment.department],['Service',payment.service_summary],['Amount',moneyWhole(official.amount)],['Issued',official.issued_at]])+`<p>Payment verified</p><a class="pending-outline" target="_blank" rel="noopener" href="${escapeHtml('/paypoint/api/v1/')}receipts/${encodeURIComponent(official.id)}/print/">Open official receipt</a>`;
              latestReceipts=(await api('record-payment/')).receipts;recent();
              message.textContent = 'The backend has confirmed payment and issued an official receipt.';
            }
          }
        }, statusControls);
      } catch (error) {
        message.textContent = error.message;
      } finally {
        if (button) button.disabled = false;
      }
      return;
    }
  });
  form.addEventListener('input',()=>{delete form.dataset.requestKey;});
  form.addEventListener('change',()=>{delete form.dataset.requestKey;});
  form.addEventListener('reset', () => {
    patient = service = null;
    unit = null;
    delete form.dataset.requestKey;
    clearReceipt();
    content.querySelector('[data-rp-results]').innerHTML = '';
    content.querySelector('[data-rp-message]').textContent = '';
    content.querySelector('[data-rp-patient]').innerHTML = '<p class="finance-empty">Find and select a patient to view their details.</p>';
    content.querySelector('[data-rp-service]').innerHTML = '<p class="finance-empty">No service selected.</p>';
    content.querySelector('[data-rp-service-line]').textContent = 'No service selected';
    setTimeout(() => {
      el('service').innerHTML = '<option value="">Select department first</option>';
      el('service').disabled = true;
      updateOrders();
      fees();
    }, 0);
  });
  fees();
  recent();
}
async function enhancedDepartmentDesk() {
  const departments=[];let url='departments/?page_size=100';
  for(let page=1;url;page++){const data=await api('departments/?page_size=100&page='+page);departments.push(...list(data).filter(d=>d.is_active!==false));url=data.next;}
  content.innerHTML=`<div class="department-desk-page"><header class="overview-preview-brand"><img src="/paypoint/images/hospital%20logo.png" alt="IMSUTH crest"><div><h1>IMSUTH Central Pay Point</h1><p>Imo State Teaching Hospital, Orlu: all payments in one place</p></div><label>Period<select data-desk-period><option value="30">Last 30 days</option><option value="7">Last 7 days</option><option value="today">Today</option><option value="all">All records</option></select></label></header><nav class="overview-preview-tabs" aria-label="Revenue control shortcuts"><a href="#dashboard-overview-preview">Overview</a><a href="#dashboard-record-payment">Record payment</a><a href="#patients" aria-current="page">Department desk</a><a href="#admin-departments">Departments</a><a href="#admin-services">Services and prices</a><a href="#cash-points">Cash points and orders</a><a href="#alerts">Alerts</a><a href="#users-audit">Users and audit</a></nav><div class="desk-check-layout"><section class="finance-card"><h2>Department desk: check a receipt before giving a service</h2><form data-desk-search><label>Department you are at<select name="department" required>${departments.map(d=>`<option value="${escapeHtml(d.id)}">${escapeHtml(d.name)}</option>`).join('')}</select></label><label>Receipt number<input name="receipt" required maxlength="120" placeholder="Enter official receipt number"></label><button class="pending-verify" type="submit" ${departments.length?'':'disabled'}>Check receipt</button><p>Only receipts for the selected department can be checked here. A receipt can be printed again, but each service can only be marked delivered once.</p></form><p data-desk-message role="status"></p></section><section class="finance-card" data-desk-result aria-live="polite"><h2>Receipt check</h2><p>Check a receipt to see patient, payment and service details.</p></section></div><section class="finance-card"><h2 data-desk-title>Department receipts</h2><div data-desk-list></div><div class="pending-pagination"><span data-desk-count></span><div><button class="pending-outline" data-desk-prev>Previous</button><span data-desk-page></span><button class="pending-outline" data-desk-next>Next</button></div></div></section></div>`;
  const root=content.querySelector('.department-desk-page'),form=root.querySelector('[data-desk-search]'),department=form.elements.department,period=root.querySelector('[data-desk-period]'),result=root.querySelector('[data-desk-result]'),message=text=>root.querySelector('[data-desk-message]').textContent=text;
  let page=1,listVersion=0,checkVersion=0,selected=null,hasNext=false,hasPrevious=false;
  const query=()=>'?department='+encodeURIComponent(department.value);
  const details=entries=>`<dl class="record-detail-list">${entries.map(([key,value])=>`<div><dt>${escapeHtml(key)}</dt><dd>${escapeHtml(value)}</dd></div>`).join('')}</dl>`;
  const load=async()=>{
    const version=++listVersion;
    if(!department.value){message('No active departments are available to this account.');return;}
    root.querySelector('[data-desk-title]').textContent='Receipts for '+(departments.find(d=>String(d.id)===department.value)?.name||'selected department');
    root.querySelector('[data-desk-list]').textContent='Loading department receipts…';
    try{
      const data=await api('department-desk/receipts/'+query()+'&period='+encodeURIComponent(period.value)+'&page_size=10&page='+page);
      if(version!==listVersion||!root.isConnected)return;
      root.querySelector('[data-desk-list]').innerHTML=`<div class="table-wrap"><table class="data-table finance-data-table"><thead><tr><th>Receipt</th><th>Patient</th><th>Service</th><th>Department</th><th>Amount paid</th><th>Status</th><th>Actions</th></tr></thead><tbody>${data.results.map(r=>`<tr><td>${escapeHtml(r.receipt_number)}</td><td>${escapeHtml(r.patient_name)}</td><td>${escapeHtml(r.items.map(i=>i.service).join(', '))}</td><td>${escapeHtml(r.department_name)}</td><td>${moneyWhole(r.amount)}</td><td>${escapeHtml(r.eligible_for_delivery?r.service_status:'Payment unavailable for delivery')}</td><td><button type="button" class="pending-outline" data-desk-reference="${escapeHtml(r.receipt_number)}">Check receipt</button>${r.payment_status==='confirmed'?` <a class="pending-outline" href="/paypoint/api/v1/receipts/${encodeURIComponent(r.id)}/print/" target="_blank" rel="noopener">Print receipt</a>`:''}</td></tr>`).join('')||'<tr><td colspan="7">No official receipts for this department and period.</td></tr>'}</tbody></table></div>`;
      hasNext=!!data.next;hasPrevious=!!data.previous;
      root.querySelector('[data-desk-count]').textContent=`Showing ${data.count?(page-1)*10+1:0}–${Math.min(page*10,data.count)} of ${data.count} receipts`;
      root.querySelector('[data-desk-page]').textContent=String(page);
      root.querySelector('[data-desk-prev]').disabled=!hasPrevious;root.querySelector('[data-desk-next]').disabled=!hasNext;
    }catch(error){if(version===listVersion&&root.isConnected)root.querySelector('[data-desk-list]').textContent=error.message;}
  };
  const renderChecked=()=>{
    const r=selected;if(!r)return;
    result.innerHTML=`<h2>${escapeHtml(r.receipt_number)}</h2><div class="desk-verification-banner ${r.eligible_for_delivery?'verified':''}"><b>${r.eligible_for_delivery?'Payment verified':'Not eligible for service delivery'}</b><p>${escapeHtml(r.service_status)}</p></div>${details([['Patient',r.patient_name],['Patient ID',r.patient_id],['Department',r.department_name],['Amount paid',moneyWhole(r.amount)],['Payment channel',r.channel],['Payment status',r.payment_status]])}<fieldset><legend>Services</legend>${r.items.map(i=>`<label class="desk-service-choice"><input type="checkbox" data-desk-item="${escapeHtml(i.id)}" ${i.delivered||!r.can_deliver?'disabled':''}> ${escapeHtml(i.service)} × ${i.quantity} — ${i.delivered?'Service delivered':'Not yet used'}</label>`).join('')}</fieldset><label>Service notes (optional)<textarea data-desk-notes maxlength="500"></textarea></label><button type="button" class="teal-button" data-desk-deliver disabled>Confirm service delivery</button>${r.payment_status==='confirmed'?` <a class="pending-outline" href="/paypoint/api/v1/receipts/${encodeURIComponent(r.id)}/print/" target="_blank" rel="noopener">Print receipt</a>`:''}${!r.can_deliver&&r.items.some(i=>!i.delivered)?'<p>Delivery requires an authorized department supervisor or finance administrator and a fully paid, undisputed invoice.</p>':''}`;
  };
  const check=async(reference)=>{
    const version=++checkVersion;selected=null;result.textContent='Checking receipt with the server…';message('');
    try{
      const row=await api('department-desk/receipts/'+encodeURIComponent(reference)+'/verify/'+query(),{method:'POST',body:'{}'});
      if(version!==checkVersion||!root.isConnected)return;
      selected=row;renderChecked();message(row.eligible_for_delivery?'Receipt checked. Review unused services before delivery.':'Receipt cannot currently authorize service delivery.');
    }catch(error){if(version===checkVersion&&root.isConnected){result.textContent='No eligible receipt was verified for this department.';message(error.message);}}
  };
  form.addEventListener('submit',event=>{event.preventDefault();const reference=form.elements.receipt.value.trim();if(reference)check(reference);});
  department.addEventListener('change',()=>{checkVersion++;selected=null;page=1;message('');form.elements.receipt.value='';result.innerHTML='<h2>Receipt check</h2><p>Check a receipt in the selected department.</p>';load();});
  period.addEventListener('change',()=>{page=1;load();});
  root.addEventListener('change',event=>{if(event.target.matches('[data-desk-item]'))root.querySelector('[data-desk-deliver]').disabled=!root.querySelector('[data-desk-item]:checked');});
  root.addEventListener('click',async event=>{
    const pick=event.target.closest('[data-desk-reference]');if(pick){form.elements.receipt.value=pick.dataset.deskReference;check(pick.dataset.deskReference);}
    if(event.target.closest('[data-desk-prev]')&&hasPrevious){page--;load();}
    if(event.target.closest('[data-desk-next]')&&hasNext){page++;load();}
    const deliver=event.target.closest('[data-desk-deliver]');
    if(deliver&&selected&&!deliver.disabled){
      const snapshot=selected,version=checkVersion,chosenDepartment=department.value,items=[...root.querySelectorAll('[data-desk-item]:checked')].map(i=>i.dataset.deskItem),notes=root.querySelector('[data-desk-notes]').value.trim();
      deliver.disabled=true;department.disabled=true;
      try{
        for(const id of items)await api('department-desk/service-items/'+encodeURIComponent(id)+'/deliver/?department='+encodeURIComponent(chosenDepartment),{method:'POST',body:JSON.stringify({receipt:snapshot.id,notes})});
        if(version===checkVersion&&root.isConnected){await check(snapshot.receipt_number);message('Service delivery recorded. Used services cannot be delivered again.');await load();}
      }catch(error){if(root.isConnected&&version===checkVersion){await check(snapshot.receipt_number);message('Delivery update: '+error.message);await load();}}
      finally{department.disabled=false;}
    }
  });
  await load();
}
async function legacyRecordPaymentPreview() {
  const fetchAll = async name => {
    let data = await api(`${name}/?page_size=100`),
      items = [...list(data)];
    for (let page = 2; data.next; page++) {
      data = await api(`${name}/?page_size=100&page=${page}`);
      items.push(...list(data));
    }
    return items;
  };
  const [patients, departments, services, tariffs, payments] = await Promise.all(['patients', 'departments', 'services', 'tariffs', 'payments'].map(fetchAll));
  let patient = null,
    service = null,
    unit = null,
    drafts = [],
    receipt = null;
  const fullName = i => i.full_name || [i.first_name, i.middle_name, i.last_name].filter(Boolean).join(' '),
    options = (items, label) => `<option value="">${label}</option>${items.map(i => `<option value="${escapeHtml(i.id)}">${escapeHtml(i.name)}</option>`).join('')}`,
    field = (label, name, type = 'text', attrs = '') => `<label>${label}<input type="${type}" name="${name}" ${attrs}></label>`,
    now = new Date(),
    localDate = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
  content.innerHTML = `<div class="record-payment-preview"><header class="overview-preview-brand"><img src="/paypoint/images/hospital%20logo.png" alt="IMSUTH crest"><div><h1>IMSUTH Central Pay Point</h1><p>Imo State Teaching Hospital, Orlu: all payments in one place</p></div><span class="record-preview-label">Record Payment</span></header><nav class="overview-preview-tabs" aria-label="Revenue control shortcuts"><a href="#dashboard-overview-preview">Overview</a><a href="#dashboard-record-payment" aria-current="page">Record payment</a><a href="#patients">Department desk</a><a href="#admin-departments">Departments</a><a href="#admin-services">Services and prices</a><a href="#cash-points">Cash points and orders</a><a href="#alerts">Alerts</a><a href="#users-audit">Users and audit</a></nav><p class="overview-preview-note">${'Payment attempts are recorded on the server. Submitted references are not confirmation; paid receipts require authoritative verification.'}</p><div class="record-preview-layout"><div class="record-preview-main"><form class="finance-card record-preview-form" data-rp-form><div class="finance-card-heading"><div><h2>Record New Payment</h2><p>Identify a patient, select a service and review the payment details.</p></div><button type="reset" class="pending-outline">Clear Form</button></div><fieldset><legend>1. Patient Information</legend><div class="record-fields"><label>Patient ID / Hospital No.<span class="record-search"><input name="patient_query" placeholder="Enter patient ID, name or phone"><button type="button" class="pending-outline" data-rp-search aria-label="Find patient">Search</button></span></label>${field('Patient Name', 'patient_name', 'text', 'readonly placeholder="Filled from selected patient"')}${field('Phone Number', 'phone', 'tel', 'readonly')}${field('Date of Birth', 'dob', 'date', 'readonly')}<label>Gender<input name="gender" readonly></label>${field('Address', 'address', 'text', 'readonly')}${field('Emergency Contact / Next of Kin', 'next_of_kin', 'text', 'readonly')}${field('Next of Kin Phone', 'kin_phone', 'tel', 'readonly placeholder="Not supplied"')}</div><div class="record-patient-results" data-rp-results aria-live="polite"></div></fieldset><fieldset><legend>2. Service and Department</legend><div class="record-fields"><label>Department *<select name="department" required>${options(departments.filter(i => i.is_active !== false), 'Select department')}</select></label><label>Service *<select name="service" required disabled><option value="">Select department first</option></select></label><label>Patient Category<select name="category"><option value="self_pay">Self Pay</option><option value="insurance" disabled>Insurance — tariff not configured</option><option value="exempt" disabled>Exempt — approval required</option></select></label>${field('Quantity *', 'quantity', 'number', 'min="1" max="100" step="1" value="1" required')}</div><div class="record-service-strip"><div><b>Service Details</b><span data-rp-service-line>No service selected</span></div><div><span>Amount to Pay (₦)</span><strong data-rp-total>₦0</strong></div></div></fieldset><fieldset><legend>3. Payment Details</legend><div class="record-fields"><label>Payment Channel *<select name="channel"><option value="pos">POS (Card)</option><option value="bank_transfer">Bank Transfer</option><option value="online">Online Payment</option><option value="cash">Cash</option></select></label>${field('Reference No. / Transaction ID *', 'reference', 'text', 'required maxlength="120" placeholder="Enter reference number"')}${field('Amount Paid (₦) *', 'paid', 'number', 'required min="0.01" step="0.01" placeholder="Enter amount"')}${field('Payment Date & Time *', 'occurred', 'datetime-local', `value="${localDate}" required`)}<label class="record-wide">Remarks (optional)<textarea name="remarks" maxlength="500" placeholder="Enter any additional notes..."></textarea></label></div></fieldset><p class="record-form-message" data-rp-message role="status"></p><div class="record-submit"><a class="pending-outline" href="#dashboard-overview-preview">Cancel</a><button type="submit" class="pending-verify">${'Record Payment Attempt'}</button></div></form><section class="finance-card"><div class="finance-card-heading"><h2>Recent Payments Recorded</h2><a href="#payments">View All</a></div><div data-rp-recent></div></section></div><aside class="record-preview-aside"><section class="finance-card"><h2>Patient Summary</h2><div data-rp-patient><p class="finance-empty">Find and select a patient to view their details.</p></div></section><section class="finance-card"><h2>Selected Service</h2><div data-rp-service><p class="finance-empty">Choose a department and service to see details here.</p></div></section><section class="finance-card"><h2>Fee Breakdown</h2><div data-rp-fees></div></section><section class="finance-card" data-rp-receipt-card hidden><h2>Official Receipt</h2><div data-rp-receipt></div></section></aside></div></div>`;
  const root = content.querySelector('.record-payment-preview'),
    form = content.querySelector('[data-rp-form]'),
    el = name => form.elements.namedItem(name),
    details = entries => `<dl class="record-detail-list">${entries.map(([label, value]) => `<div><dt>${label}</dt><dd>${escapeHtml(value || 'Not supplied')}</dd></div>`).join('')}</dl>`,
    total = () => unit === null ? 0 : Math.round(unit * Number(el('quantity').value || 0) * 100) / 100;
  const fees = () => {
    const amount = total();
    content.querySelector('[data-rp-total]').textContent = moneyWhole(amount);
    content.querySelector('[data-rp-fees]').innerHTML = details([['Service Amount', unit === null ? 'Not supplied' : moneyWhole(unit)], ['Quantity', el('quantity').value], ['Subtotal', moneyWhole(amount)], ['Discount', '₦0'], ['Total Amount', moneyWhole(amount)]]);
  };
  const recent = () => {
    const rows = [...drafts, ...payments.slice(0, 5)].slice(0, 5);
    content.querySelector('[data-rp-recent]').innerHTML = `<div class="table-wrap"><table class="data-table finance-data-table record-recent-table"><thead><tr><th>Date & Time</th><th>Patient</th><th>Channel</th><th>Amount (₦)</th><th>Reference</th><th>Status</th></tr></thead><tbody>${rows.map(i => `<tr><td>${escapeHtml(i.created_at || i.confirmed_at || 'Not supplied')}</td><td>${escapeHtml(i.patient_name || i.patient || 'Not supplied')}</td><td>${escapeHtml(i.channel)}</td><td>${moneyWhole(i.amount)}</td><td>${escapeHtml(i.reference)}</td><td>${escapeHtml(i.status)}</td></tr>`).join('') || '<tr><td colspan="6" class="finance-empty">No recent payments.</td></tr>'}</tbody></table></div>`;
  };
  const clearReceipt = () => {
    receipt = null;
    content.querySelector('[data-rp-receipt-card]').hidden = true;
  };
  const pickPatient = index => {
    patient = patients[index];
    el('patient_name').value = fullName(patient);
    el('phone').value = patient.phone || '';
    el('dob').value = patient.date_of_birth || '';
    el('gender').value = patient.sex || '';
    el('address').value = patient.address || '';
    el('next_of_kin').value = patient.emergency_contact || '';
    el('kin_phone').value = patient.next_of_kin_phone || '';
    el('patient_query').value = patient.patient_id;
    content.querySelector('[data-rp-results]').innerHTML = '';
    content.querySelector('[data-rp-patient]').innerHTML = details([['Patient ID', patient.patient_id], ['Full Name', fullName(patient)], ['Gender', patient.sex], ['Date of Birth', patient.date_of_birth], ['Phone Number', patient.phone], ['Address', patient.address], ['Emergency Contact', patient.emergency_contact], ['Next of Kin Phone', patient.next_of_kin_phone]]);
    clearReceipt();
  };
  const chooseService = () => {
    service = services.find(i => String(i.id) === el('service').value) || null;
    const time = Date.now(),
      matches = tariffs.filter(t => service && String(t.service) === String(service.id) && t.is_approved && t.currency === 'NGN' && Date.parse(t.effective_from) <= time && (!t.effective_until || Date.parse(t.effective_until) > time)).sort((a, b) => Date.parse(b.effective_from) - Date.parse(a.effective_from));
    unit = matches.length ? Number(matches[0].amount) : null;
    content.querySelector('[data-rp-service]').innerHTML = service ? details([['Service Name', service.name], ['Service Code', service.code], ['Unit Price', unit === null ? 'No single approved current NGN tariff' : moneyWhole(unit)], ['Patient Category', 'Self Pay']]) : '<p class="finance-empty">No service selected.</p>';
    content.querySelector('[data-rp-service-line]').textContent = service ? `${service.name} · ${unit === null ? 'Approved pricing unavailable' : moneyWhole(unit) + ' per unit'} · Self Pay · No discount` : 'No service selected';
    fees();
    clearReceipt();
  };
  root.addEventListener('click', event => {
    if (event.target.closest('[data-rp-search]')) {
      const query = el('patient_query').value.trim().toLowerCase();
      if (!query) {
        content.querySelector('[data-rp-results]').textContent = 'Enter a patient ID, name or phone number.';
        return;
      }
      const matches = patients.map((p, k) => ({
        p,
        k
      })).filter(({
        p
      }) => [p.patient_id, fullName(p), p.phone].join(' ').toLowerCase().includes(query));
      content.querySelector('[data-rp-results]').innerHTML = matches.length ? matches.slice(0, 20).map(({
        p,
        k
      }) => `<button type="button" class="pending-outline" data-rp-patient-index="${k}">${escapeHtml(p.patient_id)} · ${escapeHtml(fullName(p))}</button>`).join('') : 'No matching patients found.';
    }
    const pick = event.target.closest('[data-rp-patient-index]');
    if (pick) pickPatient(Number(pick.dataset.rpPatientIndex));
  });
  form.addEventListener('input', () => {
    delete form.dataset.requestKey;
    delete form.dataset.lastPayment;
    clearReceipt();
  });
  el('department').addEventListener('change', () => {
    el('service').innerHTML = options(services.filter(i => String(i.department) === el('department').value && i.is_active !== false), 'Select service');
    el('service').disabled = !el('department').value;
    el('service').value = '';
    chooseService();
  });
  el('service').addEventListener('change', chooseService);
  el('quantity').addEventListener('input', () => {
    fees();
    clearReceipt();
  });
  el('patient_query').addEventListener('input', () => {
    if (patient && el('patient_query').value !== patient.patient_id) {
      patient = null;
      ['patient_name', 'phone', 'dob', 'gender', 'address', 'next_of_kin', 'kin_phone'].forEach(k => el(k).value = '');
      content.querySelector('[data-rp-patient]').innerHTML = '<p class="finance-empty">Find and select a patient.</p>';
      clearReceipt();
    }
  });
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const message = content.querySelector('[data-rp-message]'),
      amount = total(),
      quantity = Number(el('quantity').value),
      paid = Number(el('paid').value),
      reference = el('reference').value.trim();
    if (!patient || !service || unit === null || !Number.isInteger(quantity) || quantity < 1 || quantity > 100 || !reference || !Number.isFinite(paid) || Math.round(paid * 100) !== Math.round(amount * 100)) {
      message.textContent = 'Select a patient and service with approved pricing, use a whole quantity from 1–100, enter a reference, and match the amount paid to the total.';
      return;
    }
    if (!el('occurred').value || !Number.isFinite(Date.parse(el('occurred').value)) || Date.parse(el('occurred').value) > Date.now() + 60000) {
      message.textContent = 'Enter a valid payment date and time that is not in the future.';
      return;
    }
    {
      const button = form.querySelector('[type=submit]');
      if (button) button.disabled = true;
      try {
        const key = form.dataset.requestKey || (form.dataset.requestKey = crypto.randomUUID());
        const invoice = await api('invoices/', {
          method: 'POST',
          body: JSON.stringify({
            patient: patient.id,
            department: el('department').value,
            items: [{
              service: service.id,
              quantity
            }],
            idempotency_key: key
          })
        });
        const channels = {
          'POS (Card)': 'pos',
          'POS': 'pos',
          'Bank Transfer': 'bank_transfer',
          'Cash': 'cash',
          'Online Payment': 'online'
        };
        const payment = await api('payments/', {
          method: 'POST',
          body: JSON.stringify({
            invoice: invoice.id,
            channel: channels[el('channel').value] || el('channel').value,
            idempotency_key: key,
            submitted_reference: reference,
            reported_paid_at: new Date(el('occurred').value).toISOString(),
            remarks: el('remarks').value.trim()
          })
        });
        message.textContent = `Payment attempt ${payment.reference} recorded. Status: ${payment.status}. Amount due: ${moneyWhole(invoice.outstanding_balance)}. Reference submission does not verify payment; no paid receipt has been issued.`;
        payments.unshift(payment);
        delete form.dataset.requestKey;
        form.dataset.lastPayment = String(payment.id);
        recent();
        let statusControls = root.querySelector('[data-rp-status-controls]');
        if (!statusControls) {
          statusControls = document.createElement('div');
          statusControls.dataset.rpStatusControls = '';
          message.after(statusControls);
        }
        watchPaymentStatus(payment.id, () => root.isConnected && form.dataset.lastPayment === String(payment.id), async result => {
          if (result.error) {
            message.textContent = `Status check unavailable: ${result.error}. Refresh Transactions to check this payment.`;
            return;
          }
          payment.status = result.status;
          recent();
          message.textContent = `Payment ${payment.reference}: ${result.status}. Reference submission is not verification.`;
          if (result.status === 'confirmed') {
            const response = await api(`receipts/?payment=${encodeURIComponent(payment.id)}`),
              official = list(response)[0];
            if (official) {
              content.querySelector('[data-rp-receipt-card]').hidden = false;
              content.querySelector('[data-rp-receipt]').innerHTML = `<p>Official receipt ${escapeHtml(official.receipt_number)} · ${moneyWhole(official.amount)}</p><a class="pending-outline" target="_blank" rel="noopener" href="${escapeHtml('/paypoint/api/v1/')}receipts/${encodeURIComponent(official.id)}/print/">Open official receipt</a>`;
              message.textContent = 'The backend has confirmed payment and issued an official receipt.';
            }
          }
        }, statusControls);
      } catch (error) {
        message.textContent = error.message;
      } finally {
        if (button) button.disabled = false;
      }
      return;
    }
  });
  form.addEventListener('reset', () => {
    patient = service = null;
    unit = null;
    clearReceipt();
    content.querySelector('[data-rp-results]').innerHTML = '';
    content.querySelector('[data-rp-message]').textContent = '';
    content.querySelector('[data-rp-patient]').innerHTML = '<p class="finance-empty">Find and select a patient to view their details.</p>';
    content.querySelector('[data-rp-service]').innerHTML = '<p class="finance-empty">No service selected.</p>';
    content.querySelector('[data-rp-service-line]').textContent = 'No service selected';
    setTimeout(() => {
      el('service').innerHTML = '<option value="">Select department first</option>';
      el('service').disabled = true;
      fees();
    }, 0);
  });
  fees();
  recent();
}
async function legacyDepartmentDesk() {
  const fetchAll = async resource => {
    let data = await api(`${resource}/?page_size=100`),
      items = [...list(data)];
    for (let page = 2; data.next; page++) {
      data = await api(`${resource}/?page_size=100&page=${page}`);
      items.push(...list(data));
    }
    return items;
  };
  const [receipts, payments, invoices, departments, services, tariffs, patientsData] = await Promise.all(['receipts', 'payments', 'invoices', 'departments', 'services', 'tariffs', 'patients'].map(fetchAll)),
    paymentMap = new Map(payments.map(i => [String(i.id), i])),
    invoiceMap = new Map(invoices.map(i => [String(i.id), i]));
  let department = String(departments.find(i => i.is_active !== false)?.id || ''),
    selected = null,
    verified = false,
    tab = 'recent',
    marked = new Set(),
    history = [];
  const delivered = new Set();
  const depName = () => departments.find(i => String(i.id) === department)?.name || 'Not selected',
    inv = r => invoiceMap.get(String(r.invoice)),
    pay = r => paymentMap.get(String(r.payment)),
    receiptDep = r => String(inv(r)?.department || pay(r)?.department_id || departments.find(i => i.name === (r.department || pay(r)?.department))?.id || ''),
    patient = r => patientsData.find(i => String(i.id || i.patient_id) === String(inv(r)?.patient)) || null,
    patientName = r => r.patient_name || pay(r)?.patient_name || [patient(r)?.first_name, patient(r)?.middle_name, patient(r)?.last_name].filter(Boolean).join(' ') || pay(r)?.patient || 'Not supplied',
    patientId = r => r.patient_id || patient(r)?.patient_id || 'Not supplied',
    valid = r => pay(r)?.status === 'confirmed',
    details = entries => `<dl class="record-detail-list">${entries.map(([key, value]) => `<div><dt>${key}</dt><dd>${escapeHtml(value || 'Not supplied')}</dd></div>`).join('')}</dl>`,
    lines = r => inv(r)?.line_items || r.line_items || [],
    date = value => value ? new Date(value).toLocaleString('en-GB', {
      timeZone: 'Africa/Lagos',
      dateStyle: 'medium',
      timeStyle: 'short'
    }) : 'Not supplied';
  content.innerHTML = `<div class="department-desk-page"><header class="overview-preview-brand"><img src="/paypoint/images/hospital%20logo.png" alt="IMSUTH crest"><div><h1>IMSUTH Central Pay Point</h1><p>Imo State Teaching Hospital, Orlu: all payments in one place</p></div><span class="record-preview-label">Department Desk</span></header><nav class="overview-preview-tabs" aria-label="Revenue control shortcuts"><a href="#dashboard-overview-preview">Overview</a><a href="#dashboard-record-payment">Record payment</a><a href="#patients" aria-current="page">Department desk</a><a href="#admin-departments">Departments</a><a href="#admin-services">Services and prices</a><a href="#cash-points">Cash points and orders</a><a href="#alerts">Alerts</a><a href="#users-audit">Users and audit</a></nav><p class="overview-preview-note">${'Receipt checks and service deliveries use the authenticated backend. Only eligible, fully paid services can be delivered.'} <a href="#patient-directory">Open patient directory</a></p><div class="desk-layout"><div class="desk-main"><section class="finance-card"><div class="finance-card-heading"><div><h2>Department Desk</h2><p>Verify patient payments, confirm receipts and review service delivery for this department.</p></div><label class="desk-current">Current Department<select data-desk-department>${departments.filter(i => i.is_active !== false).map(i => `<option value="${escapeHtml(i.id)}">${escapeHtml(i.name)}</option>`).join('')}</select></label></div><form class="desk-search-form" data-desk-search><h3>1. Search / Verify Receipt</h3><p>Verify the payment before providing services.</p><div><label>Receipt No.<input name="receipt" placeholder="Enter receipt number..."></label><label>Patient ID (optional)<input name="patient_id" placeholder="Enter patient ID..."></label><label>Patient Name (optional)<input name="patient_name" placeholder="Enter patient name..."></label><label>Date From<input name="from" type="date"></label><label>Date To<input name="to" type="date"></label><button type="submit" class="pending-verify">Search</button><button type="reset" class="pending-outline">Clear</button></div></form><div class="record-form-message" data-desk-message role="status"></div><div class="desk-search-matches" data-desk-matches></div><section class="desk-receipt-section"><h3>2. Receipt Information</h3><div data-desk-receipt><p class="finance-empty">Search for a receipt or choose one from Quick Receipt Lookup.</p></div></section><section class="desk-service-section"><h3>3. Service Delivery</h3><p>Confirm the services to be provided to the patient.</p><div data-desk-delivery></div><div class="desk-delivery-footer"><label>Service Notes (optional)<textarea data-desk-notes maxlength="500" placeholder="Enter notes about service delivery..."></textarea></label><button type="button" class="teal-button" data-desk-confirm disabled>Confirm Service Delivery${''}</button></div></section></section><section class="finance-card"><h2>Recent Verifications &amp; Service Delivery</h2><div data-desk-history></div></section></div><aside class="desk-aside"><section class="finance-card"><h2>Quick Receipt Lookup</h2><div class="desk-receipt-tabs" role="tablist" aria-label="Receipt lookup"><button type="button" role="tab" aria-selected="true" data-desk-tab="recent">Recent Receipts</button><button type="button" role="tab" aria-selected="false" data-desk-tab="pending">Pending Receipts</button></div><div data-desk-quick></div><a href="#payments-receipts" class="desk-more">View All Receipts →</a></section><section class="finance-card"><h2>Department Services</h2><div data-desk-services></div><a href="#admin-services" class="desk-more">Manage Department Services →</a></section></aside></div><dialog class="pending-detail-dialog desk-receipt-dialog"><div data-desk-dialog></div><form method="dialog"><button class="pending-outline">Close</button></form></dialog></div>`;
  const root = content.querySelector('.department-desk-page'),
    search = content.querySelector('[data-desk-search]'),
    scope = () => receipts.filter(r => receiptDep(r) === department),
    lineKey = index => `${selected?.id}:${index}`,
    message = text => content.querySelector('[data-desk-message]').textContent = text;
  const renderQuick = () => {
    const list = scope().filter(r => tab === 'recent' || !valid(r)).sort((a, b) => String(b.issued_at).localeCompare(String(a.issued_at))).slice(0, 5);
    content.querySelector('[data-desk-quick]').innerHTML = `<div class="table-wrap"><table class="data-table finance-data-table desk-compact-table"><thead><tr><th>Receipt No.</th><th>Patient</th><th>Amount</th><th>Status</th><th>Action</th></tr></thead><tbody>${list.map(r => `<tr><td>${escapeHtml(r.receipt_number)}</td><td>${escapeHtml(patientName(r))}</td><td>${moneyWhole(r.amount)}</td><td><span class="overview-payment-badge ${valid(r) ? 'verified' : 'pending'}">${valid(r) ? 'Verified' : 'Unverified'}</span></td><td><button type="button" class="pending-outline" data-desk-pick="${receipts.indexOf(r)}">View</button></td></tr>`).join('') || '<tr><td colspan="5" class="finance-empty">No matching receipts. Pending payments may not have an official receipt yet.</td></tr>'}</tbody></table></div>`;
  };
  const renderServices = () => {
    const now = Date.now();
    content.querySelector('[data-desk-services]').innerHTML = `<div class="table-wrap"><table class="data-table finance-data-table desk-compact-table"><thead><tr><th>Service</th><th>Unit Price (₦)</th><th>Category</th></tr></thead><tbody>${services.filter(i => String(i.department) === department && i.is_active !== false).map(s => {
      const prices = tariffs.filter(t => String(t.service) === String(s.id) && t.is_approved && t.currency === 'NGN' && Date.parse(t.effective_from) <= now && (!t.effective_until || Date.parse(t.effective_until) > now));
      return `<tr><td>${escapeHtml(s.name)}</td><td>${prices.length === 1 ? moneyWhole(prices[0].amount) : 'Not supplied'}</td><td>${escapeHtml(s.category || 'Not supplied')}</td></tr>`;
    }).join('') || '<tr><td colspan="3" class="finance-empty">No active services in this department.</td></tr>'}</tbody></table></div>`;
  };
  const renderDelivery = () => {
    const items = selected ? lines(selected) : [];
    content.querySelector('[data-desk-delivery]').innerHTML = `<div class="table-wrap"><table class="data-table finance-data-table desk-delivery-table"><thead><tr><th>#</th><th>Service</th><th>Department</th><th>Quantity</th><th>Unit Price (₦)</th><th>Total (₦)</th><th>Status</th><th>Action</th></tr></thead><tbody>${items.map((line, k) => `<tr><td>${k + 1}</td><td>${escapeHtml(line.description)}</td><td>${escapeHtml(depName())}</td><td>${escapeHtml(line.quantity)}</td><td>${Number(line.quantity) > 0 ? moneyWhole(line.unit_amount ?? Number(line.line_total) / Number(line.quantity)) : 'Not supplied'}</td><td>${moneyWhole(line.line_total)}</td><td><span class="overview-payment-badge ${delivered.has(lineKey(k)) ? 'verified' : 'pending'}">${delivered.has(lineKey(k)) ? 'Delivered' : marked.has(k) ? 'Selected' : 'Pending'}</span></td><td><button type="button" class="pending-outline" data-desk-mark="${k}" ${!verified || delivered.has(lineKey(k)) ? 'disabled' : ''}>${marked.has(k) ? 'Undo Selection' : 'Mark as Delivered'}</button></td></tr>`).join('') || '<tr><td colspan="8" class="finance-empty">Select a verified receipt with itemised services.</td></tr>'}</tbody></table></div>`;
    content.querySelector('[data-desk-confirm]').disabled = !verified || !marked.size;
  };
  const renderSelected = () => {
    if (!selected) {
      content.querySelector('[data-desk-receipt]').innerHTML = '<p class="finance-empty">Search for a receipt or choose one from Quick Receipt Lookup.</p>';
      renderDelivery();
      return;
    }
    const p = patient(selected),
      payment = pay(selected);
    content.querySelector('[data-desk-receipt]').innerHTML = `<div class="desk-receipt-grid"><article>${details([['Patient ID', patientId(selected)], ['Full Name', patientName(selected)], ['Gender', p?.sex], ['Date of Birth', p?.date_of_birth], ['Phone Number', p?.phone || selected.phone], ['Address', p?.address]])}</article><article>${details([['Receipt No.', selected.receipt_number], ['Transaction Date', date(payment?.confirmed_at || selected.issued_at)], ['Payment Channel', payment?.channel], ['Reference No.', payment?.reference], ['Amount Paid', moneyWhole(selected.amount)], ['Payment Status', verified ? 'Verified' : 'Unverified'], ['Verified By', payment?.verified_by_name], ['Verified At', date(payment?.confirmed_at)]])}</article><article><div class="desk-verification-banner ${verified ? 'verified' : ''}"><b>${verified ? 'Payment Verified' : 'Payment Not Verified'}</b><p>${verified ? 'This receipt is linked to a confirmed payment.' : 'Do not provide service until the payment is verified.'}</p></div><div class="desk-receipt-buttons"><button type="button" class="pending-outline" data-desk-print ${verified ? '' : 'disabled'}>Print Receipt</button><button type="button" class="pending-outline" data-desk-view>View Receipt</button></div></article></div>`;
    renderDelivery();
  };
  const renderHistory = () => {
    content.querySelector('[data-desk-history]').innerHTML = `<div class="table-wrap"><table class="data-table finance-data-table desk-history-table"><thead><tr><th>Date & Time</th><th>Receipt No.</th><th>Patient Name</th><th>Service</th><th>Amount (₦)</th><th>Verification Status</th><th>Service Status</th><th>Actions</th></tr></thead><tbody>${history.filter(i => i.department === department).slice(0, 5).map(i => `<tr><td>${escapeHtml(i.date)}</td><td>${escapeHtml(i.receipt.receipt_number)}</td><td>${escapeHtml(patientName(i.receipt))}</td><td>${escapeHtml(lines(i.receipt).map(l => l.description).join(', '))}</td><td>${moneyWhole(i.receipt.amount)}</td><td>${i.verified ? 'Verified' : 'Unverified'}</td><td>${i.delivered ? 'Delivered' : 'Not recorded'}</td><td><button type="button" class="pending-outline" data-desk-pick="${receipts.indexOf(i.receipt)}">View</button></td></tr>`).join('') || '<tr><td colspan="8" class="finance-empty">No receipt checks in this page session.</td></tr>'}</tbody></table></div>`;
  };
  let verificationVersion = 0;
  const pick = async index => {
    const r = receipts[index];
    if (!r || receiptDep(r) !== department) {
      message('This receipt is outside the current department.');
      return;
    }
    const version = ++verificationVersion;
    selected = r;
    verified = false;
    marked.clear();
    renderSelected();
    message('Checking receipt...');
    try {
      const check = await api(`department-desk/receipts/${encodeURIComponent(r.receipt_number)}/verify/`, {
        method: 'POST',
        body: '{}'
      });
      if (version !== verificationVersion) return;
      verified = check.eligible_for_delivery === true;
      {
        check.items.forEach((item, k) => {
          if (item.delivered) delivered.add(`${selected.id}:${k}`);
        });
      }
      message(verified ? 'Receipt verified. Review the service details before delivery.' : 'Receipt is not currently valid for service delivery.');
      history.unshift({
        receipt: r,
        department,
        verified,
        date: new Date().toLocaleString('en-GB'),
        delivered: check.items.length > 0 && check.items.every(item => item.delivered)
      });
      renderSelected();
      renderHistory();
    } catch (error) {
      if (version !== verificationVersion) return;
      message(error.message);
      renderSelected();
    }
  };
  search.addEventListener('submit', event => {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(search));
    if (values.from && values.to && values.from > values.to) {
      message('Choose a valid date range.');
      return;
    }
    const number = (values.receipt || '').trim().toLowerCase(),
      id = (values.patient_id || '').trim().toLowerCase(),
      name = (values.patient_name || '').trim().toLowerCase();
    if (!number && !id && !name) {
      message('Enter a receipt number, patient ID or patient name.');
      return;
    }
    verificationVersion++;
    selected = null;
    verified = false;
    marked.clear();
    renderSelected();
    const matches = scope().filter(r => (!number || r.receipt_number.toLowerCase().includes(number)) && (!id || patientId(r).toLowerCase().includes(id)) && (!name || patientName(r).toLowerCase().includes(name)) && (!values.from || String(r.issued_at).slice(0, 10) >= values.from) && (!values.to || String(r.issued_at).slice(0, 10) <= values.to));
    content.querySelector('[data-desk-matches]').innerHTML = matches.map(r => `<button type="button" class="pending-outline" data-desk-pick="${receipts.indexOf(r)}">${escapeHtml(r.receipt_number)} · ${escapeHtml(patientName(r))}</button>`).join('');
    message(matches.length ? `${matches.length} matching receipt(s). Select a result to verify it.` : 'No matching receipt in this department.');
    if (matches.length === 1) pick(receipts.indexOf(matches[0]));
  });
  const clear = () => {
    verificationVersion++;
    selected = null;
    verified = false;
    marked.clear();
    message('');
    content.querySelector('[data-desk-matches]').innerHTML = '';
    content.querySelector('[data-desk-notes]').value = '';
    renderSelected();
  };
  search.addEventListener('reset', clear);
  content.querySelector('[data-desk-department]').addEventListener('change', event => {
    department = event.target.value;
    search.reset();
    clear();
    renderQuick();
    renderServices();
    renderHistory();
  });
  root.addEventListener('click', async event => {
    const t = event.target,
      button = t.closest('[data-desk-pick]');
    if (button) pick(Number(button.dataset.deskPick));
    const tabButton = t.closest('[data-desk-tab]');
    if (tabButton) {
      tab = tabButton.dataset.deskTab;
      root.querySelectorAll('[data-desk-tab]').forEach(b => b.setAttribute('aria-selected', String(b === tabButton)));
      renderQuick();
    }
    const mark = t.closest('[data-desk-mark]');
    if (mark && verified) {
      const k = Number(mark.dataset.deskMark);
      if (delivered.has(lineKey(k))) return;
      marked.has(k) ? marked.delete(k) : marked.add(k);
      renderDelivery();
    }
    if (t.closest('[data-desk-confirm]') && verified && marked.size) {
      {
        const button = t.closest('[data-desk-confirm]');
        button.disabled = true;
        try {
          for (const k of [...marked]) {
            await api(`department-desk/service-items/${lines(selected)[k].id}/deliver/`, {
              method: 'POST',
              body: JSON.stringify({
                receipt: selected.id,
                notes: content.querySelector('[data-desk-notes]').value.trim()
              })
            });
            delivered.add(lineKey(k));
            marked.delete(k);
          }
          message('Service delivery recorded by the server.');
        } catch (error) {
          message(error.message);
        } finally {
          history.filter(i => i.receipt === selected && i.department === department).forEach(i => {
            i.delivered = lines(selected).every((line, k) => delivered.has(lineKey(k)));
          });
          renderDelivery();
          renderHistory();
        }
        return;
      }
    }
    if ((t.closest('[data-desk-view]') || t.closest('[data-desk-print]')) && selected) {
      {
        content.querySelector('[data-desk-dialog]').innerHTML = `<h2>Official Receipt</h2><p>${escapeHtml(selected.receipt_number)}</p><a class="pending-outline" href="${escapeHtml('/paypoint/api/v1/')}receipts/${encodeURIComponent(selected.id)}/print/" target="_blank" rel="noopener">Open official receipt</a>`;
        content.querySelector('dialog').showModal();
        return;
      }
    }
  });
  renderQuick();
  renderServices();
  renderSelected();
  renderHistory();
}
async function revenueDepartments() {
  const [departments, payments, invoices] = [[], [], []];
  const invoiceMap = new Map(invoices.map(i => [String(i.id), i])),
    today = new Date().toLocaleDateString('en-CA', {
      timeZone: 'Africa/Lagos'
    }),
    colours = ['#1687ff', '#00a995', '#ff922c', '#f53883', '#a55bff'];
  let period = 30,
    page = 1,
    search = '',
    state = '',
    sort = 'amount',
    summaries = [],
    filtered = [];
  content.innerHTML = `<div class="revenue-departments-page"><header class="overview-preview-brand"><img src="/paypoint/images/hospital%20logo.png" alt="IMSUTH crest"><div><h1>IMSUTH Central Pay Point</h1><p>Imo State Teaching Hospital, Orlu: all payments in one place</p></div><label>Period<select data-rd-period><option value="30">Last 30 days</option><option value="7">Last 7 days</option><option value="1">Today</option><option value="all">All records</option></select></label></header><nav class="overview-preview-tabs" aria-label="Revenue control shortcuts"><a href="#dashboard-overview-preview">Overview</a><a href="#dashboard-record-payment">Record payment</a><a href="#patients">Department desk</a><a href="#admin-departments" aria-current="page">Departments</a><a href="#admin-services">Services and prices</a><a href="#cash-points">Cash points and orders</a><a href="#alerts">Alerts</a><a href="#users-audit">Users and audit</a></nav><p class="overview-preview-note">${'Department catalogue and recorded payments.'} Collections include confirmed NGN payments linked to a department.</p><div class="rd-layout"><div class="rd-main"><header class="finance-overview-heading"><div><h1>Departments</h1><p>View departmental collections, transactions and performance.</p></div><button type="button" class="pending-verify" data-rd-add>Add Department</button></header><section class="finance-overview-kpis" data-rd-kpis></section><section class="finance-card"><form class="rd-filter-form" data-rd-filters><label>Search Department<input type="search" name="search" placeholder="Search department name..."></label><label>Status<select name="status"><option value="">All Departments</option><option value="active">Active</option><option value="inactive">Inactive</option></select></label><label>Sort By<select name="sort"><option value="amount">Collection Amount</option><option value="name">Department Name</option><option value="transactions">Transactions</option><option value="pending">Pending Amount</option></select></label><button class="pending-verify" type="submit">Apply Filters</button><button class="pending-outline" type="reset">Reset</button></form></section><section class="finance-card"><div data-rd-table></div><div class="pending-pagination"><span data-rd-count aria-live="polite"></span><div data-rd-pages></div></div></section></div><aside class="rd-aside"><section class="finance-card"><h2>Collections by Department</h2><div data-rd-bars></div></section><section class="finance-card"><h2>Department Performance</h2><div class="finance-department-chart" data-rd-performance></div></section><section class="finance-card"><h2>Quick Actions</h2><div class="overview-preview-actions"><button type="button" data-rd-add>Add Department<small>Create new department</small></button><a href="#admin-services">Manage Services<small>Set department services</small></a><a href="#reports-department">View Department Report<small>Detailed revenue report</small></a><a href="#administration">Assign Staff<small>Manage department staff</small></a></div><a class="rd-management-link" href="#department-management">Open department management details</a></section></aside></div><dialog class="pending-detail-dialog rd-dialog"><div data-rd-dialog></div><form method="dialog"><button class="pending-outline">Close</button></form></dialog></div>`;
  const root = content.querySelector('.revenue-departments-page'),
    form = content.querySelector('[data-rd-filters]'),
    dialog = content.querySelector('dialog'),
    open = html => {
      content.querySelector('[data-rd-dialog]').innerHTML = html;
      dialog.showModal();
    };
  const renderTable = () => {
    filtered = summaries.filter(i => !state).sort((a, b) => b.collected - a.collected);
    const pages = Math.max(1, Math.ceil(filtered.length / 10));
    page = Math.min(page, pages);
    content.querySelector('[data-rd-table]').innerHTML = `<div class="table-wrap"><table class="data-table finance-data-table rd-department-table"><thead><tr>${['#', 'Department', 'Total Collection (₦)', 'Transactions', 'Avg. Verified Amount (₦)', 'Pending (₦)', 'Last Transaction', 'Status', 'Actions'].map(label => `<th>${label}</th>`).join('')}</tr></thead><tbody>${filtered.slice((page - 1) * 10, page * 10).map((i, k) => `<tr><td>${(page - 1) * 10 + k + 1}</td><td>${escapeHtml(i.department.name)}</td><td>${moneyWhole(i.collected)}</td><td>${i.count}</td><td>${moneyWhole(i.average)}</td><td class="revenue-failed-amount">${moneyWhole(i.pending)}</td><td>${i.last ? escapeHtml(new Date(i.last).toLocaleString('en-GB', {
      timeZone: 'Africa/Lagos',
      dateStyle: 'medium',
      timeStyle: 'short'
    })) : 'No transactions'}</td><td><span class="overview-payment-badge ${i.department.is_active !== false ? 'verified' : 'failed'}">${i.department.is_active !== false ? 'Active' : 'Inactive'}</span></td><td><button type="button" class="pending-outline" data-rd-view="${escapeHtml(i.department.id)}">View</button></td></tr>`).join('') || '<tr><td colspan="9" class="finance-empty">No departments match these filters.</td></tr>'}</tbody></table></div>`;
    content.querySelector('[data-rd-count]').textContent = `Showing ${filtered.length ? (page - 1) * 10 + 1 : 0} to ${Math.min(page * 10, filtered.length)} of ${filtered.length} departments`;
    content.querySelector('[data-rd-pages]').innerHTML = `<button type="button" data-rd-page="${page - 1}" aria-label="Previous page" ${page === 1 ? 'disabled' : ''}>‹</button>${Array.from({
      length: pages
    }, (_, k) => k + 1).filter(k => k === 1 || k === pages || Math.abs(k - page) <= 1).map(k => `<button type="button" data-rd-page="${k}" ${page === k ? 'aria-current="page"' : ''}>${k}</button>`).join('')}<button type="button" data-rd-page="${page + 1}" aria-label="Next page" ${page === pages ? 'disabled' : ''}>›</button>`;
  };
  let renderVersion = 0;
  form.addEventListener('submit', event => {
    event.preventDefault();
    return;
  });
  form.addEventListener('reset', () => {
    return;
  });
  content.querySelector('[data-rd-period]').addEventListener('change', event => {
    return;
  });
  root.addEventListener('click', event => {
    const t = event.target,
      pager = t.closest('[data-rd-page]');
    if (pager && !pager.disabled) {
      page = Number(pager.dataset.rdPage);
      renderTable();
    }
    const view = t.closest('[data-rd-view]');
    if (view) {
      const item = summaries.find(i => String(i.department.id) === view.dataset.rdView);
      if (item) open(`<h2>${escapeHtml(item.department.name)}</h2><p>${escapeHtml(item.department.code)} · ${item.department.is_active !== false ? 'Active' : 'Inactive'}</p><p>${escapeHtml(item.department.description || 'No description supplied.')}</p><dl class="record-detail-list"><div><dt>Collected</dt><dd>${moneyWhole(item.collected)}</dd></div><div><dt>Transactions</dt><dd>${item.count}</dd></div><div><dt>Pending</dt><dd>${moneyWhole(item.pending)}</dd></div></dl><p><a href="#reports-department">View Department Report</a></p>`);
    }
    if (t.closest('[data-rd-add]')) open(`<h2>Add Department</h2><p>${'Creates a department in the hospital catalogue.'}</p><form class="rd-add-form" data-rd-create><label>Department Code *<input name="code" required maxlength="24"></label><label>Department Name *<input name="name" required maxlength="120"></label><label>Description<textarea name="description" maxlength="1000"></textarea></label><p data-rd-create-message role="status"></p><button type="submit" class="pending-verify">Create Department</button></form>`);
  });
  root.addEventListener('submit', async event => {
    if (!event.target.matches('[data-rd-create]')) return;
    event.preventDefault();
    const create = event.target,
      values = Object.fromEntries(new FormData(create)),
      message = create.querySelector('[data-rd-create-message]'),
      button = create.querySelector('[type="submit"]');
    values.code = values.code.trim().toUpperCase();
    values.name = values.name.trim();
    if (!values.name || !values.code) {
      message.textContent = 'Enter a department code and name.';
      return;
    }
    if (departments.some(d => d.code.toUpperCase() === values.code || d.name.toLowerCase() === values.name.toLowerCase())) {
      message.textContent = 'A department with this code or name already exists.';
      return;
    }
    button.disabled = true;
    try {
      const item = await api('departments/', {
        method: 'POST',
        body: JSON.stringify({
          ...values,
          is_active: true
        })
      });
      await revenueDepartments();
    } catch (error) {
      message.textContent = error.message;
    } finally {
      button.disabled = false;
    }
  });
  await mountDepartmentDirectory(root, escapeHtml, moneyWhole, session.user);
}
async function servicesAndPrices() {
  const fetchAll = async name => {
    let payload = await api(`${name}/?page_size=100`),
      rows = [...list(payload)];
    for (let page = 2; payload.next; page++) {
      payload = await api(`${name}/?page_size=100&page=${page}`);
      rows.push(...list(payload));
    }
    return rows;
  };
  const [services, departments, tariffs] = await Promise.all(['services', 'departments', 'tariffs'].map(fetchAll));
  let department = String(departments.find(i => i.is_active !== false)?.id || ''),
    selected = null,
    search = '',
    filterDepartment = '',
    filterCategory = '',
    filterStatus = 'active',
    page = 1,
    filtered = [],
    saving = false;
  const dep = item => departments.find(i => String(i.id) === String(item.department)),
    category = item => item.category || 'Not supplied',
    current = item => {
      const now = Date.now(),
        matches = tariffs.filter(t => String(t.service) === String(item.id) && t.is_approved && t.currency === 'NGN' && Date.parse(t.effective_from) <= now && (!t.effective_until || Date.parse(t.effective_until) > now));
      return matches.length === 1 ? matches[0] : null;
    },
    details = entries => `<dl class="record-detail-list">${entries.map(([k, v]) => `<div><dt>${k}</dt><dd>${escapeHtml(v || 'Not supplied')}</dd></div>`).join('')}</dl>`;
  content.innerHTML = `<div class="services-prices-page"><header class="overview-preview-brand"><img src="/paypoint/images/hospital%20logo.png" alt="IMSUTH crest"><div><h1>IMSUTH Central Pay Point</h1><p>Imo State Teaching Hospital, Orlu: all payments in one place</p></div><span class="record-preview-label">Service Catalogue</span></header><nav class="overview-preview-tabs" aria-label="Revenue control shortcuts"><a href="#dashboard-overview-preview">Overview</a><a href="#dashboard-record-payment">Record payment</a><a href="#patients">Department desk</a><a href="#admin-departments">Departments</a><a href="#admin-services" aria-current="page">Services and prices</a><a href="#cash-points">Cash points and orders</a><a href="#alerts">Alerts</a><a href="#users-audit">Users and audit</a></nav><p class="overview-preview-note">${'Live service catalogue.'} Standard prices show current approved NGN tariffs. New prices are saved as drafts for tariff approval; NHIS and IMSHIA pricing is not configured.</p><div class="sp-layout"><div class="sp-main"><header class="finance-overview-heading"><div><h1>Services and Prices</h1><p>Manage hospital services and approved tariffs for each department.</p></div><button type="button" class="pending-verify" data-sp-add>Add Service</button></header><section class="finance-overview-kpis" data-sp-kpis></section><section class="finance-card"><form class="sp-filters" data-sp-filters><label>Department<select name="department"><option value="">All Departments</option>${departments.map(i => `<option value="${escapeHtml(i.id)}">${escapeHtml(i.name)}</option>`).join('')}</select></label><label>Service Category<select name="category"><option value="">All Categories</option>${[...new Set(services.map(category))].sort().map(i => `<option>${escapeHtml(i)}</option>`).join('')}</select></label><label>Status<select name="status"><option value="active">Active Services</option><option value="">All Services</option><option value="inactive">Inactive Services</option></select></label><label>Search Service<input type="search" name="search" placeholder="Search service name or code..."></label><button type="submit" class="pending-verify">Search</button><button type="reset" class="pending-outline">Reset</button></form></section><section class="finance-card"><div data-sp-table></div><div class="pending-pagination"><span data-sp-count aria-live="polite"></span><div data-sp-pages></div></div></section></div><aside class="sp-aside"><section class="finance-card"><h2>Department Information</h2><label><span class="sr-only">Department information and service editor department</span><select data-sp-department>${departments.map(i => `<option value="${escapeHtml(i.id)}">${escapeHtml(i.name)}</option>`).join('')}</select></label><div data-sp-department-info></div></section><section class="finance-card"><h2 data-sp-editor-title>Add / Edit Service</h2><form class="sp-editor" data-sp-editor><label>Service Name *<input name="name" required maxlength="160" placeholder="Enter service name..."></label><label>Service Code *<input name="code" required maxlength="32" placeholder="e.g. LAB-001"></label><div class="sp-editor-pair"><label>Category<input name="category" maxlength="80" placeholder="Service category"></label><label>Unit<input name="unit" maxlength="60" placeholder="Per Service"></label></div><div class="sp-editor-pair"><label>Standard Price (₦) *<input type="number" name="price" required min="0.01" step="0.01" placeholder="Enter draft price"></label><label>NHIS Price (₦)<input disabled placeholder="Not configured"></label><label>IMSHIA Price (₦)<input disabled placeholder="Not configured"></label><label>Status<select name="status"><option value="active">Active</option><option value="inactive">Inactive</option></select></label></div><label>Description (optional)<textarea name="description" maxlength="3000" placeholder="Enter service description..."></textarea></label><label>Draft Price Effective From *<input type="datetime-local" name="effective" required></label><label>Price change reason (required for a new price)<textarea name="price_reason" maxlength="2000"></textarea></label><p class="sp-editor-note">Service details can be saved now. Price changes require separate approval in Tariff Management.</p><p class="record-form-message" data-sp-message role="status"></p><div class="sp-editor-actions"><button type="reset" class="pending-outline">Clear Form</button><button type="submit" class="pending-verify">Save Service</button></div><a href="#admin-tariffs">Review tariff versions and approvals →</a></form></section></aside></div></div>`;
  const root = content.querySelector('.services-prices-page'),
    form = content.querySelector('[data-sp-editor]'),
    filters = content.querySelector('[data-sp-filters]'),
    el = name => form.elements.namedItem(name),
    message = text => content.querySelector('[data-sp-message]').textContent = text;
  const showDepartment = () => {
    const item = departments.find(i => String(i.id) === department);
    content.querySelector('[data-sp-department]').value = department;
    content.querySelector('[data-sp-department-info]').innerHTML = item ? `<div class="sp-department-banner"><h3>${escapeHtml(item.name)}</h3><span>Code: ${escapeHtml(item.code)}</span><span class="overview-payment-badge ${item.is_active !== false ? 'verified' : 'failed'}">${item.is_active !== false ? 'Active' : 'Inactive'}</span></div>${details([['Head of Department', item.head_name], ['Phone Number', item.phone], ['Email', item.email], ['Location', item.location], ['Description', item.description]])}` : '<p class="finance-empty">Select a department before creating a service.</p>';
  };
  const effectiveNow = () => {
    const now = new Date();
    return new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
  };
  const clear = () => {
    selected = null;
    ['name', 'code', 'category', 'unit', 'price', 'description', 'price_reason'].forEach(k => el(k).value = '');
    el('status').value = 'active';
    el('effective').value = effectiveNow();
    message('');
    content.querySelector('[data-sp-editor-title]').textContent = 'Add Service';
  };
  const edit = item => {
    selected = item;
    department = String(item.department);
    showDepartment();
    el('name').value = item.name;
    el('code').value = item.code;
    el('category').value = item.category || '';
    el('unit').value = item.unit || '';
    el('price_reason').value = '';
    el('price').value = current(item)?.amount || '';
    el('description').value = item.description || '';
    el('status').value = item.is_active !== false ? 'active' : 'inactive';
    el('effective').value = effectiveNow();
    content.querySelector('[data-sp-editor-title]').textContent = `Edit Service · ${item.code}`;
    message('Editing service details. Changing the standard price creates an unapproved tariff version.');
    el('name').focus();
  };
  const render = () => {
    const active = services.filter(i => i.is_active !== false).length,
      metric = (label, value, note, icon, colour) => `<article><i class="${colour}">${icon}</i><div><span>${label}</span><strong>${escapeHtml(value)}</strong><small>${note}</small></div></article>`;
    content.querySelector('[data-sp-kpis]').innerHTML = metric('Total Services', services.length, 'Across all departments', '⚙', 'blue') + metric('Active Departments', departments.filter(d => d.is_active !== false && services.some(s => String(s.department) === String(d.id))).length, 'With services configured', '▤', 'blue') + metric('Active Services', active, `${services.length ? (active / services.length * 100).toFixed(1) : 0}% of total`, '▤', 'green') + metric('Inactive Services', services.length - active, `${services.length ? ((services.length - active) / services.length * 100).toFixed(1) : 0}% of total`, '!', 'orange');
    filtered = services.filter(i => (!filterDepartment || String(i.department) === filterDepartment) && (!filterCategory || category(i) === filterCategory) && (!filterStatus || (filterStatus === 'active' ? i.is_active !== false : i.is_active === false)) && (!search || [i.name, i.code].join(' ').toLowerCase().includes(search)));
    const pages = Math.max(1, Math.ceil(filtered.length / 10));
    page = Math.min(page, pages);
    content.querySelector('[data-sp-table]').innerHTML = `<div class="table-wrap"><table class="data-table finance-data-table sp-table"><thead><tr>${['#', 'Service Name', 'Department', 'Category', 'Standard Price (₦)', 'NHIS Price (₦)', 'IMSHIA Price (₦)', 'Status', 'Actions'].map(t => `<th>${t}</th>`).join('')}</tr></thead><tbody>${filtered.slice((page - 1) * 10, page * 10).map((i, k) => `<tr><td>${(page - 1) * 10 + k + 1}</td><td>${escapeHtml(i.name)}</td><td>${escapeHtml(dep(i)?.name || 'Not supplied')}</td><td>${escapeHtml(category(i))}</td><td>${current(i) ? moneyWhole(current(i).amount) : 'No approved tariff'}</td><td>Not configured</td><td>Not configured</td><td><span class="overview-payment-badge ${i.is_active !== false ? 'verified' : 'failed'}">${i.is_active !== false ? 'Active' : 'Inactive'}</span></td><td><button type="button" class="pending-outline" data-sp-edit="${escapeHtml(i.id)}">Edit</button></td></tr>`).join('') || '<tr><td colspan="9" class="finance-empty">No services match these filters.</td></tr>'}</tbody></table></div>`;
    content.querySelector('[data-sp-count]').textContent = `Showing ${filtered.length ? (page - 1) * 10 + 1 : 0} to ${Math.min(page * 10, filtered.length)} of ${filtered.length} services`;
    content.querySelector('[data-sp-pages]').innerHTML = `<button type="button" data-sp-page="${page - 1}" aria-label="Previous page" ${page === 1 ? 'disabled' : ''}>‹</button>${Array.from({
      length: pages
    }, (_, k) => k + 1).filter(k => k === 1 || k === pages || Math.abs(k - page) <= 1).map(k => `<button type="button" data-sp-page="${k}" ${page === k ? 'aria-current="page"' : ''}>${k}</button>`).join('')}<button type="button" data-sp-page="${page + 1}" aria-label="Next page" ${page === pages ? 'disabled' : ''}>›</button>`;
  };
  filters.addEventListener('submit', event => {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(filters));
    filterDepartment = values.department;
    filterCategory = values.category;
    filterStatus = values.status;
    search = values.search.trim().toLowerCase();
    page = 1;
    render();
  });
  filters.addEventListener('reset', () => {
    filterDepartment = filterCategory = search = '';
    filterStatus = 'active';
    page = 1;
    render();
  });
  content.querySelector('[data-sp-department]').addEventListener('change', event => {
    if (saving) return;
    department = event.target.value;
    clear();
    showDepartment();
  });
  root.addEventListener('click', event => {
    const t = event.target,
      pager = t.closest('[data-sp-page]');
    if (pager && !pager.disabled) {
      page = Number(pager.dataset.spPage);
      render();
    }
    const button = t.closest('[data-sp-edit]');
    if (button && !saving) {
      const item = services.find(i => String(i.id) === button.dataset.spEdit);
      if (item) edit(item);
    }
    if (t.closest('[data-sp-add]') && !saving) {
      clear();
      el('name').focus();
    }
  });
  form.addEventListener('reset', event => {
    event.preventDefault();
    if (!saving) clear();
  });
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (saving) return;
    const values = Object.fromEntries(new FormData(form)),
      price = Number(values.price),
      effective = Date.parse(values.effective),
      name = values.name.trim(),
      code = values.code.trim().toUpperCase();
    if (!name || !code || !department || !Number.isFinite(price) || price <= 0 || price >= 1e17 || Math.abs(price * 100 - Math.round(price * 100)) > 0.00001 || !Number.isFinite(effective)) {
      message('Enter a service name, code, department, positive price with up to two decimal places, and a valid effective date.');
      return;
    }
    if (services.some(i => i !== selected && (i.code.toUpperCase() === code || String(i.department) === department && i.name.toLowerCase() === name.toLowerCase()))) {
      message('A service with this code or department/name already exists.');
      return;
    }
    saving = true;
    const button = form.querySelector('[type="submit"]');
    button.disabled = true;
    let saved = false;
    try {
      const oldPrice = selected ? current(selected)?.amount : null,
        body = {
          name,
          code,
          department,
          category: values.category || '',
          unit: values.unit || '',
          description: values.description,
          is_active: values.status === 'active'
        };
      let item;
      {
        item = await api(selected ? `services/${selected.id}/` : 'services/', {
          method: selected ? 'PATCH' : 'POST',
          body: JSON.stringify(body)
        });
        if (selected) {
          Object.assign(selected, item);
          item = selected;
        } else services.push(item);
      }
      selected = item;
      saved = true;
      const changed = oldPrice === null || Math.round(Number(oldPrice) * 100) !== Math.round(price * 100);
      if (changed && !false && (!values.price_reason?.trim() || effective <= Date.now())) throw new Error('Enter a price-change reason and future effective date. Service details have been saved; pricing is unchanged.');
      if (changed) {
        const draft = {
          service: item.id,
          amount: price.toFixed(2),
          currency: 'NGN',
          effective_from: new Date(effective).toISOString(),
          is_approved: false
        };
        await api(`services/${item.id}/tariff-proposals/`, {
          method: 'POST',
          body: JSON.stringify({
            amount: draft.amount,
            effective_from: draft.effective_from,
            reason: values.price_reason.trim()
          })
        });
      }
      render();
      message(changed ? 'Service saved. The new standard price awaits independent tariff approval; approved pricing remains in use.' : 'Service details saved. Approved pricing is unchanged.');
      content.querySelector('[data-sp-editor-title]').textContent = `Edit Service · ${item.code}`;
    } catch (error) {
      message(`${saved ? 'Service details were saved, but the price draft was not saved. ' : ''}${error.message}`);
    } finally {
      saving = false;
      button.disabled = false;
    }
  });
  clear();
  showDepartment();
  render();
  await mountTariffProposals(root, session.user, servicesAndPrices, escapeHtml, moneyWhole);
}
async function cashPointsAndOrders() {
  const today = new Date().toLocaleDateString('en-CA', {
      timeZone: 'Africa/Lagos'
    }),
    user = session.user.full_name || session.user.username || 'Signed-in staff',
    colours = ['#1687ff', '#00ac83', '#ff922c', '#9955ff', '#f53b7b', '#94a7ce'];
  let period = 30;
  const daysAgo = n => new Date(Date.parse(today) - n * 86400000).toISOString().slice(0, 10);
  const loadAll = async name => {
    let data,
      rows = [],
      page = 1;
    do {
      data = await api(`${name}/?period=all&page=${page++}`);
      rows.push(...list(data));
    } while (data.next);
    return rows;
  };
  const liveLimits = list(await api('cash-orders/approval-limits/'));
  const points = (await loadAll('cash-points')).map(p => ({
    ...p,
    department: p.department_name || p.department,
    officer: p.assigned_officer_name || String(p.assigned_officer),
    limit: Number(p.daily_limit),
    collected: null,
    active: p.is_active
  }));
  const orders = (await loadAll('cash-orders')).map(o => ({
    ...o,
    point: o.cash_point,
    amount: Number(o.amount),
    requested_by: o.requested_by_name || o.requested_by,
    authorized_by: o.decided_by_name || 'Not yet approved'
  }));
  await Promise.all(points.map(async p => {
    const value = await api(`cash-points/${p.id}/summary/?period=today`);
    p.collected = Number(value.collections);
  }));
  const orderDay = i => new Date(i.created_at).toLocaleDateString('en-CA', {
      timeZone: 'Africa/Lagos'
    }),
    point = id => points.find(p => p.id === id),
    scope = () => orders.filter(i => period === 'all' || orderDay(i) >= daysAgo(period - 1)),
    sum = items => items.reduce((n, i) => n + i.amount, 0),
    detail = entries => `<dl class="record-detail-list">${entries.map(([label, value]) => `<div><dt>${label}</dt><dd>${escapeHtml(value || 'Not supplied')}</dd></div>`).join('')}</dl>`;
  content.innerHTML = `<div class="cash-points-page"><header class="overview-preview-brand"><img src="/paypoint/images/hospital%20logo.png" alt="IMSUTH crest"><div><h1>IMSUTH Central Pay Point</h1><p>Imo State Teaching Hospital, Orlu: all payments in one place</p></div><label>Period<select data-cp-period><option value="30">Last 30 days</option><option value="7">Last 7 days</option><option value="1">Today</option><option value="all">All records</option></select></label></header><nav class="overview-preview-tabs" aria-label="Revenue control shortcuts"><a href="#dashboard-overview-preview">Overview</a><a href="#dashboard-record-payment">Record payment</a><a href="#patients">Department desk</a><a href="#admin-departments">Departments</a><a href="#admin-services">Services and prices</a><a href="#cash-points" aria-current="page">Cash points and orders</a><a href="#alerts">Alerts</a><a href="#users-audit">Users and audit</a></nav><p class="overview-preview-note">${'Authenticated cash authorizations. Approval does not collect cash or confirm a bank deposit. Point collections require explicit verified-payment evidence.'}</p><div class="cp-layout"><div class="cp-main"><header class="finance-overview-heading"><div><h1>Cash Points and Orders</h1><p>Manage hospital cash collection points and standing orders. Cash requests require authorized approval.</p></div></header><section class="finance-overview-kpis" data-cp-kpis></section><section class="finance-card"><div class="finance-card-heading"><h2>Cash Points</h2><button type="button" class="pending-verify" data-cp-add>Add Cash Point</button></div><div data-cp-points></div></section><section class="finance-card"><div class="finance-card-heading"><h2>Recent Cash Orders</h2><button type="button" class="help-link" data-cp-all>View All</button></div><div data-cp-orders></div></section></div><aside class="cp-aside"><section class="finance-card"><h2>Create Cash Standing Order</h2><form class="cp-order-form" data-cp-request><label>Cash Point *<select name="point" data-cp-select required><option value="">Select cash point</option></select></label><div class="cp-form-pair"><label>Requested Amount (₦) *<input name="amount" type="number" min="0.01" step="0.01" required placeholder="Enter amount"></label><label>Purpose *<input name="purpose" required maxlength="160" placeholder="Enter purpose"></label></div><label>Requested By<input value="${escapeHtml(user)}" readonly></label><label>Description (optional)<textarea name="description" maxlength="1000" placeholder="Enter additional details..."></textarea></label><p class="record-form-message" data-cp-message role="status"></p><div class="cp-form-actions"><button type="reset" class="pending-outline">Clear Form</button><button type="submit" class="pending-verify" >${'Submit for Approval'}</button></div></form></section><section class="finance-card"><h2>${'Approval Limits'}</h2><div data-cp-limits></div></section><section class="finance-card"><h2>Today's Cash Collection</h2><div class="finance-department-chart" data-cp-collections></div></section></aside></div><dialog class="pending-detail-dialog cp-dialog"><div data-cp-dialog></div><form method="dialog"><button class="pending-outline">Close</button></form></dialog></div>`;
  const root = content.querySelector('.cash-points-page'),
    form = content.querySelector('[data-cp-request]'),
    dialog = content.querySelector('dialog'),
    open = html => {
      content.querySelector('[data-cp-dialog]').innerHTML = html;
      dialog.showModal();
    };
  const ordersTable = items => `<div class="table-wrap"><table class="data-table finance-data-table cp-orders-table"><thead><tr>${['Order No.', 'Cash Point', 'Requested By', 'Authorized By', 'Amount (₦)', 'Purpose / Description', 'Status', 'Created At', 'Actions'].map(t => `<th>${t}</th>`).join('')}</tr></thead><tbody>${items.map(i => `<tr><td>${escapeHtml(i.id)}</td><td>${escapeHtml(point(i.point)?.name || 'Not supplied')}</td><td>${escapeHtml(i.requested_by)}</td><td>${escapeHtml(i.status === 'pending' ? 'Not yet approved' : i.authorized_by)}</td><td>${moneyWhole(i.amount)}</td><td>${escapeHtml(i.purpose)}</td><td><span class="overview-payment-badge ${i.status === 'approved' ? 'verified' : i.status === 'rejected' ? 'failed' : 'pending'}">${i.status === 'approved' ? 'Approved' : i.status === 'rejected' ? 'Rejected' : 'Pending'}</span></td><td>${escapeHtml(new Date(i.created_at).toLocaleString('en-GB', {
    timeZone: 'Africa/Lagos',
    dateStyle: 'medium',
    timeStyle: 'short'
  }))}</td><td><button type="button" class="pending-outline" data-cp-order="${escapeHtml(i.id)}">View</button></td></tr>`).join('') || '<tr><td colspan="9" class="finance-empty">No cash orders available.</td></tr>'}</tbody></table></div>`;
  const render = () => {
    const scoped = scope(),
      pending = scoped.filter(i => i.status === 'pending'),
      metric = (label, value, note, icon, colour) => `<article><i class="${colour}">${icon}</i><div><span>${label}</span><strong>${escapeHtml(value)}</strong><small>${note}</small></div></article>`;
    content.querySelector('[data-cp-kpis]').innerHTML = metric('Total Cash Points', points.filter(i => i.active).length, 'Active collection points', '▤', 'blue') + metric('Total Cash Orders', scoped.length, 'Selected period', '▤', 'purple') + metric('Approved Amount', moneyWhole(sum(scoped.filter(i => i.status === 'approved'))), 'Authorized orders; not cash collected', '₦', 'green') + metric('Pending Approval', pending.length, moneyWhole(sum(pending)), '◷', 'orange');
    content.querySelector('[data-cp-points]').innerHTML = `<div class="table-wrap"><table class="data-table finance-data-table cp-points-table"><thead><tr>${['#', 'Cash Point Name', 'Location', 'Department', 'Assigned Officer', 'Daily Limit (₦)', "Today's Collection (₦)", 'Status', 'Actions'].map(t => `<th>${t}</th>`).join('')}</tr></thead><tbody>${points.map((i, k) => `<tr><td>${k + 1}</td><td>${escapeHtml(i.name)}</td><td>${escapeHtml(i.location)}</td><td>${escapeHtml(i.department)}</td><td>${escapeHtml(i.officer)}</td><td>${moneyWhole(i.limit)}</td><td>${i.collected === null ? 'Unavailable' : moneyWhole(i.collected)}</td><td><span class="overview-payment-badge ${i.active ? 'verified' : 'failed'}">${i.active ? 'Active' : 'Inactive'}</span></td><td><button type="button" class="pending-outline" data-cp-point="${i.id}">View</button></td></tr>`).join('') || '<tr><td colspan="9" class="finance-empty">Cash point data is not connected.</td></tr>'}</tbody></table></div>`;
    content.querySelector('[data-cp-orders]').innerHTML = ordersTable(scoped.slice(0, 5));
    const selected = form.elements.namedItem('point').value;
    content.querySelector('[data-cp-select]').innerHTML = '<option value="">Select cash point</option>' + points.filter(i => i.active).map(i => `<option value="${i.id}">${escapeHtml(i.name)}</option>`).join('');
    form.elements.namedItem('point').value = points.some(i => i.id === selected) ? selected : '';
    content.querySelector('[data-cp-limits]').innerHTML = `<ul>${liveLimits.map(l => `<li>${escapeHtml(l.role)}: ${moneyWhole(l.amount)} · ${escapeHtml(l.policy_reference)}</li>`).join('') || '<li>No approved policy limits configured.</li>'}</ul>`;
    const ranked = points.filter(i => i.collected > 0).sort((a, b) => b.collected - a.collected),
      total = ranked.reduce((n, i) => n + i.collected, 0);
    let angle = 0;
    const stops = ranked.map((i, k) => {
      const start = angle;
      angle += total ? i.collected / total * 100 : 0;
      return `${colours[k % 6]} ${start}% ${angle}%`;
    });
    content.querySelector('[data-cp-collections]').innerHTML = `<div class="finance-donut" role="img" aria-label="${'Verified cash collection by point'}" data-chart-background="${total ? `conic-gradient(${stops.join(',')})` : '#e8eef5'}"><div><strong>${moneyWhole(total)}</strong><span>${'Verified Cash'}</span></div></div><div class="finance-department-legend">${ranked.map((i, k) => `<div><span data-chart-colour="${colours[k % 6]}">${escapeHtml(i.department)}</span><b>${i.collected === null ? 'Unavailable' : moneyWhole(i.collected)} (${(i.collected / total * 100).toFixed(1)}%)</b></div>`).join('') || '<p class="finance-empty">No collection data.</p>'}</div>`;
  };
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(form)),
      cashPoint = point(values.point),
      amount = Number(values.amount),
      purpose = (values.purpose || '').trim(),
      message = content.querySelector('[data-cp-message]');
    if (!cashPoint?.active || !Number.isFinite(amount) || amount <= 0 || amount > cashPoint.limit || Math.abs(amount * 100 - Math.round(amount * 100)) > 0.00001 || purpose.length < 3) {
      message.textContent = 'Choose an active cash point, enter a positive amount within its daily limit with up to two decimal places, and a purpose of at least three characters.';
      return;
    }
    const reserved = sum(orders.filter(i => i.point === cashPoint.id && i.status !== 'rejected' && orderDay(i) === today));
    if (reserved + amount > cashPoint.limit) {
      message.textContent = 'This request would exceed the daily limit after today’s existing orders.';
      return;
    }
    {
      const button = form.querySelector('[type=submit]');
      if (button) button.disabled = true;
      try {
        const key = form.dataset.requestKey || (form.dataset.requestKey = crypto.randomUUID());
        await api('cash-orders/', {
          method: 'POST',
          body: JSON.stringify({
            cash_point: cashPoint.id,
            amount: values.amount,
            purpose,
            description: values.description || '',
            idempotency_key: key
          })
        });
        await cashPointsAndOrders();
      } catch (error) {
        message.textContent = error.message;
      } finally {
        if (button) button.disabled = false;
      }
      return;
    }
  });
  form.addEventListener('reset', () => {
    content.querySelector('[data-cp-message]').textContent = '';
  });
  content.querySelector('[data-cp-period]').addEventListener('change', event => {
    period = event.target.value === 'all' ? 'all' : Number(event.target.value);
    render();
  });
  root.addEventListener('click', event => {
    const t = event.target,
      pointButton = t.closest('[data-cp-point]'),
      orderButton = t.closest('[data-cp-order]');
    if (pointButton) {
      const i = point(pointButton.dataset.cpPoint);
      if (i) open(`<h2>${escapeHtml(i.name)}</h2>${detail([['Location', i.location], ['Department', i.department], ['Assigned Officer', i.officer], ['Daily Limit', moneyWhole(i.limit)], ['Today’s Verified Collection', moneyWhole(i.collected)]])}<p>Collection evidence and bank deposit are recorded separately.</p>`);
    }
    if (orderButton) {
      const i = orders.find(i => i.id === orderButton.dataset.cpOrder);
      if (i) open(`<h2>${escapeHtml(i.id)}</h2>${detail([['Cash Point', point(i.point)?.name], ['Requested By', i.requested_by], ['Amount', moneyWhole(i.amount)], ['Purpose', i.purpose], ['Description', i.description], ['Status', i.status], ['Authorized By', i.authorized_by]])}<p>${'Authorization record only.'} No cash was paid or moved.</p>${i.status === 'pending' ? `<form data-cp-decision="${escapeHtml(i.id)}"><label>Decision notes<textarea name="notes" required minlength="5" maxlength="2000"></textarea></label><select name="decision"><option value="approve">Approve</option><option value="reject">Reject</option></select><button class="pending-verify">Submit Decision</button><p role="status"></p></form>` : ''}`);
    }
    if (t.closest('[data-cp-all]')) open(`<h2>All Cash Orders · Selected Period</h2>${ordersTable(scope())}`);
  });
  content.querySelector('[data-cp-add]').addEventListener('click', async () => {
    try {
      const [departments, officers] = await Promise.all([loadAll('departments'), api('cash-points/officers/')]);
      open(`<h2>Add Cash Point</h2><form data-cp-create class="cp-order-form"><label>Name<input name="name" required maxlength="120"></label><label>Location<input name="location" required maxlength="200"></label><label>Department<select name="department" required>${departments.map(d => `<option value="${escapeHtml(d.id)}">${escapeHtml(d.name)}</option>`).join('')}</select></label><label>Assigned Officer<select name="officer" required>${officers.map(o => `<option value="${o.id}">${escapeHtml(o.name)}</option>`).join('')}</select></label><label>Approved Daily Limit (₦)<input name="limit" type="number" required min="0.01" step="0.01"></label><p>The assigned officer must belong to the selected department. Use an approved hospital limit.</p><p data-cp-create-message role="status"></p><button class="pending-verify">Create Cash Point</button></form>`);
    } catch (error) {
      open(`<p>${escapeHtml(error.message)}</p>`);
    }
  });
  root.addEventListener('submit', async event => {
    if (event.target.matches('[data-cp-decision]')) {
      event.preventDefault();
      const form = event.target,
        values = Object.fromEntries(new FormData(form));
      try {
        await api(`cash-orders/${form.dataset.cpDecision}/${values.decision}/`, {
          method: 'POST',
          body: JSON.stringify({
            notes: values.notes
          })
        });
        await cashPointsAndOrders();
      } catch (error) {
        form.querySelector('[role=status]').textContent = error.message;
      }
      return;
    }
    if (!event.target.matches('[data-cp-create]')) return;
    event.preventDefault();
    {
      const form = event.target,
        values = Object.fromEntries(new FormData(form)),
        button = form.querySelector('button');
      button.disabled = true;
      try {
        await api('cash-points/', {
          method: 'POST',
          body: JSON.stringify({
            name: values.name,
            location: values.location,
            department: values.department,
            assigned_officer: values.officer,
            daily_limit: values.limit,
            is_active: true
          })
        });
        await cashPointsAndOrders();
      } catch (error) {
        form.querySelector('[data-cp-create-message]').textContent = error.message;
        button.disabled = false;
      }
      return;
    }
  });
  render();
  mountCashEvidence(root, cashPointsAndOrders, escapeHtml, moneyWhole);
}
async function alertsPage() {
  const esc = escapeHtml;
  const types = ['Unmatched Payment', 'Suspicious Activity', 'Receipt Discrepancy', 'Cash Limit Exceeded', 'Duplicate Payment', 'Unusual Pattern', 'Cancelled Transaction', 'Missing Reference', 'Service Price Change', 'Multiple Receipts', 'Unmatched Payment', 'Receipt Discrepancy'];
  const descriptions = ['Payment received but no matching receipt found', 'Multiple payments from the same card', 'Amount mismatch in receipt', 'Cash point exceeded daily limit', 'Possible duplicate transaction', 'High volume of small payments', 'Payment cancelled after service delivery', 'Payment without reference number', 'Service used with outdated price', 'Patient has multiple active receipts'];
  const today = new Date().toLocaleDateString('en-CA', {
      timeZone: 'Africa/Lagos'
    }),
    dateAgo = n => {
      const d = new Date(today + 'T12:00:00Z');
      d.setUTCDate(d.getUTCDate() - n);
      return d.toISOString().slice(0, 10);
    };
  const fetchAll = async resource => {
    let data,
      items = [],
      page = 1;
    do {
      data = await api(`${resource}/?period=all&page=${page++}`);
      items.push(...list(data));
    } while (data.next);
    return items;
  };
  const liveAssignees = await api('alerts/assignees/').catch(error => {
    if (error.status === 403) return [];
    throw error;
  });
  const mapAlert = r => ({
    ...r,
    type: r.alert_type,
    date: String(r.created_at).slice(0, 10),
    time: new Date(r.created_at).toLocaleTimeString('en-GB', {
      timeZone: 'Africa/Lagos',
      hour: '2-digit',
      minute: '2-digit'
    }),
    related: r.related_id,
    amount: null,
    channel: 'Not recorded',
    assigned: r.assigned_to ? String(r.assigned_to) : '',
    notes: r.resolution_notes || ''
  });
  const rows = (await fetchAll('alerts')).map(mapAlert);
  let selected = rows[0]?.id,
    page = 1,
    applied = {
      search: '',
      severity: '',
      type: '',
      status: '',
      from: dateAgo(29),
      to: today
    };
  const label = v => ({
      in_review: 'In Review',
      open: 'Open',
      resolved: 'Resolved',
      critical: 'Critical',
      high: 'High',
      medium: 'Medium',
      low: 'Low'
    })[v] || v,
    colours = ['#ff354d', '#ff921e', '#1978ff', '#00b498', '#924cff', '#9ca8ca'];
  content.innerHTML = `<div class="alerts-page"><header class="overview-preview-brand"><img src="/paypoint/images/hospital%20logo.png" alt="IMSUTH crest"><div><h1>IMSUTH Central Pay Point</h1><p>Imo State Teaching Hospital, Orlu: all payments in one place</p></div><label>Period<select data-al-period><option value="30">Last 30 days</option><option value="7">Last 7 days</option><option value="1">Today</option></select></label></header><nav class="overview-preview-tabs" aria-label="Revenue control shortcuts"><a href="#dashboard-overview-preview">Overview</a><a href="#dashboard-record-payment">Record payment</a><a href="#patients">Department desk</a><a href="#admin-departments">Departments</a><a href="#admin-services">Services and prices</a><a href="#cash-points">Cash points and orders</a><a href="#alerts" aria-current="page">Alerts</a><a href="#users-audit">Users and audit</a></nav><p class="overview-preview-note">${'Authenticated alert records. Assignment and resolution are audited; resolving an alert does not verify a payment.'}</p><div class="al-layout"><main><header class="finance-overview-heading"><div><h1>Alerts</h1><p>Monitor and manage payment exceptions, suspicious activities and other important notifications.</p></div><button class="pending-outline" data-al-settings ${'disabled title="Alert notification preferences are not connected to a live configuration endpoint."'}>⚙ Alert Settings</button></header><section class="finance-overview-kpis" data-al-kpis></section><form class="finance-card al-filters" data-al-filters><label>Search alerts<input name="search" placeholder="Search alerts..."></label><label>Severity<select name="severity"><option value="">All Severities</option>${['critical', 'high', 'medium', 'low'].map(v => `<option value="${v}">${label(v)}</option>`).join('')}</select></label><label>Alert Type<select name="type"><option value="">All Types</option>${[...new Set(types)].map(v => `<option>${v}</option>`).join('')}</select></label><label>Status<select name="status"><option value="">All Statuses</option><option value="open">Open</option><option value="in_review">In Review</option><option value="resolved">Resolved</option></select></label><label>From<input name="from" type="date" value="${applied.from}"></label><label>To<input name="to" type="date" value="${today}"></label><button class="pending-verify">Apply Filters</button><button type="reset" class="pending-outline">Reset</button><p data-al-filter-message role="status"></p></form><section class="finance-card"><div data-al-table></div><div class="pending-pagination"><span data-al-count aria-live="polite"></span><div data-al-pages></div></div></section><div class="al-charts"><section class="finance-card"><h2>Alerts by Type</h2><div data-al-types></div></section><section class="finance-card"><h2>Alerts by Severity</h2><div data-al-severities></div></section><section class="finance-card"><h2>Alert Status</h2><div data-al-statuses></div></section></div></main><aside class="finance-card al-detail" data-al-detail></aside></div></div>`;
  const root = content.querySelector('.alerts-page'),
    q = s => root.querySelector(s),
    badge = v => `<span class="al-badge al-${esc(v)}">${esc(label(v))}</span>`;
  const matching = () => rows.filter(r => (!applied.search || [r.id, r.type, r.description, r.related].join(' ').toLowerCase().includes(applied.search.toLowerCase())) && (!applied.severity || r.severity === applied.severity) && (!applied.type || r.type === applied.type) && (!applied.status || r.status === applied.status) && (!applied.from || r.date >= applied.from) && (!applied.to || r.date <= applied.to));
  function chart(selector, items, total) {
    let start = 0;
    const stops = items.map(([name, n], i) => {
      const end = start + (total ? n / total * 100 : 0),
        s = `${colours[i % colours.length]} ${start}% ${end}%`;
      start = end;
      return s;
    });
    q(selector).innerHTML = total ? `<div class="al-donut-layout"><div class="finance-donut" data-chart-background="conic-gradient(${stops.join(',')})"><div><strong>${total}</strong><span>Total Alerts</span></div></div><div class="al-legend">${items.map(([name, n], i) => `<div><i data-chart-background="${colours[i % colours.length]}"></i><span>${esc(label(name))}</span><b>${n} (${(n / total * 100).toFixed(1)}%)</b></div>`).join('')}</div></div>` : '<p>No alerts in this selection.</p>';
  }
  function details() {
    const r = rows.find(r => r.id === selected);
    q('[data-al-detail]').innerHTML = r ? `<h2>Alert Details</h2><div class="al-banner al-${r.severity}"><b>⚠ ${esc(r.type)}</b>${badge(r.severity)}<small>${r.date}, ${r.time}</small></div><dl class="record-detail-list">${[['Alert ID', r.id], ['Type', r.type], ['Description', r.description], ['Related Item', r.related], ['Amount', r.amount === null ? 'Not recorded' : moneyWhole(r.amount)], ['Payment Channel', r.channel], ['Transaction Date', r.date + ', ' + r.time], ['Status', label(r.status)], ['Assigned To', liveAssignees.find(v => String(v.id) === String(r.assigned))?.name || 'Unassigned']].map(([k, v]) => `<div><dt>${k}</dt><dd>${esc(v)}</dd></div>`).join('')}</dl><hr><h2>Action</h2><form class="al-action" data-al-action><label>Assign To<select name="assigned"><option value="">Unassigned</option>${liveAssignees.map(v => `<option value="${esc(v.id)}" ${String(r.assigned) === String(v.id) ? 'selected' : ''}>${esc(v.name)}</option>`).join('')}</select></label><label>Status<select name="status">${['open', 'in_review', 'resolved'].map(v => `<option value="${v}" ${r.status === v ? 'selected' : ''}>${label(v)}</option>`).join('')}</select></label><label>Resolution Notes<textarea name="notes" maxlength="2000" placeholder="Enter resolution notes...">${esc(r.notes)}</textarea></label><p data-al-action-message role="status"></p><div class="al-action-buttons"><button type="button" class="pending-outline" data-al-resolve ${r.status === 'resolved' ? 'disabled' : ''}>Mark as Resolved</button><button class="pending-verify">Save Changes</button></div></form>` : '<h2>Alert Details</h2><p>No alerts match the selected filters.</p>';
    if (r) {
      q('[data-al-action]').addEventListener('submit', e => {
        e.preventDefault();
        save(false);
      });
      q('[data-al-resolve]').addEventListener('click', () => save(true));
    }
  }
  async function save(resolve) {
    const r = rows.find(r => r.id === selected),
      data = Object.fromEntries(new FormData(q('[data-al-action]'))),
      next = resolve ? 'resolved' : data.status;
    if (!['open', 'in_review', 'resolved'].includes(next)) return;
    if (next === 'resolved' && !data.notes.trim()) {
      q('[data-al-action-message]').textContent = 'Add resolution notes before marking this alert as resolved.';
      return;
    }
    {
      const msg = q('[data-al-action-message]');
      if (next === r.status && (!data.assigned || data.assigned === r.assigned)) {
        msg.textContent = 'No assignment or status change to save. Resolution notes are saved when resolving an alert.';
        return;
      }
      try {
        let updated = r;
        if (data.assigned && data.assigned !== r.assigned) updated = await api(`alerts/${r.id}/assign/`, {
          method: 'POST',
          body: JSON.stringify({
            assigned_to: data.assigned
          })
        });
        if (next !== r.status) {
          if (next === 'open') throw new Error('Alerts cannot be reopened through this screen.');
          updated = await api(`alerts/${r.id}/${next === 'resolved' ? 'resolve' : 'start-review'}/`, {
            method: 'POST',
            body: JSON.stringify({
              notes: data.notes
            })
          });
        }
        Object.assign(r, mapAlert(updated));
        render();
        q('[data-al-action-message]').textContent = 'Alert changes saved on the server.';
      } catch (error) {
        msg.textContent = error.message;
      }
      return;
    }
  }
  function render() {
    const filtered = matching();
    page = Math.max(1, Math.min(page, Math.ceil(filtered.length / 10) || 1));
    if (!filtered.some(r => r.id === selected)) selected = filtered[0]?.id;
    const counts = v => filtered.filter(r => r.status === v).length;
    q('[data-al-kpis]').innerHTML = [['Total Alerts', filtered.length, 'red'], ['Critical', filtered.filter(r => r.severity === 'critical').length, 'red'], ['Pending Review', counts('open') + counts('in_review'), 'orange'], ['Resolved', counts('resolved'), 'blue']].map(([name, n, c]) => `<article><i class="${c}">${name === 'Resolved' ? 'ⓘ' : '⚠'}</i><div><span>${name}</span><strong>${n}</strong><small>Selected filters</small></div></article>`).join('');
    q('[data-al-table]').innerHTML = `<div class="table-wrap"><table class="data-table finance-data-table"><thead><tr>${['#', 'Date & Time', 'Alert Type', 'Description', 'Related Item', 'Severity', 'Status', 'Actions'].map(v => `<th>${v}</th>`).join('')}</tr></thead><tbody>${filtered.slice((page - 1) * 10, page * 10).map((r, i) => `<tr ${r.id === selected ? 'class="al-selected"' : ''}><td>${(page - 1) * 10 + i + 1}</td><td>${r.date}, ${r.time}</td><td>${esc(r.type)}</td><td>${esc(r.description)}</td><td>${esc(r.related)}</td><td>${badge(r.severity)}</td><td>${badge(r.status)}</td><td><button class="pending-outline" data-al-view="${r.id}" aria-label="View ${r.id}">View</button></td></tr>`).join('') || '<tr><td colspan="8">No alerts available.</td></tr>'}</tbody></table></div>`;
    q('[data-al-count]').textContent = `Showing ${filtered.length ? (page - 1) * 10 + 1 : 0} to ${Math.min(page * 10, filtered.length)} of ${filtered.length} alerts`;
    q('[data-al-pages]').innerHTML = `<button class="pending-outline" data-al-page="${page - 1}" ${page === 1 ? 'disabled' : ''}>Previous</button><span> ${page} / ${Math.ceil(filtered.length / 10) || 1} </span><button class="pending-outline" data-al-page="${page + 1}" ${page * 10 >= filtered.length ? 'disabled' : ''}>Next</button>`;
    chart('[data-al-types]', [...new Set(filtered.map(r => r.type))].map(v => [v, filtered.filter(r => r.type === v).length]), filtered.length);
    chart('[data-al-statuses]', ['open', 'in_review', 'resolved'].map(v => [v, counts(v)]), filtered.length);
    q('[data-al-severities]').innerHTML = `<div class="al-severity-bars">${['critical', 'high', 'medium', 'low'].map((v, i) => {
      const n = filtered.filter(r => r.severity === v).length;
      return `<div><b>${n}</b><div><i data-chart-height="${n / Math.max(1, ...['critical', 'high', 'medium', 'low'].map(s => filtered.filter(r => r.severity === s).length)) * 100}%" data-chart-background="${colours[i]}"></i></div><span>${label(v)}</span></div>`;
    }).join('')}</div>`;
    details();
  }
  q('[data-al-filters]').addEventListener('submit', e => {
    e.preventDefault();
    const values = Object.fromEntries(new FormData(e.currentTarget));
    if (values.from && values.to && values.from > values.to) {
      q('[data-al-filter-message]').textContent = 'Choose an end date on or after the start date.';
      return;
    }
    q('[data-al-filter-message]').textContent = '';
    applied = values;
    page = 1;
    render();
  });
  q('[data-al-filters]').addEventListener('reset', () => {
    applied = {
      search: '',
      severity: '',
      type: '',
      status: '',
      from: dateAgo(29),
      to: today
    };
    q('[data-al-period]').value = '30';
    q('[data-al-filter-message]').textContent = '';
    page = 1;
    render();
  });
  q('[data-al-period]').addEventListener('change', e => {
    const from = dateAgo(Number(e.target.value) - 1);
    q('[name="from"]').value = from;
    q('[name="to"]').value = today;
    applied.from = from;
    applied.to = today;
    page = 1;
    render();
  });
  root.addEventListener('click', e => {
    const view = e.target.closest('[data-al-view]'),
      pager = e.target.closest('[data-al-page]');
    if (view) {
      selected = view.dataset.alView;
      render();
    }
    if (pager) {
      page = Number(pager.dataset.alPage);
      render();
    }
  });
  render();
}
async function usersAndAudit() {
  const esc = escapeHtml;
  const loadAll = async resource => {
    let page = 1,
      data,
      rows = [];
    do {
      data = await api(`${resource}/?period=all&page=${page++}`);
      rows.push(...list(data));
    } while (data.next);
    return rows;
  };
  const users = (await loadAll('users')).map((u, i) => ({
    ...u,
    username: u.username || `staff${i + 1}`
  }));
  const logs = await loadAll('audit-logs');
  const roles = Object.fromEntries(list(await api('users/role_choices/')).map(r=>[r.value,r.label]));
  const departmentRecords = await loadAll('departments');
  const departments = departmentRecords.map(d => String(d.id));
  const departmentName = v => departmentRecords.find(d => String(d.id) === String(v))?.name || v || '—';
  let editing = null,
    page = 1,
    filters = {
      search: '',
      role: '',
      status: ''
    },
    days = 30,
    allLogs = false;
  const date = v => v ? new Date(v).toLocaleString('en-GB', {
    timeZone: 'Africa/Lagos',
    dateStyle: 'medium',
    timeStyle: 'short'
  }) : 'Never';
  content.innerHTML = `<div class="users-audit-page"><header class="overview-preview-brand"><img src="/paypoint/images/hospital%20logo.png" alt="IMSUTH crest"><div><h1>IMSUTH Central Pay Point</h1><p>Imo State Teaching Hospital, Orlu: all payments in one place</p></div><label>Period<select data-ua-period><option value="30">Last 30 days</option><option value="7">Last 7 days</option><option value="1">Today</option><option value="all">All records</option></select></label></header><nav class="overview-preview-tabs" aria-label="Revenue control shortcuts"><a href="#dashboard-overview-preview">Overview</a><a href="#dashboard-record-payment">Record payment</a><a href="#patients">Department desk</a><a href="#admin-departments">Departments</a><a href="#admin-services">Services and prices</a><a href="#cash-points">Cash points and orders</a><a href="#alerts">Alerts</a><a href="#users-audit" aria-current="page">Users and audit</a></nav><p class="overview-preview-note">${'Connected to the authenticated backend. Changes affect real staff access and are audited. Accounts created without a password cannot sign in until secure recovery is completed.'}</p><div class="ua-layout"><main><header class="finance-overview-heading"><div><h1>Users and Audit</h1><p>Manage system users, roles and permissions. View audit logs of all important actions.</p></div><button class="pending-verify" data-ua-add >Add User</button></header><section class="finance-overview-kpis" data-ua-kpis></section><section class="finance-card"><form class="ua-filters" data-ua-filters><label>System Users<input name="search" type="search" placeholder="Search users by name, email or username..."></label><label>Role<select name="role"><option value="">All Roles</option>${Object.entries(roles).map(([v, n]) => `<option value="${v}">${n}</option>`).join('')}</select></label><label>Status<select name="status"><option value="">All Statuses</option><option value="active">Active</option><option value="inactive">Inactive</option></select></label><button class="pending-verify">Apply Filters</button><button type="reset" class="pending-outline">Reset</button></form></section><section class="finance-card"><div data-ua-users></div><div class="pending-pagination"><span data-ua-count aria-live="polite"></span><div data-ua-pages></div></div></section></main><aside><section class="finance-card"><h2 data-ua-editor-title>Add / Edit User</h2><form class="ua-editor" data-ua-editor><input type="hidden" name="id"><div class="ua-pair"><label>Full Name *<input name="full_name" required maxlength="150" placeholder="Enter full name..."></label><label>Username *<input name="username" required maxlength="150" pattern="[A-Za-z0-9_@.+-]+" placeholder="Enter username..."></label></div><label>Email Address *<input type="email" name="email" required maxlength="254" placeholder="Enter email address..."></label><div class="ua-pair"><label>Role *<select name="role" required><option value="">Select role</option>${Object.entries(roles).map(([v, n]) => `<option value="${v}">${n}</option>`).join('')}</select></label><label>Department<select name="department"><option value="">Select department</option>${departments.map(v => `<option value="${esc(v)}">${esc(departmentName(v))}</option>`).join('')}</select></label><label>Phone Number (optional)<input name="phone" type="tel" maxlength="30" placeholder="Enter phone number..."></label><label>Status *<select name="status"><option value="active">Active</option><option value="inactive">Inactive</option></select></label></div><p data-ua-message role="status"></p><div class="ua-actions"><button type="reset" class="pending-outline">Clear Form</button><button class="pending-verify" >Save User</button></div></form></section><section class="finance-card"><div class="finance-card-heading"><h2>Recent Audit Logs</h2><button type="button" class="help-link" data-ua-all>View All</button></div><div data-ua-logs></div></section></aside></div></div>`;
  const root = content.querySelector('.users-audit-page'),
    q = s => root.querySelector(s),
    form = q('[data-ua-editor]');
  const filtered = () => users.filter(u => (!filters.search || [u.full_name, u.email, u.username].join(' ').toLowerCase().includes(filters.search.toLowerCase())) && (!filters.role || u.role === filters.role) && (!filters.status || u.is_active === (filters.status === 'active')));
  const periodLogs = () => {
    const today = new Date().toLocaleDateString('en-CA', {
        timeZone: 'Africa/Lagos'
      }),
      cut = new Date(today + 'T00:00:00+01:00');
    cut.setDate(cut.getDate() - (Number(days) - 1));
    return logs.filter(l => days === 'all' || new Date(l.created_at) >= cut);
  };
  function render() {
    const found = filtered(),
      audit = periodLogs();
    page = Math.min(page, Math.ceil(found.length / 10) || 1);
    q('[data-ua-kpis]').innerHTML = [['Total Users', users.length, 'blue'], ['Active Users', users.filter(u => u.is_active).length, 'green'], ['Roles', Object.keys(roles).length, 'orange'], ['Total Audit Logs', audit.length, 'purple']].map(([name, n, c]) => `<article><i class="${c}"><img src="static/paypoint/user-audit-${c}.svg" alt=""></i><div><span>${name}</span><strong>${n}</strong><small>${name === 'Total Audit Logs' ? 'Selected period' : 'Current directory'}</small></div></article>`).join('');
    q('[data-ua-users]').innerHTML = `<div class="table-wrap"><table class="data-table finance-data-table"><thead><tr>${['#', 'Name', 'Username', 'Email', 'Role', 'Department', 'Status', 'Last Login', 'Actions'].map(v => `<th>${v}</th>`).join('')}</tr></thead><tbody>${found.slice((page - 1) * 10, page * 10).map((u, i) => `<tr><td>${(page - 1) * 10 + i + 1}</td><td>${esc(u.full_name)}</td><td>${esc(u.username)}</td><td>${esc(u.email)}</td><td><span class="ua-role ua-${esc(u.role)}">${esc(roles[u.role] || u.role)}</span></td><td>${esc(departmentName(u.department))}</td><td><span class="staff-status ${u.is_active ? 'staff-active' : 'staff-inactive'}">${u.is_active ? 'Active' : 'Inactive'}</span></td><td>${esc(date(u.last_login))}</td><td><button class="pending-outline" data-ua-edit="${esc(u.id)}" aria-label="Edit ${esc(u.full_name)}">Edit</button></td></tr>`).join('') || '<tr><td colspan="9">No users available.</td></tr>'}</tbody></table></div>`;
    q('[data-ua-count]').textContent = `Showing ${found.length ? (page - 1) * 10 + 1 : 0} to ${Math.min(page * 10, found.length)} of ${found.length} users`;
    q('[data-ua-pages]').innerHTML = `<button class="pending-outline" data-ua-page="${page - 1}" ${page === 1 ? 'disabled' : ''}>Previous</button> <span>${page} / ${Math.ceil(found.length / 10) || 1}</span> <button class="pending-outline" data-ua-page="${page + 1}" ${page * 10 >= found.length ? 'disabled' : ''}>Next</button>`;
    q('[data-ua-logs]').innerHTML = `<div class="table-wrap"><table class="data-table finance-data-table ua-log-table"><thead><tr><th>#</th><th>Date & Time</th><th>User</th><th>Action</th><th>Details</th></tr></thead><tbody>${audit.slice(0, allLogs ? audit.length : 10).map((l, i) => `<tr><td>${i + 1}</td><td>${esc(date(l.created_at))}</td><td>${esc(l.user)}</td><td>${esc(l.action)}</td><td>${esc(l.description)}</td></tr>`).join('') || '<tr><td colspan="5">No audit activity in this period.</td></tr>'}</tbody></table></div><p class="ua-log-note">Read-only activity · ${audit.length} records in selected period</p>`;
    q('[data-ua-all]').textContent = allLogs ? 'Show Recent' : 'View All';
  }
  function clear() {
    editing = null;
    q('[data-ua-editor-title]').textContent = 'Add / Edit User';
    q('[data-ua-message]').textContent = '';
  }
  form.addEventListener('reset', clear);
  q('[data-ua-add]').addEventListener('click', () => {
    form.reset();
    form.elements.namedItem('full_name').focus();
  });
  form.addEventListener('submit', async e => {
    e.preventDefault();
    const v = Object.fromEntries(new FormData(form));
    for (const key of ['full_name', 'username', 'email', 'phone']) v[key] = (v[key] || '').trim();
    const msg = q('[data-ua-message]');
    if (!v.full_name || !v.username || !v.email || !roles[v.role]) {
      msg.textContent = 'Complete the required fields.';
      return;
    }
    if (users.some(u => u.id !== editing && (u.username.toLowerCase() === v.username.toLowerCase() || u.email.toLowerCase() === v.email.toLowerCase()))) {
      msg.textContent = 'A user already has that username or email.';
      return;
    }
    const existing = users.find(u => u.id === editing),
      record = {
        full_name: v.full_name,
        username: v.username,
        email: v.email,
        phone: v.phone,
        role: v.role,
        department: v.department,
        is_active: v.status === 'active'
      };
    {
      const parts = v.full_name.split(/\s+/),
        body = {
          username: v.username,
          first_name: parts.shift(),
          last_name: parts.join(' '),
          email: v.email,
          phone: v.phone,
          role: v.role,
          department: v.department || null,
          is_active: v.status === 'active'
        };
      const button = form.querySelector('[type=submit]') || form.querySelector('.pending-verify');
      button.disabled = true;
      try {
        await api(editing ? `users/${editing}/` : 'users/', {
          method: editing ? 'PATCH' : 'POST',
          body: JSON.stringify(body)
        });
        await usersAndAudit();
      } catch (error) {
        msg.textContent = error.message;
      } finally {
        button.disabled = false;
      }
      return;
    }
  });
  q('[data-ua-filters]').addEventListener('submit', e => {
    e.preventDefault();
    filters = Object.fromEntries(new FormData(e.currentTarget));
    page = 1;
    render();
  });
  q('[data-ua-filters]').addEventListener('reset', () => {
    filters = {
      search: '',
      role: '',
      status: ''
    };
    page = 1;
    render();
  });
  q('[data-ua-period]').addEventListener('change', e => {
    days = e.target.value;
    render();
  });
  q('[data-ua-all]').addEventListener('click', () => {
    allLogs = !allLogs;
    render();
  });
  root.addEventListener('click', e => {
    const edit = e.target.closest('[data-ua-edit]'),
      pager = e.target.closest('[data-ua-page]');
    if (pager) {
      page = Number(pager.dataset.uaPage);
      render();
    }
    if (edit) {
      const u = users.find(u => String(u.id) === edit.dataset.uaEdit);
      if (!u) return;
      editing = u.id;
      for (const k of ['full_name', 'username', 'email', 'phone', 'role', 'department']) form.elements.namedItem(k).value = u[k] || '';
      form.elements.namedItem('status').value = u.is_active ? 'active' : 'inactive';
      q('[data-ua-editor-title]').textContent = 'Edit User';
      q('[data-ua-message]').textContent = 'Editing ' + u.full_name;
      form.elements.namedItem('full_name').focus();
    }
  });
  render();
}
async function notificationInbox() {
  let page = 1;
  const render = async () => {
    const data = await api(`inbox/?page=${page}`);
    content.innerHTML = `${title('Notifications')}<p>Your authenticated notification inbox.</p><section class="finance-card"><div class="table-wrap"><table class="data-table"><thead><tr><th>Subject</th><th>Message</th><th>Status</th><th>Action</th></tr></thead><tbody>${list(data).map(r => `<tr><td>${escapeHtml(r.notification.subject)}</td><td>${escapeHtml(r.notification.body)}</td><td>${r.read_at ? 'Read' : 'Unread'}</td><td><button data-inbox-read="${r.id}" ${r.read_at ? 'disabled' : ''}>Mark as read</button></td></tr>`).join('') || '<tr><td colspan="4">No notifications.</td></tr>'}</tbody></table></div><div class="pending-pagination"><button data-inbox-page="${page - 1}" ${data.previous ? '' : 'disabled'}>Previous</button><span>${page}</span><button data-inbox-page="${page + 1}" ${data.next ? '' : 'disabled'}>Next</button></div></section>`;
    content.querySelectorAll('[data-inbox-read]').forEach(b => b.onclick = async () => {
      try {
        await api(`inbox/${b.dataset.inboxRead}/read/`, {
          method: 'POST',
          body: '{}'
        });
        await render();
        const unread = await api('inbox/unread-count/');
        onUnreadCount(unread.count);
      } catch (error) {
        showError(error);
      }
    });
    content.querySelectorAll('[data-inbox-page]').forEach(b => b.onclick = () => {
      page = Number(b.dataset.inboxPage);
      render().catch(showError);
    });
  };
  await render();
}
function honestPage(heading, description, note, action = "") {
  content.innerHTML = `${title(heading)}<nav class="page-breadcrumbs"><a href="#dashboard">Dashboard</a><span>›</span><b>${escapeHtml(heading)}</b></nav><section class="panel honest-state"><h2>${escapeHtml(description)}</h2><p>${escapeHtml(note)}</p>${action}</section>`;
}
const dashboardPreset = mode => async () => {
  dashboardMode = mode;
  localStorage.setItem("imsuth-paypoint-dashboard", mode);
  await dashboard();
};
const patientSelection = () => () => livePages.patients();
const filteredBilling = (heading,statuses) => () => livePages.billing(statuses,heading);

const reportPage = () => () => livePages.reportsDashboard();
const pages = {
  notifications: notificationInbox,
  "users-audit": usersAndAudit,
  alerts: alertsPage,
  "cash-points": cashPointsAndOrders,
  "dashboard-overview-preview": overviewDashboardPreview,
  "dashboard-record-payment": recordPaymentPreview,
  dashboard,
  "dashboard-front-desk": dashboardPreset("front_desk"),
  "dashboard-cashier": dashboardPreset("cashier"),
  "dashboard-finance": dashboardPreset("finance"),
  "dashboard-daily": dashboardPreset("daily"),
  patients: departmentDesk,
  "patient-directory": patients,
  "patient-registration": patientRegistration,
  "patient-profile": patientProfile,
  "patient-search": patients,
  "patient-billing-history": patientSelection("Patient Billing History", "Choose a patient before requesting their authorised billing history."),
  billing,
  "billing-create": createInvoice,
  "billing-pending": filteredBilling("Pending Invoices", ["issued", "partially_paid"]),
  "billing-details": invoiceDetails,
  "billing-paid": filteredBilling("Paid Invoices", ["paid"]),
  "billing-cancelled": filteredBilling("Cancelled / Corrected Invoices", ["cancelled"]),
  "billing-services": servicesAndPrices,
  "billing-tariffs": tariffManagement,
  payments,
  "payments-process": processPayment,
  "payments-verify": verifyPayment,
  "payments-pending": pendingPayments,
  "payments-verified": verifiedPayments,
  "payments-failed": failedPayments,
  "payments-receipts": receipts,
  "payments-receipt-verification": receiptVerification,
  "payments-receipt-reprints": receiptReprints,
  finance: financeOverview,
  "finance-collections": revenueCollections,
  "finance-reports": revenueReports,
  "finance-daily-report": dailyCollectionReport,
  "finance-department-report": departmentRevenueReport,
  "finance-cashier-report": cashierCollectionReport,
  "finance-channel-report": paymentChannelReport,
  "finance-settlements": dailySettlement,
  "finance-reconciliation": bankReconciliation,
  "finance-discrepancies": reconciliationDiscrepancies,
  "finance-refunds": refundRequests,
  "finance-reversals": reversalRequests,
  "finance-approvals": approvalQueue,
  "admin-catalogue-setup": hospitalCatalogueSetup,
  administration: staffManagement,
  "admin-add-staff": addStaffMember,
  "admin-roles": rolesPermissions,
  "admin-departments": revenueDepartments,
  "department-management": departmentsManagement,
  "admin-services": servicesAndPrices,
  "services-management": servicesManagement,
  "admin-tariffs": tariffManagement,
  "admin-notifications": notificationsManagement,
  "admin-settings": systemSettings,
  "admin-audit": auditTrailReport,
  reports: reportsDashboard,
  "reports-revenue": revenueReports,
  "reports-daily": dailyCollectionReport,
  "reports-department": departmentRevenueReport,
  "reports-cashier": cashierCollectionReport,
  "reports-channel": paymentChannelReport,
  "reports-outstanding": outstandingInvoicesReport,
  "reports-settlement": settlementReport,
  "reports-reconciliation": reconciliationReport,
  "reports-audit": auditTrailReport,
  "reports-patients": patientRegistrationReport,
  "reports-system": systemActivityReport,
  "reports-export": reportPage("Export Reports"),
  "help-support": helpSupport,
  "help": helpSupport,
  "my-profile": userAccountSettings,
  "change-password": userAccountSettings
};

async function render(page) {
  const permission = (['admin-departments','admin-services'].includes(page) ? 'billing' : navigationPage[page]?.permission) || (page==='patient-registration' ? 'patients' : null);
  if (permission && !user.permissions?.[permission]) {showError({status:403,message:'Your role does not permit access to this module.'});return;}
  if (!pages[page]) {content.innerHTML='<div class="api-error"><h1>Page not found</h1><p>Select a page from the navigation.</p></div>';return;}
  setBusy();
  try {await pages[page]();} catch(error) {if(!abort.signal.aborted)showError(error);}
}
content.addEventListener('click', event=>{
  const anchor=event.target.closest('a[href^="#"]');
  if(anchor && !event.metaKey && !event.ctrlKey && !event.shiftKey && event.button===0){event.preventDefault();navigate(anchor.getAttribute('href').slice(1));}
  if(event.target.closest('[data-refresh]'))render(currentPage);
},{signal:abort.signal});
let currentPage='dashboard';
return {
  render(page){currentPage=page;return render(page);},
  filter(value){
    const live=content.querySelector('.live-workspace');
    if(live){live.dispatchEvent(new CustomEvent('live-search',{detail:value}));return;}
    const form=content.querySelector('[data-ua-filters],[data-al-filters],[data-sp-filters]');
    if(form?.elements.search){form.elements.search.value=value;form.requestSubmit();return;}
    const revenue=content.querySelector('.overview-preview-page,.revenue-departments-page');
    if(revenue){revenue.dispatchEvent(new CustomEvent('revenue-search',{detail:value}));return;}
    const query=value.trim().toLowerCase();
    content.querySelectorAll('tbody tr').forEach(row=>row.hidden=Boolean(query)&&!row.textContent.toLowerCase().includes(query));
  },
  dispose(){abort.abort();observer.disconnect();content.remove();},
};
}
