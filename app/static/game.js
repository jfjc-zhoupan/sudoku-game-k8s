let currentGameId = null;
let gameStartTime = null;
let timerInterval = null;

function startTimer() {
    gameStartTime = Date.now();
    const timerDisplay = document.getElementById('timer-display');

    if (timerInterval) clearInterval(timerInterval);

    timerInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - gameStartTime) / 1000);
        const minutes = String(Math.floor(elapsed / 60)).padStart(2, '0');
        const seconds = String(elapsed % 60).padStart(2, '0');
        timerDisplay.textContent = `${minutes}:${seconds}`;
    }, 1000);
}

function stopTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
    if (gameStartTime) {
        return Math.floor((Date.now() - gameStartTime) / 1000);
    }
    return 0;
}

const SIZE = 9;
const boardEl = document.getElementById("board");
const statusEl = document.getElementById("status");
const difficultyEl = document.getElementById("difficulty");

async function saveCompletion(solved) {
  if (!currentGameId) {
    console.warn('No active game to save');
    return;
  }

  const duration = stopTimer();

  try {
    const response = await fetch('/api/complete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        game_id: currentGameId,
        solved: solved,
      }),
    });

    const data = await response.json();

    if (data.success) {
      const formatted = data.game.duration_formatted;
      statusEl.textContent = `Game saved! Duration: ${formatted}`;
      console.log('Game saved:', data.game);
    } else {
      statusEl.textContent = `Error saving game: ${data.error}`;
    }
  } catch (err) {
    console.error('Failed to save game:', err);
    statusEl.textContent = 'Failed to save game. Check console.';
  } finally {
    // Prevent double-saving
    currentGameId = null;
  }
}

let puzzle = Array.from({ length: SIZE }, () => Array(SIZE).fill(0));
let solution = Array.from({ length: SIZE }, () => Array(SIZE).fill(0));
let board = Array.from({ length: SIZE }, () => Array(SIZE).fill(0));
let given = Array.from({ length: SIZE }, () => Array(SIZE).fill(false));
let selected = null;
let showErrors = false;
let cells = [];

function isValid(row, col, num) {
  for (let c = 0; c < SIZE; c++) {
    if (c !== col && board[row][c] === num) return false;
  }
  for (let r = 0; r < SIZE; r++) {
    if (r !== row && board[r][col] === num) return false;
  }
  const br = Math.floor(row / 3) * 3;
  const bc = Math.floor(col / 3) * 3;
  for (let r = br; r < br + 3; r++) {
    for (let c = bc; c < bc + 3; c++) {
      if ((r !== row || c !== col) && board[r][c] === num) return false;
    }
  }
  return true;
}

function isComplete() {
  return board.every((row) => row.every((cell) => cell !== 0));
}

function boardsEqual(a, b) {
  return a.every((row, r) => row.every((cell, c) => cell === b[r][c]));
}

function buildBoard() {
  boardEl.innerHTML = "";
  cells = [];
  for (let r = 0; r < SIZE; r++) {
    const row = [];
    for (let c = 0; c < SIZE; c++) {
      const cell = document.createElement("button");
      cell.type = "button";
      cell.className = "cell";
      cell.setAttribute("role", "gridcell");
      if (c === 2 || c === 5) cell.classList.add("box-right");
      if (r === 2 || r === 5) cell.classList.add("box-bottom");
      cell.addEventListener("click", () => selectCell(r, c));
      boardEl.appendChild(cell);
      row.push(cell);
    }
    cells.push(row);
  }
}

function selectCell(row, col) {
  selected = [row, col];
  showErrors = false;
  refresh();
}

function enterNumber(num) {
  if (!selected) {
    statusEl.textContent = "Select a cell first.";
    return;
  }
  const [row, col] = selected;
  if (given[row][col]) {
    statusEl.textContent = "That cell is given and cannot be changed.";
    return;
  }
  board[row][col] = num;
  showErrors = false;
  refresh();
  if (isComplete()) {
    if (boardsEqual(board, solution)) {
      statusEl.textContent = "Solved — nice work!";
      window.alert("You solved the puzzle!");
      // ✅ Auto-save solved game
      saveCompletion(true);
    } else {
      statusEl.textContent = "The grid is full, but something is off. Try Check.";
    }
  }
}

function erase() {
  if (!selected) return;
  const [row, col] = selected;
  if (given[row][col]) return;
  board[row][col] = 0;
  showErrors = false;
  refresh();
}

function giveHint() {
  const empties = [];
  for (let r = 0; r < SIZE; r++) {
    for (let c = 0; c < SIZE; c++) {
      if (board[r][c] === 0) empties.push([r, c]);
    }
  }
  if (!empties.length) {
    statusEl.textContent = "No empty cells left.";
    return;
  }
  const [row, col] = empties[Math.floor(Math.random() * empties.length)];
  board[row][col] = solution[row][col];
  selected = [row, col];
  showErrors = false;
  refresh();
  statusEl.textContent = `Hint placed at row ${row + 1}, column ${col + 1}.`;
  if (boardsEqual(board, solution)) {
    window.alert("You solved the puzzle!");
    // ✅ Auto-save solved game
    saveCompletion(true);
  }
}

function checkBoard() {
  let errors = 0;
  for (let r = 0; r < SIZE; r++) {
    for (let c = 0; c < SIZE; c++) {
      const val = board[r][c];
      if (val !== 0 && val !== solution[r][c]) errors += 1;
    }
  }
  if (errors === 0) {
    const filled = board.flat().filter((v) => v !== 0).length;
    if (filled === SIZE * SIZE) {
      statusEl.textContent = "Correct — puzzle complete!";
      window.alert("You solved the puzzle!");
    } else {
      statusEl.textContent = "No mistakes so far. Keep going.";
    }
  } else {
    statusEl.textContent = `${errors} cell(s) don't match the solution.`;
  }
  showErrors = true;
  refresh();
}

function refresh() {
  let selVal = null;
  if (selected) {
    selVal = board[selected[0]][selected[1]] || null;
  }

  for (let r = 0; r < SIZE; r++) {
    for (let c = 0; c < SIZE; c++) {
      const val = board[r][c];
      const cell = cells[r][c];
      cell.textContent = val ? String(val) : "";
      cell.className = "cell";
      if (c === 2 || c === 5) cell.classList.add("box-right");
      if (r === 2 || r === 5) cell.classList.add("box-bottom");
      if (given[r][c]) cell.classList.add("given");
      else cell.classList.add("entry");
      if (selVal && val === selVal) cell.classList.add("same");
      if (selected && selected[0] === r && selected[1] === c) cell.classList.add("selected");
      if (showErrors && val && val !== solution[r][c]) cell.classList.add("error");
      else if (val && !isValid(r, c, val)) cell.classList.add("error");
    }
  }
}

async function newGame() {
  statusEl.textContent = "Generating puzzle…";
  const res = await fetch("/api/new", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ difficulty: difficultyEl.value }),
  });
  if (!res.ok) {
    statusEl.textContent = "Could not generate a puzzle. Try again.";
    return;
  }
  const data = await res.json();
  puzzle = data.puzzle;
  solution = data.solution;
  board = puzzle.map((row) => row.slice());
  given = puzzle.map((row) => row.map((cell) => cell !== 0));
  selected = null;
  showErrors = false;
  refresh();
  statusEl.textContent = `New ${data.difficulty} puzzle — ${data.empty} empty cells.`;

  // ✅ Save the game ID returned from the backend
  currentGameId = data.game_id;

  // ✅ Reset the timer and start it
  stopTimer();          // Clear any previous timer
  startTimer();         // Start fresh

  // ✅ Reset timer display to 00:00
  document.getElementById('timer-display').textContent = '00:00';
}

buildBoard();
document.getElementById("new-game").addEventListener("click", newGame);
document.getElementById("check").addEventListener("click", checkBoard);
document.getElementById("hint").addEventListener("click", giveHint);
document.getElementById("erase").addEventListener("click", erase);
document.getElementById('complete').addEventListener('click', async () => {
  if (!currentGameId) {
    statusEl.textContent = 'No active game. Start a new game first.';
    return;
  }
  const solved = confirm('Did you solve the puzzle?');
  await saveCompletion(solved);
});
document.querySelectorAll(".num").forEach((btn) => {
  btn.addEventListener("click", () => enterNumber(Number(btn.dataset.num)));
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Backspace" || event.key === "Delete") {
    erase();
    return;
  }
  if (/^[1-9]$/.test(event.key)) {
    enterNumber(Number(event.key));
  }
});
newGame();
