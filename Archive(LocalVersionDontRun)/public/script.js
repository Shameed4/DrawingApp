const videoElement = document.getElementById('video');
const canvasElement = document.getElementById('canvas');
const canvasCtx = canvasElement.getContext('2d');

// Larger resolution for bigger camera and canvas
const VIDEO_WIDTH = 900;
const VIDEO_HEIGHT = 600;

videoElement.width = VIDEO_WIDTH;
videoElement.height = VIDEO_HEIGHT;
canvasElement.width = VIDEO_WIDTH;
canvasElement.height = VIDEO_HEIGHT;

let drawing = false;
let lastX = null;
let lastY = null;
let gameTime = 30; // seconds (demo)
let timerInterval = null;

/**
 * Distance between two landmarks.
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

  const landmarks = results.multiHandLandmarks[0];
  if (!landmarks) return;

  // Index Finger tip = [8], Thumb tip = [4]
  const indexFingerTip = landmarks[8];
  const thumbTip = landmarks[4];
  
  // If they're close => "draw mode"
  const distance = getDistance(indexFingerTip, thumbTip);
  const threshold = 0.05;

  if (distance < threshold) {
    drawing = true;
  } else {
    drawing = false;
    lastX = null;
    lastY = null;
  }

  // Drawing
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
    canvasCtx.strokeStyle = 'white'; // Contrasts with purple
    canvasCtx.lineWidth = 4;
    canvasCtx.stroke();
    canvasCtx.closePath();

    lastX = x;
    lastY = y;
  }
}

/**
 * MediaPipe Hands
 */
const hands = new Hands({
  locateFile: file => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`
});
hands.setOptions({
  maxNumHands: 1,
  modelComplexity: 1,
  minDetectionConfidence: 0.7,
  minTrackingConfidence: 0.5
});
hands.onResults(onResults);

/**
 * Use Camera to feed frames to MediaPipe
 */
const camera = new Camera(videoElement, {
  onFrame: async () => {
    await hands.send({ image: videoElement });
  },
  width: VIDEO_WIDTH,
  height: VIDEO_HEIGHT
});
camera.start();

/**
 * Start the game timer
 */
/*
function startTimer() {
  const timerElement = document.getElementById('timer');
  let timeLeft = gameTime;

  timerInterval = setInterval(() => {
    timeLeft--;
    timerElement.innerText = `Time Left: ${timeLeft}s`;
    
    if (timeLeft <= 0) {
      clearInterval(timerInterval);
      // Time's up - submit
      submitCanvas();
    }
  }, 1000);
}
*/
/**
 * Capture a snapshot of the user's face/hands from the webcam
 */
function captureUserPhoto() {
  // Create a temp canvas to draw the current video frame
  const tempCanvas = document.createElement('canvas');
  tempCanvas.width = VIDEO_WIDTH;
  tempCanvas.height = VIDEO_HEIGHT;
  const tempCtx = tempCanvas.getContext('2d');
  tempCtx.drawImage(videoElement, 0, 0, VIDEO_WIDTH, VIDEO_HEIGHT);
  return tempCanvas.toDataURL('image/png');
}

/**
 * Submit the canvas image + user photo to the server
 */
function submitCanvas() {
  const drawingDataURL = canvasElement.toDataURL('image/png');
  const userPhoto = captureUserPhoto();

  fetch('/submit-drawing', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      imageData: drawingDataURL,
      userPhoto: userPhoto
    })
  })
    .then(res => res.json())
    .then(data => {
      console.log(data);
      // Auto-redirect to voting page
      window.location.href = '/vote.html';
    })
    .catch(err => {
      console.error(err);
      alert('Error submitting artwork');
    });
}

// Start the game timer
//startTimer();
// Stop the game timer
// clearInterval(timerInterval);
// Submit the drawing to the server
