$("#authForm").on("submit", function (e) {
    e.preventDefault();

    const btn = $("#authSubmitBtn");
    const errorBox = $("#login-error");
    

    btn.prop("disabled", true).text("Logging in...");
    errorBox.addClass("d-none").text("");

    $.ajax({
        url: "/accounts/login/",  // Django login URL
        method: "POST",
        headers: { "X-CSRFToken": window.CSRF_TOKEN },
        data: {
            username: $("#username").val().trim(),
            password: $("#password").val().trim()
        }
    })
    .done(() => location.reload())
    .fail(xhr => {
        errorBox
            .text("Invalid username or password")
            .removeClass("d-none");
    })
    .always(() => {
        btn.prop("disabled", false).text("Login");
    });
});

$('#authModal').on('shown.bs.modal', function () {
    $("#username").trigger("focus");
    $("#login-error").addClass("d-none").text("");
});

$(document).ajaxError(function (event, xhr) {
    if (xhr.status === 401) {
        $("#authModal").modal("show");
    }
});

$("#toggleAuth").on("click", function(e) {
    e.preventDefault();
    const emailGroup = $("#emailGroup");
    const authTitle = $("#authTitle");
    const btn = $("#authSubmitBtn");

    if ($("#authMode").val() === "login") {
        $("#authMode").val("register");
        emailGroup.removeClass("d-none");
        authTitle.text("Register");
        btn.text("Register");
        $(this).text("Back to login");
    } else {
        $("#authMode").val("login");
        emailGroup.addClass("d-none");
        authTitle.text("Login");
        btn.text("Login");
        $(this).text("Create account");
    }
});
