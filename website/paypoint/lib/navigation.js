export const navigationSections = [{
  id: "dashboard",
  label: "Dashboard",
  icon: "⌂",
  permission: null,
  items: [["dashboard", "Management Dashboard"], ["dashboard-overview-preview", "Overview Dashboard"], ["dashboard-record-payment", "Record Payment"], ["dashboard-front-desk", "Front Desk Dashboard"], ["dashboard-cashier", "Cashier Dashboard"], ["dashboard-finance", "Finance Dashboard"], ["dashboard-daily", "Daily Activity Overview"]]
}, {
  id: "patients",
  label: "Patients",
  icon: "◎",
  permission: "patients",
  items: [["patients", "Department Desk"], ["patient-directory", "All Patients"], ["patient-registration", "Register Patient"], ["patient-profile", "Patient Profiles"], ["patient-search", "Patient Search"], ["patient-billing-history", "Patient Billing History"]]
}, {
  id: "billing",
  label: "Billing",
  icon: "▤",
  permission: "billing",
  items: [["billing", "All Invoices"], ["cash-points", "Cash Points and Orders"], ["billing-create", "Create Invoice"], ["billing-pending", "Pending Invoices"], ["billing-details", "Invoice Details"], ["billing-paid", "Paid Invoices"], ["billing-cancelled", "Cancelled / Corrected Invoices"], ["billing-services", "Departments & Services"], ["billing-tariffs", "Service Tariffs"]]
}, {
  id: "payments",
  label: "Payments",
  icon: "▣",
  permission: "payments",
  items: [["payments", "All Transactions"], ["payments-process", "Process Payment"], ["payments-verify", "Verify Payment"], ["payments-pending", "Pending Payments"], ["payments-verified", "Verified Payments"], ["payments-failed", "Failed Payments"], ["payments-receipts", "Receipts"], ["payments-receipt-verification", "Receipt Verification"], ["payments-receipt-reprints", "Receipt Reprints"]]
}, {
  id: "finance",
  label: "Finance",
  icon: "₦",
  permission: "finance",
  items: [["finance", "Finance Overview"], ["finance-collections", "Revenue Collections"], ["finance-settlements", "Daily Settlement"], ["finance-reports", "Revenue Reports"], ["finance-daily-report", "Daily Collection Report"], ["finance-department-report", "Department Revenue Report"], ["finance-cashier-report", "Cashier Collection Report"], ["finance-channel-report", "Payment Channel Report"], ["finance-reconciliation", "Bank Reconciliation"], ["alerts", "Alerts"], ["finance-discrepancies", "Reconciliation Discrepancies"], ["finance-refunds", "Refund Requests"], ["finance-reversals", "Reversal Requests"], ["finance-approvals", "Approval Queue"]]
}, {
  id: "administration",
  label: "Administration",
  icon: "⚙",
  permission: "administration",
  items: [["administration", "Staff Management"], ["admin-catalogue-setup", "Hospital Catalogue Setup"], ["admin-add-staff", "Add Staff"], ["admin-roles", "Roles & Permissions"], ["admin-departments", "Departments Management"], ["admin-services", "Services and Prices"], ["admin-tariffs", "Tariff Management"], ["admin-notifications", "Notifications"], ["admin-settings", "System Settings"], ["users-audit", "Users and Audit"], ["admin-audit", "Audit Logs"]]
}, {
  id: "reports",
  label: "Reports",
  icon: "▥",
  permission: "reports",
  items: [["reports", "Reports Dashboard"], ["reports-revenue", "Revenue Reports"], ["reports-daily", "Daily Collection Report"], ["reports-department", "Department Revenue Report"], ["reports-cashier", "Cashier Collection Report"], ["reports-channel", "Payment Channel Report"], ["reports-outstanding", "Outstanding Invoices Report"], ["reports-settlement", "Settlement Report"], ["reports-reconciliation", "Reconciliation Report"], ["reports-audit", "Audit Trail Report"], ["reports-patients", "Patient Registration Report"], ["reports-system", "System Activity Report"], ["reports-export", "Export Reports"]]
}];
export const navigationPage = Object.fromEntries(navigationSections.flatMap(section => section.items.map(([page, label]) => [page, {
  section: section.id,
  label,
  permission: section.permission
}])));

export const BASE_PATH = '/paypoint';
export function screenFromSegments(segments) {
  if (!segments?.length || segments.join('/') === 'index.html') return 'dashboard';
  return segments.join('/');
}
export const screenHref = screen => screen === 'dashboard' ? '/' : `/${encodeURIComponent(screen)}`;
