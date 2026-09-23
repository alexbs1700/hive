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
      iconMarkup[letter] = { attrs, inner: root.innerHTML };
    })
  );
}

function iconGroup(bugType, extraAttrs) {
  const icon = iconMarkup[bugType];
  if (!icon) return "";
  return `<g ${icon.attrs} ${extraAttrs || ""}>${icon.inner}</g>`;
}

function pieceInfo(code) {
  return { color: code[0] === "w" ? "white" : "black", bugType: code[1] };
}

async function fetchState() {
  const response = await fetch("/api/state");
  state = await response.json();
  selected = null;
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

function selectPiece(code) {
  if (selected && selected.pieceCode === code) {
    selected = null;
    render();
    return;
  }
  const destinations = state.legal_moves
    .filter((move) => move.piece === code)
    .map((move) => move.to)
    .filter(Boolean);
  if (destinations.length === 0) return;
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
  const iconOffset = -iconSize / 2;
  const iconScale = iconSize / 100;

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
      const iconTransform = `translate(${iconOffset},${iconOffset}) scale(${iconScale})`;
      html += iconGroup(info.bugType, `transform="${iconTransform}"`);
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
      html += `<svg viewBox="0 0 100 100">${iconGroup(item.code[1])}</svg>`;
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
  const pieceEl = event.target.closest("[data-piece]");
  if (pieceEl) {
    selectPiece(pieceEl.getAttribute("data-piece"));
    return;
  }
  const cellEl = event.target.closest("[data-cell]");
  if (cellEl && selected) {
    const [q, r] = cellEl.getAttribute("data-cell").split(",").map(Number);
    postJson("/api/move", { piece: selected.pieceCode, to: { q, r } });
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
