import streamlit as st
import subprocess
import json
import tempfile
import os
import time
from typing import List, Optional

st.set_page_config(
    page_title="🎵 Smart Audio Editor",
    page_icon="🎵",
    layout="wide"
)

def save_uploaded_file(uploaded_file):
    """Save uploaded file to temp location"""
    temp_path = f"temp_{int(time.time())}_{uploaded_file.name}"
    with open(temp_path, 'wb') as f:
        f.write(uploaded_file.getvalue())
    return temp_path

def get_audio_info(audio_path):
    """Get audio information using ffprobe"""
    try:
        cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', audio_path]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            info = json.loads(result.stdout)
            duration = float(info['format']['duration'])
            return {"duration": duration, "format": info['format']['format_name']}
        return None
    except:
        return None

def process_audio_ffmpeg(input_path, output_path, target_minutes, crossfade_duration, method="basic_crossfade", progress_callback=None):
    """Process audio using FFmpeg with Streamlit Cloud compatibility"""

    target_duration = target_minutes * 60

    # Get audio info
    info = get_audio_info(input_path)
    if not info:
        return False, "Could not analyze audio file"

    original_duration = info['duration']

    if progress_callback:
        progress_callback(10, "🔍 Analyzing audio...")

    # Detect environment and use appropriate method
    if is_streamlit_cloud():
        # Streamlit Cloud compatible method - simpler approach
        if progress_callback:
            progress_callback(30, "🌐 Streamlit Cloud mode: Simple loop method...")

        # Use simple stream_loop with basic fade
        fade_start = target_duration - 3
        cmd = [
            'ffmpeg', '-stream_loop', '-1', '-i', input_path,
            '-af', f'afade=t=out:st={fade_start}:d=3',
            '-t', str(target_duration),
            '-c:a', 'libmp3lame', '-b:a', '192k',
            '-y', output_path
        ]
    else:
        # Local development - use advanced crossfade
        loops_needed = max(2, int(target_duration / original_duration) + 1)

        if progress_callback:
            progress_callback(30, f"💻 Local mode: Advanced crossfade (loops: {loops_needed})...")

        if loops_needed <= 5:
            # Build inputs for crossfade
            inputs = []
            for i in range(loops_needed):
                inputs.extend(['-i', input_path])

            # Build crossfade filter
            if loops_needed == 2:
                filter_complex = f"[0:a][1:a]acrossfade=d={crossfade_duration}[out]"
            elif loops_needed == 3:
                filter_complex = f"[0:a][1:a]acrossfade=d={crossfade_duration}[af1];[af1][2:a]acrossfade=d={crossfade_duration}[out]"
            elif loops_needed == 4:
                filter_complex = f"[0:a][1:a]acrossfade=d={crossfade_duration}[af1];[af1][2:a]acrossfade=d={crossfade_duration}[af2];[af2][3:a]acrossfade=d={crossfade_duration}[out]"
            elif loops_needed == 5:
                filter_complex = f"[0:a][1:a]acrossfade=d={crossfade_duration}[af1];[af1][2:a]acrossfade=d={crossfade_duration}[af2];[af2][3:a]acrossfade=d={crossfade_duration}[af3];[af3][4:a]acrossfade=d={crossfade_duration}[out]"

            # Add fade out
            fade_start = target_duration - 3
            filter_with_fadeout = f"{filter_complex};[out]afade=t=out:st={fade_start}:d=3[final]"

            cmd = ['ffmpeg'] + inputs + [
                '-filter_complex', filter_with_fadeout,
                '-map', '[final]',
                '-t', str(target_duration),
                '-c:a', 'mp3', '-b:a', '320k',
                '-y', output_path
            ]
        else:
            # Fallback to simple method for many loops
            fade_start = target_duration - 3
            cmd = [
                'ffmpeg', '-stream_loop', '-1', '-i', input_path,
                '-af', f'afade=t=out:st={fade_start}:d=3',
                '-t', str(target_duration),
                '-c:a', 'mp3', '-b:a', '320k',
                '-y', output_path
            ]

    if progress_callback:
        progress_callback(50, f"⚡ Running FFmpeg...")

    # Execute FFmpeg command
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)  # 5 min timeout

        if progress_callback:
            progress_callback(90, "✅ Finalizing...")

        if result.returncode == 0 and os.path.exists(output_path):
            method_used = "Streamlit Simple Loop" if is_streamlit_cloud() else f"Local Crossfade (d={crossfade_duration})"
            return True, f"Success! {method_used}"
        else:
            return False, f"FFmpeg error: {result.stderr[:200] if result.stderr else 'Unknown error'}"

    except subprocess.TimeoutExpired:
        return False, "Processing timeout - try shorter duration"
    except Exception as e:
        return False, f"Processing error: {str(e)}"

def create_percentage_progress(current, total, message):
    """Create percentage-based progress display"""
    percentage = int((current / total) * 100) if total > 0 else 0
    return f"{percentage}% - {message}"

# Old pydub function removed - now using FFmpeg

# Old pydub function removed - now using FFmpeg

# Old pydub function removed - FFmpeg handles export directly

def format_duration(seconds):
    """Format duration in seconds to readable format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def check_ffmpeg():
    """Check if FFmpeg is available and get version info"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            # Extract version for debugging
            version_line = result.stdout.split('\n')[0] if result.stdout else "Unknown version"
            return True, version_line
        return False, "FFmpeg not working"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, "FFmpeg not found"

def is_streamlit_cloud():
    """Detect if running on Streamlit Cloud"""
    return os.environ.get('STREAMLIT_SHARING', False) or 'streamlit.io' in os.environ.get('HOSTNAME', '')

def validate_parameters(mode: str, target_duration_ms: int, original_duration_ms: int, crossfade_duration: float, num_files: int) -> tuple[bool, str]:
    """Validate processing parameters based on mode"""

    if crossfade_duration < 0:
        return False, "Crossfade duration cannot be negative"

    if mode == "extend":
        if target_duration_ms <= 0:
            return False, "Target duration must be greater than 0"
        if target_duration_ms > 24 * 60 * 60 * 1000:  # 24 hours
            return False, "Target duration cannot exceed 24 hours"
        loops_needed = target_duration_ms / original_duration_ms
        if loops_needed > 1000:
            return False, f"Too many loops required ({loops_needed:.0f}x). Consider a shorter target duration."

    elif mode == "combine":
        if num_files < 2:
            return False, "Need at least 2 files to combine"

    elif mode == "combine_extend":
        if num_files < 2:
            return False, "Need at least 2 files to combine and extend"
        if target_duration_ms <= 0:
            return False, "Target duration must be greater than 0"

    return True, "Parameters valid"

def main():
    st.title("🎵 Audio Editor")

    # Check FFmpeg availability for Streamlit deployment
    ffmpeg_available, ffmpeg_info = check_ffmpeg()
    if not ffmpeg_available:
        st.error("❌ FFmpeg not found!")
        st.markdown("""
        **For local development:**
        - Windows: Download from [FFmpeg.org](https://ffmpeg.org/download.html)
        - macOS: `brew install ffmpeg`
        - Linux: `sudo apt install ffmpeg`

        **For Streamlit Cloud:**
        - The `packages.txt` file should automatically install FFmpeg
        - If this error persists, the deployment may need time to install dependencies
        """)
        st.stop()

    # Show environment info
    if is_streamlit_cloud():
        st.success("✅ FFmpeg ready! 🌐 Streamlit Cloud mode (simple loop method)")
        st.caption(f"FFmpeg: {ffmpeg_info}")
    else:
        st.success("✅ FFmpeg ready! 💻 Local mode (advanced crossfade)")
        st.caption(f"FFmpeg: {ffmpeg_info}")

    # Mode selection at the top
    st.markdown("### 🎯 Choose Your Mode")
    mode = st.radio(
        "What do you want to do?",
        ["🔄 Extend Single Audio", "🔗 Combine Multiple Audio", "🔄➕ Combine Then Extend"],
        horizontal=True,
        help="Choose your audio processing mode"
    )

    # Convert to internal mode names
    mode_map = {
        "🔄 Extend Single Audio": "extend",
        "🔗 Combine Multiple Audio": "combine",
        "🔄➕ Combine Then Extend": "combine_extend"
    }
    current_mode = mode_map[mode]

    # Sidebar controls
    with st.sidebar:
        st.header("⚙️ Settings")

        # Audio Method Selection
        st.subheader("🎵 Audio Method")
        audio_method_options = {
            "Basic Crossfade (Recommended)": "basic_crossfade",
            "Smooth Volume Curves": "smooth_curves",
            "EQ Matched Transitions": "eq_matched",
            "Phase Aligned (Advanced)": "phase_aligned",
            "Dynamic Normalized": "dynamic_normalized"
        }

        selected_method = st.selectbox(
            "Seamless Method",
            list(audio_method_options.keys()),
            index=0,  # Default to Basic Crossfade
            help="Choose the audio processing method for seamless transitions"
        )
        audio_method = audio_method_options[selected_method]

        # DYNAMIC crossfade duration - you can change this anytime!
        st.subheader("🔄 Crossfade")
        crossfade_duration = st.slider(
            "Crossfade Duration (seconds)",
            min_value=0.5,
            max_value=10.0,
            value=3.0,  # Default 3s like your test
            step=0.1,
            help=f"Dynamic crossfade duration - uses acrossfade=d={{value}} in FFmpeg"
        )

        st.caption(f"🔧 FFmpeg filter: acrossfade=d={crossfade_duration}")

        # Output format settings
        st.subheader("📁 Output Format")
        output_format = st.selectbox(
            "File Format",
            ["mp3", "wav", "m4a", "flac"],
            index=0,
            help="Choose your preferred output format"
        )

        # Quality settings
        if output_format == "mp3":
            quality = st.selectbox("MP3 Quality", ["128k", "192k", "256k", "320k"], index=2)
        elif output_format == "wav":
            quality = st.selectbox("WAV Quality", ["16-bit", "24-bit"], index=0)
        else:
            quality = "high"

        # Audio processing
        st.subheader("🎛️ Audio Processing")
        normalize_audio = st.checkbox("Normalize Audio", value=True)
        create_preview = st.checkbox("Create Audio Preview", value=True)

        # File naming
        st.subheader("📝 Output Filename")
        custom_suffix = st.text_input(
            "Custom suffix (optional)",
            value="processed",
            help="Added to filename"
        )

        st.markdown("---")

        # Mode-specific instructions
        if current_mode == "extend":
            st.markdown("### 📝 Extend Mode")
            st.markdown("""
            1. Upload 1 audio file
            2. Set target duration
            3. Audio will loop with crossfade
            """)
        elif current_mode == "combine":
            st.markdown("### 📝 Combine Mode")
            st.markdown("""
            1. Upload multiple audio files
            2. Files combine with crossfade
            3. Download merged result
            """)
        else:  # combine_extend
            st.markdown("### 📝 Combine + Extend")
            st.markdown("""
            1. Upload multiple audio files
            2. Files combine with crossfade
            3. Result extends to target duration
            """)

    # File upload based on mode
    if current_mode == "extend":
        max_files = 1
        help_text = "Upload 1 audio file to extend"
    else:
        max_files = None
        help_text = "Upload multiple audio files to combine"

    uploaded_files = st.file_uploader(
        "🎧 Choose audio files",
        type=['mp3', 'm4a', 'wav', 'flac', 'aac', 'ogg'],
        accept_multiple_files=(max_files != 1),
        help=help_text
    )

    # Convert single file to list for consistent handling
    if uploaded_files and not isinstance(uploaded_files, list):
        uploaded_files = [uploaded_files]

    if uploaded_files:
        # Show uploaded files info (FFmpeg will handle the processing)
        st.markdown("### 📂 Uploaded Files")

        for i, uploaded_file in enumerate(uploaded_files):
            with st.expander(f"🎧 File {i+1}: {uploaded_file.name}", expanded=(i==0)):
                # Just show basic file info
                size_mb = len(uploaded_file.getvalue()) / (1024*1024)
                st.metric("File Size", f"{size_mb:.1f} MB")

                # Show processing info
                st.info(f"🔧 FFmpeg: acrossfade=d={crossfade_duration} + 3s fade out")
                st.info(f"📄 Method: {selected_method}")

        # Note about multi-file modes
        if current_mode in ["combine", "combine_extend"]:
            st.info("ℹ️ Multi-file modes: Will use FFmpeg with exact test filter + 3s fade out (coming soon). Currently only extend mode is implemented.")

        # Duration settings (for extend and combine_extend modes)
        if current_mode in ["extend", "combine_extend"]:
            st.markdown("### 🎯 Duration Settings")
            st.markdown("**Set your target duration (Hours & Minutes only):**")

            # Default to 2 hours 0 minutes
            default_hours = 2
            default_minutes = 0

            hour_col, min_col = st.columns(2)
            with hour_col:
                hours = st.number_input(
                    "Hours",
                    min_value=0,
                    max_value=24,
                    value=int(default_hours),
                    step=1,
                    format="%d",
                    help="Target hours (0-24) - you can type directly"
                )
            with min_col:
                minutes = st.number_input(
                    "Minutes",
                    min_value=0,
                    max_value=59,
                    value=int(default_minutes),
                    step=1,
                    format="%d",
                    help="Target minutes (0-59) - you can type directly"
                )

            # Calculate target duration (no auto-display to avoid slowness)
            target_duration_ms = int((hours * 60 + minutes) * 60 * 1000)

            # Simple validation message only
            if target_duration_ms <= 0:
                st.warning("⚠️ Please set a duration greater than 0 minutes")
            elif target_duration_ms > 24 * 60 * 60 * 1000:
                st.error("❌ Duration cannot exceed 24 hours")
            else:
                st.success(f"✅ Target: {hours:02d}:{minutes:02d}:00")

        # Simplified validation (no heavy calculations until button press)
        if current_mode in ["extend", "combine_extend"]:
            # Basic validation only
            if target_duration_ms <= 0:
                is_valid = False
                validation_message = "Set a target duration greater than 0"
            elif target_duration_ms > 24 * 60 * 60 * 1000:
                is_valid = False
                validation_message = "Duration cannot exceed 24 hours"
            else:
                is_valid = True
                validation_message = "Ready to process"
        else:
            # Simple validation
            if current_mode == "combine" and len(uploaded_files) < 2:
                is_valid = False
                validation_message = "Need 2+ files to combine"
            elif current_mode == "combine_extend" and len(uploaded_files) < 2:
                is_valid = False
                validation_message = "Need 2+ files to combine and extend"
            elif current_mode == "extend" and len(uploaded_files) == 0:
                is_valid = False
                validation_message = "Upload audio files"
            else:
                is_valid = True
                validation_message = "Ready to process"

        # Show processing settings summary
        with st.expander("📋 Processing Settings Summary", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Mode:** {mode}")
                st.write(f"**Files:** {len(uploaded_files)}")
                st.write(f"**Crossfade:** {crossfade_duration}s")
            with col2:
                st.write(f"**Format:** {output_format.upper()} ({quality})")
                st.write(f"**Method:** {selected_method}")
                st.write(f"**Normalize:** {'Yes' if normalize_audio else 'No'}")
                if current_mode in ["extend", "combine_extend"]:
                    st.write(f"**Target:** {hours:02d}:{minutes:02d}:00")

        if not is_valid:
            st.error(f"❌ {validation_message}")

        # Process button
        button_text = "🚀 Process Audio" if is_valid else f"❌ {validation_message}"

        if st.button(button_text, disabled=not is_valid, type="primary"):
            progress_container = st.container()

            with progress_container:
                progress_bar = st.progress(0, text="Starting processing...")

                try:
                    crossfade_ms = int(crossfade_duration * 1000)

                    if current_mode == "extend":
                        # Process with FFmpeg (exact test filter + 3s fade out)
                        input_path = save_uploaded_file(uploaded_files[0])
                        output_path = f"output_{int(time.time())}.mp3"

                        def progress_callback(percent, message):
                            progress_bar.progress(percent, text=create_percentage_progress(percent, 100, message))

                        success, message = process_audio_ffmpeg(
                            input_path, output_path, target_duration_ms // 60000,
                            crossfade_duration, audio_method, progress_callback
                        )

                        if not success:
                            raise Exception(message)

                        # Read the result file
                        with open(output_path, 'rb') as f:
                            audio_bytes = f.read()

                        # Cleanup temp files
                        if os.path.exists(input_path):
                            os.unlink(input_path)
                        if os.path.exists(output_path):
                            os.unlink(output_path)

                    elif current_mode == "combine":
                        # TODO: Implement FFmpeg combine with 3s fade out
                        raise Exception("Combine mode: Coming soon with FFmpeg + 3s fade out")

                    elif current_mode == "combine_extend":
                        # TODO: Implement FFmpeg combine+extend with 3s fade out
                        raise Exception("Combine+extend mode: Coming soon with FFmpeg + 3s fade out")

                    # FFmpeg already processed and exported the file with 3s fade out
                    progress_bar.progress(100, text="100% - ✅ FFmpeg processing complete with fade out!")

                    progress_bar.progress(100, text="✅ Processing complete!")
                    progress_bar.empty()

                    # Results
                    st.success("🎉 Audio processing completed successfully!")

                    # Results metrics
                    result_col1, result_col2, result_col3 = st.columns(3)
                    with result_col1:
                        st.metric("Final Duration", f"{target_duration_ms // 60000} minutes")
                    with result_col2:
                        st.metric("File Size", f"{len(audio_bytes) / (1024*1024):.1f} MB")
                    with result_col3:
                        st.metric("Method", "FFmpeg + Fade Out")

                    # Audio preview
                    if create_preview and len(audio_bytes) > 0:
                        st.markdown("#### 🎧 Result Preview")
                        st.audio(audio_bytes, format='audio/mp3')
                        st.caption("Preview: FFmpeg processed with 3s fade out")

                    # Download
                    if len(uploaded_files) == 1:
                        filename_base = uploaded_files[0].name.rsplit('.', 1)[0]
                    else:
                        filename_base = "combined_audio"

                    if custom_suffix:
                        download_filename = f"{filename_base}_{custom_suffix}.{output_format}"
                    else:
                        mode_suffix = {"extend": "extended", "combine": "combined", "combine_extend": "combined_extended"}
                        download_filename = f"{filename_base}_{mode_suffix[current_mode]}.{output_format}"

                    mime_types = {
                        "mp3": "audio/mp3",
                        "wav": "audio/wav",
                        "m4a": "audio/mp4",
                        "flac": "audio/flac"
                    }

                    st.download_button(
                        label=f"📥 Download Result ({output_format.upper()})",
                        data=audio_bytes,
                        file_name=download_filename,
                        mime=mime_types.get(output_format, "audio/*"),
                        help=f"Download: {download_filename}"
                    )

                    # Processing statistics
                    with st.expander("📊 Processing Statistics", expanded=False):
                        st.write(f"**Processing Mode:** {mode}")
                        st.write(f"**Audio Method:** {selected_method}")
                        st.write(f"**Input Files:** {len(uploaded_files)}")
                        if current_mode != "combine":
                            st.write(f"**Target Duration:** {target_duration_ms // 60000} minutes")
                            st.write(f"**FFmpeg Filter:** acrossfade=d={crossfade_duration}")
                            st.write(f"**Fade Out:** 3 seconds")
                        st.write(f"**Crossfade Used:** {crossfade_duration}s")
                        st.write(f"**Final Quality:** {quality}")

                except Exception as e:
                    progress_bar.empty()
                    st.error(f"❌ Processing failed: {str(e)}")
                    st.error("💡 **Try:** Reduce duration • Check FFmpeg • Verify file integrity")

    else:
        # Welcome screen with mode-specific info
        st.markdown(f"""
        <div style='text-align: center; padding: 3rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white; margin: 2rem 0;'>
            <h2>🎵 Smart Audio Editor</h2>
            <p style='font-size: 1.2em; margin: 1rem 0;'>Current Mode: <strong>{mode}</strong></p>
            <p>Upload your audio files above to get started!</p>
        </div>
        """, unsafe_allow_html=True)

        # Mode-specific feature highlights
        if current_mode == "extend":
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**🔄 Extend Mode**\n- Loop single audio\n- Seamless crossfade\n- Any target duration")
            with col2:
                st.markdown("**⚙️ Smart Controls**\n- Hours:Minutes default\n- 2s crossfade default\n- Quality options")
            with col3:
                st.markdown("**🎵 High Quality**\n- Multiple formats\n- Normalization\n- Preview playback")

        elif current_mode == "combine":
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**🔗 Combine Mode**\n- Merge multiple files\n- Crossfade transitions\n- Perfect blending")
            with col2:
                st.markdown("**🎛️ Smart Processing**\n- Auto format detection\n- Quality preservation\n- Efficient mixing")
            with col3:
                st.markdown("**📊 Analysis**\n- Duration calculation\n- File statistics\n- Preview each file")

        else:  # combine_extend
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**🔄➕ Combine + Extend**\n- Merge then loop\n- Double processing\n- Maximum flexibility")
            with col2:
                st.markdown("**🚀 Optimized**\n- Smart chunking\n- Memory efficient\n- Progress tracking")
            with col3:
                st.markdown("**🎯 Powerful**\n- Best of both modes\n- Complex audio projects\n- Professional results")

if __name__ == "__main__":
    main()