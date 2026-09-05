document.addEventListener('DOMContentLoaded', () => {
    normalizeNavigation();
    enhanceFooter();
    initChatAssistant();
    initMotionEffects();
    document.querySelectorAll('[data-current-year]').forEach(element => {
        element.textContent = new Date().getFullYear();
    });
    initNavigation();
    initScrollToTop();
    initAccordions();
    initTabs();
    initLazyLoading();
    initSearch();
    initAppointmentForm();
    initContactForm();
    initDepartmentFilters();
    initDoctorFilters();
    initNewsFilters();
    loadDynamicContent();
});

function initMotionEffects() {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches || !('IntersectionObserver' in window)) return;

    document.body.classList.add('motion-enabled');
    const selector = [
        '.page-hero__content', '.hero__content', '.quick-access__heading',
        '.section-heading-row', '.section-intro', '.about__content',
        '.leadership-placeholder', '.teaching-band__grid', '.visit-strip__grid',
        '.cta-block', '.directory-card', '.service-card', '.quick-access__card',
        '.profile-card', '.facility-card', '.patient-topic', '.info-card',
        '.publication-card', '.news-item', '.empty-state', '.leader-profile',
        '.privacy-layout', '.article-layout', '.form-card', '.sidebar-card'
    ].join(',');

    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            entry.target.classList.add('reveal-item--visible');
            observer.unobserve(entry.target);
        });
    }, { threshold: 0.12, rootMargin: '0px 0px -36px' });

    const register = root => {
        const candidates = [];
        if (root.nodeType === 1 && root.matches?.(selector)) candidates.push(root);
        root.querySelectorAll?.(selector).forEach(element => candidates.push(element));
        candidates.forEach((element, index) => {
            if (element.classList.contains('reveal-item')) return;
            element.classList.add('reveal-item');
            element.style.setProperty('--reveal-delay', `${Math.min(index % 6, 5) * 55}ms`);
            observer.observe(element);
        });
    };

    register(document);
    const mutations = new MutationObserver(records => {
        records.forEach(record => record.addedNodes.forEach(node => {
            if (node.nodeType === 1) register(node);
        }));
    });
    mutations.observe(document.querySelector('main') || document.body, { childList: true, subtree: true });
}

function enhanceFooter() {
    document.querySelectorAll('.footer').forEach(footer => {
        footer.querySelectorAll('.footer__grid > div > p').forEach(paragraph => {
            paragraph.classList.add('footer__brand-text');
        });
        footer.querySelectorAll('.footer__grid > div > a').forEach(link => {
            link.classList.add('footer__link');
        });
        footer.querySelectorAll('.footer__grid ul').forEach(list => {
            list.classList.add('footer__list');
        });
        footer.querySelectorAll('.footer__grid a').forEach(link => {
            link.classList.add('footer__link');
        });

        if (footer.querySelector('.footer__social')) return;
        const container = footer.querySelector('.container');
        const bottom = footer.querySelector('.footer__bottom');
        if (!container || !bottom) return;

        if (!bottom.querySelector('.footer__powered-by')) {
            const credit = document.createElement('p');
            credit.className = 'footer__powered-by';
            credit.innerHTML = 'Powered by <a href="https://richdadbtc.github.io/rdxtech.com" target="_blank" rel="noopener noreferrer">RDX TECH SERVICES</a>';
            bottom.appendChild(credit);
        }

        const social = document.createElement('div');
        social.className = 'footer__social';
        social.setAttribute('aria-label', 'IMSUTH social media channels');
        social.innerHTML = `
            <p class="footer__social-title">Follow IMSUTH</p>
            <div class="footer__social-icons">
                ${socialIcon('Facebook', '<path d="M14 8h3V4h-3c-3.3 0-5 2-5 5v3H6v4h3v8h4v-8h3.4l.6-4h-4V9c0-.7.3-1 1-1Z"/>')}
                ${socialIcon('Instagram', '<rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" class="social-icon__fill"/>')}
                ${socialIcon('X', '<path d="M5 4h4.2l3.7 5.2L17.4 4H20l-5.9 7 6.4 9H16.3l-4.1-5.8L7.3 20H4.6l6.3-7.6L5 4Zm3 2 9.3 12h1.1L9.1 6H8Z"/>')}
                ${socialIcon('LinkedIn', '<rect x="4" y="9" width="4" height="11"/><circle cx="6" cy="5.5" r="2"/><path d="M11 9h4v1.5c1-1.2 2.2-1.8 3.7-1.8 3 0 4.3 2 4.3 5.4V20h-4v-5.2c0-1.7-.6-2.5-1.9-2.5-1.5 0-2.1 1-2.1 3V20h-4V9Z"/>')}
                ${socialIcon('YouTube', '<path d="M22.5 7.1a3 3 0 0 0-2.1-2.2C18.5 4.4 12 4.4 12 4.4s-6.5 0-8.4.5a3 3 0 0 0-2.1 2.2A31 31 0 0 0 1 12a31 31 0 0 0 .5 4.9 3 3 0 0 0 2.1 2.2c1.9.5 8.4.5 8.4.5s6.5 0 8.4-.5a3 3 0 0 0 2.1-2.2A31 31 0 0 0 23 12a31 31 0 0 0-.5-4.9ZM9.8 15.4V8.6l5.8 3.4-5.8 3.4Z"/>')}
            </div>
            <p class="footer__social-note">Official profile links will be added after verification.</p>`;
        container.insertBefore(social, bottom);
    });
}

function socialIcon(label, artwork) {
    return `<span class="social-icon" role="img" aria-label="${label}" title="${label}"><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">${artwork}</svg></span>`;
}

function initChatAssistant() {
    if (document.querySelector('.chat-assistant')) return;
    const assistant = document.createElement('div');
    assistant.className = 'chat-assistant';
    assistant.innerHTML = `
        <section class="chat-assistant__panel" id="chatAssistantPanel" aria-labelledby="chatAssistantTitle" hidden>
            <div class="chat-assistant__header">
                <div><span class="chat-assistant__status" aria-hidden="true"></span><strong id="chatAssistantTitle">IMSUTH Assistant</strong></div>
                <button class="chat-assistant__close" type="button" aria-label="Close assistant">×</button>
            </div>
            <div class="chat-assistant__body">
                <p>Hello. The virtual assistant is being prepared and is not yet available for live conversations.</p>
                <p class="chat-assistant__notice"><strong>Medical emergency?</strong> Do not use website chat. Contact emergency services or visit the hospital.</p>
                <div class="chat-assistant__actions">
                    <a href="appointment.html">Book an appointment</a>
                    <a href="contact.html">Contact IMSUTH</a>
                </div>
            </div>
        </section>
        <button class="chat-assistant__toggle" type="button" aria-label="Open IMSUTH assistant" aria-controls="chatAssistantPanel" aria-expanded="false">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 4h14a3 3 0 0 1 3 3v8a3 3 0 0 1-3 3h-7l-5.2 3.2c-.7.4-1.5-.1-1.5-.9V18H5a3 3 0 0 1-3-3V7a3 3 0 0 1 3-3Zm2.5 6a1.25 1.25 0 1 0 0 2.5 1.25 1.25 0 0 0 0-2.5Zm4.5 0a1.25 1.25 0 1 0 0 2.5 1.25 1.25 0 0 0 0-2.5Zm4.5 0a1.25 1.25 0 1 0 0 2.5 1.25 1.25 0 0 0 0-2.5Z"/></svg>
            <span>Chat</span>
        </button>`;
    document.body.appendChild(assistant);

    const toggle = assistant.querySelector('.chat-assistant__toggle');
    const close = assistant.querySelector('.chat-assistant__close');
    const panel = assistant.querySelector('.chat-assistant__panel');
    const setOpen = open => {
        panel.hidden = !open;
        toggle.setAttribute('aria-expanded', String(open));
        toggle.setAttribute('aria-label', open ? 'Close IMSUTH assistant' : 'Open IMSUTH assistant');
        assistant.classList.toggle('chat-assistant--open', open);
        if (open) close.focus();
    };
    toggle.addEventListener('click', () => setOpen(panel.hidden));
    close.addEventListener('click', () => setOpen(false));
    document.addEventListener('keydown', event => {
        if (event.key === 'Escape' && !panel.hidden) {
            setOpen(false);
            toggle.focus();
        }
    });
}

function normalizeNavigation() {
    const page = document.body.dataset.page || 'home';
    const activeMap = {
        'department-detail': 'departments', 'doctor-detail': 'doctors',
        'service-detail': 'services', 'facility-detail': 'facilities', 'article-detail': 'news'
    };
    const active = activeMap[page] || page;
    const links = [
        ['home','index.html','Home'], ['about','about.html','About'],
        ['departments','departments.html','Departments'], ['doctors','doctors.html','Doctors'],
        ['services','services.html','Clinical Services'], ['patients','patients.html','Patients & Visitors'],
        ['research','research.html','Teaching & Research'], ['facilities','facilities.html','Facilities'],
        ['news','news.html','News & Events'], ['contact','contact.html','Contact']
    ];
    document.querySelectorAll('.nav__list, .mobile-nav__list').forEach(list => {
        const mobile = list.classList.contains('mobile-nav__list');
        list.innerHTML = links.map(([key, href, label]) => `<li><a class="${mobile ? 'mobile-nav__link' : 'nav__link'}${key === active ? ' active' : ''}" href="${href}"${key === active ? ' aria-current="page"' : ''}>${label}</a></li>`).join('');
    });
}

function initNavigation() {
    if (typeof Navigation !== 'undefined' && typeof Navigation.init === 'function') {
        Navigation.init();
    }
}

function initScrollToTop() {
    const scrollTopBtn = document.querySelector('.scroll-top');
    if (!scrollTopBtn) return;

    window.addEventListener('scroll', () => {
        if (window.scrollY > 500) {
            scrollTopBtn.classList.add('scroll-top--visible');
        } else {
            scrollTopBtn.classList.remove('scroll-top--visible');
        }
    }, { passive: true });

    scrollTopBtn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}

function initAccordions() {
    const accordions = document.querySelectorAll('.accordion');
    if (!accordions.length) return;

    accordions.forEach(accordion => {
        const triggers = accordion.querySelectorAll('.accordion__trigger');
        
        triggers.forEach(trigger => {
            trigger.addEventListener('click', () => {
                const item = trigger.parentElement;
                const isOpen = item.classList.contains('accordion__item--open');
                const panel = item.querySelector('.accordion__panel');
                
                accordion.querySelectorAll('.accordion__item--open').forEach(openItem => {
                    if (openItem !== item) {
                        openItem.classList.remove('accordion__item--open');
                        const openPanel = openItem.querySelector('.accordion__panel');
                        if (openPanel) {
                            openPanel.style.maxHeight = null;
                        }
                    }
                });

                if (isOpen) {
                    item.classList.remove('accordion__item--open');
                    if (panel) {
                        panel.style.maxHeight = null;
                    }
                } else {
                    item.classList.add('accordion__item--open');
                    if (panel) {
                        panel.style.maxHeight = panel.scrollHeight + 'px';
                    }
                }
            });
        });
    });
}

function initTabs() {
    const tabsContainers = document.querySelectorAll('.tabs');
    if (!tabsContainers.length) return;

    tabsContainers.forEach(container => {
        const triggers = container.querySelectorAll('.tabs__trigger');
        const panels = container.querySelectorAll('.tabs__panel');

        triggers.forEach(trigger => {
            trigger.addEventListener('click', () => {
                const targetId = trigger.getAttribute('aria-controls');
                
                triggers.forEach(t => t.classList.remove('tabs__trigger--active'));
                trigger.classList.add('tabs__trigger--active');

                panels.forEach(panel => {
                    if (panel.id === targetId) {
                        panel.classList.add('tabs__panel--active');
                    } else {
                        panel.classList.remove('tabs__panel--active');
                    }
                });
            });
        });
    });
}

function initLazyLoading() {
    if ('loading' in HTMLImageElement.prototype) {
        const images = document.querySelectorAll('img[data-src]');
        images.forEach(img => {
            img.src = img.dataset.src;
            if (img.dataset.srcset) {
                img.srcset = img.dataset.srcset;
            }
        });
    } else {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        if (img.dataset.srcset) {
                            img.srcset = img.dataset.srcset;
                        }
                    }
                    observer.unobserve(img);
                }
            });
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }
}

function initSearch() {
    if (typeof SearchUI !== 'undefined') {
        SearchUI.init();
    }
}

function initAppointmentForm() {
    const form = document.getElementById('appointmentForm');
    if (!form || typeof AppointmentForm === 'undefined') return;

    AppointmentForm.init('appointmentForm');

    DataStore.loadAll().then(data => {
        if (data.departments.length > 0) {
            AppointmentForm.populateDepartments(data.departments);
        }
        if (data.doctors.length > 0) {
            AppointmentForm.populateDoctors(data.doctors);
        }
    });
}

function initContactForm() {
    const form = document.getElementById('contactForm');
    if (!form || form.dataset.handled === 'true' || document.body.dataset.page === 'contact') return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = {
            name: form.querySelector('#contactName')?.value.trim() || '',
            email: form.querySelector('#contactEmail')?.value.trim() || '',
            phone: form.querySelector('#contactPhone')?.value.trim() || '',
            subject: form.querySelector('#contactSubject')?.value.trim() || '',
            message: form.querySelector('#contactMessage')?.value.trim() || ''
        };

        const submitButton = form.querySelector('button[type="submit"]');
        const originalText = submitButton.textContent;
        submitButton.disabled = true;
        submitButton.innerHTML = '<span class="spinner" style="width:20px;height:20px;border-width:2px;"></span> Sending...';

        try {
            await API.submitContact(formData);
            form.reset();
            const successEl = form.querySelector('.form__success');
            if (successEl) successEl.classList.add('form__success--visible');
            setTimeout(() => {
                if (successEl) successEl.classList.remove('form__success--visible');
            }, 5000);
        } catch (error) {
            console.error('Contact form error:', error);
            alert('Failed to send message. Please try again or contact us directly.');
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = originalText;
        }
    });
}

function initDepartmentFilters() {
    const searchInput = document.querySelector('#departmentSearch');
    const filterButtons = document.querySelectorAll('.filter__button');
    const cardsContainer = document.querySelector('.departments__grid');

    if (!searchInput && !filterButtons.length) return;

    let activeFilter = 'all';

    const filterDepartments = () => {
        if (!cardsContainer) return;

        const cards = cardsContainer.querySelectorAll('.department-card');
        const searchTerm = searchInput ? searchInput.value.toLowerCase().trim() : '';

        cards.forEach(card => {
            const name = card.dataset.name || '';
            const description = card.dataset.description || '';
            const category = card.dataset.category || '';

            const matchesSearch = !searchTerm || 
                name.toLowerCase().includes(searchTerm) || 
                description.toLowerCase().includes(searchTerm);

            const matchesFilter = activeFilter === 'all' || category === activeFilter;

            if (matchesSearch && matchesFilter) {
                card.style.display = '';
            } else {
                card.style.display = 'none';
            }
        });
    };

    if (searchInput) {
        searchInput.addEventListener('input', filterDepartments);
    }

    filterButtons.forEach(button => {
        button.addEventListener('click', () => {
            filterButtons.forEach(b => b.classList.remove('filter__button--active'));
            button.classList.add('filter__button--active');
            activeFilter = button.dataset.filter || 'all';
            filterDepartments();
        });
    });
}

function initDoctorFilters() {
    const searchInput = document.querySelector('#doctorSearch');
    const specialtyFilter = document.querySelector('#specialtyFilter');
    const departmentFilter = document.querySelector('#departmentFilter');
    const cardsContainer = document.querySelector('.doctors__grid');

    if (!searchInput && !specialtyFilter && !departmentFilter) return;

    let activeSpecialty = 'all';
    let activeDepartment = 'all';

    const filterDoctors = () => {
        if (!cardsContainer) return;

        const cards = cardsContainer.querySelectorAll('.doctor-card');
        const searchTerm = searchInput ? searchInput.value.toLowerCase().trim() : '';

        cards.forEach(card => {
            const name = card.dataset.name || '';
            const specialty = card.dataset.specialty || '';
            const department = card.dataset.department || '';

            const matchesSearch = !searchTerm || 
                name.toLowerCase().includes(searchTerm) || 
                specialty.toLowerCase().includes(searchTerm);

            const matchesSpecialty = activeSpecialty === 'all' || specialty === activeSpecialty;
            const matchesDepartment = activeDepartment === 'all' || department === activeDepartment;

            if (matchesSearch && matchesSpecialty && matchesDepartment) {
                card.style.display = '';
            } else {
                card.style.display = 'none';
            }
        });
    };

    if (searchInput) {
        searchInput.addEventListener('input', filterDoctors);
    }

    if (specialtyFilter) {
        specialtyFilter.addEventListener('change', (e) => {
            activeSpecialty = e.target.value;
            filterDoctors();
        });
    }

    if (departmentFilter) {
        departmentFilter.addEventListener('change', (e) => {
            activeDepartment = e.target.value;
            filterDoctors();
        });
    }
}

function initNewsFilters() {
    const filterButtons = document.querySelectorAll('.news__filter');
    const cardsContainer = document.querySelector('.news__grid');

    if (!filterButtons.length) return;

    let activeCategory = 'all';

    filterButtons.forEach(button => {
        button.addEventListener('click', () => {
            filterButtons.forEach(b => b.classList.remove('filter__button--active'));
            button.classList.add('filter__button--active');
            activeCategory = button.dataset.category || 'all';

            if (cardsContainer) {
                const cards = cardsContainer.querySelectorAll('.news-card');
                cards.forEach(card => {
                    const category = card.dataset.category || '';
                    if (activeCategory === 'all' || category === activeCategory) {
                        card.style.display = '';
                    } else {
                        card.style.display = 'none';
                    }
                });
            }
        });
    });
}

async function loadDynamicContent() {
    if (typeof DataStore === 'undefined') return;

    try {
        await DataStore.loadAll();
        if (typeof API !== 'undefined') API.configure(DataStore.getSettings());
        
        const servicesGrid = document.querySelector('.services__grid');
        if (servicesGrid && DataStore.getServices().length > 0) {
            renderServices(DataStore.getServices(), servicesGrid);
        }

        const quickAccessGrid = document.querySelector('.quick-access__grid');
        if (quickAccessGrid) {
            renderQuickAccess(quickAccessGrid);
        }

        const newsGrid = document.querySelector('.news__grid');
        if (newsGrid && DataStore.getNews().length > 0) {
            renderNews(DataStore.getNews(), newsGrid);
        }
    } catch (error) {
        console.error('Failed to load dynamic content:', error);
    }
}

function serviceIconMarkup(icon) {
    const icons = {
        stethoscope: '<path d="M6 3v5a4 4 0 0 0 8 0V3M4 3h4m4 0h4M10 12v2a5 5 0 0 0 10 0v-1"/><circle cx="20" cy="10.5" r="2"/>',
        flask: '<path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 1.8 3h10.4A2 2 0 0 0 19 18l-5-9V3M7.5 16h9"/>',
        scan: '<path d="M8 3H4a1 1 0 0 0-1 1v4m13-5h4a1 1 0 0 1 1 1v4m0 8v4a1 1 0 0 1-1 1h-4M8 21H4a1 1 0 0 1-1-1v-4"/><circle cx="12" cy="12" r="5"/><path d="M9 12h6"/>',
        oxygen: '<path d="M9 4h6v3H9zM8 7h8a2 2 0 0 1 2 2v12H6V9a2 2 0 0 1 2-2Z"/><path d="M9 12h6M12 9v6M18 11h2v5h-2"/>',
        kidney: '<path d="M10.5 4.2C6.5 2.8 3 6 3 10.5 3 15 5.4 19 9 19c2.3 0 3-1.8 3-4.2V9.5c0-2.6-.3-4.5-1.5-5.3ZM13.5 4.2C17.5 2.8 21 6 21 10.5 21 15 18.6 19 15 19c-2.3 0-3-1.8-3-4.2"/>',
        shield: '<path d="M12 3 5 6v5c0 4.7 2.8 8.2 7 10 4.2-1.8 7-5.3 7-10V6l-7-3Z"/><path d="m9 12 2 2 4-4"/>'
    };
    const artwork = icons[icon] || icons.stethoscope;
    return `<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${artwork}</svg>`;
}

function renderServices(services, container) {
    if (!container || !services.length) return;

    container.innerHTML = services.map(service => `
        <article class="service-card service-card--visual">
            <div class="service-visual service-visual--panel-${Number(service.imagePanel) || 1}" role="img" aria-label="Illustration representing ${escapeHtml(service.name)}"><span class="service-visual__icon">${serviceIconMarkup(service.icon)}</span></div>
            <div class="service-card__content">
                <h3 class="service-card__title">${escapeHtml(service.name)}</h3>
                <p class="service-card__text">${escapeHtml(service.description)}</p>
                <a href="services.html#${encodeURIComponent(service.slug)}" class="service-card__link">
                    Learn more
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" width="16" height="16">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                    </svg>
                </a>
            </div>
        </article>
    `).join('');
}

function renderQuickAccess(container) {
    if (!container) return;

    const items = [
        { title: 'Book Appointment', text: 'Request a visit with our care team', icon: 'calendar', link: 'appointment.html' },
        { title: 'About IMSUTH', text: 'Learn about our teaching hospital', icon: 'users', link: 'about.html' },
        { title: 'Find a Department', text: 'Explore clinical departments', icon: 'building', link: 'departments.html' },
        { title: 'Laboratory Services', text: 'Learn about diagnostic testing', icon: 'flask', link: 'services.html#laboratory-services' },
        { title: 'Emergency Care', text: 'Emergency services are open 24/7', icon: 'alert', link: '#emergency' },
        { title: 'Contact IMSUTH', text: 'Phone, email and location information', icon: 'info', link: 'contact.html' }
    ];

    container.innerHTML = items.map(item => `
        <a href="${item.link}" class="quick-access__card">
            <div class="quick-access__icon">
                ${quickAccessIconMarkup(item.icon)}
            </div>
            <div>
                <h3 class="quick-access__title">${escapeHtml(item.title)}</h3>
                <p class="quick-access__text">${escapeHtml(item.text)}</p>
            </div>
        </a>
    `).join('');
}

function quickAccessIconMarkup(icon) {
    const icons = {
        calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4m10-4v4M3 10h18M8 14h3v3H8z"/>',
        users: '<circle cx="12" cy="8" r="3"/><path d="M6.5 20v-2a5.5 5.5 0 0 1 11 0v2M5 10a2.5 2.5 0 0 0 0 5m14-5a2.5 2.5 0 0 1 0 5"/>',
        building: '<path d="M4 21V7l8-4 8 4v14M8 9h2m4 0h2M8 13h2m4 0h2M10 21v-4h4v4M2 21h20"/>',
        flask: '<path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 1.8 3h10.4A2 2 0 0 0 19 18l-5-9V3M7.5 16h9"/>',
        alert: '<path d="M12 3 2.8 19a1.4 1.4 0 0 0 1.2 2h16a1.4 1.4 0 0 0 1.2-2L12 3Z"/><path d="M12 9v5m0 3h.01"/>',
        info: '<path d="M7 4h3l1.5 4-2 1.5a16 16 0 0 0 5 5L16 12.5l4 1.5v3c0 1.7-1.3 3-3 3C10 20 4 14 4 7c0-1.7 1.3-3 3-3Z"/>'
    };
    return `<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${icons[icon] || icons.info}</svg>`;
}

function renderNews(news, container) {
    if (!container || !news.length) return;

    const featuredNews = news.filter(n => n.featured);
    const regularNews = news.filter(n => !n.featured);

    let html = '';

    if (featuredNews.length > 0) {
        const featured = featuredNews[0];
        html += `
            <article class="news-card news-card--featured" data-category="${featured.category}">
                <div class="news-card__image">
                    <div class="skeleton" style="width:100%;height:240px;"></div>
                </div>
                <div class="news-card__body">
                    <span class="news-card__category">${escapeHtml(featured.category)}</span>
                    <h3 class="news-card__title"><a href="/news/${featured.slug}">${escapeHtml(featured.title)}</a></h3>
                    <p class="news-card__excerpt">${escapeHtml(featured.excerpt)}</p>
                    <div class="news-card__meta">
                        <span>${formatDate(featured.publishedAt)}</span>
                        <span>${escapeHtml(featured.author)}</span>
                    </div>
                </div>
            </article>
        `;
    }

    html += '<div class="news__grid--secondary">';
    regularNews.forEach(article => {
        html += `
            <article class="news-card" data-category="${article.category}">
                <div class="news-card__body">
                    <span class="news-card__category">${escapeHtml(article.category)}</span>
                    <h3 class="news-card__title"><a href="/news/${article.slug}">${escapeHtml(article.title)}</a></h3>
                    <p class="news-card__excerpt">${escapeHtml(article.excerpt)}</p>
                    <div class="news-card__meta">
                        <span>${formatDate(article.publishedAt)}</span>
                    </div>
                </div>
            </article>
        `;
    });
    html += '</div>';

    container.innerHTML = html;
}

function escapeHtml(text) {
    if (text == null) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-NG', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}
