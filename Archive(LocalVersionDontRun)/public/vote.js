let votingTime = 10; // seconds for demo
let timerInterval = null;

const previewModal = document.getElementById('preview-modal');
const modalImage = document.getElementById('modal-image');
const ratingContainer = document.getElementById('rating-container');
const modalClose = document.getElementById('modal-close');

function loadArtworks() {
  fetch('/artworks')
    .then(res => res.json())
    .then(data => renderArtworks(data))
    .catch(err => console.error(err));
}

function renderArtworks(artworks) {
  const container = document.getElementById('artworks-container');
  container.innerHTML = '';
  artworks.forEach(art => {
    const img = document.createElement('img');
    img.src = art.dataUrl;
    img.className = 'thumbnail';
    img.addEventListener('click', () => openPreviewModal(art));

    const div = document.createElement('div');
    div.className = 'artwork-wrapper';
    div.appendChild(img);
    container.appendChild(div);
  });
}

function openPreviewModal(art) {
  previewModal.style.display = 'block';
  modalImage.src = art.dataUrl;

  // 1-5 rating buttons
  ratingContainer.innerHTML = '<p>Rate this drawing (1-5):</p>';
  for (let i = 1; i <= 5; i++) {
    const btn = document.createElement('button');
    btn.innerText = i;
    btn.className = 'rating-button';
    btn.onclick = () => rateArtwork(art.id, i);
    ratingContainer.appendChild(btn);
  }
}

modalClose.onclick = function() {
  previewModal.style.display = 'none';
};

function rateArtwork(artId, rating) {
  fetch('/rate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id: artId, rating })
  })
  .then(res => res.json())
  .then(data => {
    alert(data.message);
    previewModal.style.display = 'none';
  })
  .catch(err => console.error(err));
}

function startVotingTimer() {
  let timeLeft = votingTime;
  const voteTimerEl = document.getElementById('vote-timer');

  timerInterval = setInterval(() => {
    timeLeft--;
    voteTimerEl.innerText = `Voting Time Left: ${timeLeft}s`;
    if (timeLeft <= 0) {
      clearInterval(timerInterval);
      endVoting();
    }
  }, 1000);
}

function endVoting() {
  alert('Voting is now closed! Displaying results...');
  fetch('/results')
    .then(res => res.json())
    .then(data => showPodium(data.slice(0, 3)))
    .catch(err => console.error(err));
}

function showPodium(top3) {
  const resultsContainer = document.getElementById('results-container');
  resultsContainer.innerHTML = '<h2>Winners Podium</h2>';

  const podium = document.createElement('div');
  podium.className = 'podium';

  const [first, second, third] = [top3[0], top3[1], top3[2]];

  const secondDiv = document.createElement('div');
  secondDiv.className = 'podium-step second-step';
  secondDiv.innerHTML = second ? buildPodiumHTML(second, 2) : '<p>No 2nd place</p>';

  const firstDiv = document.createElement('div');
  firstDiv.className = 'podium-step first-step';
  firstDiv.innerHTML = first ? buildPodiumHTML(first, 1) : '<p>No 1st place</p>';

  const thirdDiv = document.createElement('div');
  thirdDiv.className = 'podium-step third-step';
  thirdDiv.innerHTML = third ? buildPodiumHTML(third, 3) : '<p>No 3rd place</p>';

  podium.appendChild(secondDiv);
  podium.appendChild(firstDiv);
  podium.appendChild(thirdDiv);
  resultsContainer.appendChild(podium);

  // Confetti + Music
  launchConfetti();
  playTriumphMusic();
}

function buildPodiumHTML(artwork, place) {
  // Show the final drawing & user snapshot (if any)
  return `
    <h3>${place} Place</h3>
    <img src="${artwork.dataUrl}" class="podium-art" alt="Drawing #${artwork.id}" />
    ${
      artwork.userPhoto
        ? `<img src="${artwork.userPhoto}" class="podium-user" alt="Snapshot #${artwork.id}" />`
        : ''
    }
    <p>Points: ${artwork.score}</p>
  `;
}

function launchConfetti() {
  const end = Date.now() + 3 * 1000;
  const colors = ['#bb0000', '#ffffff', '#00ff00'];

  (function frame() {
    confetti({
      particleCount: 8,
      angle: 60,
      spread: 55,
      origin: { x: 0 },
      colors
    });
    confetti({
      particleCount: 8,
      angle: 120,
      spread: 55,
      origin: { x: 1 },
      colors
    });
    if (Date.now() < end) {
      requestAnimationFrame(frame);
    }
  })();
}

function playTriumphMusic() {
  const audio = document.getElementById('triumph-audio');
  if (audio) {
    audio.play().catch(() => console.log('Autoplay blocked'));
  }
}

// On page load
document.addEventListener('DOMContentLoaded', () => {
  loadArtworks();
  startVotingTimer();
});
