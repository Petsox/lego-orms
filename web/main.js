// =======================================================
// LEGO-ORMS — SAFE FINAL RENDERER
// =======================================================

const svg = document.getElementById("canvas");

function el(name) {
    return document.createElementNS("http://www.w3.org/2000/svg", name);
}

// -------------------------------------------------------
// GLOBAL STATE
// -------------------------------------------------------
let PART_IMAGES = {};
let LAYOUT = null;

// -------------------------------------------------------
// LOADERS
// -------------------------------------------------------
async function loadParts() {
    const res = await fetch("/api/parts");
    PART_IMAGES = await res.json();
    console.log("Loaded part images:", Object.keys(PART_IMAGES).length);
}

async function loadLayout() {
    const res = await fetch("/api/layout");
    const data = await res.json();

    // server may return {items,...} or {layout:{items,...}}
    LAYOUT = data.items ? data : data.layout;

    console.log("Layout loaded:", LAYOUT);
}

// -------------------------------------------------------
// RENDER ENTRY POINT
// -------------------------------------------------------
async function init() {
    console.log("Renderer starting…");

    await loadParts();
    await loadLayout();

    if (!LAYOUT || !LAYOUT.items) {
        console.error("Layout missing items!");
        return;
    }

    svg.innerHTML = ""; // clear
    renderItems(LAYOUT.items);
    renderSwitches(LAYOUT.switches || []);
}

// -------------------------------------------------------
// ITEM RENDERING
// -------------------------------------------------------
function renderItems(items) {
    items.forEach(item => {
        renderItem(item);
    });
}

function normalizePartName(name) {
    return name
        .toUpperCase()
        .replace(/^TB\s+/, "")
        .replace(/^TS\s+/, "")
        .trim();
}

function renderItem(item) {
    const g = el("g");

    g.setAttribute(
        "transform",
        `translate(${item.x},${item.y}) rotate(${item.rot})`
    );

    const key = normalizePartName(item.part);
    const imgURL = PART_IMAGES[key];

    if (imgURL) {
        // ---- IMAGE RENDER ----
        const img = el("image");
        img.setAttribute("href", imgURL);
        img.setAttribute("x", -item.w / 2);
        img.setAttribute("y", -item.h / 2);
        img.setAttribute("width", item.w);
        img.setAttribute("height", item.h);
        img.setAttribute("filter", "url(#shadow)");

        g.appendChild(img);
    } else {
        // ---- SAFE FALLBACK ----
        const r = el("rect");
        r.setAttribute("x", -item.w / 2);
        r.setAttribute("y", -item.h / 2);
        r.setAttribute("width", item.w);
        r.setAttribute("height", item.h);
        r.setAttribute("fill", "#888");
        r.setAttribute("opacity", "0.6");

        g.appendChild(r);

        console.warn("Missing image for part:", key);
    }

    svg.appendChild(g);
}

// -------------------------------------------------------
// SWITCH OVERLAYS
// -------------------------------------------------------
function renderSwitches(switches) {
    switches.forEach(sw => {
        const g = el("g");

        g.setAttribute(
            "transform",
            `translate(${sw.x},${sw.y}) rotate(${sw.rot})`
        );
        g.style.cursor = "pointer";

        const dot = el("circle");
        dot.setAttribute("r", 6);
        dot.setAttribute("fill", "#2ecc71");
        dot.setAttribute("stroke", "#111");
        dot.setAttribute("stroke-width", "2");

        g.appendChild(dot);

        g.addEventListener("click", () => toggleSwitch(sw.id, dot));

        svg.appendChild(g);
    });
}

// -------------------------------------------------------
// SWITCH CONTROL
// -------------------------------------------------------
async function toggleSwitch(id, indicator) {
    console.log("Toggling switch:", id);

    try {
        const res = await fetch(`/api/switch/${id}/toggle`);
        const data = await res.json();

        // green = straight, yellow = turnout
        indicator.setAttribute(
            "fill",
            data.state === 1 ? "#f1c40f" : "#2ecc71"
        );
    } catch (err) {
        console.error("Switch toggle failed:", err);
    }
}

// -------------------------------------------------------
// START
// -------------------------------------------------------
window.onload = init;
