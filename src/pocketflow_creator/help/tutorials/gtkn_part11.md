# Part 11 — Voice, Audio, and Document Nodes

This part covers five nodes that handle audio transcription, speech synthesis, PDF
extraction, image understanding, and data validation.

**Prerequisite:** Complete Part 1 (Start / Stop / Basic) before this part.

---

## Tutorial T-N36: Speech to Text Node

### What it does

The **Speech to Text Node** transcribes an audio file (WAV, MP3, FLAC, OGG) into a
text string using a speech recognition model. The audio file path is read from the
shared store, and the transcript is written back under `output_key`.

### Use cases

- Transcribing recorded meetings or voice memos before summarising with an LLM
- Building voice-command flows where the input is spoken rather than typed
- Processing audio from IoT devices for real-time transcription pipelines

### What you'll build

A flow — **Start → AudioTranscriber → Stop** — that transcribes a short audio
clip and stores the result.

### Step-by-step

**Step 1: Create project `gtkn_part11`.**

**Step 2: Drag a Speech to Text Node** named `AudioTranscriber`.

**Step 3: Set Inspector properties:**

| Property | Value |
|---|---|
| `audio_key` | `audio_file` |
| `output_key` | `transcript` |
| `model` | `whisper` |
| `language` | `en` |

**Step 4: Wire Start → AudioTranscriber → Stop.**

**Step 5: Paste the code:**

```python
from pocketflow import Node

class AudioTranscriber(Node):
    def prep(self, shared):
        return shared.get("audio_file", "meeting_clip.wav")

    def exec(self, prep_res):
        audio_path = prep_res
        # Production: call Whisper API or local whisper model.
        # Simulation: return a canned transcript.
        return (
            "Welcome everyone. Today's agenda covers three topics: "
            "the Q2 roadmap, the hiring plan, and the infrastructure migration. "
            "Let's start with the roadmap."
        )

    def post(self, shared, prep_res, exec_res):
        shared["transcript"] = exec_res
        return "default"
```

**Step 6: Run and inspect `transcript` in the Shared Store tab.**

### What you learned

- Speech to Text Nodes abstract the transcription API — swap `model` from `whisper` to `google` or `azure` without changing flow logic
- `language` is optional; omitting it enables automatic language detection
- The plain-text transcript flows naturally into an LLM node for summarisation or classification

---

## Tutorial T-N37: Text to Speech Node

### What it does

The **Text to Speech Node** synthesises an audio file from a text string. A voice ID
and output format (MP3, WAV, OGG) are configured in the Inspector. The file is written
to the path stored under `output_path_key`.

### Use cases

- Generating spoken responses for a voice assistant flow
- Creating audio versions of articles or reports
- Providing accessibility output for visually impaired users

### What you'll build

Reverse the previous flow: a Text to Speech Node that reads the `transcript` key and
writes an audio file.

### Step-by-step

**Step 1: Add a Text to Speech Node** named `SpeechSynth` (you can reuse or extend the
previous flow).

**Step 2: Set Inspector properties:**

| Property | Value |
|---|---|
| `text_key` | `summary` |
| `output_path_key` | `audio_output` |
| `voice` | `en-US-Neural2-F` |
| `format` | `mp3` |

**Step 3: Paste the code:**

```python
import os
from pocketflow import Node

class SpeechSynth(Node):
    OUTPUT_FILE = "output_speech.mp3"

    def prep(self, shared):
        return shared.get("summary", "No summary available.")

    def exec(self, prep_res):
        text = prep_res
        # Production: call ElevenLabs, Google TTS, or pyttsx3.
        # Simulation: write a placeholder file and return its path.
        output_path = self.OUTPUT_FILE
        with open(output_path, "wb") as f:
            f.write(b"MP3_PLACEHOLDER")   # real output would be PCM/MP3 bytes
        return output_path

    def post(self, shared, prep_res, exec_res):
        shared["audio_output"] = exec_res
        return "default"
```

**Step 4: Run and check:**

```
audio_output: "output_speech.mp3"
```

### What you learned

- Text to Speech Nodes write a file and store its path — downstream nodes or the host application can play or serve the file
- `voice` IDs are provider-specific; the node abstracts the API call
- Chain a Speech to Text → LLM Summariser → Text to Speech for a full voice-in/voice-out pipeline

---

## Tutorial T-N38: PDF Extract Node

### What it does

The **PDF Extract Node** reads a PDF file and returns its text content, either as a
single string or as a list of per-page strings. Metadata (title, author, page count)
is also extracted and stored separately.

### Use cases

- Extracting text from reports or research papers before LLM analysis
- Building document Q&A systems from a PDF knowledge base
- Archiving contract text in searchable format

### What you'll build

A flow that extracts text from a two-page PDF and stores both the full text and
per-page content.

### Step-by-step

**Step 1: Add a PDF Extract Node** named `PDFReader`.

**Step 2: Set Inspector properties:**

| Property | Value |
|---|---|
| `file_key` | `pdf_path` |
| `output_key` | `pdf_text` |
| `pages_key` | `pdf_pages` |
| `metadata_key` | `pdf_meta` |

**Step 3: Wire Start → PDFReader → Stop.**

**Step 4: Paste the code:**

```python
from pocketflow import Node

class PDFReader(Node):
    def prep(self, shared):
        return shared.get("pdf_path", "report.pdf")

    def exec(self, prep_res):
        # Production: use PyMuPDF (fitz) or pdfplumber.
        pages = [
            "Page 1: Executive Summary. Revenue grew 18% YoY to $4.2M.",
            "Page 2: Details. SaaS ARR increased by $650K; churn dropped to 3%.",
        ]
        return {
            "full_text": "\n\n".join(pages),
            "pages": pages,
            "metadata": {
                "title": "Q1 Financial Report",
                "author": "Finance Team",
                "page_count": len(pages),
            },
        }

    def post(self, shared, prep_res, exec_res):
        shared["pdf_text"] = exec_res["full_text"]
        shared["pdf_pages"] = exec_res["pages"]
        shared["pdf_meta"] = exec_res["metadata"]
        return "default"
```

**Step 5: Inspect the Shared Store.** You will see `pdf_text`, `pdf_pages` (list), and
`pdf_meta` (dict with title, author, page_count).

### What you learned

- PDF Extract Nodes separate metadata from content — both are useful for different downstream nodes
- `pages_key` stores a per-page list, enabling page-level chunking in a subsequent Text Chunk Node
- Feed `pdf_text` directly into an LLM Prompt Node using `{{pdf_text}}` interpolation

---

## Tutorial T-N39: Image Vision Node

### What it does

The **Image Vision Node** sends an image file (or URL) to a multimodal LLM and returns
the model's natural-language description or answer to a question about the image.
Both the image path and the question are sourced from the shared store.

### Use cases

- Describing product images for catalogue generation
- Extracting structured data from scanned forms or invoices
- Moderating user-uploaded images for policy violations

### What you'll build

A flow that describes what is shown in an image and answers "Are there any people
in the image?"

### Step-by-step

**Step 1: Add an Image Vision Node** named `ImageAnalyser`.

**Step 2: Set Inspector properties:**

| Property | Value |
|---|---|
| `image_key` | `image_path` |
| `prompt_key` | `vision_prompt` |
| `output_key` | `vision_result` |
| `model` | _(leave empty — uses mock provider)_ |

**Step 3: Wire Start → ImageAnalyser → Stop.**

**Step 4: Paste the code:**

```python
from pocketflow import Node

class ImageAnalyser(Node):
    def prep(self, shared):
        return {
            "image": shared.get("image_path", "photo.jpg"),
            "prompt": shared.get(
                "vision_prompt",
                "Describe this image. Are there any people in it?",
            ),
        }

    def exec(self, prep_res):
        # Production: encode image as base64 and call GPT-4o or Claude 3.
        image = prep_res["image"]
        prompt = prep_res["prompt"]
        return (
            f"The image '{image}' shows an outdoor park scene with green trees "
            "and a gravel path. Two people are visible walking in the background. "
            "Answer to your question: Yes, there are people in the image."
        )

    def post(self, shared, prep_res, exec_res):
        shared["vision_result"] = exec_res
        return "default"
```

**Step 5: Run and inspect `vision_result`.**

### What you learned

- Image Vision Nodes accept either a file path or a URL — the node normalises the input before the API call
- The `prompt_key` pattern lets you vary the question without changing the node — useful for multi-question flows
- Chain an Image Vision Node before a Classifier Node to tag images with categories

---

## Tutorial T-N40: Data Validate Node

### What it does

The **Data Validate Node** applies a JSON Schema (or a set of custom rules) to a value
in the shared store and routes to `valid` or `invalid` based on the result. On the
`invalid` path it also stores the list of validation errors so a downstream node can
fix or report them.

### Use cases

- Validating LLM-generated JSON before using it to call an API
- Ensuring required form fields are present before storing a record
- Gating expensive operations (e.g. embedding, SQL insert) behind a quality check

### What you'll build

A flow that validates a customer record dict against a minimal JSON Schema.

### Step-by-step

**Step 1: Add a Data Validate Node** named `RecordValidator`.

**Step 2: Declare actions:** `valid`, `invalid`.

**Step 3: Set Inspector properties:**

| Property | Value |
|---|---|
| `input_key` | `customer_record` |
| `errors_key` | `validation_errors` |
| `schema_key` | `record_schema` |

**Step 4: Wire:**

```
Start → RecordValidator →(valid)→ Stop_OK
RecordValidator →(invalid)→ Stop_Error
```

**Step 5: Paste the code:**

```python
from pocketflow import Node

SCHEMA = {
    "required": ["name", "email", "age"],
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "email": {"type": "string", "pattern": r".+@.+"},
        "age": {"type": "integer", "minimum": 0, "maximum": 150},
    },
}

class RecordValidator(Node):
    def prep(self, shared):
        return shared.get(
            "customer_record",
            {"name": "Alice", "email": "alice@example.com", "age": 30},
        )

    def exec(self, prep_res):
        errors = []
        record = prep_res
        for field in SCHEMA["required"]:
            if field not in record:
                errors.append(f"Missing required field: {field}")
        if "email" in record and "@" not in str(record["email"]):
            errors.append("email must contain @")
        if "age" in record and not (0 <= int(record["age"]) <= 150):
            errors.append("age must be between 0 and 150")
        return errors

    def post(self, shared, prep_res, exec_res):
        shared["validation_errors"] = exec_res
        return "invalid" if exec_res else "valid"
```

**Step 6: Run with the default record.** Routes to `Stop_OK`. Change `age` to `-5`
and re-run — it routes to `Stop_Error` and `validation_errors` lists the problem.

### What you learned

- Data Validate Nodes enforce quality gates without coupling validation logic to business logic
- Two-action routing (`valid`/`invalid`) makes the error path explicit and auditable
- The errors list enables self-healing flows where a downstream LLM node corrects the data and re-validates

---

[↑ Series Index](gtkn_index.md)
[← Part 10](gtkn_part10.md)
[→ Part 12: Code Execution Nodes](gtkn_part12.md)
