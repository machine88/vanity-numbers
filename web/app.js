/* Minimal, robust fetch + render for the last 5 callers */

const API_BASE = "";
const STATUS = document.getElementById("status");
const RESULTS = document.getElementById("results");

/** small helpers **/
const fmtTime = iso => {
  try {
    const d = new Date(iso);
    return d.toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
  } catch { return iso; }
};
const h = (tag, attrs={}, children=[]) => {
  const el = document.createElement(tag);
  Object.entries(attrs).forEach(([k,v]) => {
    if (k === "class") el.className = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v);
  });
  ([]).concat(children).forEach(c => el.append(c instanceof Node ? c : document.createTextNode(c)));
  return el;
};

async function load() {
  try {
    const res = await fetch(`${API_BASE}/last5`, { headers: { "Accept": "application/json" }});
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    // data expected: [{caller_number, created_at, vanity_candidates: [..]}]
    renderRows(Array.isArray(data) ? data : []);
  } catch (err) {
    STATUS.textContent = `Couldn’t load recent calls (${err.message}).`;
    STATUS.style.background = "rgba(220,53,69,.12)";
    STATUS.style.borderColor = "rgba(220,53,69,.25)";
  }
}

function renderRows(items) {
  // clear old rows (keep the status pill for accessibility)
  [...RESULTS.querySelectorAll(".row")].forEach(n => n.remove());

  if (!items.length) {
    STATUS.innerHTML = `<span class="dot"></span> No calls yet.`;
    return;
  }

  STATUS.innerHTML = `<span class="dot"></span> Updated just now`;
  items.forEach(row => {
    const who = h("div", {}, [
      h("div", { class: "who" }, row.caller_number || "Unknown"),
      h("div", { class: "time" }, fmtTime(row.created_at || "")),
    ]);

    const pills = h("div", { class: "pills" }, (row.vanity_candidates || [])
      .slice(0, 5)
      .map((v, i) => {
        const pill = h("span", { class: "pill", role: "button", tabindex: 0 }, [
          v,
          h("small", {}, i === 0 ? "Top match" : `Option ${i+1}`)
        ]);
        pill.addEventListener("click", () => navigator.clipboard?.writeText(v));
        return pill;
      })
    );

    const wrap = h("div", { class: "row" }, [who, pills]);
    RESULTS.append(wrap);
  });
}

document.addEventListener("DOMContentLoaded", load);