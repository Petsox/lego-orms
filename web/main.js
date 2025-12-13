// =======================================================
// LEGO-ORMS — SWITCH BUTTON UI (FROM Layout.bbm)
// =======================================================

let SWITCHES = [];
let activeSwitch = null;

// -------------------------------------------------------
// LOADERS
// -------------------------------------------------------

async function loadSwitchesFromLayout() {
  const res = await fetch("/api/switches_from_layout");
  if (!res.ok) throw new Error("Failed to load switches from layout");

  SWITCHES = await res.json();
  console.log("Loaded switches:", SWITCHES.length);
}

// -------------------------------------------------------
// RENDERING
// -------------------------------------------------------

function renderSwitchButtons() {
  const container = document.getElementById("switches");
  container.innerHTML = "";

  SWITCHES.forEach((sw) => {
    const btn = document.createElement("button");
    btn.className = "switch-btn";
    btn.textContent = `Switch ${sw.id}`;
    btn.title = sw.name;

    btn.addEventListener("click", (e) => {
      if (e.shiftKey) {
        openCalibration(sw);
      } else {
        toggleSwitch(sw.id, btn);
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
// CALIBRATION UI (UNCHANGED LOGIC)
// -------------------------------------------------------

async function openCalibration(sw) {
  activeSwitch = sw;
  document.getElementById("cal-id").textContent = sw.id;

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
  await loadSwitchesFromLayout();
  renderSwitchButtons();
}

window.onload = init;
