$.ajaxSetup({
    beforeSend: function (xhr, settings) {
        const token = localStorage.getItem("access");

        if (token) {
            xhr.setRequestHeader(
                "Authorization",
                "Bearer " + token
            );
        }

        console.log("AJAX:", settings.type, settings.url);
    }
});
