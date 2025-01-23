const express = require('express');
const bodyParser = require('body-parser');

const app = express();
app.use(express.static('public'));
app.use(bodyParser.json({ limit: '10mb' }));

// In-memory storage of artworks
let artworks = [];
/**
 * Artwork: {
 *   id: number,
 *   dataUrl: string,   // base64 of final canvas
 *   userPhoto: string, // base64 of webcam snapshot
 *   score: number,
 *   votesCount: number
 * }
 */

app.post('/submit-drawing', (req, res) => {
  const { imageData, userPhoto } = req.body;
  if (!imageData) {
    return res.status(400).json({ message: 'No image data provided' });
  }
  artworks.push({
    id: artworks.length,
    dataUrl: imageData,
    userPhoto: userPhoto || null,
    score: 0,
    votesCount: 0
  });
  res.status(200).json({ message: 'Artwork submitted successfully' });
});

app.get('/artworks', (req, res) => {
  // Shuffle for random order
  const shuffled = [...artworks].sort(() => Math.random() - 0.5);
  res.json(shuffled);
});

app.post('/rate', (req, res) => {
  const { id, rating } = req.body;
  const artwork = artworks.find(a => a.id === id);
  if (!artwork) {
    return res.status(400).json({ message: 'Invalid artwork ID' });
  }
  if (typeof rating !== 'number' || rating < 1 || rating > 5) {
    return res.status(400).json({ message: 'Invalid rating' });
  }
  artwork.score += rating;
  artwork.votesCount += 1;
  res.status(200).json({ message: 'Rating recorded' });
});

app.get('/results', (req, res) => {
  const sorted = [...artworks].sort((a, b) => b.score - a.score);
  res.json(sorted);
});

const port = 3000;
app.listen(port, () => {
  console.log(`Node server running at http://localhost:${port}`);
});
