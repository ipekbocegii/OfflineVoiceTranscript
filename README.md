Offline Speech-to-Text (STT) Tool
This project provides a robust solution for converting audio files (such as meeting recordings or voice notes) into text with high accuracy. The key feature is that it works entirely offline using your local machine's power and the Whisper model. Your data never leaves your device, ensuring maximum privacy and security.

🌟 Key Features
100% Offline Operation: No internet connection is needed for transcription.

High Accuracy: Uses the powerful Whisper model developed by OpenAI.

Chunk Processing: Optimizes memory usage by dividing long audio files into manageable segments (chunks).

Multi-Format Support: Compatible with common audio formats like m4a, mp3, and wav (requires FFmpeg).

🚀 Installation and Setup
To run this project locally, you need Python 3.8 or higher and the FFmpeg library.

1. FFmpeg Installation (Mandatory)
The pydub library, which handles audio processing, relies on the external program FFmpeg.

Download the correct version of FFmpeg for your operating system from the FFmpeg official website.

You must add the bin folder from the downloaded FFmpeg package to your system's PATH environment variable. (The project will not work without FFmpeg correctly configured in your PATH.)

2. Cloning the Project
Download the project files to your local machine:

Bash

git clone https://github.com/YourUsername/OfflineSTTProject.git
cd OfflineSTTProject
3. Installing Python Dependencies
Install all necessary Python libraries listed in the requirements.txt file:

Bash

pip install -r requirements.txt
4. Usage
Run the main script, transcriber.py.py, with your audio file. The transcribed text will be saved as a new .txt file in the same folder.

Bash

python transcriber.py.py
NOTE: By default, the if __name__ == "__main__": block inside transcriber.py.py runs with a sample audio file (kocamuk.m4a). Please edit this block to use your own file.

🛠️ Core Function: ses_dosyasini_texte_cevir()
The entire transcription logic is contained within this function:

Python

def ses_dosyasini_texte_cevir(
    file_name,
    output_file=None,
    chunk_duration=60, # In seconds
    model_name="small", # Whisper model size: tiny, base, small, medium, large
    on_progress=None,
    on_status=None,
):
    # ... (code details)
    pass
🚧 Future Plans (Roadmap)
The long-term goal for this project is to evolve from a simple STT tool into a "Meeting Intelligence" application capable of automated analysis:

Meeting Summarization: Generating automatic summaries from the transcribed text.

Action Item Extraction: Automatically identifying decisions and tasks within the meeting text.

Speaker Diarization: Adding the ability to differentiate who spoke which part of the text.

🤝 Contributing
This project is open-source, and contributions are highly welcome. For bug reports, feature suggestions, and code contributions, please read the [CONTRIBUTING.md] guide.