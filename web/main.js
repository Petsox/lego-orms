async function loadLayout() {
    const data = await fetch("/api/get_layout").then(r => r.json());

    const svg = document.getElementById("track-svg");

    data.items.forEach(it => {
        let g = document.createElementNS("http://www.w3.org/2000/svg", "g");

        g.setAttribute("transform", `translate(${it.x},${it.y}) rotate(${it.rotation})`);

        // Draw a basic box for items (replace with better graphics later)
        let rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        rect.setAttribute("x", -10);
        rect.setAttribute("y", -10);
        rect.setAttribute("width", 20);
        rect.setAttribute("height", 20);
        rect.setAttribute("fill", "#888");
        g.appendChild(rect);

        svg.appendChild(g);
    });

    // Render switches with special color and click handler
    data.switches.forEach(sw => {
        let g = document.createElementNS("http://www.w3.org/2000/svg", "g");

        g.setAttribute("id", `sw-${sw.id}`);
        g.setAttribute("transform", `translate(${sw.x},${sw.y}) rotate(${sw.rotation})`);
        g.style.cursor = "pointer";

        g.onclick = () => toggleSwitch(sw.id);

        let tri = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
        tri.setAttribute("points", "-12,-10 12,-10 0,12");
        tri.setAttribute("fill", "green");

        g.appendChild(tri);
        svg.appendChild(g);
    });
}


async function toggleSwitch(id) {
    console.log("Switch clicked:", id);

    await fetch("/api/set_switch", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({id: id, state: 1})
    });

    // You can toggle visual state here later  
}

loadLayout();
