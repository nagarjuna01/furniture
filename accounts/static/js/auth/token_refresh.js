$(document).ajaxError(function (event, xhr, settings) {

    // Only handle expired/invalid access tokens
    if (xhr.status === 401) {
        console.warn("401 detected – refreshing token");

        const refresh = localStorage.getItem("refresh");
        if (!refresh) {
            localStorage.clear();
            location.href = "/login/";
            return;
        }

        $.ajax({
            url: "/api/auth/token/refresh/",
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({ refresh }),
        })
        .done(function (res) {
            console.log("Token refreshed");
            localStorage.setItem("access", res.access);
            location.reload();
        })
        .fail(function () {
            console.error("Refresh failed – logging out");
            localStorage.clear();
            location.href = "/login/";
        });
    }
});
