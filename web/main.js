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

  svg.innerHTML = "";

  const root = el("g");
  svg.appendChild(root);

  renderItems(LAYOUT.items, root);
  renderSwitches(LAYOUT.switches || [], root);

  autoFit(root, LAYOUT.items);
}

// -------------------------------------------------------
// ITEM RENDERING
// -------------------------------------------------------
function renderItems(items) {
  items.forEach((item) => {
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
  switches.forEach((sw) => {
    const g = el("g");

    g.setAttribute("transform", `translate(${sw.x},${sw.y}) rotate(${sw.rot})`);
    g.style.cursor = "pointer";

    const dot = el("circle");
    dot.setAttribute("r", 6);
    dot.setAttribute("fill", "#2ecc71");
    dot.setAttribute("stroke", "#111");
    dot.setAttribute("stroke-width", "2");

    g.appendChild(dot);

    g.addEventListener("click", (e) => {
      if (e.shiftKey) {
        openCalibration(sw);
      } else {
        toggleSwitch(sw.id, g.querySelector("circle"));
      }
    });

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
    indicator.setAttribute("fill", data.state === 1 ? "#f1c40f" : "#2ecc71");
  } catch (err) {
    console.error("Switch toggle failed:", err);
  }
}

// -------------------------------------------------------
// AUTO-FIT VIEWBOX
// -------------------------------------------------------

function autoFit(root, items) {
  const padding = 40;

  let minX = Infinity,
    minY = Infinity;
  let maxX = -Infinity,
    maxY = -Infinity;

  items.forEach((i) => {
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
    (svgW - padding * 2) / layoutW,
    (svgH - padding * 2) / layoutH
  );

  const tx = (svgW - layoutW * scale) / 2 - minX * scale;
  const ty = (svgH - layoutH * scale) / 2 - minY * scale;

  root.setAttribute("transform", `translate(${tx},${ty}) scale(${scale})`);
}

// -------------------------------------------------------
// SWITCH CALIBRATION PANEL
// -------------------------------------------------------

let activeSwitch = null;

async function openCalibration(sw) {
  activeSwitch = sw;
  document.getElementById("cal-id").textContent = sw.id;
  await loadCalibration(sw);
  document.getElementById("cal-panel").classList.add("show");
}

async function testServo(state) {
  await fetch(`/api/switch/${activeSwitch.id}/toggle`);
}

async function saveCalibration() {
  if (!activeSwitch) return;

  const channel = parseInt(document.getElementById("cal-channel").value, 10);
  const angle0 = parseInt(document.getElementById("cal-a0").value, 10);
  const angle1 = parseInt(document.getElementById("cal-a1").value, 10);

  const res = await fetch("/api/update_switch_config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      id: activeSwitch.id,
      channel,
      angle0,
      angle1,
    }),
  });

  if (!res.ok) {
    alert("Failed to save calibration");
    return;
  }

  console.log("Calibration saved for switch", activeSwitch.id);
  closeCalibration();
}

function closeCalibration() {
  document.getElementById("cal-panel").classList.remove("show");
}

// -------------------------------------------------------
// LOAD SWITCH CALIBRATION DATA
// -------------------------------------------------------

async function loadCalibration(sw) {
  const cfg = await fetch("/api/switch_config").then((r) => r.json());
  const entry = cfg.switches?.[sw.id];

  if (!entry) return;

  document.getElementById("cal-channel").value = entry.channel;
  document.getElementById("cal-a0").value = entry.angle0;
  document.getElementById("cal-a1").value = entry.angle1;
}

// -------------------------------------------------------
// START
// -------------------------------------------------------
window.onload = init;
