/**
 * Bingo Deluxe Application Controller
 */

// Confetti Particle Engine
class ConfettiSystem {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
    this.particles = [];
    this.animId = null;
    this.colors = ['#ff3366', '#ff9900', '#00e676', '#00d4ff', '#b339ff', '#ffc83b', '#ffffff'];

    if (this.canvas) {
      window.addEventListener('resize', () => this.resize());
      this.resize();
    }
  }

  resize() {
    if (!this.canvas) return;
    this.canvas.width = window.innerWidth;
    this.canvas.height = window.innerHeight;
  }

  burst(count = 120) {
    if (!this.canvas || !this.ctx) return;
    this.resize();
    
    for (let i = 0; i < count; i++) {
      this.particles.push({
        x: window.innerWidth / 2 + (Math.random() - 0.5) * 200,
        y: window.innerHeight * 0.45 + (Math.random() - 0.5) * 100,
        vx: (Math.random() - 0.5) * 18,
        vy: Math.random() * -18 - 6,
        size: Math.random() * 8 + 5,
        color: this.colors[Math.floor(Math.random() * this.colors.length)],
        rotation: Math.random() * 360,
        rotationSpeed: (Math.random() - 0.5) * 12,
        opacity: 1,
        drag: 0.96,
        gravity: 0.45
      });
    }

    if (!this.animId) {
      this.animate();
    }
  }

  animate() {
    if (!this.ctx) return;
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    for (let i = this.particles.length - 1; i >= 0; i--) {
      const p = this.particles[i];
      p.vx *= p.drag;
      p.vy *= p.drag;
      p.vy += p.gravity;
      p.x += p.vx;
      p.y += p.vy;
      p.rotation += p.rotationSpeed;
      p.opacity -= 0.007;

      if (p.opacity <= 0 || p.y > this.canvas.height + 50) {
        this.particles.splice(i, 1);
        continue;
      }

      this.ctx.save();
      this.ctx.translate(p.x, p.y);
      this.ctx.rotate((p.rotation * Math.PI) / 180);
      this.ctx.globalAlpha = Math.max(0, p.opacity);
      this.ctx.fillStyle = p.color;
      this.ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size * 0.7);
      this.ctx.restore();
    }

    if (this.particles.length > 0) {
      this.animId = requestAnimationFrame(() => this.animate());
    } else {
      this.animId = null;
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }
  }
}

// Main Game Controller
class BingoApp {
  constructor() {
    this.engine = new BingoEngine();
    this.sound = new SoundController();
    this.confetti = new ConfettiSystem('confetti-canvas');

    this.activeTab = 'player'; // 'player' | 'host' | 'printable'
    this.cardsCount = 2;
    this.playerCards = [];
    this.autoDaub = false;
    this.autoCallTimer = null;
    this.callSpeed = 4000;
    this.selectedPattern = 'any-line';
    this.dauberColor = '#ff3366';
    this.gameWon = false;
    this.gameStartTime = Date.now();

    // Stats
    this.stats = {
      gamesPlayed: 0,
      bingosWon: 0,
      callsCount: 0
    };
    this.loadStats();

    this.initElements();
    this.initEventListeners();
    this.setupNewGame();
    this.renderMasterBoard();
  }

  loadStats() {
    try {
      const saved = localStorage.getItem('bingo_deluxe_stats');
      if (saved) {
        this.stats = JSON.parse(saved);
      }
      const savedDauber = localStorage.getItem('bingo_deluxe_dauber');
      if (savedDauber) {
        this.setDauberColor(savedDauber);
      }
    } catch (e) {
      console.warn("Storage load error", e);
    }
  }

  saveStats() {
    try {
      localStorage.setItem('bingo_deluxe_stats', JSON.stringify(this.stats));
    } catch (e) {
      console.warn("Storage save error", e);
    }
  }

  initElements() {
    // Nav tabs
    this.tabPlayerBtn = document.getElementById('tab-player');
    this.tabHostBtn = document.getElementById('tab-host');
    this.tabPrintableBtn = document.getElementById('tab-printable');
    this.playerArena = document.getElementById('player-arena');
    this.hostArena = document.getElementById('host-arena');
    this.printableArena = document.getElementById('printable-arena');

    // Header buttons
    this.btnMute = document.getElementById('btn-mute');
    this.btnVoice = document.getElementById('btn-voice');
    this.btnDauber = document.getElementById('btn-dauber');
    this.btnPattern = document.getElementById('btn-pattern');
    this.btnRules = document.getElementById('btn-rules');

    // Caller Stage
    this.ballSphere = document.getElementById('current-ball-sphere');
    this.ballLetter = document.getElementById('current-ball-letter');
    this.ballNumber = document.getElementById('current-ball-number');
    this.ballNickname = document.getElementById('ball-nickname');
    this.ballCounter = document.getElementById('ball-counter');
    this.historyContainer = document.getElementById('history-balls');
    this.btnDrawBall = document.getElementById('btn-draw-ball');
    this.btnAutoCall = document.getElementById('btn-auto-call');
    this.speedSelect = document.getElementById('speed-select');
    this.btnResetGame = document.getElementById('btn-reset-game');

    // Player Options
    this.cardsContainer = document.getElementById('cards-container');
    this.autoDaubSwitch = document.getElementById('auto-daub-switch');
    this.patternBadge = document.getElementById('current-pattern-badge');
    this.btnNewCards = document.getElementById('btn-new-cards');

    // Modals
    this.modalDauber = document.getElementById('modal-dauber');
    this.modalPattern = document.getElementById('modal-pattern');
    this.modalRules = document.getElementById('modal-rules');
    this.modalWin = document.getElementById('modal-win');
    this.winTitle = document.getElementById('win-title');
    this.winSubtitle = document.getElementById('win-subtitle');
    this.winCallsCount = document.getElementById('win-calls-count');
    this.winTimeTaken = document.getElementById('win-time-taken');
    this.btnPlayAgain = document.getElementById('btn-play-again');

    // Master board container
    this.masterRowsContainer = document.getElementById('master-rows');

    // Printable container
    this.printableGrid = document.getElementById('printable-grid');
    this.printableCountSelect = document.getElementById('printable-count-select');
    this.btnPrintTrigger = document.getElementById('btn-print-trigger');
  }

  initEventListeners() {
    // Tab switching
    this.tabPlayerBtn.addEventListener('click', () => this.switchTab('player'));
    this.tabHostBtn.addEventListener('click', () => this.switchTab('host'));
    this.tabPrintableBtn.addEventListener('click', () => this.switchTab('printable'));

    // Audio & voice toggles
    this.btnMute.addEventListener('click', () => {
      this.sound.isMuted = !this.sound.isMuted;
      this.btnMute.classList.toggle('active', this.sound.isMuted);
      this.btnMute.setAttribute('title', this.sound.isMuted ? 'Unmute Sound' : 'Mute Sound');
      if (!this.sound.isMuted) this.sound.playClick();
    });

    this.btnVoice.addEventListener('click', () => {
      this.sound.voiceEnabled = !this.sound.voiceEnabled;
      this.btnVoice.classList.toggle('active', this.sound.voiceEnabled);
      this.sound.playClick();
      if (this.sound.voiceEnabled) {
        this.sound.speakText('Bingo Caller Voice Enabled');
      }
    });

    // Caller controls
    this.btnDrawBall.addEventListener('click', () => {
      this.sound.initAudio();
      this.drawNextBall();
    });

    this.btnAutoCall.addEventListener('click', () => {
      this.sound.initAudio();
      this.toggleAutoCall();
    });

    this.speedSelect.addEventListener('change', (e) => {
      this.callSpeed = parseInt(e.target.value, 10);
      if (this.autoCallTimer) {
        this.stopAutoCall();
        this.startAutoCall();
      }
    });

    this.btnResetGame.addEventListener('click', () => {
      this.sound.playClick();
      if (confirm('Start a fresh game? Current game progress will be cleared.')) {
        this.setupNewGame();
      }
    });

    // Player controls
    this.autoDaubSwitch.addEventListener('change', (e) => {
      this.autoDaub = e.target.checked;
      this.sound.playClick();
      if (this.autoDaub) {
        this.applyAutoDaub();
      }
    });

    document.querySelectorAll('.card-pill').forEach(pill => {
      pill.addEventListener('click', (e) => {
        document.querySelectorAll('.card-pill').forEach(p => p.classList.remove('active'));
        e.currentTarget.classList.add('active');
        this.cardsCount = parseInt(e.currentTarget.dataset.cards, 10);
        this.regeneratePlayerCards();
        this.sound.playClick();
      });
    });

    this.btnNewCards.addEventListener('click', () => {
      this.sound.playClick();
      this.regeneratePlayerCards();
    });

    // Modals open/close
    this.btnDauber.addEventListener('click', () => this.openModal(this.modalDauber));
    this.btnPattern.addEventListener('click', () => this.openModal(this.modalPattern));
    this.btnRules.addEventListener('click', () => this.openModal(this.modalRules));

    document.querySelectorAll('.modal-close').forEach(btn => {
      btn.addEventListener('click', () => this.closeAllModals());
    });

    document.querySelectorAll('.modal-overlay').forEach(modal => {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) this.closeAllModals();
      });
    });

    // Dauber swatch selection
    document.querySelectorAll('.palette-swatch').forEach(swatch => {
      swatch.addEventListener('click', (e) => {
        document.querySelectorAll('.palette-swatch').forEach(s => s.classList.remove('active'));
        e.currentTarget.classList.add('active');
        const color = e.currentTarget.dataset.color;
        this.setDauberColor(color);
        this.sound.playDaub();
        this.closeAllModals();
      });
    });

    // Pattern selection
    document.querySelectorAll('.pattern-card').forEach(card => {
      card.addEventListener('click', (e) => {
        document.querySelectorAll('.pattern-card').forEach(c => c.classList.remove('active'));
        e.currentTarget.classList.add('active');
        this.selectedPattern = e.currentTarget.dataset.pattern;
        const patternName = e.currentTarget.querySelector('.pattern-name').textContent;
        this.patternBadge.textContent = patternName;
        this.sound.playClick();
        this.closeAllModals();
        this.checkAllCardsWinState();
      });
    });

    // Play again from win modal
    this.btnPlayAgain.addEventListener('click', () => {
      this.closeAllModals();
      this.setupNewGame();
    });

    // Printable view triggers
    this.printableCountSelect.addEventListener('change', () => this.renderPrintableCards());
    this.btnPrintTrigger.addEventListener('click', () => {
      window.print();
    });
  }

  setDauberColor(color) {
    this.dauberColor = color;
    document.documentElement.style.setProperty('--dauber-color', color);
    document.documentElement.style.setProperty('--dauber-glow', `${color}88`);
    try {
      localStorage.setItem('bingo_deluxe_dauber', color);
    } catch (e) {}
  }

  switchTab(tab) {
    this.activeTab = tab;
    this.tabPlayerBtn.classList.toggle('active', tab === 'player');
    this.tabHostBtn.classList.toggle('active', tab === 'host');
    this.tabPrintableBtn.classList.toggle('active', tab === 'printable');

    this.playerArena.style.display = tab === 'player' ? 'block' : 'none';
    this.hostArena.style.display = tab === 'host' ? 'block' : 'none';
    this.printableArena.style.display = tab === 'printable' ? 'block' : 'none';

    if (tab === 'printable') {
      this.renderPrintableCards();
    }
    this.sound.playClick();
  }

  openModal(modal) {
    this.sound.playClick();
    modal.classList.add('open');
  }

  closeAllModals() {
    document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('open'));
  }

  setupNewGame() {
    this.stopAutoCall();
    this.engine.resetHopper();
    this.gameWon = false;
    this.gameStartTime = Date.now();
    this.stats.gamesPlayed++;
    this.saveStats();

    // Reset caller stage UI
    this.ballSphere.className = 'ball-sphere';
    this.ballLetter.textContent = '-';
    this.ballNumber.textContent = '--';
    this.ballNickname.textContent = 'Press Draw or Auto-Call to Start!';
    this.ballCounter.textContent = `Balls called: 0 / 75`;
    this.historyContainer.innerHTML = '<span style="color: var(--text-dim); font-size: 0.85rem;">No calls yet</span>';

    // Regenerate player cards
    this.regeneratePlayerCards();

    // Update Master board
    this.updateMasterBoard();
  }

  regeneratePlayerCards() {
    this.playerCards = [];
    for (let i = 1; i <= this.cardsCount; i++) {
      this.playerCards.push(this.engine.generateCard(i));
    }
    this.renderPlayerCards();
  }

  drawNextBall() {
    if (this.gameWon) {
      alert("This game has already been won! Start a new game to continue.");
      this.stopAutoCall();
      return;
    }

    const ball = this.engine.drawNextBall();
    if (!ball) {
      this.stopAutoCall();
      this.sound.speakText("All 75 balls have been called! Game over.");
      alert("All 75 balls have been called!");
      return;
    }

    // Sound & Voice
    this.sound.playPop();
    this.sound.speakBall(ball);

    // Update HUD 3D Ball
    this.ballSphere.className = `ball-sphere ${ball.letter.toLowerCase()}-col pop-in`;
    this.ballLetter.textContent = ball.letter;
    this.ballNumber.textContent = ball.number;
    this.ballNickname.textContent = ball.nickname ? `"${ball.nickname}"` : `${ball.letter} - ${ball.number}`;
    this.ballCounter.textContent = `Balls called: ${this.engine.drawnBalls.length} / 75`;

    // Re-trigger bounce animation
    void this.ballSphere.offsetWidth;

    // Update History Tray
    this.updateHistoryTray();

    // Update Master Board
    this.updateMasterBoard();

    // If auto-daub is active, automatically stamp cards
    if (this.autoDaub) {
      this.applyAutoDaub();
    } else {
      // Highlight matching un-daubed cells on cards to give subtle visual hint
      this.updateCalledCellsHint();
    }

    // Check if any card now has bingo ready
    this.checkAllCardsWinState();
  }

  updateHistoryTray() {
    const recent = this.engine.drawnBalls.slice(1, 6); // next 5 previous
    if (recent.length === 0) {
      this.historyContainer.innerHTML = '<span style="color: var(--text-dim); font-size: 0.85rem;">Drawing...</span>';
      return;
    }

    this.historyContainer.innerHTML = '';
    recent.forEach(b => {
      const el = document.createElement('div');
      el.className = `history-ball ${b.letter.toLowerCase()}`;
      el.textContent = `${b.letter}${b.number}`;
      this.historyContainer.appendChild(el);
    });
  }

  toggleAutoCall() {
    if (this.autoCallTimer) {
      this.stopAutoCall();
    } else {
      this.startAutoCall();
    }
  }

  startAutoCall() {
    this.btnAutoCall.classList.add('active');
    this.btnAutoCall.innerHTML = `
      <svg viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
      Pause Auto
    `;
    this.sound.playHopperTumble();
    this.drawNextBall();
    this.autoCallTimer = setInterval(() => {
      this.drawNextBall();
    }, this.callSpeed);
  }

  stopAutoCall() {
    if (this.autoCallTimer) {
      clearInterval(this.autoCallTimer);
      this.autoCallTimer = null;
    }
    this.btnAutoCall.classList.remove('active');
    this.btnAutoCall.innerHTML = `
      <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
      Auto Draw
    `;
  }

  renderPlayerCards() {
    this.cardsContainer.innerHTML = '';

    this.playerCards.forEach(card => {
      const cardEl = document.createElement('div');
      cardEl.className = 'bingo-card';
      cardEl.id = `card-elem-${card.id}`;

      // Top bar
      const topBar = document.createElement('div');
      topBar.className = 'card-top-bar';
      topBar.innerHTML = `
        <span class="card-id-tag">Card #${card.id}</span>
        <button class="card-bingo-btn" id="bingo-btn-${card.id}">Call BINGO!</button>
      `;

      // 5x5 Grid
      const gridEl = document.createElement('div');
      gridEl.className = 'bingo-grid';

      // Column Headers
      BINGO_LETTERS.forEach(l => {
        const h = document.createElement('div');
        h.className = `grid-col-header ${l.toLowerCase()}`;
        h.textContent = l;
        gridEl.appendChild(h);
      });

      // 5x5 Cells
      for (let r = 0; r < 5; r++) {
        for (let c = 0; c < 5; c++) {
          const cellData = card.grid[r][c];
          const cellEl = document.createElement('div');
          cellEl.className = 'bingo-cell';
          cellEl.dataset.cardId = card.id;
          cellEl.dataset.row = r;
          cellEl.dataset.col = c;
          cellEl.id = `cell-${card.id}-${r}-${c}`;

          if (cellData.isFree) {
            cellEl.classList.add('free-space', 'is-daubed');
            cellEl.innerHTML = `
              <div class="free-icon">
                <svg viewBox="0 0 24 24"><path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/></svg>
                FREE
              </div>
            `;
          } else {
            cellEl.innerHTML = `<span class="cell-val">${cellData.number}</span>`;
            if (cellData.daubed) {
              cellEl.classList.add('is-daubed');
              this.attachDaubStamp(cellEl);
            }
          }

          // Click handler for daubing
          cellEl.addEventListener('click', () => {
            this.handleCellClick(card, cellData, cellEl);
          });

          gridEl.appendChild(cellEl);
        }
      }

      cardEl.appendChild(topBar);
      cardEl.appendChild(gridEl);
      this.cardsContainer.appendChild(cardEl);

      // Bingo button event
      const bingoBtn = cardEl.querySelector(`#bingo-btn-${card.id}`);
      bingoBtn.addEventListener('click', () => {
        this.verifyBingoCall(card);
      });
    });

    this.updateCalledCellsHint();
  }

  attachDaubStamp(cellEl) {
    if (!cellEl.querySelector('.daub-stamp')) {
      const stamp = document.createElement('div');
      stamp.className = 'daub-stamp';
      cellEl.appendChild(stamp);
    }
  }

  handleCellClick(card, cellData, cellEl) {
    if (cellData.isFree) return; // Free space is always stamped

    // Only allow daubing if number has been called OR player wants manual freeplay
    const isCalled = this.engine.isNumberCalled(cellData.number);
    if (!isCalled) {
      this.sound.playError();
      // Little shake animation to show it's not called yet
      cellEl.style.transform = 'translateX(4px)';
      setTimeout(() => cellEl.style.transform = '', 120);
      return;
    }

    cellData.daubed = !cellData.daubed;
    this.sound.playDaub();

    if (cellData.daubed) {
      cellEl.classList.add('is-daubed');
      this.attachDaubStamp(cellEl);
    } else {
      cellEl.classList.remove('is-daubed');
      const stamp = cellEl.querySelector('.daub-stamp');
      if (stamp) stamp.remove();
    }

    this.checkAllCardsWinState();
  }

  applyAutoDaub() {
    this.playerCards.forEach(card => {
      for (let r = 0; r < 5; r++) {
        for (let c = 0; c < 5; c++) {
          const cell = card.grid[r][c];
          if (!cell.isFree && !cell.daubed && this.engine.isNumberCalled(cell.number)) {
            cell.daubed = true;
            const cellEl = document.getElementById(`cell-${card.id}-${r}-${c}`);
            if (cellEl) {
              cellEl.classList.add('is-daubed');
              this.attachDaubStamp(cellEl);
            }
          }
        }
      }
    });
  }

  updateCalledCellsHint() {
    this.playerCards.forEach(card => {
      for (let r = 0; r < 5; r++) {
        for (let c = 0; c < 5; c++) {
          const cell = card.grid[r][c];
          const cellEl = document.getElementById(`cell-${card.id}-${r}-${c}`);
          if (cellEl && !cell.isFree) {
            if (this.engine.isNumberCalled(cell.number)) {
              cellEl.classList.add('is-called');
            } else {
              cellEl.classList.remove('is-called');
            }
          }
        }
      }
    });
  }

  checkAllCardsWinState() {
    this.playerCards.forEach(card => {
      const winResult = this.engine.checkWin(card, this.selectedPattern);
      const btn = document.getElementById(`bingo-btn-${card.id}`);
      const cardEl = document.getElementById(`card-elem-${card.id}`);

      if (winResult.hasWon) {
        btn.classList.add('ready-to-call');
        btn.textContent = 'WINNER! CALL!';
        cardEl.classList.add('card-winner');

        // Highlight winning cells
        winResult.winningCells.forEach(([r, c]) => {
          const cellEl = document.getElementById(`cell-${card.id}-${r}-${c}`);
          if (cellEl) cellEl.classList.add('is-winning-line');
        });
      } else {
        btn.classList.remove('ready-to-call');
        btn.textContent = 'Call BINGO!';
        cardEl.classList.remove('card-winner');
        // Clear winning lines
        for (let r = 0; r < 5; r++) {
          for (let c = 0; c < 5; c++) {
            const cellEl = document.getElementById(`cell-${card.id}-${r}-${c}`);
            if (cellEl) cellEl.classList.remove('is-winning-line');
          }
        }
      }
    });
  }

  verifyBingoCall(card) {
    const winResult = this.engine.checkWin(card, this.selectedPattern);
    
    if (winResult.hasWon) {
      this.gameWon = true;
      this.stopAutoCall();
      this.sound.playWinFanfare();
      this.sound.speakText(`BINGO! We have a winner on Card Number ${card.id}! Congratulations!`);
      this.confetti.burst(180);

      this.stats.bingosWon++;
      this.saveStats();

      // Show win modal
      const timeSeconds = Math.floor((Date.now() - this.gameStartTime) / 1000);
      const mins = Math.floor(timeSeconds / 60);
      const secs = timeSeconds % 60;

      this.winTitle.textContent = `BINGO! Card #${card.id} Wins!`;
      this.winSubtitle.textContent = `Completed pattern: ${winResult.patternName}`;
      this.winCallsCount.textContent = `${this.engine.drawnBalls.length}`;
      this.winTimeTaken.textContent = `${mins}:${secs < 10 ? '0' : ''}${secs}`;

      setTimeout(() => {
        this.openModal(this.modalWin);
      }, 500);

    } else {
      this.sound.playError();
      this.sound.speakText("False Bingo! Keep playing!");
      alert(`No valid Bingo pattern detected yet for Card #${card.id}. Keep daubing!`);
    }
  }

  renderMasterBoard() {
    this.masterRowsContainer.innerHTML = '';

    BINGO_LETTERS.forEach(letter => {
      const { min, max } = BINGO_COLUMNS[letter];
      const rowEl = document.createElement('div');
      rowEl.className = `master-row row-${letter.toLowerCase()}`;

      const badge = document.createElement('div');
      badge.className = 'master-row-badge';
      badge.textContent = letter;
      rowEl.appendChild(badge);

      for (let n = min; n <= max; n++) {
        const tile = document.createElement('div');
        tile.className = 'master-tile';
        tile.id = `master-tile-${n}`;
        tile.textContent = n;
        rowEl.appendChild(tile);
      }

      this.masterRowsContainer.appendChild(rowEl);
    });
  }

  updateMasterBoard() {
    for (let n = 1; n <= 75; n++) {
      const tile = document.getElementById(`master-tile-${n}`);
      if (tile) {
        if (this.engine.isNumberCalled(n)) {
          tile.classList.add('is-called');
        } else {
          tile.classList.remove('is-called');
        }
      }
    }
  }

  renderPrintableCards() {
    const count = parseInt(this.printableCountSelect.value, 10) || 2;
    this.printableGrid.innerHTML = '';

    for (let i = 1; i <= count; i++) {
      const card = this.engine.generateCard(i);
      const cardEl = document.createElement('div');
      cardEl.className = 'printable-card';

      const title = document.createElement('div');
      title.style.cssText = 'text-align: center; font-weight: 800; font-size: 1.1rem; margin-bottom: 8px; text-transform: uppercase;';
      title.textContent = `Bingo Card #${i}`;
      cardEl.appendChild(title);

      const gridEl = document.createElement('div');
      gridEl.className = 'bingo-grid';

      BINGO_LETTERS.forEach(l => {
        const h = document.createElement('div');
        h.className = 'grid-col-header';
        h.textContent = l;
        gridEl.appendChild(h);
      });

      for (let r = 0; r < 5; r++) {
        for (let c = 0; c < 5; c++) {
          const cell = card.grid[r][c];
          const cellEl = document.createElement('div');
          cellEl.className = 'bingo-cell';
          if (cell.isFree) {
            cellEl.classList.add('free-space');
            cellEl.textContent = 'FREE';
          } else {
            cellEl.textContent = cell.number;
          }
          gridEl.appendChild(cellEl);
        }
      }

      cardEl.appendChild(gridEl);
      this.printableGrid.appendChild(cardEl);
    }
  }
}

// Bootstrap on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
  window.bingoApp = new BingoApp();
});
