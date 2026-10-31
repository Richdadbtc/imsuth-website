const Navigation = {
    mobileNavOpen: false,
    dropdownsOpen: [],

    init() {
        this.cacheElements();
        this.bindEvents();
        this.handleResize();
        this.updateActiveLink();
    },

    cacheElements() {
        this.menuToggle = document.querySelector('.header__menu-toggle');
        this.mobileNav = document.querySelector('.mobile-nav');
        this.mobileNavClose = document.querySelector('.mobile-nav__close');
        this.mobileNavOverlay = document.querySelector('.mobile-nav__overlay');
        this.mobileNavLinks = document.querySelectorAll('.mobile-nav__link');
        this.header = document.querySelector('.header');
        this.lastScrollY = 0;
    },

    bindEvents() {
        if (this.menuToggle) {
            this.menuToggle.addEventListener('click', () => this.openMobileNav());
        }

        if (this.mobileNavClose) {
            this.mobileNavClose.addEventListener('click', () => this.closeMobileNav());
        }

        if (this.mobileNavOverlay) {
            this.mobileNavOverlay.addEventListener('click', () => this.closeMobileNav());
        }

        this.mobileNavLinks.forEach(link => {
            link.addEventListener('click', () => this.closeMobileNav());
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.mobileNavOpen) {
                this.closeMobileNav();
            }
        });

        window.addEventListener('scroll', () => this.handleScroll(), { passive: true });
        window.addEventListener('resize', () => this.handleResize());
    },

    openMobileNav() {
        this.mobileNavOpen = true;
        document.body.style.overflow = 'hidden';
        this.mobileNav.classList.add('mobile-nav--open');
        this.mobileNavOverlay.classList.add('mobile-nav__overlay--visible');
        this.menuToggle.setAttribute('aria-expanded', 'true');
        this.mobileNavClose.focus();
    },

    closeMobileNav() {
        this.mobileNavOpen = false;
        document.body.style.overflow = '';
        this.mobileNav.classList.remove('mobile-nav--open');
        this.mobileNavOverlay.classList.remove('mobile-nav__overlay--visible');
        this.menuToggle.setAttribute('aria-expanded', 'false');
        this.menuToggle.focus();
    },

    handleScroll() {
        const currentScrollY = window.scrollY;
        
        if (currentScrollY > 100) {
            this.header.style.boxShadow = 'var(--shadow-md)';
        } else {
            this.header.style.boxShadow = 'var(--shadow-sm)';
        }

        this.lastScrollY = currentScrollY;
    },

    handleResize() {
        if (window.innerWidth >= 768 && this.mobileNavOpen) {
            this.closeMobileNav();
        }
    },

    updateActiveLink() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.nav__link, .mobile-nav__link');
        
        navLinks.forEach(link => {
            const href = link.getAttribute('href');
            if (href && (href === currentPath || (href !== '/' && currentPath.startsWith(href)))) {
                link.classList.add('active');
            } else if (href === '/' && currentPath === '/') {
                link.classList.add('active');
            }
        });
    },

    toggleDropdown(dropdown) {
        const isOpen = dropdown.classList.contains('dropdown--open');
        
        document.querySelectorAll('.dropdown--open').forEach(d => {
            d.classList.remove('dropdown--open');
        });

        if (!isOpen) {
            dropdown.classList.add('dropdown--open');
        }
    }
};

if (typeof module !== 'undefined' && module.exports) {
    module.exports = Navigation;
}
