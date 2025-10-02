// web/app.js
async function loadCallers() {
  const list = document.getElementById("callers");
  list.innerHTML = "<li>Loading...</li>";

  try {
    // 👇 Replace this placeholder with your real API URL (Terraform output)
    const API_BASE = "https://yck4rmhbo3.execute-api.us-west-2.amazonaws.com";

    const resp = await fetch(`${API_BASE}/last5`);
    if (!resp.ok) throw new Error(`API returned ${resp.status}`);
    const data = await resp.json();

    list.innerHTML = "";
    data.forEach(item => {
      const li = document.createElement("li");
      li.innerHTML = `
        <div class="caller">${item.caller_number}</div>
        <div class="time">${item.created_at}</div>
        <div>Candidates: ${item.vanity_candidates.join(", ")}</div>
      `;
      list.appendChild(li);
    });
  } catch (err) {
    list.innerHTML = `<li>Error: ${err.message}</li>`;
  }
}

// Run on page load
loadCallers();