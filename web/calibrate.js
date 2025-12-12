async function loadConfig() {
    const cfg = await fetch("/api/switch_config").then(r => r.json());
    const div = document.getElementById("cal-list");

    Object.entries(cfg.switches).forEach(([id, sw]) => {
        let box = document.createElement("div");
        box.style.border = "1px solid #ccc";
        box.style.padding = "12px";
        box.style.margin = "8px";

        box.innerHTML = `
            <h3>Switch ${id}</h3>
            Channel: <input id="ch-${id}" type="number" min="0" max="15" value="${sw.channel}"><br>
            Angle 0: <input id="a0-${id}" type="number" value="${sw.angle0}"><br>
            Angle 1: <input id="a1-${id}" type="number" value="${sw.angle1}"><br><br>

            <button onclick="test('${id}', 0)">Test 0</button>
            <button onclick="test('${id}', 1)">Test 1</button>
            <button onclick="save('${id}')">Save</button>
        `;

        div.appendChild(box);
    });
}


async function test(id, state) {
    await fetch("/api/test_servo", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({id, state})
    });
}


async function save(id) {
    const channel = document.getElementById(`ch-${id}`).value;
    const a0 = document.getElementById(`a0-${id}`).value;
    const a1 = document.getElementById(`a1-${id}`).value;

    await fetch("/api/update_switch_config", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            id,
            channel,
            angle0: a0,
            angle1: a1
        })
    });

    alert("Saved!");
}

loadConfig();
