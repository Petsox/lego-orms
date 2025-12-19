// =======================================================
// LEGO-ORMS — SWITCH BUTTON UI (FROM Layout.bbm)
// =======================================================

let SWITCHES = [];
let activeSwitch = null;
const STUD_PX = 8;
let layoutScale = 1.07; // >1 = zoom out, <1 = zoom in
const TRACK_COLOR = "#666";
const SWITCH_COLOR = "#7a7a7a"; // slightly brighter, neutral
const SVG_NS = "http://www.w3.org/2000/svg";

// -------------------------------------------------------
// LOADERS
// -------------------------------------------------------

async function loadSwitchesFromLayout() {
  const res = await fetch("/api/switches");
  if (!res.ok) throw new Error("Failed to load switches from layout");

  const data = await res.json();

  SWITCHES = Object.entries(data).map(([id, sw]) => ({
    id,
    ...sw,
  }));

  console.log("Loaded switches:", SWITCHES.length);
}

async function loadAndRenderLayout() {
  const layoutData = await fetch("/api/layout").then((r) => r.json());
  const switchConfig = await fetch("/api/switches").then((r) => r.json());

  renderLayout(layoutData.bricks);
  renderMarkers(
    document.getElementById("layout-svg"),
    layoutData.bricks,
    switchConfig
  );
}

// -------------------------------------------------------
// RENDERING
// -------------------------------------------------------

function updateMarkerHighlight() {
  const markers = document.querySelectorAll("#markers > *");

  markers.forEach((el) => {
    const sid = el.dataset.switchId;

    if (!hoveredSwitchId) {
      el.style.opacity = "1";
      el.style.filter = "none";
      return;
    }

    if (sid === hoveredSwitchId) {
      el.style.opacity = "1";
      el.style.filter = "drop-shadow(0 0 12px rgba(255,255,255,0.9))";
    } else {
      el.style.opacity = "0.25";
      el.style.filter = "none";
    }
  });
}

function renderSwitchButtons() {
  const container = document.getElementById("switches");
  container.innerHTML = "";

  SWITCHES.forEach((sw) => {
    if (sw.hidden) return;

    const btn = document.createElement("button");
    btn.className = "switch-btn";

    // 🔹 Build button label with channel
    const baseName =
      sw.user_name && sw.user_name.trim() !== ""
        ? sw.user_name
        : `Switch ${sw.id}`;

    const channelText =
      sw.channel !== null && sw.channel !== undefined
        ? ` (CH ${sw.channel})`
        : " (no channel)";

    btn.textContent = baseName + channelText;

    // 🔹 Tooltip keeps technical name
    btn.title = sw.name || `Switch ${sw.id}`;

    // 🟡 Hover highlight → layout markers
    btn.addEventListener("mouseenter", () => {
      hoveredSwitchId = String(sw.id);
      updateMarkerHighlight();
    });

    btn.addEventListener("mouseleave", () => {
      hoveredSwitchId = null;
      updateMarkerHighlight();
    });

    // 🔵 Click behavior (unchanged)
    btn.addEventListener("click", (e) => {
      if (e.shiftKey) {
        openCalibration(sw);
        return;
      }

      // 🔴 Guard: channel not assigned
      if (sw.channel === null || sw.channel === undefined) {
        alert(
          "This switch has no channel assigned yet.\n" +
            "Please calibrate it before using it."
        );
        return;
      }

      toggleSwitch(sw.id, btn);
    });

    container.appendChild(btn);
  });
}

//Render Layout Map

function computeLayoutBounds(bricks) {
  let minX = Infinity,
    minY = Infinity;
  let maxX = -Infinity,
    maxY = -Infinity;

  bricks.forEach((b) => {
    minX = Math.min(minX, b.x);
    minY = Math.min(minY, b.y);
    maxX = Math.max(maxX, b.x + b.w);
    maxY = Math.max(maxY, b.y + b.h);
  });

  return {
    x: minX * STUD_PX,
    y: minY * STUD_PX,
    width: (maxX - minX) * STUD_PX,
    height: (maxY - minY) * STUD_PX,
  };
}

function renderLayout(bricks) {
  const svg = document.getElementById("layout-svg");
  svg.innerHTML = "";

  const bounds = computeLayoutBounds(bricks);

  const centerX = bounds.x + bounds.width / 2;
  const centerY = bounds.y + bounds.height / 2;

  const scaledWidth = bounds.width * layoutScale;
  const scaledHeight = bounds.height * layoutScale;

  svg.setAttribute(
    "viewBox",
    `${centerX - scaledWidth / 2}
   ${centerY - scaledHeight / 2}
   ${scaledWidth}
   ${scaledHeight}`
  );

  bricks.forEach((b) => {
    const rect = document.createElementNS(SVG_NS, "rect");

    rect.setAttribute("x", b.x * STUD_PX);
    rect.setAttribute("y", b.y * STUD_PX);
    rect.setAttribute("width", b.w * STUD_PX);
    rect.setAttribute("height", b.h * STUD_PX);
    rect.setAttribute("fill", b.is_switch ? SWITCH_COLOR : TRACK_COLOR);

    svg.appendChild(rect);
  });
}

//Render hidden switches
document
  .getElementById("show-hidden-btn")
  .addEventListener("click", openHiddenPanel);

function openHiddenPanel() {
  closeCalibration();

  const panel = document.getElementById("hidden-switches-panel");
  const list = document.getElementById("hidden-switches-list");

  list.innerHTML = "";

  SWITCHES.forEach((sw) => {
    if (!sw.hidden) return;

    const row = document.createElement("div");

    const btn = document.createElement("button");

    // Determine display name (same logic as main buttons)
    const switchLabel =
      sw.user_name && sw.user_name.trim() !== ""
        ? sw.user_name
        : sw.name || `Switch ${sw.id}`;

    btn.textContent = `Unhide ${switchLabel}`;

    btn.onclick = function () {
      unhideSwitch(sw);
    };

    row.appendChild(btn);
    list.appendChild(row);
  });

  panel.classList.add("show");
}

function closeHiddenPanel() {
  document.getElementById("hidden-switches-panel").classList.remove("show");
}

//Render Markers

function channelColor(channel) {
  const hue = (channel * 47) % 360; // deterministic, well-distributed
  return `hsl(${hue}, 70%, 55%)`;
}

function renderMarkers(svg, bricks, switchConfig) {
  let markerGroup = svg.querySelector("#markers");

  if (!markerGroup) {
    markerGroup = document.createElementNS(SVG_NS, "g");
    markerGroup.setAttribute("id", "markers");
    svg.appendChild(markerGroup);
  }

  markerGroup.innerHTML = "";

  bricks.forEach((b) => {
    if (!b.is_switch) return;

    const sw = switchConfig[b.id];
    if (!sw || sw.hidden) return;

    const cx = (b.x + b.w / 2) * STUD_PX;
    const cy = (b.y + b.h / 2) * STUD_PX;

    const hasChannel = sw.channel !== null && sw.channel !== undefined;

    const color = hasChannel ? channelColor(sw.channel) : "#999"; // neutral gray for unassigned

    // 🔵 Marker circle (BIGGER)
    const circle = document.createElementNS(SVG_NS, "circle");
    circle.setAttribute("cx", cx);
    circle.setAttribute("cy", cy);
    circle.setAttribute("r", 54);
    circle.setAttribute("fill", color);
    circle.setAttribute("stroke", "#111");
    circle.setAttribute("stroke-width", "3");

    // Store channel for hover logic (even if null)
    circle.dataset.switchId = String(b.id);
    circle.dataset.channel = hasChannel ? sw.channel : "";

    // 🔢 Channel number or placeholder
    const text = document.createElementNS(SVG_NS, "text");
    text.setAttribute("x", cx);
    text.setAttribute("y", cy + 16); // optical centering
    text.setAttribute("text-anchor", "middle");
    text.setAttribute("font-size", "50");
    text.setAttribute("font-weight", "bold");
    text.setAttribute("fill", hasChannel ? "#000" : "#222");

    text.textContent = hasChannel ? sw.channel : "–";
    text.dataset.switchId = String(b.id);
    text.dataset.channel = hasChannel ? sw.channel : "";

    markerGroup.appendChild(circle);
    markerGroup.appendChild(text);
  });
}

// -------------------------------------------------------
// SWITCH CONTROL
// -------------------------------------------------------

async function toggleSwitch(id, button) {
  try {
    const res = await fetch(`/api/switch/${id}/toggle`);
    if (!res.ok) {
      button.classList.add("error");
      return;
    }

    const data = await res.json();
    updateButtonState(button, data.state);
  } catch (err) {
    console.error("Toggle error:", err);
  }
}

function updateButtonState(button, state) {
  button.classList.remove("state-0", "state-1");

  if (state === 0) button.classList.add("state-0");
  if (state === 1) button.classList.add("state-1");
}

// Unhide a switch

async function unhideSwitch(sw) {
  const res = await fetch("/api/update_switch_config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      id: sw.id,
      hidden: false,
      user_name: sw.user_name || "",
    }),
  });

  if (!res.ok) {
    console.error("Failed to unhide switch");
    return;
  }

  // 🔑 RELOAD FROM BACKEND — DO NOT MUTATE LOCAL STATE
  await loadSwitches();          // <-- THIS IS THE FIX
  renderSwitchButtons();
  openHiddenPanel();
  await loadAndRenderLayout();
}


// -------------------------------------------------------
// CALIBRATION UI (UNCHANGED LOGIC)
// -------------------------------------------------------

function bindCalibrationSliders() {
  const a0 = document.getElementById("cal-a0");
  const a0Val = document.getElementById("cal-a0-val");

  const a1 = document.getElementById("cal-a1");
  const a1Val = document.getElementById("cal-a1-val");

  if (!a0 || !a1 || !a0Val || !a1Val) {
    console.warn("Calibration sliders not found");
    return;
  }

  // Initial values
  a0Val.textContent = a0.value;
  a1Val.textContent = a1.value;

  // Live update on move
  a0.addEventListener("input", () => {
    a0Val.textContent = a0.value;
  });

  a1.addEventListener("input", () => {
    a1Val.textContent = a1.value;
  });
}

async function openCalibration(sw) {
  closeHiddenPanel();

  activeSwitch = sw;
  document.getElementById("cal-user-name").value = sw.user_name || "";
  document.getElementById("cal-id").textContent =
    sw.id + (sw.name ? " (" + sw.name + ")" : "");
  document.getElementById("cal-hidden").checked = !!sw.hidden;
  document.getElementById("show-hidden-btn").style.display = "none";

  try {
    const res = await fetch("/api/switch_config");
    if (res.ok) {
      const cfg = await res.json();
      const c = cfg.switches?.[sw.id];

      if (c) {
        document.getElementById("cal-channel").value = c.channel ?? 0;
        document.getElementById("cal-a0").value = c.angle0 ?? 65;
        document.getElementById("cal-a1").value = c.angle1 ?? 105;

        document.getElementById("cal-a0-val").textContent =
          document.getElementById("cal-a0").value;
        document.getElementById("cal-a1-val").textContent =
          document.getElementById("cal-a1").value;
      }
    }
  } catch (err) {
    console.error("Failed to load calibration:", err);
  }

  document.getElementById("cal-panel").classList.add("show");
}

async function testServo() {
  if (!activeSwitch) return;
  await fetch(`/api/switch/${activeSwitch.id}/toggle`);
}

async function saveCalibration() {
  if (!activeSwitch) return;

  const channel = parseInt(document.getElementById("cal-channel").value, 10);
  const angle0 = parseInt(document.getElementById("cal-a0").value, 10);
  const angle1 = parseInt(document.getElementById("cal-a1").value, 10);
  const userName = document.getElementById("cal-user-name").value || "";
  const hidden = document.getElementById("cal-hidden").checked;

  const res = await fetch("/api/update_switch_config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      id: activeSwitch.id,
      channel,
      angle0,
      angle1,
      user_name: userName,
      hidden: hidden,
    }),
  });

  if (!res.ok) {
    let msg = "The selected channel is not valid.";

    try {
      const err = await res.json();
      msg = err.message || err.error || msg;
    } catch (e) {}

    alert(msg);
    return;
  }

  // ✅ UPDATE FRONTEND STATE IMMEDIATELY
  activeSwitch.user_name = userName;
  activeSwitch.hidden = hidden;
  activeSwitch.channel = channel;
  activeSwitch.angle0 = angle0;
  activeSwitch.angle1 = angle1;

  renderSwitchButtons();
  closeCalibration();

  await loadAndRenderLayout(); // re-render layout + markers
}

function closeCalibration() {
  document.getElementById("cal-panel").classList.remove("show");
  document.getElementById("show-hidden-btn").style.display = "";
  activeSwitch = null;
}

// -------------------------------------------------------
// INIT
// -------------------------------------------------------

async function init() {
  await loadSwitchesFromLayout();
  await loadAndRenderLayout();
  renderSwitchButtons();
  bindCalibrationSliders();
}

window.onload = init;
