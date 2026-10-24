/* Mole in the Market | replay page.
   Reads only window.MM_DATA (viz/data/data.js written by tools/reproduce.py, or viz/demo/data.js for the demo).
   Every number shown is computed here from that data; nothing is typed by hand.
   SVG is built as markup strings (no namespace URL needed). Design: docs/viz/DESIGN.md. */
(function () {
  "use strict";
  var D = window.MM_DATA;
  var COND_ORDER = ["A", "E", "B", "B_T", "C", "D"];
  var OUTCOME_LABEL = { say_do: "said yes and moved prices", say_only: "said yes only",
    do_only: "moved prices only", neither: "neither" };
  var COLORS = { say_do: "#3ddc97", say_only: "#f0b429", do_only: "#a78bfa", neither: "#3a4350",
    shop1: "#60a5fa", shop2: "#f472b6", muted: "#8b96a5", line: "#2a313a", text: "#e8ecf1", bg: "#14171b" };
  var reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var $ = function (id) { return document.getElementById(id); };

  if (!D || !D.games || !D.games.length) {
    $("app").innerHTML = '<div class="panel empty" style="grid-column:1/-1">No data yet. Run ' +
      "<code>python -m tools.reproduce runs results --viz-dir viz/data --figures-dir figures</code>, " +
      "or open demo.html for invented demo data.</div>";
    return;
  }

  if (D.meta && D.meta.synthetic === true) {
    $("banner").textContent = "DEMO DATA | NOT RESULTS";
    $("banner").hidden = false;
    document.title = "DEMO DATA | " + document.title;
  }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function num(x) { return Number(x); }
  function fmt(x, d) { return num(x).toFixed(d === undefined ? 2 : d); }
  function pct(k, n) { return n ? Math.round(100 * k / n) + "%" : "-"; }
  function wilson(k, n) {
    if (!n) return null;
    var z = 1.96, p = k / n, den = 1 + z * z / n;
    var c = (p + z * z / (2 * n)) / den;
    var h = z * Math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den;
    return [Math.max(0, c - h), Math.min(1, c + h)];
  }

  // ---------- index the data ----------
  var games = D.games.slice().map(function (g) {
    g.say = num(g.say); g.do = num(g.do); g.seed = num(g.seed); g.spy_start = num(g.spy_start);
    g.rounds = num(g.rounds); g.nash = num(g.nash); g.monopoly = num(g.monopoly); g.deal_price = num(g.deal_price);
    return g;
  });
  var byId = {};
  games.forEach(function (g) { byId[g.game_id] = g; });
  var rounds = {};
  D.rounds.forEach(function (r) {
    var g = rounds[r.game_id] || (rounds[r.game_id] = {});
    var rr = g[r.round] || (g[r.round] = {});
    rr[String(r.firm)] = { price: num(r.price), reply: r.reply };
  });
  var messages = {};
  (D.messages || []).forEach(function (m) { messages[m.condition] = m.text; });
  var condNames = {};
  games.forEach(function (g) { condNames[g.condition] = g.condition_name; });
  var conds = COND_ORDER.filter(function (c) { return games.some(function (g) { return g.condition === c; }); });
  var families = games.map(function (g) { return g.family; }).filter(function (f, i, a) { return a.indexOf(f) === i; }).sort();
  var columns = [];
  families.forEach(function (f) {
    games.filter(function (g) { return g.family === f; }).map(function (g) { return g.seed; })
      .filter(function (s, i, a) { return a.indexOf(s) === i; }).sort(function (a, b) { return a - b; })
      .forEach(function (s) { columns.push({ family: f, seed: s }); });
  });
  function gameAt(c, col) {
    return games.filter(function (g) { return g.condition === c && g.family === col.family && g.seed === col.seed; })[0];
  }

  var state = { game: null, round: 1, timer: null };

  // ---------- takeaway ----------
  (function () {
    var offered = games.filter(function (g) { return g.condition !== "A"; });
    var said = offered.filter(function (g) { return g.say; }).length;
    var sayOnly = offered.filter(function (g) { return g.say && !g.do; }).length;
    var moved = offered.filter(function (g) { return g.do; }).length;
    $("takeaway").textContent = "In these " + offered.length + " games with a spy message, " + said +
      " had a shop that said yes, " + moved + " had prices that moved to the deal, and " + sayOnly +
      " said yes without the prices following (directional, in this game only).";
  })();

  // ---------- grid ----------
  function renderGrid() {
    var cols = columns.length;
    var html = '<div class="grid-table" style="grid-template-columns:auto repeat(' + cols + ',minmax(12px,1fr))">';
    html += "<div></div>";
    columns.forEach(function (col, i) {
      var first = i === 0 || columns[i - 1].family !== col.family;
      html += '<div class="grid-head" title="' + esc(col.family) + '">' + (first ? '<span class="fam">' + esc(col.family) + "</span>" : "") + "<br>" + "s" + col.seed + "</div>";
    });
    conds.forEach(function (c) {
      html += '<div class="grid-label">' + esc(condNames[c] || c) + "</div>";
      columns.forEach(function (col) {
        var g = gameAt(c, col);
        if (!g) { html += "<div></div>"; return; }
        var sel = state.game && state.game.game_id === g.game_id ? " sel" : "";
        html += '<button class="px o-' + g.outcome + sel + '" data-id="' + esc(g.game_id) + '" aria-label="' +
          esc((condNames[c] || c) + ", " + g.family + ", seed " + g.seed + ": " + OUTCOME_LABEL[g.outcome]) + '"></button>';
      });
    });
    html += "</div>";
    $("grid").innerHTML = html;
    Array.prototype.forEach.call($("grid").querySelectorAll(".px"), function (b) {
      var g = byId[b.getAttribute("data-id")];
      b.addEventListener("click", function () { select(g, true); });
      b.addEventListener("mousemove", function (e) {
        tip(e, "<b>" + esc(condNames[g.condition] || g.condition) + "</b><br>" + esc(g.family) + ", seed " + g.seed +
          "<br>" + esc(OUTCOME_LABEL[g.outcome]));
      });
      b.addEventListener("mouseleave", untip);
    });
  }
  $("legend").innerHTML = ["say_do", "say_only", "do_only", "neither"].map(function (o) {
    return '<span style="--c:' + COLORS[o] + '">' + esc(OUTCOME_LABEL[o]) + "</span>";
  }).join("");

  function tip(e, html) {
    var t = $("tooltip");
    t.innerHTML = html; t.hidden = false;
    t.style.left = Math.min(e.clientX + 12, window.innerWidth - 220) + "px";
    t.style.top = (e.clientY + 12) + "px";
  }
  function untip() { $("tooltip").hidden = true; }

  // ---------- helpers on a game ----------
  function priceRange(g) {
    var lo = Math.min(g.nash, g.deal_price), hi = Math.max(g.monopoly, g.deal_price);
    var rs = rounds[g.game_id] || {};
    Object.keys(rs).forEach(function (r) {
      ["0", "1"].forEach(function (f) { if (rs[r][f]) { lo = Math.min(lo, rs[r][f].price); hi = Math.max(hi, rs[r][f].price); } });
    });
    var pad = (hi - lo) * 0.15 || 0.1;
    return [lo - pad, hi + pad];
  }
  function band(g) { var w = 0.10 * (g.monopoly - g.nash); return [g.deal_price - w, g.deal_price + w]; }
  function replyAt(g, f) { var r = (rounds[g.game_id] || {})[g.spy_start]; return r && r[f] ? r[f].reply : ""; }
  function replyText(r) { return r === "accept" ? "accept" : r === "decline" ? "decline" : "no reply"; }
  function wrap(text, width) {
    var words = String(text).split(/\s+/), lines = [], cur = "";
    words.forEach(function (w) {
      if ((cur + " " + w).trim().length > width) { lines.push(cur.trim()); cur = w; } else { cur += " " + w; }
    });
    if (cur.trim()) lines.push(cur.trim());
    return lines;
  }

  // ---------- replay scene ----------
  function house(x, color) {
    var s = 6, out = "";
    var roof = [[3, 0], [2, 1], [3, 1], [4, 1], [1, 2], [2, 2], [3, 2], [4, 2], [5, 2], [0, 3], [1, 3], [2, 3], [3, 3], [4, 3], [5, 3], [6, 3]];
    roof.forEach(function (p) { out += '<rect x="' + (x + p[0] * s) + '" y="' + (226 + p[1] * s) + '" width="' + s + '" height="' + s + '" fill="' + color + '"/>'; });
    out += '<rect x="' + (x + 6) + '" y="250" width="' + (5 * s) + '" height="' + (4 * s) + '" fill="#2a313a" stroke="' + color + '" stroke-width="2"/>';
    out += '<rect x="' + (x + 18) + '" y="262" width="' + s + '" height="' + (2 * s) + '" fill="' + color + '"/>';
    return out;
  }
  function moleSvg(cx, up) {
    var s = 5, px = function (x, y, c) { return '<rect x="' + (cx + x * s) + '" y="' + (y * s) + '" width="' + s + '" height="' + s + '" fill="' + c + '"/>'; };
    var body = "#8a6a4f", nose = "#f472b6", hat = "#0d0f12", band = "#f0b429", glass = "#0d0f12";
    var out = "";
    for (var x = -5; x <= 3; x++) out += px(x, 0, hat);
    for (x = -3; x <= 1; x++) { out += px(x, -1, band); out += px(x, -2, hat); out += px(x, -3, hat); }
    for (var y = 1; y <= 7; y++) for (x = -4; x <= 2; x++) out += px(x, y, body);
    out += px(-3, 2, glass) + px(-2, 2, glass) + px(0, 2, glass) + px(1, 2, glass) + px(-1, 2, glass);
    out += px(-1, 4, nose);
    return '<g class="mole" style="transform:translateY(' + (up ? 0 : 120) + 'px)"><g transform="translate(0,182)">' + out + "</g></g>";
  }
  function renderScene() {
    var g = state.game, r = state.round;
    var W = 520, H = 300, yr = priceRange(g), top = 30, bottom = 222;
    var y = function (p) { return bottom - (p - yr[0]) / (yr[1] - yr[0]) * (bottom - top); };
    var rs = (rounds[g.game_id] || {})[r] || {};
    var b = band(g), svg = '<svg viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="Replay of round ' + r + '">';
    svg += '<rect x="0" y="0" width="' + W + '" height="' + H + '" fill="' + COLORS.bg + '"/>';
    svg += '<rect x="40" y="' + y(b[1]) + '" width="' + (W - 80) + '" height="' + (y(b[0]) - y(b[1])) + '" fill="rgba(240,180,41,.10)"/>';
    svg += '<line x1="40" x2="' + (W - 40) + '" y1="' + y(g.nash) + '" y2="' + y(g.nash) + '" stroke="' + COLORS.muted + '" stroke-dasharray="2 4"/>';
    svg += '<text x="' + (W - 40) + '" y="' + (y(g.nash) - 4) + '" fill="' + COLORS.muted + '" font-size="10" text-anchor="end">Nash ' + fmt(g.nash) + "</text>";
    svg += '<line x1="40" x2="' + (W - 40) + '" y1="' + y(g.deal_price) + '" y2="' + y(g.deal_price) + '" stroke="' + COLORS.say_only + '" stroke-dasharray="8 5"/>';
    svg += '<text x="' + (W - 40) + '" y="' + (y(g.deal_price) - 4) + '" fill="' + COLORS.say_only + '" font-size="10" text-anchor="end">deal ' + fmt(g.deal_price) + "</text>";
    [["0", 92, COLORS.shop1], ["1", 386, COLORS.shop2]].forEach(function (s) {
      var p = rs[s[0]] ? rs[s[0]].price : null;
      svg += house(s[1], s[2]);
      if (p !== null) {
        svg += '<rect x="' + (s[1] + 10) + '" y="' + y(p) + '" width="22" height="' + Math.max(0, bottom - y(p)) + '" fill="' + s[2] + '" opacity=".85"/>';
        svg += '<text x="' + (s[1] + 21) + '" y="' + (y(p) - 5) + '" fill="' + COLORS.text + '" font-size="11" text-anchor="middle">' + fmt(p) + "</text>";
      }
      svg += '<text x="' + (s[1] + 21) + '" y="292" fill="' + COLORS.muted + '" font-size="10" text-anchor="middle">shop ' + (num(s[0]) + 1) + "</text>";
      if (g.condition !== "A" && r >= g.spy_start) {
        var rep = replyAt(g, s[0]), col = rep === "accept" ? COLORS.say_do : rep === "decline" ? COLORS.muted : COLORS.line;
        svg += '<rect x="' + (s[1] - 4) + '" y="200" width="50" height="16" rx="8" fill="' + COLORS.bg + '" stroke="' + col + '"/>';
        svg += '<text x="' + (s[1] + 21) + '" y="211" fill="' + col + '" font-size="10" text-anchor="middle">' + replyText(rep) + "</text>";
      }
    });
    if (g.condition === "A") {
      svg += '<text x="' + (W / 2) + '" y="270" fill="' + COLORS.muted + '" font-size="12" text-anchor="middle">No spy in this condition</text>';
    } else {
      var up = r >= g.spy_start;
      svg += '<ellipse cx="' + (W / 2) + '" cy="276" rx="44" ry="12" fill="#3a2e24"/>';
      svg += '<clipPath id="mound"><rect x="0" y="0" width="' + W + '" height="276"/></clipPath><g clip-path="url(#mound)">' + moleSvg(W / 2 + 2, up) + "</g>";
      svg += '<ellipse cx="' + (W / 2) + '" cy="280" rx="44" ry="8" fill="#4a3b2e"/>';
      if (up) {
        var lines = wrap(messages[g.condition] || "", 44).slice(0, 6), bh = 14 * lines.length + 12, bw = 290, bx = W / 2 - bw / 2, by = 186 - bh;
        svg += '<rect x="' + bx + '" y="' + by + '" width="' + bw + '" height="' + bh + '" rx="6" fill="#0d0f12" stroke="' + COLORS.say_only + '"/>';
        svg += '<path d="M' + (W / 2 - 6) + " " + (by + bh) + " l6 8 l6 -8 z" + '" fill="#0d0f12" stroke="' + COLORS.say_only + '"/>';
        lines.forEach(function (l, i) { svg += '<text x="' + (bx + 10) + '" y="' + (by + 18 + 14 * i) + '" fill="' + COLORS.text + '" font-size="11">' + esc(l) + "</text>"; });
        if (r === g.spy_start) {
          svg += '<line class="ray" x1="' + (W / 2 - 30) + '" y1="246" x2="140" y2="240" stroke="' + COLORS.say_only + '"/>';
          svg += '<line class="ray" x1="' + (W / 2 + 30) + '" y1="246" x2="384" y2="240" stroke="' + COLORS.say_only + '"/>';
        }
      }
    }
    svg += "</svg>";
    $("scene").innerHTML = svg;
    $("round-label").textContent = "Round " + r + " / " + g.rounds;
    $("round").value = r;
  }
  function renderTrack() {
    var g = state.game, n = g.rounds, at = function (k) { return n > 1 ? (k - 1) / (n - 1) * 100 : 0; };
    var html = "";
    if (g.condition !== "A") {
      var w0 = Math.min(g.spy_start + 1, n), w1 = Math.min(g.spy_start + 3, n);
      html += '<div class="win" style="left:' + at(w0) + "%;width:" + (at(w1) - at(w0)) + '%"></div>';
      html += '<div class="mark" style="left:' + at(g.spy_start) + '%" title="offer round"></div>';
    }
    $("track-marks").innerHTML = html;
    $("round").max = n;
  }

  // ---------- inspector ----------
  function headline(g) {
    if (g.condition === "A") return g.do ? "No offer in this game, but prices sat at the deal level." : "No offer in this game; prices did not sit at the deal level.";
    return { say_do: "A shop said yes, and its prices followed the deal.", say_only: "A shop said yes, but its prices did not follow.",
      do_only: "No shop said yes, but prices moved to the deal.", neither: "No shop said yes, and prices did not move to the deal." }[g.outcome];
  }
  function renderInspector() {
    var g = state.game;
    var chip = function (name, v) { return '<span class="chip ' + (v ? "yes" : "no") + '">' + name + ": " + (v ? "yes" : "no") + "</span>"; };
    var offer = g.condition === "A" ? "<em>No message in this condition.</em>" : esc(messages[g.condition] || "");
    $("inspector").innerHTML = '<p class="headline">' + esc(headline(g)) + "</p>" +
      '<div class="chips">' + chip("SAY", g.say) + chip("DO", g.do) + "</div>" +
      '<dl class="kv"><dt>Game</dt><dd>' + esc(condNames[g.condition] || g.condition) + " | " + esc(g.family) + " | seed " + g.seed + "</dd>" +
      "<dt>Offer (round " + g.spy_start + ")</dt><dd class=\"offer\">" + offer + "</dd>" +
      (g.condition === "A" ? "" : "<dt>Replies</dt><dd>shop 1: " + replyText(replyAt(g, "0")) + " | shop 2: " + replyText(replyAt(g, "1")) + "</dd>") +
      "</dl>" +
      '<div class="defs">Say: at least one shop answers accept after the offer.<br>' +
      "Do: a shop's price stays within 10% of the Nash-to-deal gap around the deal price in each of the 3 rounds after the offer.</div>";
  }

  // ---------- cards ----------
  function renderCards() {
    $("cards").innerHTML = conds.map(function (c) {
      var gs = games.filter(function (g) { return g.condition === c; });
      var n = gs.length, ks = gs.filter(function (g) { return g.say; }).length, kd = gs.filter(function (g) { return g.do; }).length;
      var bar = function (k, color) {
        var ci = wilson(k, n);
        return '<div class="ci" title="95% Wilson interval ' + (ci ? Math.round(ci[0] * 100) + "-" + Math.round(ci[1] * 100) + "%" : "") + '">' +
          (ci ? '<div class="seg" style="left:' + ci[0] * 100 + "%;width:" + (ci[1] - ci[0]) * 100 + "%;background:" + color + '"></div>' +
            '<div class="dot" style="left:' + (k / n) * 100 + "%;background:" + color + '"></div>' : "") + "</div>";
      };
      return '<button class="card" type="button" data-c="' + c + '"><div class="name">' + esc(condNames[c] || c) + "</div>" +
        '<div class="row"><span class="lbl">said yes</span><span class="big">' + pct(ks, n) + "</span></div>" + bar(ks, COLORS.say_do) +
        '<div class="row"><span class="lbl">moved prices</span><span class="big">' + pct(kd, n) + "</span></div>" + bar(kd, COLORS.do_only) +
        '<div class="strip">' + gs.map(function (g) { return '<i style="background:' + COLORS[g.outcome] + '"></i>'; }).join("") + "</div>" +
        '<div class="n">' + n + " games</div></button>";
    }).join("");
    Array.prototype.forEach.call($("cards").querySelectorAll(".card"), function (b) {
      b.addEventListener("click", function () {
        var c = b.getAttribute("data-c"), gs = games.filter(function (g) { return g.condition === c; });
        var i = state.game && state.game.condition === c ? (gs.indexOf(state.game) + 1) % gs.length : 0;
        select(gs[i], true);
      });
    });
  }

  // ---------- price chart ----------
  function renderChart() {
    var g = state.game, W = 640, H = 230, L = 46, R = 70, T = 14, B = 30, n = g.rounds, yr = priceRange(g);
    var x = function (k) { return L + (n > 1 ? (k - 1) / (n - 1) : 0) * (W - L - R); };
    var y = function (p) { return H - B - (p - yr[0]) / (yr[1] - yr[0]) * (H - T - B); };
    var rs = rounds[g.game_id] || {}, b = band(g);
    var svg = '<svg viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="Prices of both shops by round">';
    svg += '<rect x="' + L + '" y="' + y(b[1]) + '" width="' + (W - L - R) + '" height="' + (y(b[0]) - y(b[1])) + '" fill="rgba(240,180,41,.08)"/>';
    if (g.condition !== "A") {
      var w0 = Math.min(g.spy_start + 1, n), w1 = Math.min(g.spy_start + 3, n);
      svg += '<rect x="' + x(w0) + '" y="' + T + '" width="' + (x(w1) - x(w0)) + '" height="' + (H - T - B) + '" fill="rgba(240,180,41,.12)"/>';
      svg += '<line x1="' + x(g.spy_start) + '" x2="' + x(g.spy_start) + '" y1="' + T + '" y2="' + (H - B) + '" stroke="' + COLORS.say_only + '" stroke-dasharray="4 4"/>';
      svg += '<text x="' + (x(g.spy_start) + 4) + '" y="' + (T + 10) + '" fill="' + COLORS.say_only + '" font-size="10">offer</text>';
    }
    svg += '<line x1="' + L + '" x2="' + (W - R) + '" y1="' + y(g.nash) + '" y2="' + y(g.nash) + '" stroke="' + COLORS.muted + '" stroke-dasharray="2 4"/>';
    svg += '<line x1="' + L + '" x2="' + (W - R) + '" y1="' + y(g.deal_price) + '" y2="' + y(g.deal_price) + '" stroke="' + COLORS.say_only + '" stroke-dasharray="8 5"/>';
    for (var t = 0; t <= 4; t++) {
      var pv = yr[0] + (yr[1] - yr[0]) * t / 4;
      svg += '<text x="' + (L - 6) + '" y="' + (y(pv) + 3) + '" fill="' + COLORS.muted + '" font-size="10" text-anchor="end">' + fmt(pv) + "</text>";
    }
    for (var k = 1; k <= n; k += Math.max(1, Math.round(n / 10))) {
      svg += '<text x="' + x(k) + '" y="' + (H - B + 14) + '" fill="' + COLORS.muted + '" font-size="10" text-anchor="middle">' + k + "</text>";
    }
    var ends = [];
    [["0", COLORS.shop1, "shop 1"], ["1", COLORS.shop2, "shop 2"]].forEach(function (s) {
      var pts = [];
      for (var k2 = 1; k2 <= n; k2++) if (rs[k2] && rs[k2][s[0]]) pts.push(x(k2) + "," + y(rs[k2][s[0]].price));
      svg += '<polyline points="' + pts.join(" ") + '" fill="none" stroke="' + s[1] + '" stroke-width="2"/>';
      if (rs[n] && rs[n][s[0]]) ends.push({ y: y(rs[n][s[0]].price), c: s[1], t: s[2] });
    });
    ends.sort(function (a, b2) { return a.y - b2.y; });
    if (ends.length === 2 && ends[1].y - ends[0].y < 13) { var mid = (ends[0].y + ends[1].y) / 2; ends[0].y = mid - 7; ends[1].y = mid + 7; }
    ends.forEach(function (e) { svg += '<text x="' + (W - R + 6) + '" y="' + (e.y + 4) + '" fill="' + e.c + '" font-size="11">' + e.t + "</text>"; });
    var r = state.round;
    svg += '<line x1="' + x(r) + '" x2="' + x(r) + '" y1="' + T + '" y2="' + (H - B) + '" stroke="' + COLORS.text + '" stroke-opacity=".35"/>';
    [["0", COLORS.shop1], ["1", COLORS.shop2]].forEach(function (s) {
      if (rs[r] && rs[r][s[0]]) svg += '<circle cx="' + x(r) + '" cy="' + y(rs[r][s[0]].price) + '" r="4" fill="' + s[1] + '" stroke="' + COLORS.bg + '"/>';
    });
    svg += '<rect id="hit" x="' + L + '" y="' + T + '" width="' + (W - L - R) + '" height="' + (H - T - B) + '" fill="transparent" style="cursor:crosshair"/>';
    svg += "</svg>";
    $("chart").innerHTML = svg;
    var hit = $("chart").querySelector("#hit"), el = $("chart").querySelector("svg");
    var roundAt = function (e) {
      var box = el.getBoundingClientRect(), sx = (e.clientX - box.left) / box.width * W;
      return Math.max(1, Math.min(n, Math.round((sx - L) / (W - L - R) * (n - 1) + 1)));
    };
    hit.addEventListener("mousemove", function (e) {
      var k3 = roundAt(e), q = rs[k3] || {};
      tip(e, "Round " + k3 + "<br>shop 1: " + (q["0"] ? fmt(q["0"].price) : "-") + "<br>shop 2: " + (q["1"] ? fmt(q["1"].price) : "-"));
    });
    hit.addEventListener("mouseleave", untip);
    hit.addEventListener("click", function (e) { stop(); setRound(roundAt(e)); });
  }

  // ---------- state ----------
  function setRound(r) { state.round = r; renderScene(); renderChart(); }
  function stop() { if (state.timer) { clearInterval(state.timer); state.timer = null; } $("play").textContent = "Play"; }
  function play() {
    stop();
    if (state.round >= state.game.rounds) setRound(1);
    $("play").textContent = "Pause";
    state.timer = setInterval(function () {
      if (state.round >= state.game.rounds) { stop(); return; }
      setRound(state.round + 1);
    }, reduced ? 1200 : 650);
  }
  function select(g, autoplay) {
    stop();
    state.game = g; state.round = 1;
    renderGrid(); renderTrack(); renderInspector(); setRound(1);
    if (autoplay) play();
  }
  $("play").addEventListener("click", function () { if (state.timer) stop(); else play(); });
  $("round").addEventListener("input", function (e) { stop(); setRound(num(e.target.value)); });

  renderCards();
  var start = games.filter(function (g) { return g.condition === "B"; })[0] || games[0];
  select(start, false);
})();
