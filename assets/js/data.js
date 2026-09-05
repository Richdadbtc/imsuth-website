const DataStore = {
    cache: {},
    loaded: false,

    async loadAll() {
        if (this.loaded) return this.cache;

        try {
            const [departments, doctors, services, news, settings, facilities, research, publications, patientInfo, careers, leadership] = await Promise.all([
                this.fetchJSON('/data/departments.json'),
                this.fetchJSON('/data/doctors.json'),
                this.fetchJSON('/data/services.json'),
                this.fetchJSON('/data/news.json'),
                this.fetchJSON('/data/settings.json'),
                this.fetchJSON('/data/facilities.json'),
                this.fetchJSON('/data/research.json'),
                this.fetchJSON('/data/publications.json'),
                this.fetchJSON('/data/patient-info.json'),
                this.fetchJSON('/data/careers.json'),
                this.fetchJSON('/data/leadership.json')
            ]);

            this.cache = {
                departments: departments?.departments || departments || [],
                doctors: (doctors?.doctors || doctors || []).filter(item => item.verified === true),
                services: services?.services || services || [],
                news: (news?.news || news || []).filter(item => item.verified === true),
                settings: settings || {},
                facilities: (facilities?.facilities || facilities || []).filter(item => item.verified === true),
                research: (research?.sections || []).filter(item => item.verified === true),
                publications: (publications?.publications || []).filter(item => item.verified === true),
                careers: (careers?.careers || careers || []).filter(item => item.verified === true),
                leadership: (leadership?.leaders || leadership || []).filter(item => item.verified === true),
                patientInfo: {
                    preparingForVisit: (patientInfo?.preparingForVisit || []).filter(item => item.verified === true),
                    faqs: (patientInfo?.faqs || []).filter(item => item.verified === true)
                }
            };

            this.loaded = true;
            return this.cache;
        } catch (error) {
            console.error('Failed to load data:', error);
            return this.cache;
        }
    },

    async fetchJSON(url) {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`Failed to fetch ${url}`);
        return response.json();
    },

    getDepartments() {
        return this.cache.departments || [];
    },

    getDoctors() {
        return this.cache.doctors || [];
    },

    getServices() {
        return this.cache.services || [];
    },

    getNews() {
        return this.cache.news || [];
    },

    getSettings() {
        return this.cache.settings || {};
    },

    getFacilities() { return this.cache.facilities || []; },
    getResearch() { return this.cache.research || []; },
    getPublications() { return this.cache.publications || []; },
    getPatientInfo() { return this.cache.patientInfo || { preparingForVisit: [], faqs: [] }; },
    getCareers() { return this.cache.careers || []; },
    getLeadership() { return this.cache.leadership || []; },

    getDepartmentBySlug(slug) {
        return this.getDepartments().find(d => d.slug === slug);
    },

    getDoctorById(id) {
        return this.getDoctors().find(d => d.id === id);
    },

    getNewsBySlug(slug) {
        return this.getNews().find(n => n.slug === slug);
    },

    getFeaturedNews() {
        return this.getNews().filter(n => n.featured);
    },

    getNewsByCategory(category) {
        return this.getNews().filter(n => n.category === category);
    },

    searchDoctors(query) {
        const q = query.toLowerCase().trim();
        if (!q) return this.getDoctors();
        return this.getDoctors().filter(doctor => 
            doctor.name.toLowerCase().includes(q) ||
            doctor.specialty.toLowerCase().includes(q) ||
            (doctor.departmentId || '').toLowerCase().includes(q)
        );
    },

    filterDoctorsByDepartment(departmentSlug) {
        if (!departmentSlug) return this.getDoctors();
        return this.getDoctors().filter(d => d.departmentId === departmentSlug);
    },

    filterDoctorsBySpecialty(specialty) {
        if (!specialty) return this.getDoctors();
        return this.getDoctors().filter(d => d.specialty === specialty);
    },

    searchDepartments(query) {
        const q = query.toLowerCase().trim();
        if (!q) return this.getDepartments();
        return this.getDepartments().filter(dept => 
            dept.name.toLowerCase().includes(q) ||
            dept.description.toLowerCase().includes(q)
        );
    },

    searchNews(query) {
        const q = query.toLowerCase().trim();
        if (!q) return this.getNews();
        return this.getNews().filter(article => 
            article.title.toLowerCase().includes(q) ||
            article.excerpt.toLowerCase().includes(q) ||
            article.category.toLowerCase().includes(q)
        );
    },

    getUniqueSpecialties() {
        const doctors = this.getDoctors();
        const specialties = [...new Set(doctors.map(d => d.specialty))];
        return specialties.filter(s => s && s !== 'Doctor Name');
    },

    getUniqueDepartments() {
        const doctors = this.getDoctors();
        const departments = [...new Set(doctors.map(d => d.department))];
        return departments.filter(d => d && d !== 'Doctor Name');
    }
};

if (typeof module !== 'undefined' && module.exports) {
    module.exports = DataStore;
}
