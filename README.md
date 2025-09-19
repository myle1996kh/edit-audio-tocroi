# 🎵 Audio Editor

A streamlined Streamlit app for extending audio duration with seamless FFmpeg-powered crossfades.

## Features

- 🎵 **Multi-format Support**: MP3, M4A, WAV, FLAC, AAC, OGG
- 🔄 **Seamless Extend**: FFmpeg crossfade with exact filter control
- 📤 **Multi-file Upload**: Upload multiple files for batch processing
- ⏱️ **Flexible Duration**: Set hours & minutes directly
- 🎭 **Auto Fade Out**: 3-second fade out on all outputs
- 📊 **Progress Tracking**: Real-time percentage progress
- 🎧 **Audio Preview**: Instant playback of results
- ⚙️ **Clean Interface**: Minimal UI with collapsible settings

## Installation

1. **Install Python** (3.8 or higher recommended)

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install FFmpeg** (required for audio processing):
   - **Windows**: Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg`

## Usage

1. **Run the application**:
   ```bash
   streamlit run app.py
   ```

2. **Open your browser** to `http://localhost:8501`

3. **Upload audio files** (supports multiple files)

4. **Set target duration** using hours & minutes inputs

5. **Adjust settings** (click ⚙️ Settings to expand):
   - **Method**: Choose crossfade type (Basic, Smooth, EQ Matched, etc.)
   - **Crossfade Duration**: Transition length (default: 3s)
   - **Format**: MP3 or WAV output

6. **Click Process** and download your seamless extended audio

## How It Works

Uses FFmpeg with exact filter specifications:

1. **FFmpeg Crossfade**: `acrossfade=d={duration}` filter for seamless loops
2. **Auto Fade Out**: 3-second fade out automatically added
3. **Multiple Methods**: Basic, Smooth Curves, EQ Matched, Phase Aligned, Dynamic Normalized
4. **Real-time Progress**: Percentage-based progress tracking

## Examples

- **30-second clip** → **2-hour background music** with seamless transitions
- **Short jingle** → **Extended presentation audio** with professional fade out
- **Multiple files** → **Batch processing** with consistent quality

## Audio Methods

- **Basic Crossfade**: Simple, smooth dissolve (recommended)
- **Smooth Curves**: Gradual volume fade curves
- **EQ Matched**: Frequency response matched transitions
- **Phase Aligned**: Advanced phase-aware crossfading
- **Dynamic Normalized**: Volume-optimized processing

## Requirements

- **Python 3.8+**
- **FFmpeg** (for audio processing)
- **Streamlit** (for web interface)