/* ============================================================
   GLOBAL ENGINE: AUTOCOMPLETE & FORENSIC VALIDATION
   ============================================================ */

/**
 * 1. TOKEN DISCOVERY
 * Gathers available variables based on scope (Global vs Part).
 */
function getAllExpressionTokens(isLogic = false) {
    const tokens = new Set([
        "product_length", "product_width", "product_height", 
        "quantity", "min(", "max(", "round(", "abs("
    ]);

    // Logic-specific operators
    if (isLogic) {
        ["and", "or", "not", "True", "False", "==", "!=", ">", "<", ">=", "<="].forEach(t => tokens.add(t));
    }

    // PARAMETERS (from UI table)
    document.querySelectorAll("#parameter-body tr").forEach(tr => {
        const abbr = tr.children[1]?.innerText;
        if (abbr) tokens.add(abbr.toLowerCase());
    });

    // PARTS (from Global State)
    (window.productState?.parts || []).forEach(p => {
        const base = p.name.toLowerCase().replace(/\s+/g, "_");
        tokens.add(`${base}_length`);
        tokens.add(`${base}_width`);
        tokens.add(`${base}_thickness`);
    });

    return [...tokens].sort();
}

/**
 * 2. CURSOR TRACKING
 */
function getCursorWord(text, cursorPos) {
    if (!text) return "";
    const left = text.slice(0, cursorPos);
    const match = left.match(/[a-zA-Z_][a-zA-Z0-9_]*$/);
    return match ? match[0] : "";
}

/**
 * 3. THE FORENSIC BOUNCER
 * Checks for balanced parentheses and whitelisted variables.
 */
window.validateAndCommit = function(el, successCallback, scope = 'PART') {
    const val = el.value.trim();
    if (!val) return;

    // Check 1: Balanced Parentheses
    const isBalanced = (val.match(/\(/g) || []).length === (val.match(/\)/g) || []).length;
    
    // Check 2: Scope-based variable check
    const allowed = (scope === 'PART') ? ['L', 'W', 'T', 'H', 'D'] : ['product_length', 'product_width', 'product_height', 'product_depth'];
    const params = (window.productSubmissionState?.parameters || []).map(p => p.slug);
    const allTokens = [...allowed, ...params, 'and', 'or', 'not', 'min', 'max', 'round', 'abs'];

    const usedVars = val.match(/[a-zA-Z_][a-zA-Z0-9_]*/g) || [];
    const unknowns = usedVars.filter(v => !allTokens.includes(v) && isNaN(v));

    let feedbackEl = el.parentElement.querySelector(".validation-msg");
    if (!feedbackEl) {
        feedbackEl = document.createElement("div");
        feedbackEl.className = "validation-msg small mt-1";
        el.after(feedbackEl);
    }

    if (!isBalanced || unknowns.length > 0) {
        el.classList.add('is-invalid');
        el.classList.remove('is-valid');
        feedbackEl.innerHTML = `❌ ${!isBalanced ? 'Unbalanced brackets' : 'Unknown: ' + unknowns.join(', ')}`;
        feedbackEl.className = "text-danger small mt-1 validation-msg";
        return; 
    }

    // Pass the Gate
    el.classList.remove('is-invalid');
    el.classList.add('is-valid');
    feedbackEl.innerHTML = "✅ Validated & Saved";
    feedbackEl.className = "text-success small mt-1 validation-msg";
    
    successCallback(val);
};

/**
 * 4. SMART ENGINE ATTACHMENT
 * Ties Autocomplete (Live) and Validation (Blur) together.
 */
window.applySmartEngine = function(inputElement, scope = 'PART') {
    if (!inputElement || inputElement.dataset.smartActive) return;

    // Attach Autocomplete UI
    attachExpressionAutocomplete(inputElement, scope === 'GLOBAL');

    // THE CLEAN KILL: Validate & Save to state only on BLUR
    inputElement.addEventListener("blur", function() {
        window.validateAndCommit(this, (validatedValue) => {
            if (this.id === 'validation-expr') {
                window.productSubmissionState.validation_logic = validatedValue;
            } else if (this.dataset.key) {
                window.currentPartState[this.dataset.key] = validatedValue;
            }
            console.log(`🎯 Committed [${scope}]:`, validatedValue);
        }, scope);
    });

    // Reset UI while typing
    inputElement.addEventListener("input", function() {
        this.classList.remove("is-valid", "is-invalid");
        const msg = this.parentElement.querySelector(".validation-msg");
        if (msg) msg.innerText = "Editing...";
    });

    inputElement.dataset.smartActive = "true";
};

/**
 * 5. AUTOCOMPLETE UI LOGIC
 */
function attachExpressionAutocomplete(textarea, isLogic = false) {
    const dropdown = document.createElement("div");
    dropdown.className = "autocomplete-box shadow-sm border bg-white";
    dropdown.style.cssText = "position:absolute; z-index:2100; display:none; max-height:200px; overflow-y:auto; cursor:pointer;";
    document.body.appendChild(dropdown);

    let selectedIndex = -1;

    textarea.addEventListener("input", () => {
        const rect = textarea.getBoundingClientRect();
        const cursorPos = textarea.selectionStart;
        const text = textarea.value;
        const current = getCursorWord(text, cursorPos).toLowerCase();

        if (!current) { dropdown.style.display = "none"; return; }

        const suggestions = getAllExpressionTokens(isLogic).filter(t => t.startsWith(current));
        if (!suggestions.length) { dropdown.style.display = "none"; return; }

        dropdown.innerHTML = suggestions.map(s => `<div class="autocomplete-item px-2 py-1">${s}</div>`).join("");
        dropdown.style.left = `${rect.left + window.scrollX}px`;
        dropdown.style.top = `${rect.bottom + window.scrollY}px`;
        dropdown.style.width = `${rect.width}px`;
        dropdown.style.display = "block";
        selectedIndex = -1;
    });

    // Handle Clicks
    dropdown.addEventListener("mousedown", (e) => {
        if (e.target.classList.contains("autocomplete-item")) {
            e.preventDefault();
            const val = textarea.value;
            const cursorPos = textarea.selectionStart;
            const current = getCursorWord(val, cursorPos);
            const before = val.slice(0, cursorPos - current.length);
            const after = val.slice(cursorPos);
            textarea.value = before + e.target.innerText + after;
            textarea.focus();
            dropdown.style.display = "none";
        }
    });

    // Close on outside click
    document.addEventListener("mousedown", (e) => {
        if (!dropdown.contains(e.target) && e.target !== textarea) dropdown.style.display = "none";
    });
}

/**
 * 6. INITIALIZATION
 */
document.addEventListener("DOMContentLoaded", () => {
    const exprInput = document.getElementById("validation-expr");
    if (exprInput) window.applySmartEngine(exprInput, 'GLOBAL');
});