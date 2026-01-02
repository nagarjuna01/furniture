function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!(/^GET|HEAD|OPTIONS|TRACE$/.test(settings.type))) {
            xhr.setRequestHeader("X-CSRFToken", getCSRFToken());
        }
    },
    error: function(xhr) {
        console.error("AJAX Error:", xhr.status, xhr.responseText);
    }
});
