// web/app.js
(() => {
  const API_PATH = "/last5"; // goes CloudFront -> API Gateway

  const $status  = document.getElementById("status");
  const $results = document.getElementById("results");

  function fmtWhen(iso) {
    try {
      const d = new Date(iso);
      const opts = { year: 'numeric', month: 'short', day: 'numeric',
                     hour: 'numeric', minute: '2-digit' };
      return d.toLocaleString(undefined, opts);
    } catch {
      return iso || "";
    }
  }

  function pill(text, label) {
    const $p = document.createElement("div");
    $p.className = "pill";
    $p.textContent = text || "—";
    const $s = document.createElement("small");
    $s.textContent = label;
    $p.appendChild($s);
    return $p;
  }

  function row(item) {
    const $row = document.createElement("div");
    $row.className = "row";

    const $left = document.createElement("div");
    const $who  = document.createElement("div");
    $who.className = "who";
    $who.textContent = item.caller_number || "Unknown";
    const $time = document.createElement("div");
    $time.className = "time";
    $time.textContent = fmtWhen(item.created_at || "");

    $left.appendChild($who);
    $left.appendChild($time);

    const $right = document.createElement("div");
    $right.className = "pills";

    const cands = Array.isArray(item.vanity_candidates) ? item.vanity_candidates.slice(0, 3) : [];

    $right.appendChild(pill(cands[0] || "", "Top match"));
    $right.appendChild(pill(cands[1] || "", "Option 2"));
    $right.appendChild(pill(cands[2] || "", "Option 3"));

    $row.appendChild($left);
    $row.appendChild($right);
    return $row;
  }

  async function load() {
    try {
      const r = await fetch(API_PATH, { headers: { "Accept": "application/json" } });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);

      // The API is Lambda-proxy shaped: { statusCode, headers, body: "<json string>" }
      const raw = await r.json();
      const payload = typeof raw?.body === "string" ? JSON.parse(raw.body) : raw;

      // Normalize to what the renderer expects
      const items = (Array.isArray(payload?.items) ? payload.items
                      : Array.isArray(payload) ? payload
                      : [])
        .map(it => ({
          caller_number: it.caller || it.caller_number || "Unknown",
          created_at: it.created_at || it.createdAt || it.ts || "",
          // map top3 -> vanity_candidates
          vanity_candidates: Array.isArray(it.top3) ? it.top3
                            : Array.isArray(it.vanity_candidates) ? it.vanity_candidates
                            : [],
        }));

      // newest → oldest
      items.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));

      // render
      $results.innerHTML = "";
      const $badge = document.createElement("div");
      $badge.className = "status";
      $badge.innerHTML = '<span class="dot"></span> Updated just now';
      $results.appendChild($badge);

      items.slice(0, 5).forEach(i => $results.appendChild(row(i)));
    } catch (err) {
      if ($status) $status.textContent = `Couldn't load recent calls (${err.message}).`;
    }
  }

  load();
  // setInterval(load, 30000); // optional auto-refresh
})();