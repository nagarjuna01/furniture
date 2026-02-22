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

// 4. Toastr Configuration (SAFE)
document.addEventListener("DOMContentLoaded", function () {

    if (typeof window.toastr === "undefined") {
        console.warn("Toastr is not loaded. Falling back to console.");
        window.showToast = function (message, type = "info", title = "") {
            console.log(`[${type.toUpperCase()}] ${title} ${message}`);
            alert(message);
        };
        return;
    }

    toastr.options = {
        closeButton: true,
        newestOnTop: true,
        progressBar: true,
        positionClass: "toast-top-right",
        timeOut: 5000,
        showDuration: 300,
        hideDuration: 1000,
        showMethod: "fadeIn",
        hideMethod: "fadeOut"
    };

    window.showToast = function (message, type = "success", title = "") {
        toastr[type](message, title);
    };
});
//5 
$(document).ready(function () {
    console.log("Select2 loaded:", $.fn.select2);

    if ($.fn.select2) {
        $('.select2').select2({
            theme: 'bootstrap-5',
            width: '100%',
            allowClear: true,
            placeholder: 'Select'
        });
    } else {
        console.error("❌ Select2 NOT loaded");
    }
});

