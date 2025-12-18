$(document).ready(function () {
    const isAuth = !!localStorage.getItem("access");
    $("#loginBtn").toggleClass("d-none", isAuth);
    $("#logoutBtn").toggleClass("d-none", !isAuth);

    $("#logoutBtn").click(function () {
        localStorage.clear();
        location.reload();
    });
});
