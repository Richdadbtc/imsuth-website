# Revenue Departments QA

Reference: codex-clipboard-bec5ad18-49fa-42c0-aa40-160c7f4f40b0.png.
Route: #admin-departments. Original management details: #department-management.

The initial desktop implementation was inspected at 1536 × 1024. It includes the
revenue-control header and active Departments tab, four summary cards, search/status/
sort controls, department table, collection bars, performance donut and quick actions.
Figures use confirmed NGN department-linked payments rather than screenshot values.
The desktop table was then compacted to retain access to its action column at the
available content width. A final screenshot of that adjustment is outstanding.

Functional checks passed: pagination, search, department details, empty-period charts,
demo catalogue creation and duplicate detection. Live creation uses POST departments/;
backend permissions remain authoritative. Demo creation is page-local only.

Final result: blocked.
Final screenshot comparison after the table-width adjustment remains incomplete.
No exact visual-fidelity claim is made.
