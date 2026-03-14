const messagesDiv = document.getElementById('messages');
const input       = document.getElementById('user-input');
const sendBtn     = document.getElementById('send-btn');
const cardsDiv    = document.getElementById('movie-cards');

marked.setOptions({ breaks: true, gfm: true });

const ICON = `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M18 4l2 4h-3l-2-4h-2l2 4h-3l-2-4H8l2 4H7L5 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V4h-4z"/></svg>`;

function addMessage(text, role) {
  const wrap = document.createElement('div');
  wrap.classList.add('msg-enter');
  if (role === 'user') {
    wrap.classList.add('msg-user');
    wrap.innerHTML = `<div class="bubble-user">${text}</div>`;
  } else {
    wrap.classList.add('msg-bot');
    wrap.innerHTML = `
      <div class="msg-meta">
        <div class="msg-avatar">${ICON}</div>
        <span class="msg-name">CINEBOT</span>
      </div>
      <div class="bubble-bot">${marked.parse(text)}</div>`;
  }
  messagesDiv.appendChild(wrap);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
  return wrap;
}

function showTyping() {
  const wrap = document.createElement('div');
  wrap.classList.add('msg-bot', 'msg-enter');
  wrap.id = 'typing-indicator';
  wrap.innerHTML = `
    <div class="msg-meta">
      <div class="msg-avatar">${ICON}</div>
      <span class="msg-name">CINEBOT</span>
    </div>
    <div class="bubble-bot">
      <div class="typing-dots"><span></span><span></span><span></span></div>
    </div>`;
  messagesDiv.appendChild(wrap);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
  return wrap;
}

function renderMovieCards(movies) {
  cardsDiv.innerHTML = '';
  if (!movies || movies.length === 0) { cardsDiv.classList.add('hidden'); return; }
  cardsDiv.classList.remove('hidden');
  movies.forEach((m, i) => {
    const card = document.createElement('div');
    card.className = 'movie-card card-enter';
    card.style.animationDelay = `${i * 90}ms`;
    const ratingPct = Math.min((m.rating / 10) * 100, 100);
    card.innerHTML = `
      ${m.poster ? `<img src="${m.poster}" alt="${m.title}" loading="lazy" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">` : ''}
      <div class="movie-card-fallback" style="display:${m.poster ? 'none' : 'flex'}">${ICON}</div>
      <div class="movie-card-info">
        <p class="movie-card-title" title="${m.title}">${m.title}</p>
        <p class="movie-card-meta">${m.year || '—'} &middot; ${m.rating}/10</p>
        <div class="rating-bar"><div class="rating-fill" style="width:${ratingPct}%"></div></div>
      </div>`;
    cardsDiv.appendChild(card);
  });
}

async function sendMessage(messageText) {
  const msg = messageText || input.value.trim();
  if (!msg) return;
  addMessage(msg, 'user');
  input.value = '';
  sendBtn.disabled = true;
  cardsDiv.classList.add('hidden');
  const typingEl = showTyping();
  try {
    const res  = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: msg }) });
    const data = await res.json();
    typingEl.remove();
    addMessage(data.message || data.error, 'assistant');
    renderMovieCards(data.movies);
  } catch(e) {
    typingEl.remove();
    addMessage('Something went wrong. Please try again.', 'assistant');
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
}

function sendSuggestion(text) { sendMessage(text); }
sendBtn.addEventListener('click', () => sendMessage());
input.addEventListener('keypress', e => { if (e.key === 'Enter') sendMessage(); });