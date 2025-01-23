let votingTime = 10; // seconds (change to 600 for 10 minutes if desired)
let timerInterval = null;

/**
 * Fetch artworks from the server and display them
 */
function loadArtworks() {
  fetch('/artworks')
    .then(res => res.json())
    .then(data => {
      const container = document.getElementById('artworks-container');
      container.innerHTML = '';
      data.forEach(art => {
        // Display each artwork (base64 image)
        const img = document.createElement('img');
        img.src = art.dataUrl;
        img.width = 320;
        img.height = 240;
        img.style.margin = '10px';

        // Create a Vote button
        const btn = document.createElement('button');
        btn.innerText = 'Vote';
        btn.onclick = () => voteFor(art.id);

        const div = document.createElement('div');
        div.style.display = 'inline-block';
        div.style.verticalAlign = 'top';
        div.appendChild(img);
        div.appendChild(document.createElement('br'));
        div.appendChild(btn);

        container.appendChild(div);
      });
    })
    .catch(err => console.error(err));
}

/**
 * Send a vote to the server for a given artwork ID
 */
function voteFor(id) {
  fetch('/vote', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ id })
  })
    .then(res => res.json())
    .then(data => {
      alert('Vote recorded!');
    })
    .catch(err => console.error(err));
}

/**
 * Start a voting countdown timer
 */
function startVotingTimer() {
  const voteTimerElement = document.getElementById('vote-timer');
  let timeLeft = votingTime;

  timerInterval = setInterval(() => {
    timeLeft--;
    voteTimerElement.innerText = `Voting Time Left: ${timeLeft}s`;
    
    if (timeLeft <= 0) {
      clearInterval(timerInterval);
      alert('Voting is now closed!');
      // Optionally disable the vote buttons or hide them
    }
  }, 1000);
}

/**
 * View the results (sorted by number of votes)
 */
function viewResults() {
  fetch('/results')
    .then(res => res.json())
    .then(data => {
      const resultsContainer = document.getElementById('results-container');
      resultsContainer.innerHTML = '<h2>Results</h2>';
      data.forEach(art => {
        const p = document.createElement('p');
        p.innerText = `Artwork #${art.id} - Votes: ${art.votes}`;
        resultsContainer.appendChild(p);
      });
    })
    .catch(err => console.error(err));
}

document.getElementById('view-results').addEventListener('click', viewResults);

// On page load:
loadArtworks();
startVotingTimer();
