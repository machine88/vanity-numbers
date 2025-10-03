// web/app.js
(() => {
  const API_PATH = "/last5"; // CloudFront -> API Gateway

  const $status  = document.getElementById("status");
  const $results = document.getElementById("results");

  function fmtWhen(iso) {
    if (!iso) return "";
    try {
      const d = new Date(iso);
      const opts = {
        year: "numeric", month: "short", day: "numeric",
        hour: "numeric", minute: "2-digit"
      };
      return d.toLocaleString(undefined, opts);
    } catch {
      return iso;
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
    $who.textContent = item.caller || item.caller_number || "Unknown";

    const $time = document.createElement("div");
    $time.className = "time";
    $time.textContent = fmtWhen(item.created_at || item.time || "");

    $left.appendChild($who);
    $left.appendChild($time);

    const $right = document.createElement("div");
    $right.className = "pills";

    // Prefer API shape: items[].top3
    let cands = [];
    if (Array.isArray(item.top3) && item.top3.length) {
      cands = item.top3.filter(Boolean).slice(0, 3);
    } else if (Array.isArray(item.vanity_candidates) && item.vanity_candidates.length) {
      // backward compat
      cands = item.vanity_candidates.filter(Boolean).slice(0, 3);
    } else if (Array.isArray(item.raw)) {
      // very old shape: [{display: "..."}]
      cands = item.raw.map(r => r && r.display).filter(Boolean).slice(0, 3);
    }

    $right.appendChild(pill(cands[0] || "", "Top match"));
    $right.appendChild(pill(cands[1] || "", "Option 2"));
    $right.appendChild(pill(cands[2] || "", "Option 3"));

    $row.appendChild($left);
    $row.appendChild($right);
    return $row;
  }

  async function load() {
    try {
      $status.textContent = "Loading…";
      const r = await fetch(API_PATH, { headers: { "Accept": "application/json" } });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();

      // normalize to an array
      const items = Array.isArray(data?.items) ? data.items
                   : Array.isArray(data)       ? data
                   : [];

      // newest → oldest
      items.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));

      // render
      $results.innerHTML = "";
      const $badge = document.createElement("div");
      $badge.className = "status";
      $badge.innerHTML = '<span class="dot"></span> Updated just now';
      $results.appendChild($badge);

      const show = items.slice(0, 5);
      if (!show.length) {
        const $empty = document.createElement("div");
        $empty.className = "empty";
        $empty.textContent = "No recent calls yet.";
        $results.appendChild($empty);
      } else {
        show.forEach(i => $results.appendChild(row(i)));
      }

      $status.textContent = "";
    } catch (err) {
      $status.textContent = `Couldn't load recent calls (${err.message}).`;
    }
  }

  load();
  // Optional periodic refresh:
  // setInterval(load, 30000);
})();