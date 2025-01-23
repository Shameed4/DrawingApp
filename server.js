const express = require('express');
const bodyParser = require('body-parser');

const app = express();
app.use(express.static('public'));
app.use(bodyParser.json({ limit: '10mb' })); // Allow larger payload for image data

// In-memory storage of drawings (base64 images) and votes:
let artworks = [];

/**
 * Endpoint to handle submitted drawings
 */
app.post('/submit-drawing', (req, res) => {
  const { imageData } = req.body;
  if (!imageData) {
    return res.status(400).send('No image data provided');
  }
  // Store the drawing in memory. Each artwork has { id, dataUrl, votes }.
  artworks.push({
    id: artworks.length, 
    dataUrl: imageData, 
    votes: 0
  });

  return res.status(200).send({ message: 'Artwork submitted successfully' });
});

/**
 * Endpoint to fetch all artworks in random order (for the voting page)
 */
app.get('/artworks', (req, res) => {
  // Shuffle the artworks array to randomize display order
  const shuffled = [...artworks].sort(() => Math.random() - 0.5);
  return res.json(shuffled);
});

/**
 * Endpoint to record a vote for a given artwork ID
 */
app.post('/vote', (req, res) => {
  const { id } = req.body;
  const artwork = artworks.find(a => a.id === id);
  if (artwork) {
    artwork.votes += 1;
    return res.status(200).send({ message: 'Vote recorded' });
  } else {
    return res.status(400).send({ message: 'Invalid artwork ID' });
  }
});

/**
 * Endpoint to return results in descending order of votes
 */
app.get('/results', (req, res) => {
  const sorted = [...artworks].sort((a, b) => b.votes - a.votes);
  return res.json(sorted);
});

const port = process.env.PORT || 3000;
app.listen(port, () => {
  console.log(`Server running on http://localhost:${port}`);
});
