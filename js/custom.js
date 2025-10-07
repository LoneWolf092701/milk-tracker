// custom.js
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            // Optional: Add loading spinner or something, but for now alert
            alert('Form submitted successfully!');
            // To make it faster, could implement AJAX here, but keeping simple
        });
    });
});