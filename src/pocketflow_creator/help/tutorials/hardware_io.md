# Tutorial: Hardware I/O Nodes — Serial, Audio, Video, and Webcam

**What you'll learn:** Use Hardware I/O nodes to interact with USB serial devices, microphones, speakers, cameras, and webcams.

**Prerequisites:** Tutorial 2 (Your First Flow), Tutorial 22 (Standalone Scripts)

---

## Hardware I/O Node Categories

PocketFlow Creator includes 7 Hardware I/O node types:

| Node Type | Purpose | Requires |
|-----------|---------|----------|
| **USB Serial Input** | Read data from serial port (e.g., Arduino, sensor) | `pyserial` |
| **USB Serial Output** | Send data to serial port | `pyserial` |
| **Audio Input** | Record audio from microphone | `sounddevice`, `soundfile` |
| **Audio Output** | Play audio from speaker | `sounddevice`, `soundfile` |
| **Video Input** | Record video from camera | `opencv-python` |
| **Video Output** | Play video file | `opencv-python` |
| **Webcam** | Capture frame or stream from webcam | `opencv-python` |

---

## Example 1: Read from USB Serial (Arduino)

### Scenario
You have an Arduino connected via USB that reports temperature readings every second.

### Setup

1. **New Project** → `arduino_monitor`
2. **Create flow** → `read_temperature.pfcgraph.yaml`
3. **Add nodes:**
   - **Start** node
   - **USB Serial Input** node (center)
   - **Log** node (right)
   - **Stop** node (far right)

4. **Wire edges:**
   - Start → USB Serial Input
   - USB Serial Input → Log
   - Log → Stop

5. **Configure USB Serial Input** (Object Inspector):
   - `port`: `/dev/ttyUSB0` (or `COM3` on Windows)
   - `baudrate`: `9600`
   - `output_key`: `temperature_raw`

6. **Configure Log** node:
   - `input_key`: `temperature_raw`
   - `log_level`: `info`

### Run

```bash
python exports/arduino_monitor/standalone/read_temperature_standalone.py

# Output:
# INFO in Log Node: 23.5C
```

---

## Example 2: Record Audio from Microphone

### Scenario
Record a 5-second audio clip, save it to a file, then play it back.

### Setup

1. **New Project** → `voice_recorder`
2. **Create flow** → `record_and_play.pfcgraph.yaml`
3. **Add nodes:**
   - **Start** node
   - **Audio Input** node (left)
   - **Audio Output** node (right)
   - **Stop** node (far right)

4. **Wire edges:**
   - Start → Audio Input
   - Audio Input → Audio Output
   - Audio Output → Stop

5. **Configure Audio Input** (Object Inspector):
   - `duration`: `5.0` (seconds)
   - `sample_rate`: `16000` (Hz)
   - `output_file`: `recording.wav`
   - `output_key`: `audio_file`

6. **Configure Audio Output**:
   - `input_key`: `audio_file`
   - `output_key`: `status`

### Run

```bash
python exports/voice_recorder/standalone/record_and_play_standalone.py

# Records 5 seconds from microphone → saves to recording.wav
# Then plays recording.wav back through speaker
```

---

## Example 3: Capture Webcam and Send to LLM

### Scenario
Take a screenshot from webcam, send it to Claude for image analysis.

### Setup

1. **New Project** → `webcam_analyzer`
2. **Create flow** → `analyze_webcam.pfcgraph.yaml`
3. **Add nodes:**
   - **Start** node
   - **Webcam** node (left)
   - **Image Vision** node (center) — requires Anthropic provider
   - **Log** node (right)
   - **Stop** node (far right)

4. **Wire edges:**
   - Start → Webcam
   - Webcam → Image Vision
   - Image Vision → Log
   - Log → Stop

5. **Configure Webcam** (Object Inspector):
   - `operation`: `capture` (single frame)
   - `output_file`: `frame.jpg`
   - `output_key`: `image_path`

6. **Configure Image Vision**:
   - `image_path_key`: `image_path`
   - `task`: `describe what you see`
   - `output_key`: `description`
   - Set provider to Anthropic (Tools > Provider Manager)

7. **Configure Log**:
   - `input_key`: `description`

### Run

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python exports/webcam_analyzer/standalone/analyze_webcam_standalone.py

# Output:
# INFO in Log Node: "I can see a desk with a laptop, keyboard, and monitor..."
```

---

## Example 4: Video Recording with Duration Limit

### Scenario
Record 10 seconds of video from the camera.

### Setup

1. **New Project** → `video_capture`
2. **Create flow** → `record_video.pfcgraph.yaml`
3. **Add nodes:**
   - **Start** node
   - **Video Input** node (center)
   - **Stop** node (right)

4. **Wire:**
   - Start → Video Input → Stop

5. **Configure Video Input** (Object Inspector):
   - `duration`: `10.0` (seconds)
   - `output_file`: `output.mp4`
   - `output_key`: `video_path`

### Run

```bash
python exports/video_capture/standalone/record_video_standalone.py

# Records 10 seconds of video from camera to output.mp4
```

---

## Example 5: Serial Communication Loop (Arduino ↔ Creator)

### Scenario
Continuously read sensor data from Arduino, process it, and send commands back.

### Setup

1. **New Project** → `bidirectional_serial`
2. **Create flow** → `arduino_control.pfcgraph.yaml`
3. **Add nodes:**
   - **Start** node
   - **USB Serial Input** node (reads sensor)
   - **Condition** node (checks if temp > threshold)
   - **USB Serial Output** node (sends control command)
   - **Log** node
   - **Stop** node

4. **Wire edges:**
   - Start → USB Serial Input
   - USB Serial Input → Condition (route: `default`)
   - Condition → USB Serial Output (action: `true`)
   - USB Serial Output → Log
   - Log → Stop

5. **Configure USB Serial Input**:
   - `port`: `/dev/ttyUSB0`
   - `baudrate`: `9600`
   - `output_key`: `sensor_reading`

6. **Configure Condition**:
   - `input_key`: `sensor_reading`
   - `condition`: `float(input) > 25.0` (route to `true` if temp > 25°C)

7. **Configure USB Serial Output**:
   - `input_key`: `command` (value to send)
   - `output_key`: `status`

### Run

```bash
python exports/bidirectional_serial/standalone/arduino_control_standalone.py

# Reads: "23.5"
# Condition: False (≤ 25)
#
# Reads: "26.2"
# Condition: True (> 25)
# Sends: "FAN_ON" to Arduino
```

---

## Installation of Optional Dependencies

By default, Creator includes only stdlib imports. Hardware nodes require optional libraries:

### For USB Serial
```bash
pip install pyserial
```

### For Audio (Input/Output)
```bash
pip install sounddevice soundfile
```

### For Video (Input/Output, Webcam)
```bash
pip install opencv-python
```

Once installed, Hardware I/O nodes work seamlessly in standalone scripts.

---

## Properties Reference

### **USB Serial Input**
| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `port` | string | `/dev/ttyUSB0` | Serial port path (e.g., `/dev/ttyUSB0`, `COM3`) |
| `baudrate` | integer | `9600` | Baud rate (9600, 115200, etc.) |
| `output_key` | string | `data` | Shared store key for received data |

**Actions:** `default` (success), `timeout` (no data within 5 sec)

---

### **USB Serial Output**
| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `port` | string | `/dev/ttyUSB0` | Serial port path |
| `baudrate` | integer | `9600` | Baud rate |
| `input_key` | string | `data` | Shared store key for data to send |
| `output_key` | string | `status` | Shared store key for status |

**Actions:** `default` (success), `error`

---

### **Audio Input**
| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `duration` | float | `5.0` | Recording duration (seconds) |
| `sample_rate` | integer | `16000` | Sample rate (Hz) |
| `output_file` | string | `recording.wav` | Output WAV file path |
| `output_key` | string | `audio_file` | Shared store key for file path |

**Actions:** `default` (success), `error`

---

### **Audio Output**
| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `input_key` | string | `audio_file` | Shared store key for audio file path |
| `output_key` | string | `status` | Shared store key for status |

**Actions:** `default` (success), `error`

---

### **Video Input**
| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `duration` | float | `5.0` | Recording duration (seconds) |
| `output_file` | string | `recording.mp4` | Output MP4 file path |
| `output_key` | string | `video_file` | Shared store key for file path |

**Actions:** `default` (success), `error`

---

### **Video Output**
| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `input_key` | string | `video_file` | Shared store key for video file path |
| `output_key` | string | `status` | Shared store key for status |

**Actions:** `default` (success), `error`

---

### **Webcam**
| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `operation` | string | `capture` | `capture` (single frame) or `stream` (multiple frames) |
| `frame_count` | integer | `30` | Frames to capture in stream mode |
| `output_file` | string | `frame.jpg` | Output file path for captured frame |
| `output_key` | string | `image` | Shared store key for output |

**Actions:** `default` (success), `error`

---

## Tips and Best Practices

### **Serial Communication**
- Always check the correct port: `ls /dev/tty*` (Mac/Linux) or Device Manager (Windows)
- Verify baud rate matches your device (usually 9600 or 115200)
- Data is read as a string; parse with **String Ops** or **Regex** node

### **Audio**
- Microphone input streams to WAV file (lossless)
- Specify duration carefully — recording will block until complete
- Test microphone permissions (`sudo` may be needed on Linux)

### **Video**
- Video recording uses your primary camera device
- Recording duration ties up the camera — no concurrent use
- MP4 codec assumes OpenCV ffmpeg support

### **Webcam**
- Capture mode returns a single frame (JPEG)
- Stream mode returns N frames as a list (useful for motion detection)
- Check camera permissions in System Preferences (macOS) or Privacy Settings (Windows)

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'serial'` | `pip install pyserial` |
| `Serial port not found` | Check device connection; verify port path with `ls /dev/tty*` |
| `No permission to access /dev/ttyUSB0` | `sudo usermod -a -G dialout $USER` (Linux) or run with `sudo` |
| `Microphone permission denied` | Check Privacy > Microphone (macOS) or Sound settings (Windows) |
| `Camera busy or not found` | Close other apps using camera; check device manager |

---

## Next Steps

- Combine Hardware I/O with **LLM** nodes for intelligent sensor processing
- Use **API Call** node to upload captured images to cloud services
- Create flows that bridge IoT devices and AI services
- Deploy as standalone scripts to Raspberry Pi or other edge devices

