// --- Global Utility Functions (scripts.js) ---

// 1. CSRF Token Retrieval
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// 2. Expose CSRF token FIRST
window.CSRF_TOKEN = getCookie('csrftoken');

// 3. Global AJAX CSRF enforcement
$.ajaxSetup({
    beforeSend: function (xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type)) {
            xhr.setRequestHeader('X-CSRFToken', window.CSRF_TOKEN);
        }
    }
});

// 4. Toastr Configuration
document.addEventListener("DOMContentLoaded", function () {
    toastr.options = {
        closeButton: true,
        newestOnTop: true,
        progressBar: true,
        positionClass: "toast-top-right",
        timeOut: "5000",
        showDuration: "300",
        hideDuration: "1000",
        showMethod: "fadeIn",
        hideMethod: "fadeOut"
    };

    window.showToast = (message, type = 'success', title = '') => {
        toastr[type](message, title);
    };
});
