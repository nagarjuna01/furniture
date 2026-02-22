/* ==========================================
   EXPRESSION VALIDATOR (STATIC)
========================================== */

function normalizeVar(v) {
    return v.toLowerCase().trim();
}

function extractVariables(expr) {
    // Matches identifiers but excludes numbers and keywords
    const tokens = expr.match(/[a-zA-Z_][a-zA-Z0-9_]*/g) || [];

    const keywords = ["and", "or", "not", "true", "false", "min", "max", "round", "abs"];
    return [...new Set(tokens)]
        .map(normalizeVar)
        .filter(v => !keywords.includes(v));
}

function buildAllowedVariables() {
    const vars = new Set([
        "product_length",
        "product_width",
        "product_height",
        "quantity"
    ]);

    // PARAMETERS
    document.querySelectorAll("#parameter-body tr").forEach(tr => {
        const abbr = tr.children[1]?.innerText;
        if (abbr) vars.add(normalizeVar(abbr));
    });

    // PARTS
    (window.productState?.parts || []).forEach(p => {
        const base = normalizeVar(p.name.replace(/\s+/g, "_"));
        vars.add(`${base}_length`);
        vars.add(`${base}_width`);
        vars.add(`${base}_thickness`);
        vars.add(`part_${p.id}_length`);
        vars.add(`part_${p.id}_width`);
        vars.add(`part_${p.id}_thickness`);
    });

    return vars;
}

function validateExpressionStatic(expr) {
    if (!expr.trim()) return { ok: true };

    const varsUsed = extractVariables(expr);
    const allowed = buildAllowedVariables();

    const unknown = varsUsed.filter(v => !allowed.has(v));

    if (unknown.length) {
        return {
            ok: false,
            error: `Unknown variables: ${unknown.join(", ")}`
        };
    }

    return { ok: true };
}

const validationInput = document.getElementById("validation-expr");
const validationMsg = document.createElement("div");
validationMsg.className = "small mt-1";
validationInput.after(validationMsg);

let debounceTimer;

validationInput.addEventListener("input", () => {
    clearTimeout(debounceTimer);

    debounceTimer = setTimeout(async () => {
        const expr = validationInput.value;

        // 1️⃣ Static check
        const staticCheck = validateExpressionStatic(expr);
        if (!staticCheck.ok) {
            validationMsg.innerHTML = `❌ ${staticCheck.error}`;
            validationMsg.className = "text-danger small mt-1";
            return;
        }

        // 2️⃣ Backend validation
        try {
            const res = await fetch("/modularcalc/api/validate-expression/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": window.CSRF_TOKEN
                },
                body: JSON.stringify({
                    expression: expr,
                    product_dims: {
                        product_length: 1000,
                        product_width: 600,
                        product_height: 800,
                        quantity: 1
                    },
                    parameters: collectParameters()
                        .reduce((o, p) => (o[p.abbr.toLowerCase()] = p.default, o), {}),
                    parts: productState.parts.reduce((o, p) => {
                        o[p.id] = {
                            name: p.name,
                            length: 500,
                            width: 300,
                            thickness: 18
                        };
                        return o;
                    }, {})
                })
            });

            const data = await res.json();

            if (!data.valid) throw new Error(data.error);

            validationMsg.innerHTML = "✅ Expression is valid";
            validationMsg.className = "text-success small mt-1";

        } catch (err) {
            validationMsg.innerHTML = `❌ ${err.message}`;
            validationMsg.className = "text-danger small mt-1";
        }
    }, 500);
});
