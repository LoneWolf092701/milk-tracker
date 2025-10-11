// Filename: custom.js
// Full path: static/custom.js

// custom.js
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            // Add a simple loading indicator
            const submitBtn = form.querySelector('.btn-primary');
            submitBtn.disabled = true;
            submitBtn.innerText = 'Submitting...';
            // No alert, as it may not be needed
        });
    });

    // Dark mode toggle
    const htmlElement = document.documentElement;
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = themeToggle.querySelector('i');

    // Load theme from localStorage
    const savedTheme = localStorage.getItem('theme') || 'dark';
    htmlElement.setAttribute('data-bs-theme', savedTheme);
    updateIconAndNavbar(savedTheme);

    themeToggle.addEventListener('click', () => {
        const currentTheme = htmlElement.getAttribute('data-bs-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        htmlElement.setAttribute('data-bs-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateIconAndNavbar(newTheme);
    });

    function updateIconAndNavbar(theme) {
        if (theme === 'light') {
            themeIcon.classList.remove('bi-sun-fill');
            themeIcon.classList.add('bi-moon-stars-fill');
            document.querySelectorAll('.navbar').forEach(nav => {
                nav.classList.remove('navbar-dark');
                nav.classList.add('navbar-light');
            });
        } else {
            themeIcon.classList.remove('bi-moon-stars-fill');
            themeIcon.classList.add('bi-sun-fill');
            document.querySelectorAll('.navbar').forEach(nav => {
                nav.classList.remove('navbar-light');
                nav.classList.add('navbar-dark');
            });
        }
    }
});