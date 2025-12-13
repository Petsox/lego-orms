// =======================================================
// LEGO-ORMS — BUTTON-ONLY SWITCH CONTROL
// =======================================================

let SWITCH_CONFIG = {};
let activeSwitch = null;

// -------------------------------------------------------
// LOADERS
// -------------------------------------------------------

async function loadSwitchConfig() {
  const res = await fetch("/api/switch_config");
  if (!res.ok) throw new Error("Failed to load switch config");

  const cfg = await res.json();
  SWITCH_CONFIG = cfg.switches || {};
}

// -------------------------------------------------------
// RENDERING
// -------------------------------------------------------

function renderSwitchButtons() {
  const container = document.getElementById("switches");
  container.innerHTML = "";

  Object.keys(SWITCH_CONFIG).forEach((id) => {
    const btn = document.createElement("button");
    btn.className = "switch-btn";
    btn.textContent = `Switch ${id}`;
    btn.dataset.id = id;

    btn.addEventListener("click", (e) => {
      if (e.shiftKey) {
        openCalibration({ id });
      } else {
        toggleSwitch(id, btn);
      }
    });

    container.appendChild(btn);
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

// -------------------------------------------------------
// CALIBRATION (REUSED)
// -------------------------------------------------------

async function openCalibration(item) {
  activeSwitch = item;
  document.getElementById("cal-id").textContent = item.id;

  try {
    const res = await fetch("/api/switch_config");
    if (res.ok) {
      const cfg = await res.json();
      const sw = cfg.switches?.[item.id];

      if (sw) {
        document.getElementById("cal-channel").value = sw.channel ?? 0;
        document.getElementById("cal-a0").value = sw.angle0 ?? 65;
        document.getElementById("cal-a1").value = sw.angle1 ?? 105;

        document.getElementById("cal-a0-val").textContent =
          document.getElementById("cal-a0").value;
        document.getElementById("cal-a1-val").textContent =
          document.getElementById("cal-a1").value;
      }
    }
  } catch (err) {
    console.error("Calibration load failed:", err);
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

  await fetch("/api/update_switch_config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      id: activeSwitch.id,
      channel,
      angle0,
      angle1,
    }),
  });

  closeCalibration();
}

function closeCalibration() {
  document.getElementById("cal-panel").classList.remove("show");
  activeSwitch = null;
}

// -------------------------------------------------------
// INIT
// -------------------------------------------------------

async function init() {
  await loadSwitchConfig();
  renderSwitchButtons();
}

window.onload = init;
