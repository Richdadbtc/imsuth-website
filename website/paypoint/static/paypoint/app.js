(() => {
  "use strict";

  const menuButton = document.querySelector(".menu-toggle");
  if (menuButton) {
    const closeMenu = () => {
      document.body.classList.remove("nav-open");
      menuButton.setAttribute("aria-expanded", "false");
    };
    menuButton.addEventListener("click", () => {
      const open = document.body.classList.toggle("nav-open");
      menuButton.setAttribute("aria-expanded", String(open));
    });
    document.addEventListener("keydown", event => {
      if (event.key === "Escape") closeMenu();
    });
    document.querySelectorAll(".side-nav a").forEach(link => link.addEventListener("click", closeMenu));
  }

  const sidebarCollapse = document.querySelector(".sidebar-collapse");
  if (sidebarCollapse) {
    const collapsed = window.localStorage.getItem("paypoint-sidebar-collapsed") === "true";
    document.body.classList.toggle("sidebar-collapsed", collapsed);
    sidebarCollapse.setAttribute("aria-expanded", String(!collapsed));
    sidebarCollapse.addEventListener("click", () => {
      const nextCollapsed = document.body.classList.toggle("sidebar-collapsed");
      sidebarCollapse.setAttribute("aria-expanded", String(!nextCollapsed));
      window.localStorage.setItem("paypoint-sidebar-collapsed", String(nextCollapsed));
    });
  }

  document.querySelectorAll("[data-confirm]").forEach(control => {
    control.addEventListener("click", event => {
      if (!window.confirm(control.dataset.confirm)) event.preventDefault();
    });
  });

  document.querySelectorAll("[data-dismiss-toast]").forEach(button => {
    button.addEventListener("click", () => button.closest("[data-toast]")?.remove());
  });

  document.querySelectorAll("[data-print]").forEach(button => {
    button.addEventListener("click", () => window.print());
  });

  document.querySelectorAll("[data-password-toggle]").forEach(button => {
    button.addEventListener("click", () => {
      const input = document.getElementById(button.getAttribute("aria-controls"));
      const showing = input.type === "text";
      input.type = showing ? "password" : "text";
      button.textContent = showing ? "Show" : "Hide";
      button.setAttribute("aria-pressed", String(!showing));
    });
  });

  const invoiceForm = document.querySelector("[data-invoice-form]");
  if (invoiceForm) {
    const template = document.querySelector("#invoice-line-template");
    const extraLines = invoiceForm.querySelector("[data-extra-lines]");
    const primaryService = invoiceForm.querySelector("#id_service");
    const hiddenItems = invoiceForm.querySelector("#id_line_items");
    invoiceForm.querySelector("[data-add-line]")?.addEventListener("click", () => {
      const fragment = template.content.cloneNode(true);
      const select = fragment.querySelector("[data-line-service]");
      select.innerHTML = primaryService.innerHTML;
      extraLines.appendChild(fragment);
    });
    extraLines.addEventListener("click", event => {
      const remove = event.target.closest("[data-remove-line]");
      if (remove) remove.closest("[data-extra-line]")?.remove();
    });
    invoiceForm.addEventListener("submit", () => {
      const items = [...extraLines.querySelectorAll("[data-extra-line]")].map(line => ({
        service: line.querySelector("[data-line-service]").value,
        quantity: line.querySelector("[data-line-quantity]").value
      })).filter(item => item.service);
      hiddenItems.value = JSON.stringify(items);
    });
  }

  document.querySelectorAll("form[data-submit-state]").forEach(form => {
    form.addEventListener("submit", () => {
      const submitter = form.querySelector('button[type="submit"]');
      if (submitter) {
        submitter.disabled = true;
        submitter.setAttribute("aria-busy", "true");
        submitter.textContent = submitter.dataset.loadingLabel || "Working…";
      }
    });
  });

  document.querySelectorAll("[data-bar-height]").forEach(bar => {
    const value = Math.max(0, Math.min(100, Number(bar.dataset.barHeight) || 0));
    bar.style.setProperty("--bar-height", String(value));
  });

  const dashboardFilterToggle = document.querySelector("[data-dashboard-filter-toggle]");
  const dashboardFilter = document.querySelector("[data-dashboard-filter]");
  if (dashboardFilterToggle && dashboardFilter) {
    dashboardFilterToggle.addEventListener("click", () => {
      const open = dashboardFilter.hasAttribute("hidden");
      dashboardFilter.toggleAttribute("hidden", !open);
      dashboardFilterToggle.setAttribute("aria-expanded", String(open));
    });
  }

  const navSearch = document.querySelector("[data-nav-search]");
  const navSearchStatus = document.querySelector("[data-nav-search-status]");
  if (navSearch && navSearchStatus) {
    const navigationLinks = [...document.querySelectorAll(".side-nav a, .sidebar-quick a")];
    navSearch.addEventListener("input", () => {
      const query = navSearch.value.trim().toLowerCase();
      const match = query ? navigationLinks.find(link => link.textContent.toLowerCase().includes(query)) : null;
      navSearchStatus.textContent = match ? `Press Enter to open ${match.textContent.trim()}` : query ? "No matching page" : "";
      navSearch.dataset.match = match?.href || "";
    });
    navSearch.addEventListener("keydown", event => {
      if (event.key === "Enter" && navSearch.dataset.match) {
        event.preventDefault();
        window.location.assign(navSearch.dataset.match);
      }
    });
  }

  const patientTabs = [...document.querySelectorAll("[data-patient-tab]")];
  const openPatientTab = id => {
    patientTabs.forEach(tab => {
      const selected = tab.dataset.patientTab === id;
      tab.setAttribute("aria-selected", String(selected));
      document.getElementById(tab.dataset.patientTab)?.toggleAttribute("hidden", !selected);
    });
  };
  patientTabs.forEach(tab => {
    tab.addEventListener("click", () => openPatientTab(tab.dataset.patientTab));
    tab.addEventListener("keydown", event => {
      if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
      event.preventDefault();
      const current = patientTabs.indexOf(tab);
      const direction = event.key === 'ArrowRight' ? 1 : -1;
      const next = patientTabs[(current + direction + patientTabs.length) % patientTabs.length];
      next.focus();
      openPatientTab(next.dataset.patientTab);
    });
  });
  document.querySelectorAll("[data-open-patient-tab]").forEach(link => {
    link.addEventListener("click", event => {
      event.preventDefault();
      openPatientTab(link.dataset.openPatientTab);
      document.getElementById(link.dataset.openPatientTab)?.scrollIntoView({behavior:"smooth", block:"start"});
    });
  });

  document.querySelectorAll(".side-nav a").forEach(link => {
    const currentPath = window.location.pathname;
    const linkPath = new URL(link.href, window.location.origin).pathname;
    if (linkPath !== "/" && currentPath.startsWith(linkPath)) link.setAttribute("aria-current", "page");
    else if (linkPath === currentPath) link.setAttribute("aria-current", "page");
  });

  const svgNamespace = "http://www.w3.org/2000/svg";
  const createSvgElement = (name, attributes = {}) => {
    const element = document.createElementNS(svgNamespace, name);
    Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value));
    return element;
  };

  const revenueChart = document.querySelector("[data-revenue-chart]");
  const revenueSeriesElement = document.getElementById("revenue-series");
  if (revenueChart && revenueSeriesElement) {
    const revenueSeries = JSON.parse(revenueSeriesElement.textContent);
    const channelColours = {cash:"#008c91",bank_transfer:"#2563eb",pos:"#684bd3",online:"#38a9e8"};
    const renderRevenueChart = period => {
      [...revenueChart.children].forEach(child => {
        if (!["title", "desc"].includes(child.tagName.toLowerCase())) child.remove();
      });
      const series = revenueSeries[period] || [];
      const totals = series.map(item => Object.values(item.channels).reduce((sum, value) => sum + Number(value || 0), 0));
      const maximum = Math.max(...totals, 1);
      [35, 85, 135, 185].forEach(y => revenueChart.appendChild(createSvgElement("line", {x1:45,y1:y,x2:745,y2:y,class:"chart-grid-line"})));
      const slot = 690 / Math.max(series.length, 1);
      series.forEach((item, index) => {
        const total = totals[index];
        const x = 50 + index * slot + slot * .24;
        const width = slot * .52;
        let bottom = 200;
        revenueSeries.channels.forEach(channel => {
          const value = Number(item.channels[channel.key] || 0);
          const height = (value / maximum) * 155;
          bottom -= height;
          revenueChart.appendChild(createSvgElement("rect", {x,y:bottom,width,height:Math.max(height,1),fill:channelColours[channel.key] || "#9aafc0",class:"chart-bar-segment"}));
        });
        const valueText = createSvgElement("text", {x:x+width/2,y:Math.max(bottom-6,14),"text-anchor":"middle",class:"chart-value"});
        valueText.textContent = `₦${Math.round(total).toLocaleString()}`;
        revenueChart.appendChild(valueText);
        const label = createSvgElement("text", {x:x+width/2,y:224,"text-anchor":"middle",class:"chart-label"});
        label.textContent = item.label;
        revenueChart.appendChild(label);
      });
    };
    document.querySelectorAll("[data-chart-period]").forEach(button => button.addEventListener("click", () => {
      document.querySelectorAll("[data-chart-period]").forEach(control => control.classList.toggle("active", control === button));
      renderRevenueChart(button.dataset.chartPeriod);
    }));
    renderRevenueChart("daily");
  }

  const departmentChart = document.querySelector("[data-department-chart]");
  const departmentData = [...document.querySelectorAll("[data-department-data] [data-value]")];
  if (departmentChart && departmentData.length) {
    const palette = ["#008c91","#2563eb","#684bd3","#f59e0b","#16a34a","#9aafc0","#dc2626"];
    const radius = 68;
    const circumference = 2 * Math.PI * radius;
    let offset = 0;
    departmentData.forEach((item, index) => {
      const percentage = Number(item.dataset.percentage) || 0;
      const dashArray = String((percentage / 100) * circumference) + " " + String(circumference);
      const segment = createSvgElement("circle", {cx:95,cy:95,r:radius,fill:"none",stroke:palette[index % palette.length],"stroke-width":28,"stroke-dasharray":dashArray,"stroke-dashoffset":-offset,transform:"rotate(-90 95 95)",class:"department-segment"});
      departmentChart.appendChild(segment);
      offset += (percentage / 100) * circumference;
      const dot = item.querySelector(".department-dot");
      if (dot) dot.style.backgroundColor = palette[index % palette.length];
    });
  }
})();
