// =======================================================
// LEGO-ORMS — DOM-ONLY RENDERER (NO SVG / NO CANVAS)
// =======================================================

let PART_IMAGES = {};
let LAYOUT = null;
let activeSwitch = null;

// -------------------------------------------------------
// UTILITIES
// -------------------------------------------------------

function normalizePartName(name) {
  return name
    .toUpperCase()
    .replace(/^TB\s+/, "")
    .replace(/^TS\s+/, "")
    .trim();
}

function bbOrientationToDegrees(o) {
  // BlueBrick orientation units: 0–2520, where 630 = 90°
  return (o || 0) / 10;
}

// -------------------------------------------------------
// LOADERS
// -------------------------------------------------------

async function loadParts() {
  const res = await fetch("/api/parts");
  if (!res.ok) throw new Error("Failed to load parts");

  PART_IMAGES = await res.json();
  console.log("Loaded part images:", Object.keys(PART_IMAGES).length);
}

async function loadLayout() {
  const res = await fetch("/res/layout.json");
  if (!res.ok) throw new Error("Failed to load layout.json");

  LAYOUT = await res.json();
  console.log("Layout loaded:", LAYOUT.items.length, "items");
}

async function loadCalibration(item) {
  try {
    const res = await fetch("/api/switch_config");
    if (!res.ok) return;

    const cfg = await res.json();
    const sw = cfg.switches?.[item.id];
    if (!sw) return;

    document.getElementById("cal-channel").value = sw.channel ?? 0;
    document.getElementById("cal-a0").value = sw.angle0 ?? 65;
    document.getElementById("cal-a1").value = sw.angle1 ?? 105;

    document.getElementById("cal-a0-val").textContent =
      document.getElementById("cal-a0").value;
    document.getElementById("cal-a1-val").textContent =
      document.getElementById("cal-a1").value;
  } catch (err) {
    console.error("Failed to load calibration:", err);
  }
}

// -------------------------------------------------------
// SWITCH DETECTION
// -------------------------------------------------------

const SWITCH_PART_IDS = new Set([
  "2861", // left switch
  "2859", // right switch
  "7996", // crossover / special
]);

function isSwitchPart(item) {
  if (!item?.part) return false;

  const name = item.part.toUpperCase();

  if (
    name.includes("SWITCH") ||
    name.includes("POINT") ||
    name.includes("TURNOUT") ||
    name.includes("SLIP")
  ) {
    return true;
  }

  const match = name.match(/\b\d{4}\b/);
  return !!(match && SWITCH_PART_IDS.has(match[0]));
}

// -------------------------------------------------------
// RENDERING
// -------------------------------------------------------

function renderLayout(items) {
  const panel = document.getElementById("panel");
  panel.innerHTML = "";

  items.forEach((item) => {
    const img = document.createElement("img");
    img.className = "part";

    const key = normalizePartName(item.part);
    img.src = PART_IMAGES[key] || "";

    // Position & size (absolute, no scaling)
    img.style.left = `${item.x}px`;
    img.style.top = `${item.y}px`;
    img.style.width = `${item.w}px`;
    img.style.height = `${item.h}px`;

    // Rotation
    const deg = bbOrientationToDegrees(item.orientation);
    img.style.transform = `rotate(${deg}deg)`;

    // Interaction for switches
    if (isSwitchPart(item)) {
      img.style.cursor = "pointer";

      img.addEventListener("click", (e) => {
        if (e.shiftKey) {
          openCalibration(item);
        } else {
          toggleSwitch(item.id, img);
        }
      });
    }

    panel.appendChild(img);
  });
}

// -------------------------------------------------------
// SWITCH CONTROL
// -------------------------------------------------------

async function toggleSwitch(id, element) {
  try {
    const res = await fetch(`/api/switch/${id}/toggle`);
    if (!res.ok) {
      console.warn("Switch toggle failed:", id);
      element.style.filter = "brightness(0.6)";
      return;
    }

    const data = await res.json();
    if (typeof data.state !== "number") return;

    element.style.filter =
      data.state === 1 ? "brightness(1.3)" : "brightness(1)";
  } catch (err) {
    console.error("Toggle error:", err);
  }
}

// -------------------------------------------------------
// CALIBRATION UI
// -------------------------------------------------------

function bindSlider(sliderId, labelId) {
  const slider = document.getElementById(sliderId);
  const label = document.getElementById(labelId);
  if (!slider || !label) return;

  label.textContent = slider.value;
  slider.oninput = () => (label.textContent = slider.value);
}

async function openCalibration(item) {
  activeSwitch = item;
  document.getElementById("cal-id").textContent = item.id;

  await loadCalibration(item);

  bindSlider("cal-a0", "cal-a0-val");
  bindSlider("cal-a1", "cal-a1-val");

  document.getElementById("cal-panel").classList.add("show");
}

async function testServo() {
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

    if (res.ok) closeCalibration();
  } catch (err) {
    console.error("Save calibration error:", err);
  }
}

function closeCalibration() {
  document.getElementById("cal-panel").classList.remove("show");
  activeSwitch = null;
}

// -------------------------------------------------------
// INIT
// -------------------------------------------------------

async function init() {
  console.log("DOM renderer starting…");

  await loadParts();
  await loadLayout();

  renderLayout(LAYOUT.items);
}

window.onload = init;
