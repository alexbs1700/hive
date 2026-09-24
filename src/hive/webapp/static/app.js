// Hive web UI — a thin rendering layer over the server's JSON API.
// Every click resolves against `state.legal_moves`, which the server derived
// from Game.legal_moves(); this file never decides what's legal on its own.

const HEX_SIZE = 38;

const BUG_LETTER_TO_FILE = {
  Q: "queen_bee",
  B: "beetle",
  G: "grasshopper",
  S: "spider",
  A: "soldier_ant",
  M: "mosquito",
  L: "ladybug",
  P: "pillbug",
};

const iconMarkup = {};
let state = null;
let selected = null; // { pieceCode, destinations: [{q, r}, ...] }
let hintMessage = ""; // explains why a click landed on nothing, until the next real change

function cellKey(q, r) {
  return `${q},${r}`;
}

function axialToPixel(q, r) {
  const x = HEX_SIZE * (Math.sqrt(3) * q + (Math.sqrt(3) / 2) * r);
  const y = HEX_SIZE * (1.5 * r);
  return [x, y];
}

function hexPoints() {
  const points = [];
  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 180) * (60 * i - 30);
    points.push(`${HEX_SIZE * Math.cos(angle)},${HEX_SIZE * Math.sin(angle)}`);
  }
  return points.join(" ");
}

async function loadIcons() {
  // Each icon's own root <svg> carries presentation attributes (fill,
  // stroke, stroke-width, ...) that its children inherit rather than
  // repeat. Inlining just the inner markup into a plain <g> would drop
  // that inheritance (SVG defaults to fill="black" stroke="none"), so the
  // root's attributes are carried over onto the wrapping <g> at render time.
  //
  // Icons are sourced from third-party artwork with varying native
  // viewBoxes (e.g. 512x512, 36x36) rather than a shared 100x100 convention,
  // so each one's viewBox is recorded too and used to scale/center it
  // uniformly regardless of its native size — see iconGroup().
  const presentationAttributes = [
    "fill",
    "stroke",
    "stroke-width",
    "stroke-linecap",
    "stroke-linejoin",
  ];
  const entries = Object.entries(BUG_LETTER_TO_FILE);
  await Promise.all(
    entries.map(async ([letter, file]) => {
      const response = await fetch(`/static/pieces/${file}.svg`);
      const text = await response.text();
      const doc = new DOMParser().parseFromString(text, "image/svg+xml");
      const root = doc.documentElement;
      const attrs = presentationAttributes
        .filter((name) => root.hasAttribute(name))
        .map((name) => `${name}="${root.getAttribute(name)}"`)
        .join(" ");
      const viewBoxAttr = root.getAttribute("viewBox") || "0 0 100 100";
      const [minX, minY, vbWidth, vbHeight] = viewBoxAttr.trim().split(/\s+/).map(Number);
      iconMarkup[letter] = { attrs, inner: root.innerHTML, minX, minY, vbWidth, vbHeight };
    })
  );
}

/** A <g>, centered on its own local (0,0), rendering `bugType`'s icon at `size` across its longest dimension. */
function iconGroup(bugType, size) {
  const icon = iconMarkup[bugType];
  if (!icon) return "";
  const scale = size / Math.max(icon.vbWidth, icon.vbHeight);
  const offsetX = -(icon.minX + icon.vbWidth / 2) * scale;
  const offsetY = -(icon.minY + icon.vbHeight / 2) * scale;
  return `<g ${icon.attrs} transform="translate(${offsetX},${offsetY}) scale(${scale})">${icon.inner}</g>`;
}

function pieceInfo(code) {
  return { color: code[0] === "w" ? "white" : "black", bugType: code[1] };
}

async function fetchState() {
  const response = await fetch("/api/state");
  state = await response.json();
  selected = null;
  hintMessage = "";
  render();
}

async function postJson(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) {
    console.warn(data.error || "request failed");
    return false;
  }
  state = data;
  selected = null;
  hintMessage = "";
  render();
  return true;
}

function relevantCells() {
  const cells = new Map();
  for (const cell of state.board) cells.set(cellKey(cell.q, cell.r), cell);
  for (const move of state.legal_moves) {
    if (move.to) cells.set(cellKey(move.to.q, move.to.r), move.to);
    if (move.from) cells.set(cellKey(move.from.q, move.from.r), move.from);
  }
  if (cells.size === 0) cells.set(cellKey(0, 0), { q: 0, r: 0 });
  return [...cells.values()];
}

function movablePieceCodes() {
  return new Set(state.legal_moves.map((move) => move.piece).filter(Boolean));
}

function colorName(color) {
  return color === "white" ? "White" : "Black";
}

function explainWhyInert(code) {
  const pieceColor = pieceInfo(code).color;
  const currentColor = state.current_turn;
  const queenStillInReserve = (state.reserves[currentColor] || []).some(
    (item) => item.bug_type === "QUEEN_BEE"
  );

  if (pieceColor === currentColor) {
    if (queenStillInReserve) {
      return `Place ${colorName(currentColor)}'s Queen Bee before moving other pieces.`;
    }
    return "That piece has no legal move right now — it may be pinned (moving it would split the Hive), covered, or was just moved.";
  }

  // A piece of the *opponent's* color is only ever selectable via one of
  // the current Player's own Pillbugs (or a Mosquito copying one) Throwing
  // it — never by ordinary Movement, which only ever acts on your own color.
  if (queenStillInReserve) {
    return `Place ${colorName(currentColor)}'s Queen Bee before a Pillbug can Throw another piece.`;
  }
  return `None of your Pillbugs can Throw ${colorName(pieceColor)}'s piece right now (it may be stacked, pinned, or was just moved).`;
}

function explainSelection(code) {
  const pieceColor = pieceInfo(code).color;
  if (pieceColor === state.current_turn) return "";
  const throwMove = state.legal_moves.find(
    (move) => move.kind === "throw" && move.piece === code
  );
  if (!throwMove) return "";
  return `Throwing ${colorName(pieceColor)}'s piece with your Pillbug (${throwMove.thrower}) — a Pillbug may relocate an adjacent piece, friend or enemy.`;
}

function selectPiece(code) {
  if (state.is_over) return;

  if (selected && selected.pieceCode === code) {
    selected = null;
    hintMessage = "";
    render();
    return;
  }
  const destinations = state.legal_moves
    .filter((move) => move.piece === code)
    .map((move) => move.to)
    .filter(Boolean);
  if (destinations.length === 0) {
    selected = null;
    hintMessage = explainWhyInert(code);
    render();
    return;
  }
  hintMessage = explainSelection(code);
  selected = { pieceCode: code, destinations };
  render();
}

function renderStatusBar() {
  const bar = document.getElementById("status-bar");
  const turnColor = state.current_turn;
  let html = `
    <span class="turn-pill">
      <span class="turn-dot ${turnColor}"></span>
      ${turnColor === "white" ? "White" : "Black"}'s turn
    </span>
  `;

  if (state.is_over) {
    const message =
      state.result.outcome === "draw"
        ? "Draw — both Queen Bees surrounded at once"
        : `${state.result.winner === "white" ? "White" : "Black"} wins!`;
    html += `<span class="result-banner">${message}</span>`;
  } else if (state.legal_moves.length === 1 && state.legal_moves[0].kind === "pass") {
    html += `<button id="pass-button" class="button button-primary">No legal moves — Pass</button>`;
  } else if (hintMessage) {
    html += `<span class="hint-banner">${hintMessage}</span>`;
  }

  bar.innerHTML = html;
  const passButton = document.getElementById("pass-button");
  if (passButton) passButton.addEventListener("click", () => postJson("/api/move", { pass: true }));
}

function renderBoard() {
  const svg = document.getElementById("board");
  const cells = relevantCells().map((cell) => {
    const [x, y] = axialToPixel(cell.q, cell.r);
    return { ...cell, x, y };
  });

  const pad = HEX_SIZE * 1.6;
  const minX = Math.min(...cells.map((c) => c.x)) - pad;
  const maxX = Math.max(...cells.map((c) => c.x)) + pad;
  const minY = Math.min(...cells.map((c) => c.y)) - pad;
  const maxY = Math.max(...cells.map((c) => c.y)) + pad;
  svg.setAttribute("viewBox", `${minX} ${minY} ${maxX - minX} ${maxY - minY}`);

  const boardMap = new Map(state.board.map((cell) => [cellKey(cell.q, cell.r), cell]));
  const destSet = new Set((selected ? selected.destinations : []).map((d) => cellKey(d.q, d.r)));
  const movable = movablePieceCodes();
  const points = hexPoints();
  const iconSize = HEX_SIZE * 1.45;

  let html = "";
  for (const cell of cells) {
    const key = cellKey(cell.q, cell.r);
    const occupant = boardMap.get(key);
    const cellClasses = ["cell"];
    if (destSet.has(key)) cellClasses.push("cell-destination");

    html += `<g class="${cellClasses.join(" ")}" data-cell="${key}" transform="translate(${cell.x},${cell.y})">`;
    html += `<polygon class="hex" points="${points}" />`;

    if (occupant && occupant.stack.length) {
      const topCode = occupant.stack[occupant.stack.length - 1];
      const info = pieceInfo(topCode);
      const pieceClasses = ["piece", info.color];
      if (selected && selected.pieceCode === topCode) pieceClasses.push("piece-selected");
      else if (movable.has(topCode)) pieceClasses.push("piece-clickable");

      html += `<g class="${pieceClasses.join(" ")}" data-piece="${topCode}">`;
      html += `<polygon class="piece-hex" points="${points}" />`;
      html += iconGroup(info.bugType, iconSize);
      if (occupant.stack.length > 1) {
        html += `<text class="stack-badge" x="${HEX_SIZE * 0.55}" y="${-HEX_SIZE * 0.5}">&times;${
          occupant.stack.length
        }</text>`;
      }
      html += `</g>`;
    }

    html += `</g>`;
  }
  svg.innerHTML = html;
}

function renderReserves() {
  for (const color of ["white", "black"]) {
    const container = document.getElementById(`reserve-${color}`);
    const isCurrent = state.current_turn === color;
    const placeablePieces = new Map(
      state.legal_moves
        .filter((move) => move.kind === "placement" && pieceInfo(move.piece).color === color)
        .map((move) => [move.piece, move])
    );

    let html = "";
    for (const item of state.reserves[color]) {
      const isActive = isCurrent && placeablePieces.has(item.code);
      const classes = ["reserve-piece"];
      if (isActive) classes.push("active");
      if (selected && selected.pieceCode === item.code) classes.push("selected");
      html += `<div class="${classes.join(" ")}" data-reserve="${item.code}" title="${item.bug_type}">`;
      html += `<svg viewBox="-50 -50 100 100">${iconGroup(item.code[1], 90)}</svg>`;
      html += `<span class="reserve-count">${item.count}</span>`;
      html += `</div>`;
    }
    container.innerHTML = html;
  }
}

function renderControls() {
  document.getElementById("undo-button").disabled = !state.can_undo;
}

function render() {
  renderStatusBar();
  renderBoard();
  renderReserves();
  renderControls();
}

function handleBoardClick(event) {
  const cellEl = event.target.closest("[data-cell]");

  // A highlighted destination always completes the selected Piece's Move,
  // even when it's occupied (a Beetle — or a Mosquito copying one —
  // climbing onto another Piece). Checked before piece-selection below:
  // the piece sitting on a climb target is nested inside that same Cell,
  // so without this check a click there would re-select it instead of
  // completing the climb.
  if (selected && cellEl) {
    const [q, r] = cellEl.getAttribute("data-cell").split(",").map(Number);
    const isDestination = selected.destinations.some((d) => d.q === q && d.r === r);
    if (isDestination) {
      postJson("/api/move", { piece: selected.pieceCode, to: { q, r } });
      return;
    }
  }

  const pieceEl = event.target.closest("[data-piece]");
  if (pieceEl) {
    selectPiece(pieceEl.getAttribute("data-piece"));
  }
}

function handleReserveClick(event) {
  const el = event.target.closest("[data-reserve]");
  if (el) selectPiece(el.getAttribute("data-reserve"));
}

async function main() {
  await loadIcons();
  document.getElementById("board").addEventListener("click", handleBoardClick);
  document.getElementById("reserve-white").addEventListener("click", handleReserveClick);
  document.getElementById("reserve-black").addEventListener("click", handleReserveClick);
  document.getElementById("undo-button").addEventListener("click", () => postJson("/api/undo", {}));
  document.getElementById("new-game-button").addEventListener("click", () => postJson("/api/new_game", {}));
  await fetchState();
}

main();
