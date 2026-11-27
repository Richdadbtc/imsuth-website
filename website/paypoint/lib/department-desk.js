export function departmentDeskState(records, user) {
  const supervisor = user.role === 'department_supervisor';
  const assigned = user.department == null ? '' : String(user.department);
  const permitted = supervisor ? records.filter(row => String(row.id) === assigned) : records;
  const departments = permitted.filter(row => row.is_active !== false);
  let notice = '';
  if (supervisor && !assigned) notice = 'Ask an administrator to assign your department in Users and Audit.';
  else if (supervisor && !departments.length) notice = 'Your assigned department is inactive or unavailable. Ask an administrator to check your department assignment.';
  else if (!departments.length) notice = 'No active departments are available to this account. Ask an administrator to check department setup.';
  return {departments, selected: departments.length ? String(departments[0].id) : '', locked: supervisor, notice};
}
