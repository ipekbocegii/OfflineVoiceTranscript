import os

# --- Configuration Load and FFmpeg Path Setup ---
try:
    # Attempt to load the personal FFmpeg path from local_config.py (ignored by Git)
    from local_config import FFMPEG_BIN_PATH as ffmpeg_bin

    if not os.path.isdir(ffmpeg_bin):
        # Warning if path is invalid, falls back to system PATH
        print(f"WARNING: Invalid path in local_config. Falling back to system PATH.")
    else:
        # If valid, prepend the FFmpeg directory to the system PATH
        os.environ["PATH"] = ffmpeg_bin + os.pathsep + os.environ.get("PATH", "")
except ImportError:
    # This runs for users who cloned the repo (no local_config.py)
    print("WARNING: local_config.py not found. Ensure FFmpeg is installed and added to your system PATH.")

from pydub import AudioSegment
import whisper


def transcribe_audio_file(
        file_path,
        output_file=None,
        chunk_duration=60,
        model_name="small",
        on_progress=None,
        on_status=None,
):
    # Resolve file path: Check absolute path, then relative to the script's directory
    if not os.path.isabs(file_path) and not os.path.exists(file_path):
        script_dir = os.path.dirname(__file__)
        candidate = os.path.join(script_dir, file_path)
        if os.path.exists(candidate):
            file_path = candidate

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found at: {file_path}")

    # If no output file is specified, create a .txt file next to the input file
    if output_file is None:
        input_dir = os.path.dirname(file_path)
        input_base = os.path.splitext(os.path.basename(file_path))[0]
        output_file = os.path.join(input_dir, f"{input_base}.txt") if input_dir else f"{input_base}.txt"

    # Status update: Loading audio
    status_message = "Loading audio file…"
    if on_status:
        try:
            on_status(status_message)
        except Exception:
            pass
    else:
        print(status_message)

    try:
        # Load audio using pydub, specifying format for robustness (assuming m4a from your example)
        audio = AudioSegment.from_file(file_path, format="m4a")
    except Exception as e:
        raise Exception(f"Failed to load audio file. Ensure FFmpeg is working and the format is correct: {str(e)}")

    # Calculate chunks
    chunk_length_ms = chunk_duration * 1000
    total_chunks = (len(audio) + chunk_length_ms - 1) // chunk_length_ms

    status_message = f"Total {total_chunks} chunks detected."
    if on_status:
        try:
            on_status(status_message)
        except Exception:
            pass
    else:
        print(status_message)

    # Status update: Loading model
    status_message = f"Loading Whisper '{model_name}' model…"
    if on_status:
        try:
            on_status(status_message)
        except Exception:
            pass
    else:
        print(status_message)
    model = whisper.load_model(model_name)

    full_text = ""
    for idx, start in enumerate(range(0, len(audio), chunk_length_ms), start=1):
        # Slice the audio chunk
        chunk = audio[start:start + chunk_length_ms]
        temp_chunk_file = f"temp_chunk_{idx}.wav"

        # Export chunk for Whisper processing (Whisper prefers WAV)
        chunk.export(temp_chunk_file, format="wav")

        # Status update: Processing current chunk
        status_message = f"Processing chunk {idx} / {total_chunks}…"
        if on_status:
            try:
                on_status(status_message)
            except Exception:
                pass
        else:
            print(status_message)

        if on_progress:
            try:
                on_progress(total_chunks, idx - 1)
            except Exception:
                pass

        try:
            # Perform transcription on the temporary file, specifying Turkish language
            result = model.transcribe(temp_chunk_file, language="tr")
            full_text += result.get("text", "").strip() + " "
        except Exception as e:
            error_message = f"Error processing chunk {idx}: {e}"
            if on_status:
                try:
                    on_status(error_message)
                except Exception:
                    pass
            else:
                print(error_message)
        finally:
            # Clean up: Remove the temporary file regardless of success/failure
            if os.path.exists(temp_chunk_file):
                os.remove(temp_chunk_file)

        if on_progress:
            try:
                on_progress(total_chunks, idx)
            except Exception:
                pass

    # Write the final combined text to the output file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(full_text)

    status_message = f"Transcription saved to '{output_file}'."
    if on_status:
        try:
            on_status(status_message)
        except Exception:
            pass
    else:
        print(status_message)


if __name__ == "__main__":
    try:
        # Example usage: Change 'voice.m4a' to your test file path
        transcribe_audio_file("voice.m4a", chunk_duration=60, model_name="small")
    except Exception as e:
        print(f"An error occurred: {e}")