import cv2
import mediapipe as mp
import time
import random

# Constants required as per mediapipe
FINGER_IDS = {'INDEX': 8, 'MIDDLE': 12, 'RING': 16, 'PINKY': 20}
MOVES = ["Rock", "Paper", "Scissors"]
WIN_CONDITIONS = {"Rock": "Scissors", "Paper": "Rock", "Scissors": "Paper"}

# Helper Functions
def get_finger_status(hand_landmarks, finger_name):
    """Check if a finger is extended. Returns True of it's extended else false"""
    tip = hand_landmarks.landmark[FINGER_IDS[finger_name]].y
    mcp = hand_landmarks.landmark[FINGER_IDS[finger_name] - 2].y
    return tip < mcp

def get_thumb_status(hand_landmarks):
    """Check if the thumb is extended. Returns True of it's extended else false"""
    thumb_tip = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.THUMB_TIP].x
    thumb_ip = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.THUMB_IP].x
    thumb_mcp = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.THUMB_MCP].x
    return thumb_tip > thumb_ip > thumb_mcp

def detect_move(hand_landmarks):
    """Detect the player's move based on hand landmarks."""
    states = [
        "1" if get_thumb_status(hand_landmarks) else "0",
        "1" if get_finger_status(hand_landmarks, 'INDEX') else "0",
        "1" if get_finger_status(hand_landmarks, 'MIDDLE') else "0",
        "1" if get_finger_status(hand_landmarks, 'RING') else "0",
        "1" if get_finger_status(hand_landmarks, 'PINKY') else "0"
    ]
    gesture = "".join(states)
    return {
        "00000": "Rock",
        "11111": "Paper",
        "01100": "Scissors"
    }.get(gesture, "UNKNOWN")

def calculate_game_result(player_move):
    """Determine the game result."""
    computer_move = random.choice(MOVES)
    if player_move == computer_move:
        return 0, computer_move  # Draw
    if WIN_CONDITIONS[player_move] == computer_move:
        return 1, computer_move  # Player wins
    return -1, computer_move  # Player loses

# Main Game Function
def start_game():
    mp_drawing = mp.solutions.drawing_utils
    mp_hands = mp.solutions.hands
    capture = cv2.VideoCapture(0)

    # Game State Variables
    timer_started, hold_for_play = False, False
    game_over_text, computer_played = "", ""
    start_time, time_left_now = 0, 3

    with mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.4, max_num_hands=1) as hands:
        while True:
            ret, frame = capture.read()
            frame = cv2.flip(frame, 1)
            if not ret:
                break

            # Timer Logic
            if timer_started:
                elapsed = time.time() - start_time
                if elapsed >= 1:
                    time_left_now -= 1
                    start_time = time.time()
                    if time_left_now <= 0:
                        hold_for_play = True
                        timer_started = False

            # Hand Detection
            results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            player_move = "UNKNOWN"

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    player_move = detect_move(hand_landmarks)

            # Play Game
            if hold_for_play and player_move != "UNKNOWN":
                hold_for_play = False
                game_result, computer_move = calculate_game_result(player_move)
                computer_played = f"You: {player_move} | Computer: {computer_move}"
                game_over_text = ["It's a draw!", "You've won!", "You've lost!"][game_result]

            # Display Info
            cv2.putText(frame, game_over_text + " " + computer_played, (10, 450),
                        cv2.FONT_HERSHEY_COMPLEX, 0.75, (255, 255, 255), 2)
            label = "PLAY NOW!" if hold_for_play else f"STARTING IN {time_left_now}" if timer_started else "PRESS SPACE TO START!"
            cv2.putText(frame, label, (150, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 255), 2)

            # Show Frame
            cv2.imshow('Rock Paper Scissors!', frame)

            key = cv2.waitKey(1)
            if key == 32:  # Space Key
                timer_started, time_left_now = True, 3
                start_time = time.time()
            if key == 27:  # Escape Key
                break

    capture.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    start_game()