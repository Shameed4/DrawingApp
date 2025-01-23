const videoElement = document.getElementById('video');
const canvasElement = document.getElementById('canvas');
const canvasCtx = canvasElement.getContext('2d');

// Set canvas size (you can adjust these to your preference)
canvasElement.width = 640;
canvasElement.height = 480;

let drawing = false;
let lastX = null;
let lastY = null;
let gameTime = 30; // seconds (set to 30 for demo; change to 1800 for 30 minutes if desired)
let timerInterval = null;

/**
 * Calculate distance between two landmarks.
 * Landmarks have x, y in [0..1] range (normalized by MediaPipe).
 */
function getDistance(p1, p2) {
  const dx = p1.x - p2.x;
  const dy = p1.y - p2.y;
  return Math.sqrt(dx * dx + dy * dy);
}

/**
 * Handle results from MediaPipe Hands
 */
function onResults(results) {
  if (!results.multiHandLandmarks) return;

  // We'll just track the first detected hand
  const landmarks = results.multiHandLandmarks[0];
  if (!landmarks) return;

  // Index Finger tip is landmarks[8], thumb tip is landmarks[4]
  const indexFingerTip = landmarks[8];
  const thumbTip = landmarks[4];
  
  // If index finger tip and thumb tip are close => "pen down"
  const distance = getDistance(indexFingerTip, thumbTip);
  const threshold = 0.05; // Adjust as needed

  if (distance < threshold) {
    // User is "pinching" => drawing mode
    drawing = true;
  } else {
    // Not pinching => pen up
    drawing = false;
    lastX = null;
    lastY = null;
  }

  // If drawing, convert normalized coords to canvas coords and draw
  if (drawing) {
    const x = indexFingerTip.x * canvasElement.width;
    const y = indexFingerTip.y * canvasElement.height;
    
    if (lastX === null || lastY === null) {
      lastX = x;
      lastY = y;
    }
    
    // Draw a line from last to current
    canvasCtx.beginPath();
    canvasCtx.moveTo(lastX, lastY);
    canvasCtx.lineTo(x, y);
    canvasCtx.strokeStyle = 'black';
    canvasCtx.lineWidth = 4;
    canvasCtx.stroke();
    canvasCtx.closePath();

    lastX = x;
    lastY = y;
  }
}

/**
 * Configure MediaPipe Hands
 */
const hands = new Hands({
  locateFile: (file) => {
    return `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`;
  }
});
hands.setOptions({
  maxNumHands: 1,
  modelComplexity: 1,
  minDetectionConfidence: 0.7,
  minTrackingConfidence: 0.5
});
hands.onResults(onResults);

/**
 * Use camera_utils to capture webcam and pipe frames into MediaPipe
 */
const camera = new Camera(videoElement, {
  onFrame: async () => {
    await hands.send({ image: videoElement });
  },
  width: 640,
  height: 480
});
camera.start();

/**
 * Start the game timer
 */
function startTimer() {
  const timerElement = document.getElementById('timer');
  let timeLeft = gameTime;

  timerInterval = setInterval(() => {
    timeLeft--;
    timerElement.innerText = `Time Left: ${timeLeft}s`;
    
    if (timeLeft <= 0) {
      clearInterval(timerInterval);
      // Time's up - submit canvas automatically
      submitCanvas();
    }
  }, 1000);
}

/**
 * Submit the canvas image to the server
 */
function submitCanvas() {
  // Convert canvas to a base64 data URL (PNG)
  const dataURL = canvasElement.toDataURL('image/png');
  
  fetch('/submit-drawing', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ imageData: dataURL })
  })
    .then(res => res.json())
    .then(data => {
      console.log(data);
      alert('Your artwork has been submitted!');
      // Redirect to the voting page
      window.location.href = '/vote.html';
    })
    .catch(err => {
      console.error(err);
      alert('Error submitting artwork');
    });
}

// Start the timer on page load
startTimer();
