const SearchUI = {
    currentPage: 'homepage',

    init() {
        this.cacheElements();
        this.bindEvents();
    },

    cacheElements() {
        this.searchInput = document.querySelector('.search__input');
        this.searchClear = document.querySelector('.search__clear');
        this.searchResults = document.querySelector('.search-results');
        this.searchContainer = document.querySelector('.search');
    },

    bindEvents() {
        if (this.searchInput) {
            this.searchInput.addEventListener('input', (e) => this.handleInput(e));
            this.searchInput.addEventListener('focus', () => this.showResults());
        }

        if (this.searchClear) {
            this.searchClear.addEventListener('click', () => this.clearSearch());
        }

        document.addEventListener('click', (e) => {
            if (this.searchContainer && !this.searchContainer.contains(e.target)) {
                this.hideResults();
            }
        });
    },

    async handleInput(e) {
        const query = e.target.value.trim();
        
        if (this.searchClear) {
            this.searchClear.classList.toggle('search__clear--visible', query.length > 0);
        }

        if (query.length < 2) {
            this.hideResults();
            return;
        }

        let results = [];

        switch (this.currentPage) {
            case 'doctors':
                results = DataStore.searchDoctors(query);
                break;
            case 'departments':
                results = DataStore.searchDepartments(query);
                break;
            case 'news':
                results = DataStore.searchNews(query);
                break;
            default:
                results = this.searchGlobal(query);
        }

        this.displayResults(results, query);
    },

    searchGlobal(query) {
        const q = query.toLowerCase();
        const results = {
            departments: DataStore.getDepartments().filter(d => 
                d.name.toLowerCase().includes(q) || d.description.toLowerCase().includes(q)
            ),
            doctors: DataStore.searchDoctors(query),
            news: DataStore.searchNews(query)
        };

        return results;
    },

    displayResults(results, query) {
        if (!this.searchResults) return;

        if (this.currentPage === 'homepage' && typeof results === 'object' && !Array.isArray(results)) {
            const totalResults = results.departments.length + results.doctors.length + results.news.length;
            
            if (totalResults === 0) {
                this.searchResults.innerHTML = `
                    <div class="search-results__empty">
                        <p>No results found for "${this.escapeHtml(query)}"</p>
                    </div>
                `;
            } else {
                let html = '';
                
                if (results.departments.length > 0) {
                    html += '<div class="search-results__section"><h4>Departments</h4><ul>';
                    results.departments.slice(0, 3).forEach(dept => {
                        html += `<li><a href="/departments/${dept.slug}">${this.escapeHtml(dept.name)}</a></li>`;
                    });
                    html += '</ul></div>';
                }
                
                if (results.doctors.length > 0) {
                    html += '<div class="search-results__section"><h4>Doctors</h4><ul>';
                    results.doctors.slice(0, 3).forEach(doctor => {
                        html += `<li><a href="/doctors/${doctor.id}">${this.escapeHtml(doctor.name)}</a></li>`;
                    });
                    html += '</ul></div>';
                }
                
                if (results.news.length > 0) {
                    html += '<div class="search-results__section"><h4>News</h4><ul>';
                    results.news.slice(0, 3).forEach(article => {
                        html += `<li><a href="/news/${article.slug}">${this.escapeHtml(article.title)}</a></li>`;
                    });
                    html += '</ul></div>';
                }
                
                this.searchResults.innerHTML = html;
            }
        } else if (Array.isArray(results)) {
            if (results.length === 0) {
                this.searchResults.innerHTML = `
                    <div class="search-results__empty">
                        <p>No results found for "${this.escapeHtml(query)}"</p>
                    </div>
                `;
            } else {
                let html = '<ul>';
                results.slice(0, 5).forEach(item => {
                    const title = item.name || item.title || 'Untitled';
                    const url = this.getResultUrl(item);
                    html += `<li><a href="${url}">${this.escapeHtml(title)}</a></li>`;
                });
                html += '</ul>';
                this.searchResults.innerHTML = html;
            }
        }

        this.showResults();
    },

    getResultUrl(item) {
        if (item.slug) return `/${this.currentPage}/${item.slug}`;
        if (item.id) return `/${this.currentPage}/${item.id}`;
        return '#';
    },

    showResults() {
        if (this.searchResults) {
            this.searchResults.style.display = 'block';
        }
    },

    hideResults() {
        if (this.searchResults) {
            this.searchResults.style.display = 'none';
        }
    },

    clearSearch() {
        if (this.searchInput) {
            this.searchInput.value = '';
        }
        if (this.searchClear) {
            this.searchClear.classList.remove('search__clear--visible');
        }
        this.hideResults();
    },

    setPage(page) {
        this.currentPage = page;
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

if (typeof module !== 'undefined' && module.exports) {
    module.exports = SearchUI;
}
