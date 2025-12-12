//
// main.js — LEGO-ORMS Layout Renderer
//

async function loadLayout() {
    try {
        const res = await fetch("/api/layout");
        if (!res.ok) {
            console.error("Failed to load layout:", res.status);
            return;
        }

        const data = await res.json();
        console.log("Full /api/layout response:", data);

        const layout = data.layout;          // <- layout_loader.py output
        const items = layout.items || [];
        const switches = layout.switches || [];

        console.log("Items:", items);
        console.log("Switches:", switches);

        const svg = document.getElementById("track-svg");
        if (!svg) {
            console.error("track-svg element not found in HTML");
            return;
        }

        // Clear any previous drawings
        svg.innerHTML = "";

        // --- DRAW ALL TRACK ITEMS ---
        items.forEach(item => {
            drawItem(svg, item);
        });

        // --- DRAW SWITCHES (CLICKABLE) ---
        switches.forEach(sw => {
            drawSwitch(svg, sw);
        });

    } catch (err) {
        console.error("Error loading layout:", err);
    }
}


// --------------------------------------------------------
// DRAWING FUNCTIONS
// --------------------------------------------------------

function drawItem(svg, item) {
    const g = createSvgElement("g");
    g.setAttribute("transform", `translate(${item.x_norm}, ${item.y_norm}) rotate(${item.rotation_deg})`);

    // Basic rectangle to represent track pieces (custom graphics later)
    const rect = createSvgElement("rect");
    rect.setAttribute("x", -item.width / 2);
    rect.setAttribute("y", -item.height / 2);
    rect.setAttribute("width", item.width);
    rect.setAttribute("height", item.height);
    rect.setAttribute("fill", "#555");
    rect.setAttribute("opacity", "0.4");

    g.appendChild(rect);
    svg.appendChild(g);
}


function drawSwitch(svg, sw) {
    const g = createSvgElement("g");

    g.setAttribute("transform", `translate(${sw.x_norm}, ${sw.y_norm}) rotate(${sw.rotation_deg})`);
    g.style.cursor = "pointer";
    g.dataset.switchId = sw.id;

    // Switch icon — triangle pointer
    const tri = createSvgElement("polygon");
    tri.setAttribute("points", "0,-12 10,10 -10,10");
    tri.setAttribute("fill", "limegreen");
    tri.setAttribute("stroke", "black");
    tri.setAttribute("stroke-width", "1");

    g.appendChild(tri);

    // On click → toggle switch
    g.addEventListener("click", () => {
        console.log("Clicked switch:", sw.id);
        toggleSwitch(sw.id);
    });

    svg.appendChild(g);
}


// Utility to create SVG nodes
function createSvgElement(name) {
    return document.createElementNS("http://www.w3.org/2000/svg", name);
}


// --------------------------------------------------------
// SEND COMMAND TO SERVER
// --------------------------------------------------------
async function toggleSwitch(id) {
    console.log("Sending toggle request:", id);

    try {
        const res = await fetch(`/api/switch/${id}/toggle`);
        const json = await res.json();
        console.log("Switch response:", json);
    } catch (err) {
        console.error("Error toggling switch:", err);
    }
}


// Load layout on startup
window.onload = loadLayout;
