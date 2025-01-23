import cv2
import mediapipe as mp
import numpy as np
from flask import Flask, Response, send_file
import io
from PIL import Image

app = Flask(__name__)

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

cap = cv2.VideoCapture(0)

canvas = None
prev_x, prev_y = None, None
color = (0, 0, 0)  # default black
brush_thickness = 5
palette = []
slider_coords = None

# We'll keep a copy of the last raw webcam frame for snapshots
last_raw_frame = None

def draw_palette_and_slider(img, thickness, s_coords):
    # Draw color palette
    for col, rect in palette:
        x1, y1, x2, y2 = rect
        cv2.rectangle(img, (x1, y1), (x2, y2), col, -1)
        cv2.rectangle(img, (x1, y1), (x2, y2), (255, 255, 255), 2)
    # Draw slider
    sx1, sy1, sx2, sy2 = s_coords
    cv2.rectangle(img, (sx1, sy1), (sx2, sy2), (200, 200, 200), 2)
    pos_y = sy1 + int((thickness / 50) * (sy2 - sy1))
    cv2.line(img, (sx1, pos_y), (sx2, pos_y), (0, 0, 255), 3)

def detect_color_selection(x, y):
    for c, rect in palette:
        x1, y1, x2, y2 = rect
        if x1 <= x <= x2 and y1 <= y <= y2:
            return c
    return None

def is_in_slider_area(x, y, coords):
    x1, y1, x2, y2 = coords
    return x1 <= x <= x2 and y1 <= y <= y2

def generate_drawing_frames():
    """
    MJPEG stream for the real-time drawing (white canvas + palette + brush).
    """
    global canvas, prev_x, prev_y, color, brush_thickness, palette, slider_coords

    while True:
        success, frame = cap.read()
        if not success:
            break
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        # Store raw frame for snapshot
        global last_raw_frame
        last_raw_frame = frame.copy()

        # Initialize the white canvas if needed
        if canvas is None:
            canvas = np.ones_like(frame, dtype=np.uint8) * 255

            # Build color palette
            palette_width = int(0.1 * w)
            palette_height = int(0.1 * h)
            px = w - palette_width - 20
            py = 20
            gap = 10

            palette = [
                ((0, 0, 0),   (px, py, px + palette_width, py + palette_height)),  # Black
                ((255, 0, 0), (px, py + palette_height + gap,
                               px + palette_width, py + 2*palette_height+gap)),    # Blue
                ((0, 255, 0), (px, py + 2*(palette_height+gap),
                               px + palette_width, py + 3*palette_height+2*gap)),  # Green
                ((0, 0, 255), (px, py + 3*(palette_height+gap),
                               px + palette_width, py + 4*palette_height+3*gap)),  # Red
                ((255, 255, 0),(px, py + 4*(palette_height+gap),
                                px + palette_width, py + 5*palette_height+4*gap)), # Yellow
                ((255, 255, 255),(px, py + 5*(palette_height+gap),
                                  px + palette_width, py + 6*palette_height+5*gap))# White
            ]

            # Brush thickness slider
            slider_coords = (
                20,           # x1
                20,           # y1
                20 + palette_width,        # x2
                20 + int(0.3 * h)          # y2
            )

        # Convert to RGB for MediaPipe
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        # Make a copy of the canvas to overlay palette + landmarks
        display_canvas = canvas.copy()

        # Draw palette + slider
        draw_palette_and_slider(display_canvas, brush_thickness, slider_coords)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Index fingertip
                x_f = int(hand_landmarks.landmark[8].x * w)
                y_f = int(hand_landmarks.landmark[8].y * h)

                # Detect color selection
                new_color = detect_color_selection(x_f, y_f)
                if new_color is not None:
                    color = new_color
                    prev_x, prev_y = None, None

                # Detect brush slider usage
                if is_in_slider_area(x_f, y_f, slider_coords):
                    brush_thickness = int(((y_f - slider_coords[1]) /
                                          (slider_coords[3] - slider_coords[1])) * 50)
                    brush_thickness = max(1, min(50, brush_thickness))
                    prev_x, prev_y = None, None

                # Avoid drawing over palette or slider area
                if x_f >= palette[-1][1][0] or x_f <= slider_coords[2]:
                    prev_x, prev_y = None, None
                else:
                    # If fingertip is above DIP => "draw"
                    if hand_landmarks.landmark[8].y < hand_landmarks.landmark[6].y:
                        if prev_x is None or prev_y is None:
                            prev_x, prev_y = x_f, y_f
                        cv2.line(canvas, (prev_x, prev_y), (x_f, y_f), color, brush_thickness)
                        prev_x, prev_y = x_f, y_f
                    else:
                        prev_x, prev_y = None, None

                # Draw hand landmarks on display copy
                mp_drawing.draw_landmarks(
                    display_canvas,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS
                )

        # Convert display_canvas to JPEG
        ret2, buffer = cv2.imencode('.jpg', display_canvas)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

def generate_webcam_frames():
    """
    MJPEG stream of the raw flipped webcam feed only.
    """
    global last_raw_frame
    while True:
        if last_raw_frame is None:
            success, frame = cap.read()
            if not success:
                break
            frame = cv2.flip(frame, 1)
            last_raw_frame = frame
        ret, buffer = cv2.imencode('.jpg', last_raw_frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/video_feed')
def video_feed():
    # Stream the drawing canvas
    return Response(generate_drawing_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/webcam_feed')
def webcam_feed():
    # Stream the raw webcam feed
    return Response(generate_webcam_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/canvas_image')
def canvas_image():
    # Return the final drawn canvas as PNG
    global canvas
    img_pil = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
    buf = io.BytesIO()
    img_pil.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@app.route('/snapshot_image')
def snapshot_image():
    # Return the last raw webcam frame as PNG
    global last_raw_frame
    if last_raw_frame is None:
        return ('No snapshot available', 404)

    img_pil = Image.fromarray(cv2.cvtColor(last_raw_frame, cv2.COLOR_BGR2RGB))
    buf = io.BytesIO()
    img_pil.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

if __name__ == '__main__':
    # Run Python server on port 5001
    app.run(host='0.0.0.0', port=5001, debug=True)
