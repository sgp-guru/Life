document.addEventListener('DOMContentLoaded', () => {
    // --- Mobile Menu Toggle ---
    const menuToggle = document.querySelector('.menu-toggle');
    const navLinks = document.querySelector('.nav-links');

    if (menuToggle && navLinks) {
        menuToggle.addEventListener('click', () => {
            navLinks.classList.toggle('active');
            const icon = menuToggle.querySelector('i');
            if (icon) {
                icon.className = navLinks.classList.contains('active') ? 'fas fa-times' : 'fas fa-bars';
            }
        });
    }

    // --- Dark Mode Toggler ---
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const savedTheme = localStorage.getItem('theme') || 'light';
    
    // Set initial theme
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeIcon(newTheme);
            
            showFloatingAlert(`Theme switched to ${newTheme} mode.`, "info");
        });
    }

    function updateThemeIcon(theme) {
        if (!themeToggleBtn) return;
        const icon = themeToggleBtn.querySelector('i');
        if (icon) {
            icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
    }

    // --- Alert Message Closing ---
    const alertCloses = document.querySelectorAll('.alert-close');
    alertCloses.forEach(closeBtn => {
        closeBtn.addEventListener('click', (e) => {
            const alert = e.target.closest('.alert');
            if (alert) {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 300);
            }
        });
    });

    // Auto-remove flash alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });

    // --- FAQ Accordion ---
    const faqItems = document.querySelectorAll('.faq-item');
    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');
        if (question) {
            question.addEventListener('click', () => {
                const isActive = item.classList.contains('active');
                faqItems.forEach(faq => faq.classList.remove('active'));
                if (!isActive) item.classList.add('active');
            });
        }
    });

    // --- Animated Blood Availability Chart ---
    const chartBars = document.querySelectorAll('.chart-bar-fill');
    setTimeout(() => {
        chartBars.forEach(bar => {
            const percentage = bar.getAttribute('data-percentage');
            if (percentage) {
                bar.style.width = `${percentage}%`;
            }
        });
    }, 150);

    // --- Dynamic Indian Locations Dropdown (AJAX) ---
    const stateSelect = document.querySelector('select[name="state"]');
    const citySelect = document.querySelector('select[name="city"]');
    let locationDataCache = null;

    if (stateSelect && citySelect) {
        const initialCityVal = citySelect.getAttribute('data-selected');
        
        // Load locations mapping
        fetchLocations().then(data => {
            locationDataCache = data;
            
            // Populate State list if it is not pre-populated
            if (stateSelect.children.length <= 1) {
                stateSelect.innerHTML = '<option value="" disabled selected>Select State</option>';
                Object.keys(data).sort().forEach(state => {
                    const opt = document.createElement('option');
                    opt.value = state;
                    opt.textContent = state;
                    stateSelect.appendChild(opt);
                });
            }

            // If a state was pre-selected (e.g. edit donor form), trigger city population
            if (stateSelect.value) {
                populateCities(stateSelect.value, initialCityVal);
            }
        });

        stateSelect.addEventListener('change', (e) => {
            populateCities(e.target.value, "");
        });
    }

    async function fetchLocations() {
        if (locationDataCache) return locationDataCache;
        try {
            const res = await fetch('/api/locations');
            return await res.json();
        } catch (err) {
            console.error("Failed to load locations API:", err);
            return {};
        }
    }

    function populateCities(stateName, selectedCity) {
        if (!locationDataCache || !citySelect) return;
        const cities = locationDataCache[stateName] || [];
        
        citySelect.innerHTML = '<option value="" disabled selected>Select City</option>';
        cities.sort().forEach(city => {
            const opt = document.createElement('option');
            opt.value = city;
            opt.textContent = city;
            if (city === selectedCity) {
                opt.selected = true;
            }
            citySelect.appendChild(opt);
        });
    }

    // --- Password Reset AJAX handler ---
    const resetTrigger = document.getElementById('forgot-password-trigger');
    if (resetTrigger) {
        resetTrigger.addEventListener('click', async (e) => {
            e.preventDefault();
            const emailInput = document.querySelector('input[name="email"]');
            if (!emailInput || !emailInput.value.trim()) {
                showFloatingAlert("Please enter your email address in the input field first.", "warning");
                if (emailInput) emailInput.focus();
                return;
            }

            try {
                resetTrigger.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
                resetTrigger.style.pointerEvents = 'none';

                const response = await fetch('/password-reset', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: new URLSearchParams({ email: emailInput.value.trim() })
                });
                
                const result = await response.json();
                
                if (response.ok && result.success) {
                    showFloatingAlert(result.message, "success");
                } else {
                    showFloatingAlert(result.message || "Failed to trigger reset.", "danger");
                }
            } catch (err) {
                showFloatingAlert("Connection failed. Could not send password reset request.", "danger");
            } finally {
                resetTrigger.innerHTML = "Forgot Password?";
                resetTrigger.style.pointerEvents = 'auto';
            }
        });
    }

    // --- Client-side donor forms validation (Age, Weight, Declaration) ---
    const registrationForm = document.querySelector('form[action*="register-donor"], form[action*="edit-donor"]');
    if (registrationForm) {
        registrationForm.addEventListener('submit', (e) => {
            const ageInput = registrationForm.querySelector('input[name="age"]');
            const weightInput = registrationForm.querySelector('input[name="weight"]');
            const healthDeclInput = registrationForm.querySelector('input[name="health_declaration"]');
            const phoneInput = registrationForm.querySelector('input[name="phone"]');

            // Age Check
            if (ageInput) {
                const age = parseInt(ageInput.value, 10);
                if (isNaN(age) || age < 18 || age > 65) {
                    e.preventDefault();
                    showFloatingAlert("Donors must be between 18 and 65 years old.", "danger");
                    ageInput.focus();
                    return;
                }
            }

            // Weight Check (India criteria is min 50kg)
            if (weightInput) {
                const weight = parseFloat(weightInput.value);
                if (isNaN(weight) || weight < 50) {
                    e.preventDefault();
                    showFloatingAlert("You must weigh at least 50 kg (110 lbs) to donate blood.", "danger");
                    weightInput.focus();
                    return;
                }
            }

            // Health Declaration Checkbox
            if (healthDeclInput && !healthDeclInput.checked) {
                e.preventDefault();
                showFloatingAlert("You must agree to the health declaration guidelines to register.", "danger");
                healthDeclInput.focus();
                return;
            }

            // Indian phone format check (10 digits)
            if (phoneInput) {
                const phone = phoneInput.value.trim().replace(/[\s\-()]/g, '');
                if (phone.length < 10) {
                    e.preventDefault();
                    showFloatingAlert("Please enter a valid 10-digit mobile number.", "danger");
                    phoneInput.focus();
                    return;
                }
            }
        });
    }

    // Helper: Floating Alerts
    function showFloatingAlert(message, type = "info") {
        let container = document.querySelector('.alerts-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'alerts-container';
            document.body.appendChild(container);
        }

        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        
        let iconClass = 'info-circle';
        if (type === 'success') iconClass = 'check-circle';
        if (type === 'danger') iconClass = 'exclamation-circle';
        if (type === 'warning') iconClass = 'exclamation-triangle';

        alert.innerHTML = `
            <div class="alert-content">
                <i class="fas fa-${iconClass}"></i>
                <span>${message}</span>
            </div>
            <i class="fas fa-times alert-close"></i>
        `;

        container.appendChild(alert);

        const closeBtn = alert.querySelector('.alert-close');
        closeBtn.addEventListener('click', () => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        });

        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    }
});
