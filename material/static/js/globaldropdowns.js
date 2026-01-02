function loadDropdown(url, selectors, opts = {}) {
    const {
        placeholder = "-- Select --",
        valueKey = "id",
        labelKey = "name",
        extraLabelKey = null,
        allowEmpty = true,
        onLoaded = null,
    } = opts;

    const $targets = Array.isArray(selectors)
        ? selectors.map(s => (s instanceof jQuery ? s : $(s)))
        : [(selectors instanceof jQuery ? selectors : $(selectors))];

    console.log("[loadDropdown] URL:", url);

    $.get(url)
        .done(res => {
            const items = res?.results || res || [];

            let options = allowEmpty
                ? `<option value="">${placeholder}</option>`
                : "";

            options += items.map(item => {
                const extra = extraLabelKey && item[extraLabelKey]
                    ? ` (${item[extraLabelKey]})`
                    : "";
                return `<option value="${item[valueKey]}">${item[labelKey]}${extra}</option>`;
            }).join("");

            $targets.forEach($el => {
                if (!$el || !$el.length) {
                    console.warn("[loadDropdown] Target not found");
                    return;
                }
                $el.html(options);
            });

            if (typeof onLoaded === "function") {
                onLoaded(items);
            }
        })
        .fail(err => {
            console.error(`[loadDropdown] Failed: ${url}`, err.responseText || err);
            if (window.showToast) {
                showToast("Failed to load dropdown", "danger");
            }
        });
}