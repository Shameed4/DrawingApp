<<<<<<< HEAD
import cv2
import mediapipe as mp
import numpy as np

# Initialize Mediapipe and OpenCV
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

# Initialize canvas
canvas = None
cap = cv2.VideoCapture(0)

# Variables for drawing state and color
prev_x, prev_y = None, None
color = (0, 0, 0)  # Default black
brush_thickness = 5

# Color palette (each entry is a tuple: (color, (x1, y1, x2, y2)))
palette = []

def draw_palette_and_slider(frame, brush_thickness, slider_coords):
    """Draw the color palette and brush size slider on the frame."""
    # Draw the color palette
    for color_option, rect in palette:
        x1, y1, x2, y2 = rect
        cv2.rectangle(frame, (x1, y1), (x2, y2), color_option, -1)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 2)  # Border

    # Draw the slider
    slider_x1, slider_y1, slider_x2, slider_y2 = slider_coords
    cv2.rectangle(frame, (slider_x1, slider_y1), (slider_x2, slider_y2), (200, 200, 200), 2)  # Slider border
    slider_pos_y = slider_y1 + int((brush_thickness / 50) * (slider_y2 - slider_y1))
    cv2.line(frame, (slider_x1, slider_pos_y), (slider_x2, slider_pos_y), (0, 0, 255), 3)  # Slider position line
    cv2.circle(frame, ((slider_x1 + slider_x2) // 2, slider_y2 + 100), brush_thickness // 2, color, -1)
    
    

def detect_color_selection(x, y):
    """Detect if the finger is selecting a color from the palette."""
    for color, rect in palette:
        x1, y1, x2, y2 = rect
        if x1 <= x <= x2 and y1 <= y <= y2:
            return color
    return None

def is_in_slider_area(x, y, slider_coords):
    """Check if the finger is interacting with the slider."""
    slider_x1, slider_y1, slider_x2, slider_y2 = slider_coords
    return slider_x1 <= x <= slider_x2 and slider_y1 <= y <= slider_y2

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
        canvas[:, :, :] = (255, 255, 255)
        
        # Dynamically calculate palette and slider positions
        palette_width = int(0.1 * width)  # Palette width is 10% of the frame width
        palette_height = int(0.1 * height)  # Each palette box height is 10% of the frame height
        palette_start_x = width - palette_width - 20  # Leave a margin of 20px from the right
        palette_start_y = 20  # Start from 20px margin at the top
        
        palette = [
            ((0, 0, 0), (palette_start_x, palette_start_y, palette_start_x + palette_width, palette_start_y + palette_height)),  # Black
            ((255, 0, 0), (palette_start_x, palette_start_y + palette_height + 10, palette_start_x + palette_width, palette_start_y + 2 * palette_height + 10)),  # Blue
            ((0, 255, 0), (palette_start_x, palette_start_y + 2 * (palette_height + 10), palette_start_x + palette_width, palette_start_y + 3 * palette_height + 20)),  # Green
            ((0, 0, 255), (palette_start_x, palette_start_y + 3 * (palette_height + 10), palette_start_x + palette_width, palette_start_y + 4 * palette_height + 30)),  # Red
            ((255, 255, 0), (palette_start_x, palette_start_y + 4 * (palette_height + 10), palette_start_x + palette_width, palette_start_y + 5 * palette_height + 40)),  # Yellow
            ((255, 255, 255), (palette_start_x, palette_start_y + 5 * (palette_height + 10), palette_start_x + palette_width, palette_start_y + 6 * palette_height + 50))  # White
        ]
        
        # Slider position
        slider_width = int(0.1 * width)  # Palette width is 10% of the frame width
        slider_height = int(0.2 * height)  # Each palette box height is 10% of the frame height
        slider_start_x = 20  # Leave a margin of 20px from the right
        slider_start_y = 20  # Start from 20px margin at the top
        
        slider_x1 = slider_start_x
        slider_y1 = slider_start_y
        slider_x2 = slider_start_x + palette_width
        slider_y2 = slider_y1 + slider_height  # Slider height is 100px
        slider_coords = (slider_x1, slider_y1, slider_x2, slider_y2)
    
    # Draw the color palette and slider
    draw_palette_and_slider(frame, brush_thickness, slider_coords)
    
    # Check if hands are detected
    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            # Get index finger tip coordinates (landmark 8)
            x, y = int(hand_landmarks.landmark[8].x * width), int(hand_landmarks.landmark[8].y * height)
            
            # Detect color selection
            selected_color = detect_color_selection(x, y)
            if selected_color:
                color = selected_color
                prev_x, prev_y = None, None  # Reset drawing to prevent accidental lines
            
            # Detect brush size adjustment
            if is_in_slider_area(x, y, slider_coords):
                brush_thickness = int(((y - slider_y1) / (slider_y2 - slider_y1)) * 50)
                brush_thickness = max(1, min(50, brush_thickness))  # Clamp between 1 and 50
                prev_x, prev_y = None, None  # Reset drawing to prevent accidental lines
            
            # Prevent drawing on the palette or slider
            if x >= palette_start_x or x <= slider_x2 or y <= 20 or y >= height - 20:  # Avoid drawing in the palette/slider area
                prev_x, prev_y = None, None
                continue
            
            # Check if the user wants to draw
            if hand_landmarks.landmark[8].y < hand_landmarks.landmark[6].y:  # Finger raised
                if prev_x is None or prev_y is None:
                    prev_x, prev_y = x, y
                
                # Draw on the canvas
                cv2.line(canvas, (prev_x, prev_y), (x, y), color, brush_thickness)
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
=======
import cv2
import mediapipe as mp
import numpy as np
import math

# Initialize Mediapipe and OpenCV
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

# Initialize canvas
canvas = None
cap = cv2.VideoCapture(0)

# Variables for drawing state and color
prev_x, prev_y = None, None
color = (0, 0, 0)  # Default black
brush_thickness = 5

# Color palette (each entry is a tuple: (color, (x1, y1, x2, y2)))
palette = []

def draw_palette_and_slider(frame, brush_thickness, slider_coords):
    """Draw the color palette and brush size slider on the frame."""
    # Draw the color palette
    for color_option, rect in palette:
        x1, y1, x2, y2 = rect
        cv2.rectangle(frame, (x1, y1), (x2, y2), color_option, -1)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 2)  # Border

    
    cv2.rectangle(frame, (0, 0), (int(0.15*width), height), (0, 0, 0), -1)  # Border
    
    # Draw the slider
    slider_x1, slider_y1, slider_x2, slider_y2 = slider_coords
    cv2.rectangle(frame, (slider_x1, slider_y1), (slider_x2, slider_y2), (200, 200, 200), 2)  # Slider border
    slider_pos_y = slider_y1 + int((brush_thickness / 50) * (slider_y2 - slider_y1))
    cv2.line(frame, (slider_x1, slider_pos_y), (slider_x2, slider_pos_y), (0, 0, 255), 3)  # Slider position line
    cv2.circle(frame, ((slider_x1 + slider_x2) // 2, slider_y2 + 100), brush_thickness // 2, color, -1)
    
    

def detect_color_selection(x, y):
    """Detect if the finger is selecting a color from the palette."""
    for color, rect in palette:
        x1, y1, x2, y2 = rect
        if x1 <= x <= x2 and y1 <= y <= y2:
            return color
    return None

def is_in_slider_area(x, y, slider_coords):
    """Check if the finger is interacting with the slider."""
    slider_x1, slider_y1, slider_x2, slider_y2 = slider_coords
    return slider_x1 <= x <= slider_x2 and slider_y1 <= y <= slider_y2


# Calculate the distance between two points (x, y)
def distance(a, b):
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2)

# Calculate the angle between two vectors
def calculate_angle(vec1, vec2):
    dot_product = vec1[0] * vec2[0] + vec1[1] * vec2[1] + vec1[2] * vec2[2]
    magnitude_vec1 = math.sqrt(vec1[0]**2 + vec1[1]**2 + vec1[2]**2)
    magnitude_vec2 = math.sqrt(vec2[0]**2 + vec2[1]**2 + vec2[2]**2)
    cos_theta = dot_product / (magnitude_vec1 * magnitude_vec2)
    return math.acos(max(min(cos_theta, 1), -1))  # Clamp for precision errors

def is_thumb_pointer_perpendicular(thumb_tip, thumb_cmc, index_tip, index_mcp):
    # Define vectors for thumb and index finger
    thumb_vector = (thumb_tip.x - thumb_cmc.x, thumb_tip.y - thumb_cmc.y, thumb_tip.z - thumb_cmc.z)
    index_vector = (index_tip.x - index_mcp.x, index_tip.y - index_mcp.y, index_tip.z - index_mcp.z)
    
    # Calculate the angle between the vectors
    angle = calculate_angle(thumb_vector, index_vector)
    
    # Threshold for near perpendicular (85 to 95 degrees, in radians)
    lower_bound = math.radians(30)
    upper_bound = math.radians(100)
    
    # print(f"{(lower_bound, angle, upper_bound, lower_bound <= angle <= upper_bound)}")
    
    return lower_bound <= angle <= upper_bound

# Check if the finger is extended based on direction (3D)
def is_finger_extended(tip, pip, mcp):
    # Calculate the vector direction between each consecutive pair of landmarks
    vec_tip_pip = (tip.x - pip.x, tip.y - pip.y, tip.z - pip.z)
    vec_pip_mcp = (pip.x - mcp.x, pip.y - mcp.y, pip.z - mcp.z)
    
    # Calculate the angle between the two vectors
    dot_product = vec_tip_pip[0] * vec_pip_mcp[0] + vec_tip_pip[1] * vec_pip_mcp[1] + vec_tip_pip[2] * vec_pip_mcp[2]
    magnitude_tip_pip = math.sqrt(vec_tip_pip[0]**2 + vec_tip_pip[1]**2 + vec_tip_pip[2]**2)
    magnitude_pip_mcp = math.sqrt(vec_pip_mcp[0]**2 + vec_pip_mcp[1]**2 + vec_pip_mcp[2]**2)
    
    # Calculate the angle between the vectors (in radians)
    cos_theta = dot_product / (magnitude_tip_pip * magnitude_pip_mcp)
    angle_between_vectors = math.acos(max(min(cos_theta, 1), -1))  # Clamp to [-1, 1] for precision errors
    
    # If the angle is large enough, the finger is extended
    return angle_between_vectors < math.pi / 4  # Threshold angle for an extended finger (45 degrees)

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
        canvas[:, :, :] = (255, 255, 255)
        
        # Dynamically calculate palette and slider positions
        palette_width = int(0.1 * width)  # Palette width is 10% of the frame width
        palette_height = int(0.1 * height)  # Each palette box height is 10% of the frame height
        palette_start_x = width - palette_width - 20  # Leave a margin of 20px from the right
        palette_start_y = 20  # Start from 20px margin at the top
        
        palette = [
            ((0, 0, 0), (palette_start_x, palette_start_y, palette_start_x + palette_width, palette_start_y + palette_height)),  # Black
            ((255, 0, 0), (palette_start_x, palette_start_y + palette_height + 10, palette_start_x + palette_width, palette_start_y + 2 * palette_height + 10)),  # Blue
            ((0, 255, 0), (palette_start_x, palette_start_y + 2 * (palette_height + 10), palette_start_x + palette_width, palette_start_y + 3 * palette_height + 20)),  # Green
            ((0, 0, 255), (palette_start_x, palette_start_y + 3 * (palette_height + 10), palette_start_x + palette_width, palette_start_y + 4 * palette_height + 30)),  # Red
            ((255, 255, 0), (palette_start_x, palette_start_y + 4 * (palette_height + 10), palette_start_x + palette_width, palette_start_y + 5 * palette_height + 40)),  # Yellow
            ((255, 255, 255), (palette_start_x, palette_start_y + 5 * (palette_height + 10), palette_start_x + palette_width, palette_start_y + 6 * palette_height + 50))  # White
        ]
        
        # Slider position
        slider_width = int(0.1 * width)  # Palette width is 10% of the frame width
        slider_height = int(0.2 * height)  # Each palette box height is 10% of the frame height
        slider_start_x = 20  # Leave a margin of 20px from the right
        slider_start_y = 20  # Start from 20px margin at the top
        
        slider_x1 = slider_start_x
        slider_y1 = slider_start_y
        slider_x2 = slider_start_x + palette_width
        slider_y2 = slider_y1 + slider_height  # Slider height is 100px
        slider_coords = (slider_x1, slider_y1, slider_x2, slider_y2)
    
    # Draw the color palette and slider
    draw_palette_and_slider(frame, brush_thickness, slider_coords)
    
    # Check if hands are detected
    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            # Get index finger tip coordinates (landmark 8)
            x, y = int(hand_landmarks.landmark[8].x * width), int(hand_landmarks.landmark[8].y * height)
            
            # Detect color selection
            selected_color = detect_color_selection(x, y)
            if selected_color:
                color = selected_color
                prev_x, prev_y = None, None  # Reset drawing to prevent accidental lines
            
            # Detect brush size adjustment
            if is_in_slider_area(x, y, slider_coords):
                brush_thickness = int(((y - slider_y1) / (slider_y2 - slider_y1)) * 50)
                brush_thickness = max(1, min(50, brush_thickness))  # Clamp between 1 and 50
                prev_x, prev_y = None, None  # Reset drawing to prevent accidental lines
            
            # Prevent drawing on the palette or slider
            if x >= palette_start_x or x <= slider_x2 or y <= 20 or y >= height - 20:  # Avoid drawing in the palette/slider area
                prev_x, prev_y = None, None
                continue
            
            
            # Get the landmarks for the thumb
            thumb_tip = hand_landmarks.landmark[4]  # Tip of the thumb
            thumb_ip = hand_landmarks.landmark[3]   # Interphalangeal joint (IP)
            thumb_mcp = hand_landmarks.landmark[2]  # Metacarpophalangeal joint (MCP)
            thumb_cmc = hand_landmarks.landmark[1]  # Carpometacarpal joint (CMC)
            
            # Check if the user wants to draw
            tip = hand_landmarks.landmark[8]
            pip = hand_landmarks.landmark[6]
            mcp = hand_landmarks.landmark[5]

            # print(is_finger_extended(tip, pip, mcp), is_thumb_pointer_perpendicular(thumb_tip, thumb_cmc, tip, mcp))
            if is_finger_extended(tip, pip, mcp) and not is_thumb_pointer_perpendicular(thumb_tip, thumb_cmc, tip, mcp):  # Finger raised
                if prev_x is None or prev_y is None:
                    prev_x, prev_y = x, y
                
                # Draw on the canvas
                cv2.line(canvas, (prev_x, prev_y), (x, y), color, brush_thickness)
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
>>>>>>> 509c5d0c2610bb5cf5c1d07584f41d2f3527010e
