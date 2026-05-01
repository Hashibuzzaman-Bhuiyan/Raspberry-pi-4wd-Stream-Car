import cv2
from flask import Flask, render_template, Response, request, jsonify
import RPi.GPIO as GPIO
import threading

# Initialize Flask app
app = Flask(__name__)

# GPIO Pins
PIN_IN1M = 27
PIN_IN2M = 22
PIN_IN3M = 24
PIN_IN4M = 23

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_IN1M, GPIO.OUT)
GPIO.setup(PIN_IN2M, GPIO.OUT)
GPIO.setup(PIN_IN3M, GPIO.OUT)
GPIO.setup(PIN_IN4M, GPIO.OUT)

# Initialize video capture
cap = cv2.VideoCapture(0)

# Streaming control variables
streaming = False
streaming_lock = threading.Lock()


# GPIO control functions
def stop():
    GPIO.output(PIN_IN1M, GPIO.LOW)
    GPIO.output(PIN_IN2M, GPIO.LOW)
    GPIO.output(PIN_IN3M, GPIO.LOW)
    GPIO.output(PIN_IN4M, GPIO.LOW)


def forward():
    GPIO.output(PIN_IN1M, GPIO.LOW)
    GPIO.output(PIN_IN2M, GPIO.HIGH)
    GPIO.output(PIN_IN3M, GPIO.LOW)
    GPIO.output(PIN_IN4M, GPIO.HIGH)


def backward():
    GPIO.output(PIN_IN1M, GPIO.HIGH)
    GPIO.output(PIN_IN2M, GPIO.LOW)
    GPIO.output(PIN_IN3M, GPIO.HIGH)
    GPIO.output(PIN_IN4M, GPIO.LOW)


def left():
    GPIO.output(PIN_IN1M, GPIO.HIGH)
    GPIO.output(PIN_IN2M, GPIO.LOW)
    GPIO.output(PIN_IN3M, GPIO.LOW)
    GPIO.output(PIN_IN4M, GPIO.HIGH)


def right():
    GPIO.output(PIN_IN1M, GPIO.LOW)
    GPIO.output(PIN_IN2M, GPIO.HIGH)
    GPIO.output(PIN_IN3M, GPIO.HIGH)
    GPIO.output(PIN_IN4M, GPIO.LOW)


# Video streaming generator
def generate_frames():
    global streaming
    while True:
        with streaming_lock:
            if not streaming:
                continue

        success, frame = cap.read()
        if not success:
            break

        # Rotate the frame by 180 degrees
        frame = cv2.rotate(frame, cv2.ROTATE_180)

        # Mirror the frame horizontally
        frame = cv2.flip(frame, 1)

        # Encode the frame in JPEG format
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        # Yield the frame in HTTP response format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


# Flask routes
@app.route('/')
def index():
    return render_template('index.html')  # Serve the HTML page


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/start_stream', methods=['POST'])
def start_stream():
    global streaming
    with streaming_lock:
        streaming = True
    return jsonify({'success': True})


@app.route('/stop_stream', methods=['POST'])
def stop_stream():
    global streaming
    with streaming_lock:
        streaming = False
    return jsonify({'success': True})


@app.route('/move', methods=['POST'])
def move():
    command = request.form['command']
    if command == 'w':
        forward()
    elif command == 's':
        backward()
    elif command == 'a':
        left()
    elif command == 'd':
        right()
    elif command == 'q':
        stop()
    return '', 200


if __name__ == '__main__':
    try:
        print("Starting the web server...")
        app.run(host='0.0.0.0', port=5000, threaded=True, debug=False)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        # Stop GPIO and release camera
        stop()
        GPIO.cleanup()
        cap.release()
        cv2.destroyAllWindows()




