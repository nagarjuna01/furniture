// --- Global Utility Functions (scripts.js) ---

// 1. CSRF Token Retrieval
// Used to securely send data to Django views (POST/PUT/DELETE)
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// 2. Toastr Configuration (for success/error notifications)
document.addEventListener("DOMContentLoaded", function() {
    toastr.options = {
        "closeButton": true,
        "debug": false,
        "newestOnTop": true,
        "progressBar": true,
        "positionClass": "toast-top-right",
        "preventDuplicates": false,
        "onclick": null,
        "showDuration": "300",
        "hideDuration": "1000",
        "timeOut": "5000",
        "extendedTimeOut": "1000",
        "showEasing": "swing",
        "hideEasing": "linear",
        "showMethod": "fadeIn",
        "hideMethod": "fadeOut"
    };

    // If you need to expose a function to show toasts globally:
    window.showToast = (message, type = 'success', title = '') => {
        toastr[type](message, title);
    };
});

// 3. Expose the CSRF token for global use
window.CSRF_TOKEN = getCookie('csrftoken');