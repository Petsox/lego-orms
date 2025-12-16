// =======================================================
// LEGO-ORMS — SWITCH BUTTON UI (FROM Layout.bbm)
// =======================================================

let SWITCHES = [];
let activeSwitch = null;

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

// -------------------------------------------------------
// RENDERING
// -------------------------------------------------------

function renderSwitchButtons() {
  const container = document.getElementById("switches");
  container.innerHTML = "";

  SWITCHES.forEach((sw) => {
    if (sw.hidden) return;
    const btn = document.createElement("button");
    btn.className = "switch-btn";

    // Prefer user_name, fallback to old text
    btn.textContent =
      sw.user_name && sw.user_name.trim() !== ""
        ? sw.user_name
        : `Switch ${sw.id}`;

    // Keep technical name as tooltip (useful)
    btn.title = sw.name || `Switch ${sw.id}`;

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
      channel: sw.channel,
      angle0: sw.angle0,
      angle1: sw.angle1,
      user_name: sw.user_name || "",
    }),
  });

  if (!res.ok) return;

  // Update frontend state
  sw.hidden = false;

  renderSwitchButtons();
  openHiddenPanel(); // refresh list
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
  renderSwitchButtons();
  bindCalibrationSliders();
}

window.onload = init;
