import cv2
import mediapipe as mp
import numpy as np

# Initialize Mediapipe and OpenCV
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Initialize canvas
canvas = None
cap = cv2.VideoCapture(0)

# Variables to track drawing state
drawing = False
prev_x, prev_y = None, None

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    # Flip the frame for better UX and convert to RGB
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Process frame with Mediapipe
    result = hands.process(rgb_frame)
    height, width, _ = frame.shape
    
    # Initialize canvas if it doesn't exist
    if canvas is None:
        canvas = np.zeros_like(frame)
    
    # Check if hands are detected
    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            # Get index finger tip coordinates (landmark 8)
            x, y = hand_landmarks.landmark[8].x * width, hand_landmarks.landmark[8].y * height
            x, y = int(x), int(y)
            
            # Check if the user wants to draw
            if hand_landmarks.landmark[8].y < hand_landmarks.landmark[6].y:  # Finger raised
                if prev_x is None or prev_y is None:
                    prev_x, prev_y = x, y
                
                # Draw on the canvas
                cv2.line(canvas, (prev_x, prev_y), (x, y), (0, 255, 0), 5)
                prev_x, prev_y = x, y
            else:
                prev_x, prev_y = None, None  # Reset if the finger is not raised

            # Draw hand landmarks
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
    
    # Merge canvas with the frame
    blended = cv2.addWeighted(frame, 0.5, canvas, 0.5, 0)
    
    # Show the output
    cv2.imshow("Drawing App", blended)
    
    # Exit on pressing 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()