/**
 * Bingo Deluxe Engine
 * Standard 75-Ball Bingo implementation
 * 
 * B: 1 - 15
 * I: 16 - 30
 * N: 31 - 45 (Center is FREE)
 * G: 46 - 60
 * O: 61 - 75
 */

const BINGO_COLUMNS = {
  B: { min: 1, max: 15, label: 'B', color: '#ff3366' },
  I: { min: 16, max: 30, label: 'I', color: '#ff9900' },
  N: { min: 31, max: 45, label: 'N', color: '#00e676' },
  G: { min: 46, max: 60, label: 'G', color: '#00d4ff' },
  O: { min: 61, max: 75, label: 'O', color: '#b339ff' }
};

const BINGO_LETTERS = ['B', 'I', 'N', 'G', 'O'];

// Fun Nicknames / Calls for 75-ball bingo
const BINGO_NICKNAMES = {
  1: "Kelly's Eye",
  7: "Lucky Seven",
  11: "Legs Eleven",
  13: "Unlucky for Some",
  17: "Dancing Queen",
  21: "Key of the Door",
  22: "Two Little Ducks",
  44: "All the Fours",
  45: "Halfway There",
  69: "Either Way Up",
  75: "Top of the Shop"
};

class BingoEngine {
  constructor() {
    this.totalBalls = 75;
    this.drawnBalls = [];
    this.uncalledBalls = [];
    this.currentBall = null;
    this.resetHopper();
  }

  resetHopper() {
    this.uncalledBalls = [];
    this.drawnBalls = [];
    this.currentBall = null;
    for (let i = 1; i <= this.totalBalls; i++) {
      this.uncalledBalls.push(i);
    }
    // Fisher-Yates shuffle
    for (let i = this.uncalledBalls.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [this.uncalledBalls[i], this.uncalledBalls[j]] = [this.uncalledBalls[j], this.uncalledBalls[i]];
    }
  }

  getLetterForNumber(num) {
    if (num >= 1 && num <= 15) return 'B';
    if (num >= 16 && num <= 30) return 'I';
    if (num >= 31 && num <= 45) return 'N';
    if (num >= 46 && num <= 60) return 'G';
    if (num >= 61 && num <= 75) return 'O';
    return '?';
  }

  drawNextBall() {
    if (this.uncalledBalls.length === 0) {
      return null;
    }
    const num = this.uncalledBalls.pop();
    const letter = this.getLetterForNumber(num);
    const ball = {
      number: num,
      letter: letter,
      callString: `${letter} ${num}`,
      nickname: BINGO_NICKNAMES[num] || null,
      timestamp: Date.now()
    };
    this.drawnBalls.unshift(ball);
    this.currentBall = ball;
    return ball;
  }

  isNumberCalled(num) {
    return this.drawnBalls.some(b => b.number === num);
  }

  /**
   * Generates a 5x5 Bingo Card
   * Returns a 2D array [row][col] or flat representation
   * row 0..4, col 0..4
   */
  generateCard(cardId = 1) {
    const card = {
      id: cardId,
      grid: [], // 5x5 array of { number, letter, isFree, daubed: false, row, col }
      numbersSet: new Set()
    };

    // Pick 5 random numbers for each column
    const colNumbers = {};
    BINGO_LETTERS.forEach(letter => {
      const { min, max } = BINGO_COLUMNS[letter];
      const range = [];
      for (let n = min; n <= max; n++) range.push(n);
      
      // Shuffle range
      for (let i = range.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [range[i], range[j]] = [range[j], range[i]];
      }
      colNumbers[letter] = range.slice(0, 5);
      // Sort column numbers ascending for cleaner traditional card look
      colNumbers[letter].sort((a, b) => a - b);
    });

    for (let r = 0; r < 5; r++) {
      const row = [];
      for (let c = 0; c < 5; c++) {
        const letter = BINGO_LETTERS[c];
        const isCenter = (r === 2 && c === 2);
        const number = isCenter ? 0 : colNumbers[letter][r];
        
        if (!isCenter) {
          card.numbersSet.add(number);
        }

        row.push({
          row: r,
          col: c,
          letter: letter,
          number: number,
          isFree: isCenter,
          daubed: isCenter // Center is automatically daubed
        });
      }
      card.grid.push(row);
    }

    return card;
  }

  /**
   * Check winning patterns on a card
   * patterns: 'any-line', 'four-corners', 'postage-stamp', 'plus', 'x-pattern', 'blackout'
   */
  checkWin(card, patternType = 'any-line') {
    const g = card.grid;
    const isDaubed = (r, c) => g[r][c].daubed || g[r][c].isFree;

    // Helper to test if a list of [r, c] cells are all daubed
    const checkCells = (coords) => {
      return coords.every(([r, c]) => isDaubed(r, c));
    };

    // 1. Horizontal Lines (5 rows)
    const rowsWin = [];
    for (let r = 0; r < 5; r++) {
      const coords = [[r, 0], [r, 1], [r, 2], [r, 3], [r, 4]];
      if (checkCells(coords)) {
        rowsWin.push(coords);
      }
    }

    // 2. Vertical Lines (5 columns)
    const colsWin = [];
    for (let c = 0; c < 5; c++) {
      const coords = [[0, c], [1, c], [2, c], [3, c], [4, c]];
      if (checkCells(coords)) {
        colsWin.push(coords);
      }
    }

    // 3. Diagonal Lines
    const diag1 = [[0, 0], [1, 1], [2, 2], [3, 3], [4, 4]];
    const diag2 = [[0, 4], [1, 3], [2, 2], [3, 1], [4, 0]];
    const diagsWin = [];
    if (checkCells(diag1)) diagsWin.push(diag1);
    if (checkCells(diag2)) diagsWin.push(diag2);

    // 4. Four Corners
    const fourCorners = [[0, 0], [0, 4], [4, 0], [4, 4]];
    const hasFourCorners = checkCells(fourCorners);

    // 5. Postage Stamp (2x2 in any corner)
    const stamps = [
      [[0, 0], [0, 1], [1, 0], [1, 1]], // Top-left
      [[0, 3], [0, 4], [1, 3], [1, 4]], // Top-right
      [[3, 0], [3, 1], [4, 0], [4, 1]], // Bottom-left
      [[3, 3], [3, 4], [4, 3], [4, 4]]  // Bottom-right
    ];
    const stampsWin = stamps.filter(s => checkCells(s));

    // 6. Plus / Cross (+)
    const plusCoords = [
      [2, 0], [2, 1], [2, 2], [2, 3], [2, 4],
      [0, 2], [1, 2], [3, 2], [4, 2]
    ];
    const hasPlus = checkCells(plusCoords);

    // 7. X-Pattern
    const hasX = checkCells(diag1) && checkCells(diag2);

    // 8. Full House / Blackout
    let allCells = [];
    for (let r = 0; r < 5; r++) {
      for (let c = 0; c < 5; c++) {
        allCells.push([r, c]);
      }
    }
    const hasBlackout = checkCells(allCells);

    let hasWon = false;
    let matchingPatternName = '';
    let winningCoords = [];

    switch (patternType) {
      case 'blackout':
        if (hasBlackout) {
          hasWon = true;
          matchingPatternName = 'Blackout / Full House!';
          winningCoords = allCells;
        }
        break;

      case 'four-corners':
        if (hasFourCorners) {
          hasWon = true;
          matchingPatternName = 'Four Corners!';
          winningCoords = fourCorners;
        }
        break;

      case 'x-pattern':
        if (hasX) {
          hasWon = true;
          matchingPatternName = 'X-Pattern!';
          winningCoords = [...diag1, ...diag2];
        }
        break;

      case 'plus':
        if (hasPlus) {
          hasWon = true;
          matchingPatternName = 'Cross / Plus Pattern!';
          winningCoords = plusCoords;
        }
        break;

      case 'postage-stamp':
        if (stampsWin.length > 0) {
          hasWon = true;
          matchingPatternName = 'Postage Stamp!';
          winningCoords = stampsWin.flat();
        }
        break;

      case 'any-line':
      default:
        // Any standard line, diagonal, or 4 corners
        if (rowsWin.length > 0 || colsWin.length > 0 || diagsWin.length > 0) {
          hasWon = true;
          matchingPatternName = 'Line Bingo!';
          winningCoords = [...rowsWin.flat(), ...colsWin.flat(), ...diagsWin.flat()];
        } else if (hasFourCorners) {
          hasWon = true;
          matchingPatternName = 'Four Corners!';
          winningCoords = fourCorners;
        }
        break;
    }

    // Deduplicate coords
    const uniqueMap = new Map();
    winningCoords.forEach(([r, c]) => uniqueMap.set(`${r},${c}`, [r, c]));

    return {
      hasWon,
      patternName: matchingPatternName,
      winningCells: Array.from(uniqueMap.values())
    };
  }
}

// Export for browser window
if (typeof window !== 'undefined') {
  window.BingoEngine = BingoEngine;
  window.BINGO_COLUMNS = BINGO_COLUMNS;
  window.BINGO_LETTERS = BINGO_LETTERS;
}
