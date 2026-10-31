const API = {
    baseURL: '',
    developmentMode: true,
    endpoints: {
        departments: '/api/departments',
        doctors: '/api/doctors',
        services: '/api/services',
        news: '/api/news',
        appointment: '/api/appointments',
        contact: '/api/contact'
    },

    async request(endpoint, options = {}) {
        const url = this.baseURL ? `${this.baseURL}${endpoint}` : endpoint;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        if (config.body && typeof config.body === 'object') {
            config.body = JSON.stringify(config.body);
        }

        const response = await fetch(url, config);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return response.json();
    },

    async getDepartments() {
        return this.request(this.endpoints.departments);
    },

    async getDoctors() {
        return this.request(this.endpoints.doctors);
    },

    async getServices() {
        return this.request(this.endpoints.services);
    },

    async getNews() {
        return this.request(this.endpoints.news);
    },

    async submitAppointment(data) {
        if (this.developmentMode && !this.baseURL) {
            await new Promise(resolve => setTimeout(resolve, 500));
            return { ok: true, mode: 'development', data };
        }
        return this.request(this.endpoints.appointment, {
            method: 'POST',
            body: data
        });
    },

    async submitContact(data) {
        if (this.developmentMode && !this.baseURL) {
            await new Promise(resolve => setTimeout(resolve, 500));
            return { ok: true, mode: 'development', data };
        }
        return this.request(this.endpoints.contact, {
            method: 'POST',
            body: data
        });
    },

    setBaseURL(url) {
        this.baseURL = url.replace(/\/$/, '');
        this.developmentMode = false;
    },

    configure(settings = {}) {
        const forms = settings.forms || {};
        this.developmentMode = forms.mode !== 'production';
        if (forms.appointmentEndpoint) this.endpoints.appointment = forms.appointmentEndpoint;
        if (forms.contactEndpoint) this.endpoints.contact = forms.contactEndpoint;
    },

    useLocalData() {
        this.endpoints.departments = '/data/departments.json';
        this.endpoints.doctors = '/data/doctors.json';
        this.endpoints.services = '/data/services.json';
        this.endpoints.news = '/data/news.json';
    }
};

if (typeof module !== 'undefined' && module.exports) {
    module.exports = API;
}
