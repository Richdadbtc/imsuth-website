const InternalPages = {
  escape(value) {
    const node = document.createElement('div');
    node.textContent = value == null ? '' : String(value);
    return node.innerHTML;
  },

  async init() {
    document.querySelectorAll('[data-current-year]').forEach(el => el.textContent = new Date().getFullYear());
    const page = document.body.dataset.page;
    if (!page) return;
    const data = await DataStore.loadAll();
    if (typeof API !== 'undefined') API.configure(data.settings);
    const simpleBreadcrumbs = {
      about: 'About IMSUTH', departments: 'Departments', services: 'Clinical Services',
      appointment: 'Appointment', contact: 'Contact', doctors: 'Doctors & Specialists',
      patients: 'Patients & Visitors', facilities: 'Facilities', research: 'Teaching & Research',
      news: 'News & Events', careers: 'Careers', privacy: 'Privacy Policy'
    };
    if (simpleBreadcrumbs[page]) this.addBreadcrumbSchema(['Home', simpleBreadcrumbs[page]], ['https://www.imsuth.org/', `https://www.imsuth.org/${location.pathname.split('/').pop()}`]);
    if (page === 'departments') this.renderDirectory(data.departments);
    if (page === 'department-detail') this.renderDepartment(data.departments);
    if (page === 'services') this.renderServices(data.services);
    if (page === 'service-detail') this.renderService(data.services, data.departments);
    if (page === 'contact') this.renderContact(data.settings);
    if (page === 'doctors') this.renderDoctors(data.doctors, data.departments);
    if (page === 'doctor-detail') this.renderDoctor(data.doctors, data.departments, data.services);
    if (page === 'patients') this.renderPatientInfo(data.patientInfo);
    if (page === 'facilities') this.renderFacilities(data.facilities);
    if (page === 'facility-detail') this.renderFacility(data.facilities, data.departments, data.services);
    if (page === 'research') this.renderResearch(data.research, data.publications);
    if (page === 'news') this.renderNewsDirectory(data.news);
    if (page === 'article-detail') this.renderArticle(data.news);
    if (page === 'careers') this.renderCareers(data.careers);
    if (page === 'leadership-detail') this.renderLeader(data.leadership);
  },

  setupSearch(input, cards, count) {
    const update = () => {
      const query = input.value.trim().toLowerCase();
      let shown = 0;
      cards.forEach(card => {
        const visible = !query || card.dataset.search.includes(query);
        card.hidden = !visible;
        if (visible) shown++;
      });
      count.textContent = `${shown} ${shown === 1 ? 'result' : 'results'}`;
    };
    input.addEventListener('input', update);
    update();
  },

  renderDirectory(departments) {
    const grid = document.querySelector('[data-department-grid]');
    if (!grid) return;
    grid.innerHTML = departments.map(dept => `<article class="directory-card" data-search="${this.escape(`${dept.name} ${dept.description}`.toLowerCase())}"><span class="number-mark">DEPARTMENT</span><h2>${this.escape(dept.name)}</h2><p>${this.escape(dept.description)}</p><a class="directory-card__link" href="department-details.html?id=${encodeURIComponent(dept.id)}">View department <span aria-hidden="true">→</span></a></article>`).join('');
    this.setupSearch(document.querySelector('#departmentSearch'), [...grid.children], document.querySelector('[data-result-count]'));
  },

  renderDepartment(departments) {
    const id = new URLSearchParams(location.search).get('id');
    const dept = departments.find(item => item.id === id || item.slug === id);
    const target = document.querySelector('[data-detail]');
    if (!dept) {
      target.innerHTML = `<div class="empty-state"><h2>Department not found</h2><p>We could not find the requested department.</p><a class="btn btn--primary" href="departments.html">Back to departments</a></div>`;
      document.title = 'Department Not Found | IMSUTH';
      return;
    }
    document.title = `${dept.name} Department | IMSUTH`;
    document.querySelector('meta[property="og:title"]').content = `${dept.name} Department | IMSUTH`;
    document.querySelector('[data-page-title]').textContent = dept.name;
    document.querySelector('[data-breadcrumb-current]').textContent = dept.name;
    document.querySelector('meta[name="description"]').setAttribute('content', `${dept.name} at Imo State University Teaching Hospital, Orlu.`);
    const services = dept.services?.length ? `<h2>Services</h2><ul class="detail-list">${dept.services.map(x => `<li>${this.escape(x)}</li>`).join('')}</ul>` : `<h2>Services</h2><p>Detailed service information is awaiting departmental approval.</p>`;
    const schedule = dept.clinicSchedule && dept.clinicSchedule !== 'To be confirmed' ? `<li><span>Clinic schedule</span><strong>${this.escape(dept.clinicSchedule)}</strong></li>` : '';
    const contact = dept.contact && (dept.contact.phone || dept.contact.email || dept.contact.location) ? `<h3>Department contact</h3><ul class="sidebar-list">${dept.contact.phone ? `<li><span>Phone</span><strong>${this.escape(dept.contact.phone)}</strong></li>` : ''}${dept.contact.email ? `<li><span>Email</span><strong>${this.escape(dept.contact.email)}</strong></li>` : ''}${dept.contact.location ? `<li><span>Location</span><strong>${this.escape(dept.contact.location)}</strong></li>` : ''}</ul>` : `<h3>Department contact</h3><p>Direct contact information will be published after hospital confirmation.</p>`;
    target.innerHTML = `<div class="detail-layout"><article class="detail-copy"><h2>About this department</h2><p>${this.escape(dept.description)}</p>${services}<h2>Specialists</h2><p>${dept.specialists?.length ? dept.specialists.map(this.escape).join(', ') : 'Approved specialist profiles are not yet available.'}</p></article><aside class="detail-sidebar" aria-label="Department information"><div class="sidebar-card"><h2>At a glance</h2><ul class="sidebar-list">${schedule}<li><span>Status</span><strong>Department information published</strong></li></ul></div><div class="sidebar-card">${contact}</div><a class="btn btn--primary btn--block" href="appointment.html?department=${encodeURIComponent(dept.id)}">Request an appointment</a></aside></div>`;
    const canonical = `https://www.imsuth.org/department-details.html?id=${encodeURIComponent(dept.id)}`;
    document.querySelector('link[rel="canonical"]').href = canonical;
    document.querySelector('meta[property="og:url"]').content = canonical;
    this.addBreadcrumbSchema(['Home','Departments',dept.name], ['https://www.imsuth.org/','https://www.imsuth.org/departments.html',canonical]);
  },

  renderServices(services) {
    const grid = document.querySelector('[data-service-grid]');
    if (!grid) return;
    grid.innerHTML = services.map(service => `<article class="directory-card directory-card--visual" data-search="${this.escape(`${service.name} ${service.description}`.toLowerCase())}"><div class="service-visual service-visual--panel-${Number(service.imagePanel) || 1}" role="img" aria-label="Illustration representing ${this.escape(service.name)}"><span class="service-visual__icon">${serviceIconMarkup(service.icon)}</span></div><div class="directory-card__body"><span class="number-mark">CLINICAL SERVICE</span><h2>${this.escape(service.name)}</h2><p>${this.escape(service.description)}</p><a class="directory-card__link" href="service-details.html?id=${encodeURIComponent(service.id)}">Explore service <span aria-hidden="true">→</span></a></div></article>`).join('');
    this.setupSearch(document.querySelector('#serviceSearch'), [...grid.children], document.querySelector('[data-result-count]'));
  },

  renderService(services, departments) {
    const id = new URLSearchParams(location.search).get('id');
    const service = services.find(item => item.id === id || item.slug === id);
    const target = document.querySelector('[data-detail]');
    if (!service) {
      target.innerHTML = `<div class="empty-state"><h2>Service not found</h2><p>We could not find the requested clinical service.</p><a class="btn btn--primary" href="services.html">Back to clinical services</a></div>`;
      document.title = 'Service Not Found | IMSUTH'; return;
    }
    document.title = `${service.name} | IMSUTH Clinical Services`;
    document.querySelector('meta[property="og:title"]').content = `${service.name} | IMSUTH Clinical Services`;
    document.querySelector('[data-page-title]').textContent = service.name;
    document.querySelector('[data-breadcrumb-current]').textContent = service.name;
    document.querySelector('meta[name="description"]').setAttribute('content', `${service.name} at Imo State University Teaching Hospital, Orlu.`);
    const related = (service.relatedDepartments || []).map(id => departments.find(d => d.id === id)).filter(Boolean);
    target.innerHTML = `<div class="detail-layout"><article class="detail-copy"><h2>About this service</h2><p>${this.escape(service.description)}</p><h2>What the service covers</h2><p>Detailed care pathways are awaiting clinical review and hospital approval.</p><h2>Preparing for your visit</h2><p>Preparation requirements vary. Please contact IMSUTH before your visit for instructions specific to your care.</p>${related.length ? `<h2>Related departments</h2><div class="content-grid">${related.map(d => `<a class="related-card" href="department-details.html?id=${encodeURIComponent(d.id)}"><h3>${this.escape(d.name)}</h3><p>${this.escape(d.description)}</p></a>`).join('')}</div>` : ''}</article><aside class="detail-sidebar"><div class="sidebar-card"><h2>Need this service?</h2><p>Send an appointment request or contact the hospital for guidance.</p></div><a class="btn btn--primary btn--block" href="appointment.html">Request appointment</a><a class="btn btn--secondary btn--block" href="contact.html">Contact IMSUTH</a></aside></div>`;
    const canonical = `https://www.imsuth.org/service-details.html?id=${encodeURIComponent(service.id)}`;
    document.querySelector('link[rel="canonical"]').href = canonical;
    document.querySelector('meta[property="og:url"]').content = canonical;
    this.addBreadcrumbSchema(['Home','Clinical Services',service.name], ['https://www.imsuth.org/','https://www.imsuth.org/services.html',canonical]);
  },

  renderDoctors(doctors, departments) {
    const grid = document.querySelector('[data-doctor-grid]');
    const count = document.querySelector('[data-result-count]');
    const department = document.querySelector('#doctorDepartment');
    const specialty = document.querySelector('#doctorSpecialty');
    departments.forEach(item => department?.insertAdjacentHTML('beforeend', `<option value="${this.escape(item.id)}">${this.escape(item.name)}</option>`));
    [...new Set(doctors.map(item => item.specialty).filter(Boolean))].sort().forEach(item => specialty?.insertAdjacentHTML('beforeend', `<option value="${this.escape(item)}">${this.escape(item)}</option>`));
    if (!doctors.length) {
      grid.innerHTML = '<div class="empty-state"><h2>Clinician profiles are being prepared</h2><p>Approved clinician profiles will be published following hospital confirmation.</p><a class="btn btn--primary" href="appointment.html">Request an appointment</a></div>';
      count.textContent = '0 profiles'; return;
    }
    grid.innerHTML = doctors.map(doctor => `<article class="profile-card" data-name="${this.escape(doctor.name.toLowerCase())}" data-department="${this.escape(doctor.departmentId)}" data-specialty="${this.escape(doctor.specialty)}"><div class="profile-card__photo">${doctor.photo ? `<img src="${this.escape(doctor.photo)}" alt="${this.escape(doctor.name)}" width="420" height="420" loading="lazy">` : ''}</div><div class="profile-card__body"><p class="eyebrow">${this.escape(doctor.specialty)}</p><h2>${this.escape(doctor.name)}</h2><p>${this.escape(doctor.title)}</p><a class="directory-card__link" href="doctor-details.html?id=${encodeURIComponent(doctor.id)}">View profile →</a></div></article>`).join('');
    const filter = () => { const q=document.querySelector('#doctorSearch').value.toLowerCase().trim(); let shown=0; [...grid.children].forEach(card=>{const visible=(!q||card.dataset.name.includes(q))&&(!department.value||card.dataset.department===department.value)&&(!specialty.value||card.dataset.specialty===specialty.value);card.hidden=!visible;if(visible)shown++;});count.textContent=`${shown} ${shown===1?'profile':'profiles'}`; };
    document.querySelector('#doctorSearch').addEventListener('input',filter); department.addEventListener('change',filter); specialty.addEventListener('change',filter); filter();
  },

  renderDoctor(doctors, departments, services) {
    const id = new URLSearchParams(location.search).get('id'); const doctor = doctors.find(item => item.id === id || item.slug === id); const target=document.querySelector('[data-detail]');
    if (!doctor) { target.innerHTML='<div class="empty-state"><h2>Clinician profile not found</h2><p>This profile may be unavailable or awaiting hospital approval.</p><a class="btn btn--primary" href="doctors.html">Back to doctors</a></div>'; document.title='Clinician Profile Not Found | IMSUTH'; return; }
    const dept=departments.find(item=>item.id===doctor.departmentId); document.title=`${doctor.name} | IMSUTH`; document.querySelector('[data-page-title]').textContent=doctor.name; document.querySelector('[data-breadcrumb-current]').textContent=doctor.name;
    const canonical=`https://www.imsuth.org/doctor-details.html?id=${encodeURIComponent(doctor.id)}`; document.querySelector('link[rel=canonical]').href=canonical; document.querySelector('meta[property="og:url"]').content=canonical; document.querySelector('meta[property="og:title"]').content=`${doctor.name} | IMSUTH`;
    target.innerHTML=`<div class="detail-layout"><article class="detail-copy">${doctor.photo?`<img class="profile-detail__photo" src="${this.escape(doctor.photo)}" alt="${this.escape(doctor.name)}">`:''}<h2>Profile</h2><p>${this.escape(doctor.bio)}</p>${doctor.qualifications?.length?`<h2>Qualifications</h2><ul class="detail-list">${doctor.qualifications.map(x=>`<li>${this.escape(x)}</li>`).join('')}</ul>`:''}${doctor.clinicalInterests?.length?`<h2>Clinical interests</h2><ul class="detail-list">${doctor.clinicalInterests.map(x=>`<li>${this.escape(x)}</li>`).join('')}</ul>`:''}</article><aside class="detail-sidebar"><div class="sidebar-card"><h2>${this.escape(doctor.title)}</h2><p>${this.escape(doctor.specialty)}</p>${dept?`<a class="directory-card__link" href="department-details.html?id=${encodeURIComponent(dept.id)}">${this.escape(dept.name)} →</a>`:''}</div><a class="btn btn--primary btn--block" href="appointment.html?department=${encodeURIComponent(doctor.departmentId)}&doctor=${encodeURIComponent(doctor.id)}">Request appointment</a></aside></div>`;
    this.addBreadcrumbSchema(['Home','Doctors',doctor.name],['https://www.imsuth.org/','https://www.imsuth.org/doctors.html',canonical]);
  },

  renderPatientInfo(info) {
    const prep=document.querySelector('[data-preparation]'); const faq=document.querySelector('[data-patient-faq]');
    prep.innerHTML=info.preparingForVisit.map((item,index)=>`<div class="accordion__item${index===0?' accordion__item--open':''}"><button class="accordion__trigger" aria-expanded="${index===0}" aria-controls="panel-${this.escape(item.id)}"><span>${this.escape(item.title)}</span><span class="accordion__icon">+</span></button><div class="accordion__panel" id="panel-${this.escape(item.id)}"><div class="accordion__panel-inner"><p>${this.escape(item.content)}</p></div></div></div>`).join('');
    faq.innerHTML=info.faqs.map(item=>`<div class="accordion__item"><button class="accordion__trigger" aria-expanded="false" aria-controls="faq-${this.escape(item.id)}"><span>${this.escape(item.question)}</span><span class="accordion__icon">+</span></button><div class="accordion__panel" id="faq-${this.escape(item.id)}"><div class="accordion__panel-inner"><p>${this.escape(item.answer)}</p></div></div></div>`).join('');
    const initialPanel = prep.querySelector('.accordion__item--open .accordion__panel');
    if (initialPanel) initialPanel.style.maxHeight = `${initialPanel.scrollHeight}px`;
    [prep,faq].forEach(group=>group.querySelectorAll('.accordion__trigger').forEach(button=>button.addEventListener('click',()=>{const item=button.parentElement;const open=item.classList.toggle('accordion__item--open');button.setAttribute('aria-expanded',String(open));item.querySelector('.accordion__panel').style.maxHeight=open?`${item.querySelector('.accordion__panel').scrollHeight}px`:'';})));
  },

  renderFacilities(facilities) {
    const grid=document.querySelector('[data-facility-grid]');
    grid.innerHTML=facilities.length?facilities.map(item=>`<article class="facility-card"><div class="facility-card__image">${item.image?`<img src="${this.escape(item.image)}" alt="${this.escape(item.name)} at IMSUTH" width="900" height="600" loading="lazy">`:'<span aria-hidden="true">IMSUTH</span>'}</div><div class="facility-card__body"><p class="eyebrow">Hospital facility</p><h2>${this.escape(item.name)}</h2><p>${this.escape(item.description)}</p><a class="directory-card__link" href="facility-details.html?id=${encodeURIComponent(item.id)}">View facility →</a></div></article>`).join(''):'<div class="empty-state"><h2>Facility information is being reviewed</h2><p>Confirmed facilities will be published here.</p></div>';
  },

  renderFacility(facilities, departments, services) {
    const id=new URLSearchParams(location.search).get('id');const facility=facilities.find(item=>item.id===id||item.slug===id);const target=document.querySelector('[data-detail]');
    if(!facility){target.innerHTML='<div class="empty-state"><h2>Facility not found</h2><p>This facility may be unavailable or awaiting approval.</p><a class="btn btn--primary" href="facilities.html">Back to facilities</a></div>';document.title='Facility Not Found | IMSUTH';return;}
    document.title=`${facility.name} | IMSUTH Facilities`;document.querySelector('[data-page-title]').textContent=facility.name;document.querySelector('[data-breadcrumb-current]').textContent=facility.name;const canonical=`https://www.imsuth.org/facility-details.html?id=${encodeURIComponent(facility.id)}`;document.querySelector('link[rel=canonical]').href=canonical;document.querySelector('meta[property="og:url"]').content=canonical;document.querySelector('meta[property="og:title"]').content=`${facility.name} | IMSUTH`;
    const relatedDepartments=facility.relatedDepartments.map(id=>departments.find(x=>x.id===id)).filter(Boolean);const relatedServices=facility.relatedServices.map(id=>services.find(x=>x.id===id)).filter(Boolean);
    target.innerHTML=`${facility.image?`<img class="facility-hero-image" src="${this.escape(facility.image)}" alt="${this.escape(facility.name)} at IMSUTH" width="1200" height="700">`:''}<div class="detail-layout"><article class="detail-copy"><h2>Overview</h2><p>${this.escape(facility.description)}</p><h2>How this supports patients</h2><p>${this.escape(facility.patientRelevance)}</p>${relatedServices.length?`<h2>Services supported</h2><ul class="detail-list">${relatedServices.map(x=>`<li><a href="service-details.html?id=${encodeURIComponent(x.id)}">${this.escape(x.name)}</a></li>`).join('')}</ul>`:''}</article><aside class="detail-sidebar">${relatedDepartments.length?`<div class="sidebar-card"><h2>Related departments</h2><ul class="sidebar-list">${relatedDepartments.map(x=>`<li><a href="department-details.html?id=${encodeURIComponent(x.id)}">${this.escape(x.name)}</a></li>`).join('')}</ul></div>`:''}<a class="btn btn--primary btn--block" href="contact.html">Contact IMSUTH</a></aside></div>`;this.addBreadcrumbSchema(['Home','Facilities',facility.name],['https://www.imsuth.org/','https://www.imsuth.org/facilities.html',canonical]);
  },

  renderResearch(sections, publications) {
    const sectionGrid=document.querySelector('[data-research-sections]');const publicationGrid=document.querySelector('[data-publications]');
    sectionGrid.innerHTML=sections.map((item,index)=>`<article class="info-card"><span class="number-mark">0${index+1}</span><h2>${this.escape(item.title)}</h2><p>${this.escape(item.summary)}</p></article>`).join('');
    publicationGrid.innerHTML=publications.length?publications.map(item=>`<article class="publication-card"><p class="eyebrow">${this.escape(item.category)}</p><h3>${this.escape(item.title)}</h3><p>${this.escape(item.summary)}</p><p>${this.escape(item.authors.join(', '))} · ${this.escape(item.date)}</p></article>`).join(''):'<div class="empty-state"><h2>Publications are being reviewed</h2><p>Verified IMSUTH publications will be published following institutional review.</p></div>';
  },

  renderNewsDirectory(items) {
    const featured=document.querySelector('[data-featured-news]'); const grid=document.querySelector('[data-news-grid]'); const count=document.querySelector('[data-result-count]');
    const categories=[...new Set(items.map(item=>item.category).filter(Boolean))].sort(); const category=document.querySelector('#newsCategory'); categories.forEach(value=>category.insertAdjacentHTML('beforeend',`<option value="${this.escape(value)}">${this.escape(value)}</option>`));
    const featuredItem=items.find(item=>item.featured); featured.innerHTML=featuredItem?this.newsCard(featuredItem,true):'';
    const regular=items.filter(item=>item!==featuredItem); grid.innerHTML=regular.length?regular.map(item=>this.newsCard(item,false)).join(''):'<div class="empty-state"><h2>News and updates</h2><p>Official IMSUTH news and updates will be published here.</p></div>';
    if(!items.length){count.textContent='0 updates';return;}
    const filter=()=>{const q=document.querySelector('#newsSearch').value.toLowerCase().trim();let shown=0;[...grid.querySelectorAll('.news-item')].forEach(card=>{const visible=(!q||card.dataset.search.includes(q))&&(!category.value||card.dataset.category===category.value);card.hidden=!visible;if(visible)shown++;});count.textContent=`${shown} ${shown===1?'update':'updates'}`;};document.querySelector('#newsSearch').addEventListener('input',filter);category.addEventListener('change',filter);filter();
  },

  newsCard(item, featured) {
    return `<article class="news-item${featured?' news-item--featured':''}" data-search="${this.escape(`${item.title} ${item.excerpt}`.toLowerCase())}" data-category="${this.escape(item.category)}">${item.image?`<img src="${this.escape(item.image)}" alt="" width="900" height="600" loading="lazy">`:''}<div><p class="eyebrow">${this.escape(item.type==='event'?'Event':item.category)}</p><h2><a href="article.html?id=${encodeURIComponent(item.id)}">${this.escape(item.title)}</a></h2><p>${this.escape(item.excerpt)}</p><p class="content-meta">${this.escape(item.author)}${item.publishedAt?` · ${this.escape(new Date(item.publishedAt).toLocaleDateString('en-NG'))}`:''}</p></div></article>`;
  },

  renderArticle(items) {
    const id=new URLSearchParams(location.search).get('id');const item=items.find(record=>record.id===id||record.slug===id);const target=document.querySelector('[data-detail]');
    if(!item){target.innerHTML='<div class="empty-state"><h2>Article not found</h2><p>This story may be unavailable or awaiting publication approval.</p><a class="btn btn--primary" href="news.html">Back to news</a></div>';document.title='Article Not Found | IMSUTH';document.querySelector('meta[name=robots]').content='noindex,follow';return;}
    document.title=`${item.title} | IMSUTH`;document.querySelector('[data-page-title]').textContent=item.title;document.querySelector('[data-breadcrumb-current]').textContent=item.title;document.querySelector('meta[name=description]').content=item.excerpt;const canonical=`https://www.imsuth.org/article.html?id=${encodeURIComponent(item.id)}`;document.querySelector('link[rel=canonical]').href=canonical;document.querySelector('meta[property="og:title"]').content=item.title;document.querySelector('meta[property="og:description"]').content=item.excerpt;document.querySelector('meta[property="og:url"]').content=canonical;
    const related=items.filter(record=>record.id!==item.id&&record.category===item.category).slice(0,3);target.innerHTML=`<article class="article-layout">${item.image?`<img class="article-image" src="${this.escape(item.image)}" alt="" width="1200" height="700">`:''}<p class="content-meta">${this.escape(item.category)} · ${this.escape(item.author)} · ${this.escape(new Date(item.publishedAt).toLocaleDateString('en-NG',{dateStyle:'long'}))}</p><div class="article-body">${(item.body||[]).map(block=>block.type==='heading'?`<h2>${this.escape(block.text)}</h2>`:`<p>${this.escape(block.text)}</p>`).join('')}</div><div class="share-actions" aria-label="Share this article"><a href="mailto:?subject=${encodeURIComponent(item.title)}&body=${encodeURIComponent(canonical)}">Share by email</a><button type="button" data-copy-link>Copy link</button><span role="status" data-copy-status></span></div>${related.length?`<section><h2>Related stories</h2><div class="content-grid">${related.map(x=>this.newsCard(x,false)).join('')}</div></section>`:''}</article>`;target.querySelector('[data-copy-link]').addEventListener('click',async()=>{await navigator.clipboard.writeText(canonical);target.querySelector('[data-copy-status]').textContent='Link copied.';});
    const schema=document.createElement('script');schema.type='application/ld+json';schema.textContent=JSON.stringify({'@context':'https://schema.org','@type':'NewsArticle',headline:item.title,datePublished:item.publishedAt,author:{'@type':'Organization',name:item.author||'IMSUTH'},publisher:{'@type':'Organization',name:'Imo State University Teaching Hospital'},mainEntityOfPage:canonical});document.head.appendChild(schema);this.addBreadcrumbSchema(['Home','News',item.title],['https://www.imsuth.org/','https://www.imsuth.org/news.html',canonical]);
  },

  renderCareers(items) {
    const grid=document.querySelector('[data-careers-grid]');grid.innerHTML=items.length?items.map(job=>`<article class="directory-card"><p class="eyebrow">${this.escape(job.employmentType)}</p><h2>${this.escape(job.title)}</h2><p>${this.escape(job.summary)}</p><p class="content-meta">${this.escape(job.department)} · ${this.escape(job.location)}</p></article>`).join(''):'<div class="empty-state"><h2>Current vacancies</h2><p>There are currently no published vacancies.</p></div>';
  },

  renderLeader(items) {
    const id = new URLSearchParams(location.search).get('id');
    const leader = items.find(item => item.id === id || item.slug === id);
    const target = document.querySelector('[data-detail]');
    if (!leader) {
      target.innerHTML = '<div class="empty-state"><h2>Leadership profile not found</h2><p>This profile is unavailable.</p><a class="btn btn--primary" href="about.html">About IMSUTH</a></div>';
      document.title = 'Leadership Profile Not Found | IMSUTH';
      return;
    }
    document.title = `${leader.name} | IMSUTH Leadership`;
    document.querySelector('[data-page-title]').textContent = leader.name;
    document.querySelector('[data-breadcrumb-current]').textContent = leader.name;
    document.querySelector('meta[name="description"]').content = leader.summary;
    const canonical = `https://www.imsuth.org/leadership-profile.html?id=${encodeURIComponent(leader.id)}`;
    document.querySelector('link[rel="canonical"]').href = canonical;
    document.querySelector('meta[property="og:title"]').content = `${leader.name} | IMSUTH Leadership`;
    document.querySelector('meta[property="og:description"]').content = leader.summary;
    document.querySelector('meta[property="og:url"]').content = canonical;
    target.innerHTML = `<div class="leader-profile"><aside><img class="leader-profile__photo" src="${this.escape(leader.photo)}" alt="${this.escape(leader.name)}" width="532" height="640"></aside><article class="detail-copy"><p class="eyebrow">Hospital leadership</p><h2>Biography</h2>${leader.biography.map(paragraph => `<p>${this.escape(paragraph)}</p>`).join('')}<h2>Education and professional experience</h2><p>${this.escape(leader.education)}</p><p>${this.escape(leader.experience)}</p><h2>Research</h2><p>${this.escape(leader.research)}</p><a class="btn btn--secondary" href="about.html">About IMSUTH</a></article></div>`;
    this.addBreadcrumbSchema(['Home','About IMSUTH',leader.name],['https://www.imsuth.org/','https://www.imsuth.org/about.html',canonical]);
  },

  renderContact(settings) {
    const contact = settings.contact || {};
    document.querySelectorAll('[data-contact-address]').forEach(el => el.textContent = contact.address || 'Address awaiting confirmation');
    document.querySelectorAll('[data-contact-hours]').forEach(el => el.textContent = contact.hours || 'Opening hours awaiting confirmation');
    document.querySelectorAll('[data-contact-phone]').forEach(el => { el.textContent = contact.phone || 'Phone awaiting confirmation'; if (contact.phone && el.tagName === 'A') el.href = `tel:${contact.phone.replace(/\s/g,'')}`; });
    document.querySelectorAll('[data-contact-email]').forEach(el => { el.textContent = contact.email || 'Email awaiting confirmation'; if (contact.email && el.tagName === 'A') el.href = `mailto:${contact.email}`; });
    const emergency = document.querySelector('[data-emergency-contact]');
    emergency.textContent = settings.emergency?.phone || 'Emergency contact information will be published following hospital confirmation.';
    const form = document.querySelector('#contactForm');
    if (form) this.setupContactForm(form);
  },

  setupContactForm(form) {
    form.dataset.handled = 'true';
    form.addEventListener('submit', async event => {
      event.preventDefault();
      const fields = [...form.querySelectorAll('[data-validate]')];
      let valid = true;
      fields.forEach(field => {
        const error = form.querySelector(`[data-error="${field.name}"]`);
        let message = '';
        if (field.required && !field.value.trim()) message = 'This field is required.';
        if (!message && field.type === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(field.value)) message = 'Enter a valid email address.';
        field.classList.toggle('form__input--error', Boolean(message));
        error.textContent = message; error.classList.toggle('form__error--visible', Boolean(message));
        if (message) valid = false;
      });
      if (!valid) { form.querySelector('.form__input--error')?.focus(); return; }
      const button = form.querySelector('[type="submit"]');
      const status = form.querySelector('[role="status"]');
      button.disabled = true; button.textContent = 'Sending…';
      try { await API.submitContact(Object.fromEntries(new FormData(form))); status.textContent = API.developmentMode ? 'Your message has been received in development mode. No message was sent externally.' : 'Your message has been received.'; status.className = 'form__status form__status--success form__status--visible'; form.reset(); }
      catch { status.textContent = 'We could not submit your message. Please contact the hospital directly.'; status.className = 'form__status form__status--error form__status--visible'; }
      finally { button.disabled = false; button.textContent = 'Send message'; }
    });
  },

  addBreadcrumbSchema(names, urls) {
    const script = document.createElement('script'); script.type = 'application/ld+json';
    script.textContent = JSON.stringify({'@context':'https://schema.org','@type':'BreadcrumbList',itemListElement:names.map((name,index)=>({'@type':'ListItem',position:index+1,name,item:urls[index]}))});
    document.head.appendChild(script);
  }
};
document.addEventListener('DOMContentLoaded', () => InternalPages.init());
