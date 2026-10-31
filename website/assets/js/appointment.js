const AppointmentForm = {
    form: null,
    fields: {},
    errors: {},
    isValid: false,

    init(formId) {
        this.form = document.getElementById(formId);
        if (!this.form) return;

        this.cacheFields();
        this.bindEvents();
        this.setMinimumDate();
    },

    cacheFields() {
        this.fields = {
            fullName: this.form.querySelector('#fullName'),
            phone: this.form.querySelector('#phone'),
            email: this.form.querySelector('#email'),
            patientType: this.form.querySelector('#patientType'),
            department: this.form.querySelector('#department'),
            preferredDoctor: this.form.querySelector('#preferredDoctor'),
            preferredDate: this.form.querySelector('#preferredDate'),
            preferredTime: this.form.querySelector('#preferredTime'),
            reason: this.form.querySelector('#reason'),
            consent: this.form.querySelector('#consent')
        };
    },

    bindEvents() {
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        if (this.fields.department) this.fields.department.addEventListener('change', () => this.filterDoctors());

        Object.keys(this.fields).forEach(fieldName => {
            const field = this.fields[fieldName];
            if (!field) return;

            field.addEventListener('blur', () => this.validateField(fieldName));
            field.addEventListener('input', () => this.clearFieldError(fieldName));
            field.addEventListener('change', () => this.clearFieldError(fieldName));
        });
    },

    validateField(fieldName) {
        const field = this.fields[fieldName];
        if (!field) return true;

        let error = null;

        switch (fieldName) {
            case 'fullName':
                if (!field.value.trim()) {
                    error = 'Full name is required';
                } else if (field.value.trim().length < 2) {
                    error = 'Name must be at least 2 characters';
                }
                break;

            case 'phone':
                if (!field.value.trim()) {
                    error = 'Phone number is required';
                } else if (!this.isValidPhone(field.value)) {
                    error = 'Please enter a valid phone number';
                }
                break;

            case 'email':
                if (!field.value.trim()) {
                    error = 'Email address is required';
                } else if (!this.isValidEmail(field.value)) {
                    error = 'Please enter a valid email address';
                }
                break;

            case 'patientType':
                if (!field.value) {
                    error = 'Please select patient type';
                }
                break;

            case 'department':
                if (!field.value) {
                    error = 'Please select a department';
                }
                break;

            case 'preferredDate':
                if (!field.value) {
                    error = 'Please select a preferred date';
                } else {
                    const selectedDate = new Date(`${field.value}T00:00:00`);
                    const today = new Date(); today.setHours(0, 0, 0, 0);
                    if (selectedDate <= today) {
                        error = 'Please select a date after today';
                    }
                }
                break;

            case 'preferredTime':
                if (!field.value) {
                    error = 'Please select a preferred time';
                }
                break;

            case 'reason':
                if (!field.value.trim()) {
                    error = 'Please provide a reason for your visit';
                } else if (field.value.trim().length < 10) {
                    error = 'Please provide more details (at least 10 characters)';
                }
                break;

            case 'consent':
                if (!field.checked) {
                    error = 'You must consent to the terms';
                }
                break;
        }

        if (error) {
            this.showFieldError(fieldName, error);
            return false;
        } else {
            this.clearFieldError(fieldName);
            return true;
        }
    },

    showFieldError(fieldName, error) {
        const field = this.fields[fieldName];
        if (!field) return;

        field.classList.add('form__input--error');
        field.setAttribute('aria-invalid', 'true');
        
        const errorElement = this.form.querySelector(`[data-error="${fieldName}"]`);
        if (errorElement) {
            errorElement.textContent = error;
            errorElement.classList.add('form__error--visible');
        }
    },

    clearFieldError(fieldName) {
        const field = this.fields[fieldName];
        if (!field) return;

        field.classList.remove('form__input--error');
        field.removeAttribute('aria-invalid');
        
        const errorElement = this.form.querySelector(`[data-error="${fieldName}"]`);
        if (errorElement) {
            errorElement.classList.remove('form__error--visible');
        }
    },

    validateAll() {
        let isValid = true;
        Object.keys(this.fields).forEach(fieldName => {
            if (!this.validateField(fieldName)) {
                isValid = false;
            }
        });
        return isValid;
    },

    async handleSubmit(e) {
        e.preventDefault();

        if (!this.validateAll()) {
            const firstError = this.form.querySelector('.form__input--error');
            if (firstError) {
                firstError.focus();
            }
            return;
        }

        const submitButton = this.form.querySelector('button[type="submit"]');
        const originalText = submitButton.textContent;
        submitButton.disabled = true;
        submitButton.textContent = 'Submitting…';

        const formData = {
            fullName: this.fields.fullName.value.trim(),
            phone: this.fields.phone.value.trim(),
            email: this.fields.email.value.trim(),
            patientType: this.fields.patientType.value,
            department: this.fields.department.value,
            preferredDoctor: this.fields.preferredDoctor ? this.fields.preferredDoctor.value : '',
            preferredDate: this.fields.preferredDate.value,
            preferredTime: this.fields.preferredTime.value,
            reason: this.fields.reason.value.trim(),
            consent: this.fields.consent.checked
        };

        try {
            await appointmentService.submit(formData);
            this.showSuccess();
            this.form.reset();
        } catch (error) {
            this.showError('We could not submit your request. Please try again or contact the hospital directly.');
            console.error('Appointment submission error:', error);
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = originalText;
        }
    },

    showSuccess() {
        const successElement = this.form.querySelector('.form__success');
        if (successElement) {
            successElement.textContent = API.developmentMode ? 'Your request was validated in development mode. It has not been sent to the hospital.' : 'Your appointment request has been received. The hospital will contact you to confirm.';
            successElement.classList.add('form__success--visible');
        }
        
        setTimeout(() => {
            if (successElement) {
                successElement.classList.remove('form__success--visible');
            }
        }, 5000);
    },

    showError(message) {
        const errorElement = this.form.querySelector('.form__status--error');
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.classList.add('form__status--visible');
        }
    },

    isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    },

    isValidPhone(phone) {
        const compact = phone.replace(/[\s\-\(\)]/g, '');
        return /^(?:\+234|234|0)[789][01]\d{8}$/.test(compact);
    },

    setMinimumDate() {
        if (!this.fields.preferredDate) return;
        const tomorrow = new Date(); tomorrow.setDate(tomorrow.getDate() + 1);
        this.fields.preferredDate.min = tomorrow.toISOString().split('T')[0];
    },

    populateDoctors(doctors) {
        this.allDoctors = doctors;
        this.filterDoctors();
    },

    filterDoctors() {
        const select = this.fields.preferredDoctor;
        if (!select) return;

        const doctors = this.allDoctors || [];
        const department = this.fields.department?.value || '';
        const matches = department ? doctors.filter(doctor => (doctor.departmentId || doctor.department) === department) : doctors;
        select.innerHTML = `<option value="">${matches.length ? 'Select a doctor (optional)' : 'Approved profiles not yet available'}</option>`;
        
        matches.forEach(doctor => {
            const option = document.createElement('option');
            option.value = doctor.id;
            option.textContent = `${doctor.name} - ${doctor.specialty}`;
            select.appendChild(option);
        });
        const requestedDoctor = new URLSearchParams(location.search).get('doctor');
        if (requestedDoctor && matches.some(doctor => doctor.id === requestedDoctor)) select.value = requestedDoctor;
    },

    populateDepartments(departments) {
        const select = this.fields.department;
        if (!select) return;

        select.innerHTML = '<option value="">Select a department</option>';
        
        departments.forEach(dept => {
            const option = document.createElement('option');
            option.value = dept.id;
            option.textContent = dept.name;
            select.appendChild(option);
        });
        const requested = new URLSearchParams(location.search).get('department');
        if (requested && departments.some(dept => dept.id === requested)) {
            select.value = requested;
            this.filterDoctors();
        }
    }
};

const appointmentService = {
    async submit(data) {
        return API.submitAppointment(data);
    }
};

if (typeof module !== 'undefined' && module.exports) {
    module.exports = AppointmentForm;
}
