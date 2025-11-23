/* script.js -- AJAX + overlay highlighting + dark mode + safe regex highlighting
   Drop-in replacement; expects /api/run JSON endpoint returning:
   { translated, highlighted, accepted, error }
*/

// ---------- DOM elements
const body = document.body;
const themeBtn = document.getElementById("themeToggle");
const copyRegexBtn = document.getElementById("copyRegexBtn");
const patternEl = document.getElementById("pattern");
const constraintsEl = document.getElementById("constraints");
const textEl = document.getElementById("text");
const runBtn = document.getElementById("runBtn");
const clearBtn = document.getElementById("clearBtn");
const regexBox = document.getElementById("regexBox");
const matchesBox = document.getElementById("matchesBox");
const acceptTable = document.getElementById("acceptTable");
const errorBox = document.getElementById("errorBox");
const overlay = document.getElementById("overlay");
const overlayPre = document.getElementById("overlayPre");

// ---------- Theme (dark) toggle, persisted
(function initTheme(){
    const stored = localStorage.getItem("theme");
    if (stored === "dark") {
        body.classList.add("dark");
        if (themeBtn) themeBtn.textContent = "☀️";
    } else {
        if (themeBtn) themeBtn.textContent = "🌙";
    }
    if (themeBtn) {
        themeBtn.addEventListener("click", () => {
            body.classList.toggle("dark");
            const isDark = body.classList.contains("dark");
            localStorage.setItem("theme", isDark ? "dark" : "light");
            themeBtn.textContent = isDark ? "☀️" : "🌙";
            // reapply regex box highlighting colors
            applyRegexHighlighting();
        });
    }
})();

// ---------- Copy translated regex
if (copyRegexBtn) {
    copyRegexBtn.addEventListener("click", () => {
        const txt = regexBox ? regexBox.textContent : "";
        if (!txt) return;
        navigator.clipboard?.writeText(txt).then(()=> {
            copyRegexBtn.textContent = "✓";
            setTimeout(()=> copyRegexBtn.textContent = "📋", 900);
        }).catch(()=> {
            copyRegexBtn.textContent = "✖";
            setTimeout(()=> copyRegexBtn.textContent = "📋", 900);
        });
    });
}

// ---------- Helpers
function escapeHTML(str) {
    if (!str) return "";
    return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

// Tokenizer for translated regex syntax-highlighting
function highlightRegexSyntax(text) {
    if (!text) return "";
    const safe = escapeHTML(text);
    const tokenRe = /(\(\?:|\(|\)|\[[^\]]+\]|\{[^}]+\}|\\.|[\*\+\?\|]|[^()\[\]\{\}\*\+\?\|\\]+)/g;
    const parts = [];
    let m;
    while ((m = tokenRe.exec(safe)) !== null) {
        const tok = m[0];
        if (tok.startsWith("(?:")) parts.push(`<span class="group">${tok}</span>`);
        else if (tok === "(" || tok === ")") parts.push(`<span class="group">${tok}</span>`);
        else if (tok.startsWith("[") && tok.endsWith("]")) parts.push(`<span class="class">${tok}</span>`);
        else if (tok.startsWith("{") && tok.endsWith("}")) parts.push(`<span class="quant">${tok}</span>`);
        else if (/^[\*\+\?]$/.test(tok)) parts.push(`<span class="quant">${tok}</span>`);
        else if (tok === "|") parts.push(`<span class="alt">|</span>`);
        else if (tok.length >= 2 && tok[0] === "\\") parts.push(`<span class="literal">${tok}</span>`);
        else parts.push(tok.replace(/([A-Za-z0-9])/g, '<span class="literal">$1</span>'));
    }
    return parts.join("");
}

// Apply syntax highlighting to regexBox (uses textContent to avoid HTML injection)
function applyRegexHighlighting() {
    if (!regexBox) return;
    const text = regexBox.textContent || regexBox.innerText || "";
    regexBox.innerHTML = highlightRegexSyntax(text);
}

// Sync overlay scroll with textarea
function syncScroll() {
    if (!overlay || !textEl) return;
    overlay.scrollTop = textEl.scrollTop;
    overlay.scrollLeft = textEl.scrollLeft;
}

// Update overlay content (expects HTML with <mark> tags OR plain text)
function updateOverlayWithHighlighted(htmlOrText) {
    if (!overlayPre) return;
    if (!htmlOrText) {
        overlayPre.innerHTML = escapeHTML(textEl.value || "");
        return;
    }
    // If server returned raw HTML with <mark>, use it; else escape
    // We assume server-provided highlighted HTML is safe (trusted project code)
    if (/<\/?mark/.test(htmlOrText) || /<[^>]+>/.test(htmlOrText)) {
        // preserve line breaks
        overlayPre.innerHTML = htmlOrText.replace(/\n/g, "<br>");
    } else {
        overlayPre.innerHTML = escapeHTML(htmlOrText).replace(/\n/g, "<br>");
    }
}

// Update match summary box (server-provided HTML)
function updateMatchesBox(html) {
    if (!matchesBox) return;
    if (!html) {
        matchesBox.innerHTML = '<span class="placeholder-text">No matches</span>';
    } else {
        matchesBox.innerHTML = html;
    }
}

// Update acceptance table
function updateAcceptanceTable(pairs) {
    if (!acceptTable) return;
    const tbody = acceptTable.querySelector("tbody");
    if (!tbody) return;
    tbody.innerHTML = "";
    (pairs || []).forEach(([line, ok]) => {
        const tr = document.createElement("tr");
        const td1 = document.createElement("td");
        td1.textContent = line;
        const td2 = document.createElement("td");
        td2.textContent = ok ? "ACCEPTED" : "REJECTED";
        td2.className = ok ? "ok" : "bad";
        tr.appendChild(td1);
        tr.appendChild(td2);
        tbody.appendChild(tr);
    });
}

// Show or hide error
function showError(msg) {
    if (!errorBox) return;
    if (!msg) {
        errorBox.style.display = "none";
        errorBox.innerHTML = "";
    } else {
        errorBox.style.display = "block";
        errorBox.innerHTML = `<strong>Error:</strong> ${escapeHTML(String(msg))}`;
    }
}

// ---------- AJAX call to /api/run
async function callApiRun(payload) {
    try {
        const res = await fetch("/api/run", {
            method: "POST",
            headers: {"Content-Type":"application/json","Accept":"application/json"},
            body: JSON.stringify(payload)
        });
        const json = await res.json();
        return json;
    } catch (err) {
        return { error: "Network error: " + String(err) };
    }
}

// ---------- Debounce helper
function debounce(fn, ms) {
    let t = null;
    return function(...args) {
        clearTimeout(t);
        t = setTimeout(() => fn.apply(this, args), ms);
    };
}

// ---------- Main run function
let lastRunPayload = null;
async function runOnce() {
    const payload = {
        pattern: patternEl ? patternEl.value : "",
        constraints: constraintsEl ? constraintsEl.value : "",
        text: textEl ? textEl.value : ""
    };
    lastRunPayload = payload;
    // Call API
    const res = await callApiRun(payload);
    if (res.error) {
        showError(res.error);
        // update overlay with plain text so user still sees input
        updateOverlayWithHighlighted(null);
        if (regexBox) regexBox.textContent = res.translated || "";
        applyRegexHighlighting();
        updateMatchesBox("");
        updateAcceptanceTable([]);
        return;
    }
    showError(null);
    // Update translated regex
    if (regexBox) regexBox.textContent = res.translated || "";
    applyRegexHighlighting();
    // Update overlay (inline highlighting on textarea)
    updateOverlayWithHighlighted(res.highlighted || "");
    // Update matches summary and acceptance table
    updateMatchesBox(res.highlighted || "");
    updateAcceptanceTable(res.accepted || []);
    // sync scroll and focus preservation handled elsewhere
    syncScroll();
}

// Debounced autorun (600ms)
const debouncedRun = debounce(runOnce, 600);

// ---------- Event wiring
if (patternEl) patternEl.addEventListener("input", debouncedRun);
if (constraintsEl) constraintsEl.addEventListener("input", debouncedRun);
if (textEl) {
    textEl.addEventListener("input", debouncedRun);
    textEl.addEventListener("scroll", syncScroll);
}

// Manual buttons
if (runBtn) runBtn.addEventListener("click", (e) => { e.preventDefault(); runOnce(); });
if (clearBtn) clearBtn.addEventListener("click", (e)=> {
    e.preventDefault();
    if (patternEl) patternEl.value = "";
    if (constraintsEl) constraintsEl.value = "";
    if (textEl) textEl.value = "";
    updateOverlayWithHighlighted(null);
    updateMatchesBox("");
    updateAcceptanceTable([]);
    if (regexBox) { regexBox.textContent = ""; applyRegexHighlighting(); }
    showError(null);
});

// Keep caret position on reloads (store focused element)
[patternEl, constraintsEl, textEl].forEach(el => {
    if (!el) return;
    el.addEventListener("focus", ()=> localStorage.setItem("focus",""+el.id));
});
window.addEventListener("load", ()=> {
    const f = localStorage.getItem("focus");
    if (f) {
        const el = document.getElementById(f);
        if (el) el.focus();
    }
    // initial highlight (if server rendered something)
    applyRegexHighlighting();
    // initial overlay from existing server-highlighted HTML if present in matchesBox
    if (matchesBox && matchesBox.innerHTML.trim().length > 0) {
        updateOverlayWithHighlighted(matchesBox.innerHTML);
    } else {
        updateOverlayWithHighlighted(null);
    }
    syncScroll();
});

// Ensure overlay scroll stays synced during typing (in case of rapid changes)
setInterval(syncScroll, 150);

