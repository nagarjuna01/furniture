function handleQuoteMode(resp) {
    if (resp.mode === "snapshot") {
        lockUI();
        showReadonlyBanner();
    }
}

function lockUI() {
    $(".editable").prop("disabled", true)
}
