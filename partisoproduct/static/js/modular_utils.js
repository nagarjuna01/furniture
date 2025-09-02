// modular_utils.js
export function validateExpression(expression, l, w, h) {
    const L = l;
    const W = w;
    const H = h;
    const safeExpression = expression
        .replace(/L/g, `(${L})`)
        .replace(/W/g, `(${W})`)
        .replace(/H/g, `(${H})`);

    try {
        return Function(`'use strict'; return (${safeExpression})`)();
    } catch (e) {
        console.error("Expression evaluation failed:", e);
        return false;
    }
}