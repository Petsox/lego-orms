const svg = document.getElementById("canvas");

let parts = {};

function norm(name) {
    return name.toUpperCase().replace(/^TB |^TS /, "").trim();
}

function el(name) {
    return document.createElementNS("http://www.w3.org/2000/svg", name);
}

async function loadAll() {
    const layout = await fetch("/api/layout").then(r => r.json());
    parts = await fetch("/api/parts").then(r => r.json());

    layout.items.forEach(drawItem);
    layout.switches.forEach(drawSwitchOverlay);
}

function drawItem(item) {
    const key = norm(item.part);
    const imgURL = parts[key];
    if (!imgURL) return;

    const img = el("image");
    img.setAttribute("href", imgURL);
    img.setAttribute("x", item.x - item.w / 2);
    img.setAttribute("y", item.y - item.h / 2);
    img.setAttribute("width", item.w);
    img.setAttribute("height", item.h);
    img.setAttribute(
        "transform",
        `rotate(${item.rot} ${item.x} ${item.y})`
    );

    svg.appendChild(img);
}

function drawSwitchOverlay(sw) {
    const g = el("g");
    g.setAttribute(
        "transform",
        `translate(${sw.x},${sw.y}) rotate(${sw.rot})`
    );
    g.style.cursor = "pointer";

    const tri = el("polygon");
    tri.setAttribute("points", "0,-12 10,10 -10,10");
    tri.setAttribute("fill", "lime");

    g.appendChild(tri);
    g.onclick = () => toggle(sw.id);

    svg.appendChild(g);
}

async function toggle(id) {
    await fetch(`/api/switch/${id}/toggle`);
}

loadAll();
