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
    img.setAttribute("filter", "url(#shadow)");
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

function fitToView(items) {
    const margin = 50;

    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;

    items.forEach(i => {
        minX = Math.min(minX, i.x - i.w / 2);
        minY = Math.min(minY, i.y - i.h / 2);
        maxX = Math.max(maxX, i.x + i.w / 2);
        maxY = Math.max(maxY, i.y + i.h / 2);
    });

    const layoutW = maxX - minX;
    const layoutH = maxY - minY;

    const svgW = svg.clientWidth;
    const svgH = svg.clientHeight;

    const scale = Math.min(
        (svgW - margin * 2) / layoutW,
        (svgH - margin * 2) / layoutH
    );

    const tx = (svgW - layoutW * scale) / 2 - minX * scale;
    const ty = (svgH - layoutH * scale) / 2 - minY * scale;

    return `translate(${tx},${ty}) scale(${scale})`;
}

function drawSwitchOverlay(sw) {
    const g = el("g");
    g.setAttribute("transform", `translate(${sw.x},${sw.y}) rotate(${sw.rot})`);
    g.style.cursor = "pointer";

    const circle = el("circle");
    circle.setAttribute("r", 6);
    circle.setAttribute("fill", "#2ecc71"); // green = straight
    circle.setAttribute("stroke", "#111");
    circle.setAttribute("stroke-width", "2");

    g.appendChild(circle);
    g.onclick = () => toggle(sw.id, circle);

    root.appendChild(g);
}

async function toggle(id, indicator) {
    const res = await fetch(`/api/switch/${id}/toggle`);
    const data = await res.json();

    indicator.setAttribute(
        "fill",
        data.state === 1 ? "#f1c40f" : "#2ecc71"
    );
}

const root = el("g");
svg.appendChild(root);

const transform = fitToView(layout.items);
root.setAttribute("transform", transform);

let viewBox = { x: 0, y: 0, w: 1000, h: 600 };

svg.setAttribute("viewBox", "0 0 1000 600");

svg.addEventListener("wheel", e => {
    e.preventDefault();
    const zoom = e.deltaY > 0 ? 1.1 : 0.9;
    viewBox.w *= zoom;
    viewBox.h *= zoom;
    svg.setAttribute(
        "viewBox",
        `${viewBox.x} ${viewBox.y} ${viewBox.w} ${viewBox.h}`
    );
});

const label = el("text");
label.textContent = sw.id;
label.setAttribute("y", -10);
label.setAttribute("fill", "#aaa");
label.setAttribute("font-size", "8px");
g.appendChild(label);


loadAll();