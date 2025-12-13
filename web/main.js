// =======================================================
// LEGO-ORMS — IMPROVED RENDERER WITH BETTER SWITCH DETECTION
// =======================================================

const svg = document.getElementById("canvas");

function el(name) {
  return document.createElementNS("http://www.w3.org/2000/svg", name);
}

let PART_IMAGES = {};
let PART_GEOMETRY = {};
let LAYOUT = null;
let activeSwitch = null;

function bbOrientationToDegrees(o) {
  // BlueBrick orientation units: 0–2520, where 630 = 90°
  return (o / 7) % 360;
}

// -------------------------------------------------------
// LOADERS
// -------------------------------------------------------
async function loadParts() {
  const res = await fetch("/api/parts");
  const parts = await res.json();

  for (const [key, url] of Object.entries(parts)) {
    PART_IMAGES[key] = url;

    // Load image to get intrinsic size
    const img = new Image();
    img.src = url;
    await img.decode();

    PART_IMAGE_SIZE[key] = {
      w: img.naturalWidth,
      h: img.naturalHeight,
    };
  }

  console.log("Loaded part images:", Object.keys(PART_IMAGES).length);
}

async function loadLayout() {
  const res = await fetch("/res/layout.json");
  if (!res.ok) {
    throw new Error("Failed to load layout.json");
  }
  LAYOUT = await res.json();
  console.log("Layout loaded:", LAYOUT.items.length, "items");
}

async function loadPartGeometry() {
  const res = await fetch("/res/part_geometry.json");
  if (!res.ok) {
    throw new Error("Failed to load part_geometry.json");
  }
  PART_GEOMETRY = await res.json();
  console.log("Loaded part geometry:", Object.keys(PART_GEOMETRY).length);
}

async function loadCalibration(item) {
  try {
    const res = await fetch("/api/switch_config");
    if (!res.ok) return;

    const cfg = await res.json();
    const sw = cfg.switches?.[item.id];
    if (!sw) return;

    // Populate UI fields
    document.getElementById("cal-channel").value = sw.channel ?? 0;
    document.getElementById("cal-a0").value = sw.angle0 ?? 65;
    document.getElementById("cal-a1").value = sw.angle1 ?? 105;

    // Update visible values
    document.getElementById("cal-a0-val").textContent =
      document.getElementById("cal-a0").value;
    document.getElementById("cal-a1-val").textContent =
      document.getElementById("cal-a1").value;
  } catch (err) {
    console.error("Failed to load calibration:", err);
  }
}

// -------------------------------------------------------
// SWITCH DETECTION (ROBUST)
// -------------------------------------------------------

const SWITCH_PART_IDS = new Set([
  "2861", // Left switch
  "2859", // Right switch
  "7996", // Double crossover / special switch
]);

function isSwitchPart(item) {
  if (!item || !item.part) return false;

  const name = item.part.toUpperCase();

  // Keyword-based detection
  if (
    name.includes("SWITCH") ||
    name.includes("POINT") ||
    name.includes("TURNOUT") ||
    name.includes("SLIP")
  ) {
    return true;
  }

  // Part-number-based detection (BlueBrick reality)
  // Extract numeric ID from part name if present
  const match = name.match(/\b\d{4}\b/);
  if (match && SWITCH_PART_IDS.has(match[0])) {
    return true;
  }

  return false;
}

// -------------------------------------------------------
// RENDER ENTRY POINT
// -------------------------------------------------------
async function init() {
  console.log("Renderer starting…");

  await loadParts();
  await loadPartGeometry();
  await loadLayout();

  svg.innerHTML = "";

  const root = el("g");
  svg.appendChild(root);

  renderLayout(root);
  renderSwitches(LAYOUT.items, root);
  autoFit(root, LAYOUT.items);
}

// -------------------------------------------------------
// AUTO CENTER + SCALE
// -------------------------------------------------------
function autoFit(root, items) {
  const pad = 40;
  let minX = Infinity,
    minY = Infinity;
  let maxX = -Infinity,
    maxY = -Infinity;

  items.forEach((i) => {
    const geo = PART_GEOMETRY[i.part];
    if (!geo) return;

    minX = Math.min(minX, i.x - geo.origin.x);
    minY = Math.min(minY, i.y - geo.origin.y);
    maxX = Math.max(maxX, i.x + (geo.width - geo.origin.x));
    maxY = Math.max(maxY, i.y + (geo.height - geo.origin.y));
  });

  const layoutW = maxX - minX;
  const layoutH = maxY - minY;

  const svgW = svg.clientWidth;
  const svgH = svg.clientHeight;

  const scale = Math.min(
    (svgW - pad * 2) / layoutW,
    (svgH - pad * 2) / layoutH
  );

  const tx = (svgW - layoutW * scale) / 2 - minX * scale;
  const ty = (svgH - layoutH * scale) / 2 - minY * scale;

  root.setAttribute("transform", `translate(${tx},${ty}) scale(${scale})`);
}

// -------------------------------------------------------
// ITEMS
// -------------------------------------------------------
function normalizePartName(name) {
  return name
    .toUpperCase()
    .replace(/^TB\s+/, "")
    .replace(/^TS\s+/, "")
    .trim();
}

function renderLayout(root) {
  LAYOUT.items.forEach((item) => {
    const geo = PART_GEOMETRY[item.part];
    const imgURL = PART_IMAGES[normalizePartName(item.part)];

    if (!geo || !imgURL) return;

    const angle = bbOrientationToDegrees(item.orientation);

    const g = el("g");
    g.setAttribute(
      "transform",
      `translate(${item.x},${item.y}) rotate(${angle})`
    );

    const img = el("image");
    img.setAttribute("href", imgURL);

    img.setAttribute("x", -geo.origin.x);
    img.setAttribute("y", -geo.origin.y);
    img.setAttribute("width", geo.width);
    img.setAttribute("height", geo.height);

    g.appendChild(img);
    root.appendChild(g);
  });
}

// -------------------------------------------------------
// SWITCH OVERLAYS (IMPROVED)
// -------------------------------------------------------
function switchButtonOffset(item) {
  let dx = 0,
    dy = 0;
  const n = item.part.toUpperCase();

  if (n.includes("LEFT")) dx = -item.w * 0.25;
  if (n.includes("RIGHT")) dx = item.w * 0.25;
  if (n.includes("CURVE")) dy = -item.h * 0.15;

  return { dx, dy };
}

function renderSwitches(items, root) {
  items.forEach((item) => {
    if (!isSwitchPart(item)) return;

    const { dx, dy } = switchButtonOffset(item);

    const g = el("g");
    g.setAttribute(
      "transform",
      `translate(${item.x + dx},${item.y + dy}) rotate(${bbOrientationToDegrees(
        item.orientation
      )})`
    );
    g.style.cursor = "pointer";

    const dot = el("circle");
    dot.setAttribute("r", 6);
    dot.setAttribute("fill", "#2ecc71");
    dot.setAttribute("stroke", "#111");
    dot.setAttribute("stroke-width", "2");
    g.appendChild(dot);

    g.addEventListener("click", (e) => {
      if (e.shiftKey) {
        openCalibration(item);
      } else {
        toggleSwitch(item.id, dot);
      }
    });

    root.appendChild(g);
  });
}

// -------------------------------------------------------
// SWITCH CONTROL
// -------------------------------------------------------
async function toggleSwitch(id, indicator) {
  try {
    const res = await fetch(`/api/switch/${id}/toggle`);

    if (!res.ok) {
      console.warn("Switch toggle failed:", id);
      indicator.setAttribute("fill", "#e74c3c"); // red = not configured
      return; // DO NOT change color
    }

    const data = await res.json();

    if (typeof data.state !== "number") {
      console.warn("Invalid switch response:", data);
      return; // DO NOT change color
    }

    indicator.setAttribute("fill", data.state === 1 ? "#f1c40f" : "#2ecc71");
  } catch (err) {
    console.error("Toggle error:", err);
  }
}

// -------------------------------------------------------
// CALIBRATION UI (unchanged logic)
// -------------------------------------------------------

function bindSlider(sliderId, labelId) {
  const slider = document.getElementById(sliderId);
  const label = document.getElementById(labelId);

  if (!slider || !label) return;

  label.textContent = slider.value;

  slider.oninput = () => {
    label.textContent = slider.value;
  };
}

async function openCalibration(item) {
  activeSwitch = item;
  document.getElementById("cal-id").textContent = item.id;
  await loadCalibration(item);

  bindSlider("cal-a0", "cal-a0-val");
  bindSlider("cal-a1", "cal-a1-val");

  document.getElementById("cal-panel").classList.add("show");
}

async function testServo(state) {
  if (!activeSwitch) return;

  try {
    await fetch(`/api/switch/${activeSwitch.id}/toggle`);
  } catch (err) {
    console.error("Test servo failed:", err);
  }
}

async function saveCalibration() {
  if (!activeSwitch) return;

  const channel = parseInt(document.getElementById("cal-channel").value, 10);
  const angle0 = parseInt(document.getElementById("cal-a0").value, 10);
  const angle1 = parseInt(document.getElementById("cal-a1").value, 10);

  try {
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
      console.error("Save calibration failed");
      return;
    }

    closeCalibration();
  } catch (err) {
    console.error("Save calibration error:", err);
  }
}

function closeCalibration() {
  document.getElementById("cal-panel").classList.remove("show");
  activeSwitch = null;
}

window.onload = init;
