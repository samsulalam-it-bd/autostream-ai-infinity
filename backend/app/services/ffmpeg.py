import os
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

WATERMARK_PATH = os.getenv("WATERMARK_PATH", "/app/assets/watermark.png")
VIDEO_TMP_DIR = "/tmp/videos"


def create_text_overlay_image(text, w, h, output_path, tx, ty):
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new('RGBA', (int(w), int(h)), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font_size = int(h * 0.05) 
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()

    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    text_w = right - left
    text_h = bottom - top
    
    x = (w - text_w) * tx
    y = (h - text_h) * ty

    stroke_width = 3
    draw.text((x, y), text, font=font, fill="white", stroke_fill="black", stroke_width=stroke_width)
    img.save(output_path)

def get_video_dimensions(video_path):
    try:
        cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", video_path]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
        w, h = map(int, result.stdout.strip().split('x'))
        return w, h
    except:
        return 1920, 1080

def process_video(
    input_path: str, 
    add_watermark: bool = True,
    text_text: str = "",
    target_platform: str = "general",
    settings: dict = None

) -> str:
    """
    Video Uniquifier Engine using FFmpeg.
    Incorporates advanced Green Screen (Chroma Key) video/PNG overlays and Text overlays.
    """
    if settings is None:
        settings = {
            'width': 0.15, # Premium small watermark
            'height': 0.15,
            'x': 0.95,
            'y': 0.95,
            'tx': 0.50,
            'ty': 0.10
        }

    # Map named positions to coordinates
    position = settings.get('position', 'bottom-right')
    pos_map = {
        'top-left': (0.05, 0.05),
        'top-right': (0.95, 0.05),
        'bottom-left': (0.05, 0.95),
        'bottom-right': (0.95, 0.95),
    }
    coords = pos_map.get(position, (0.95, 0.95))
    pos_x, pos_y = coords


    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input video not found: {input_path}")

    # Ensure temporary directory exists
    Path(VIDEO_TMP_DIR).mkdir(parents=True, exist_ok=True)

    output_filename = f"processed_{input_path.stem}.mp4"
    output_path = Path(VIDEO_TMP_DIR) / output_filename
    
    is_image = WATERMARK_PATH.lower().endswith(('.png', '.jpg', '.jpeg'))
    chroma_hex = "0x00FF00"  # Default green screen hex
    temp_text_img = str(Path(VIDEO_TMP_DIR) / f"temp_text_{input_path.stem}.png")
    has_text = False

    if text_text:
        try:
            w, h = get_video_dimensions(str(input_path))
            create_text_overlay_image(text_text, w, h, temp_text_img, settings['tx'], settings['ty'])
            has_text = True
        except Exception as e:
            logger.error(f"Text overlay generation failed: {e}")
            has_text = False

    w_scale = settings.get('width', 0.15)
    h_scale = settings.get('height', 0.15)


    cmd = ["ffmpeg", "-y", "-i", str(input_path)]

    watermark_exists = add_watermark and Path(WATERMARK_PATH).exists()

    if watermark_exists:
        if is_image:
            cmd.extend(["-loop", "1", "-i", WATERMARK_PATH])
        else:
            cmd.extend(["-stream_loop", "-1", "-i", WATERMARK_PATH])

    if has_text:
        cmd.extend(["-loop", "1", "-i", temp_text_img])

    filter_parts = []
    
    # 1. Uniquifier (crop + brightness shift) + Smart Reformatting
    # We always do a tiny crop and brightness shift to avoid copyright hash detection.
    base_filter = "crop=iw-1:ih-1,eq=brightness=0.01"
    
    # 2. Platform Specific Aspect Ratio Adjustment (9:16 for Reels/Shorts)
    if target_platform.lower() in ["instagram", "youtube_shorts", "facebook_reels"]:
        # Logic: If video is wider than 9:16, we scale and crop to 9:16.
        # Or better: "Blurred background" style if it's horizontal.
        # For simplicity, we'll use a "smart crop to center 9:16" or "pad with blur".
        # Let's do: scale to height, then crop width to 9:16.
        reformat_filter = "scale=ih*9/16:ih,crop=iw:ih"
        filter_parts.append(f"[0:v]{base_filter},{reformat_filter}[base]")
    else:
        filter_parts.append(f"[0:v]{base_filter}[base]")

    map_out = "[base]"

    curr_v = "[base]"
    input_idx = 1

    if watermark_exists:
        wm_idx = input_idx
        input_idx += 1
        
        if is_image:
            filter_parts.append(f"[{wm_idx}:v]{curr_v}scale2ref=w=iw*{w_scale}:h=ih*{h_scale}[logo_sized][video_ref]")
        else:
            filter_parts.append(f"[{wm_idx}:v]colorkey={chroma_hex}:0.3:0.2[logo_clean]")
            filter_parts.append(f"[logo_clean]{curr_v}scale2ref=w=iw*{w_scale}:h=ih*{h_scale}[logo_sized][video_ref]")

        filter_parts.append(f"[logo_sized]setsar=1[logo_final]")
        filter_parts.append(f"[video_ref][logo_final]overlay=x='(W-w)*{pos_x}':y='(H-h)*{pos_y}':shortest=1[v_wm]")
        curr_v = "[v_wm]"
        map_out = curr_v

    if has_text:
        txt_idx = input_idx
        filter_parts.append(f"{curr_v}[{txt_idx}:v]overlay=0:0[v_out]")
        map_out = "[v_out]"

    if filter_parts:
        filter_str = ";".join(filter_parts)
        cmd.extend(["-filter_complex", filter_str, "-map", map_out])
    else:
        cmd.extend(["-vf", "crop=iw-1:ih-1,eq=brightness=0.01"])

    cmd.extend([
        "-map_metadata", "-1", 
        "-map", "0:a?",
        "-c:v", "libx264", 
        "-preset", "fast", 
        "-crf", "23",
        "-c:a", "aac", 
        "-b:a", "128k",
        "-movflags", "+faststart",
        str(output_path)
    ])

    logger.info(f"Running FFmpeg: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600,
        )

        if result.returncode != 0:
            logger.error(f"FFmpeg STDERR: {result.stderr}")
            raise RuntimeError(f"FFmpeg failed with code {result.returncode}: {result.stderr[-500:]}")

        logger.info(f"FFmpeg processing complete. Output: {output_path}")
        
        if has_text and os.path.exists(temp_text_img):
            os.remove(temp_text_img)
            
        return str(output_path)

    except subprocess.TimeoutExpired:
        raise RuntimeError("FFmpeg processing timed out after 1 hour.")


def extract_frames(video_path: str, num_frames: int = 3) -> list[str]:
    """
    Extract N evenly-spaced frames from a video as JPEG images.
    Returns a list of paths to the extracted frame images.
    Used by the Gemini AI analysis step.
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    frame_dir = Path(VIDEO_TMP_DIR) / f"frames_{video_path.stem}"
    frame_dir.mkdir(parents=True, exist_ok=True)

    # Get video duration using ffprobe
    probe_cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        str(video_path)
    ]
    probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=30)

    duration = 60.0  # Default fallback
    try:
        import json
        probe_data = json.loads(probe_result.stdout)
        duration = float(probe_data["format"].get("duration", 60.0))
    except Exception:
        pass

    # Calculate evenly-spaced timestamps
    interval = duration / (num_frames + 1)
    timestamps = [interval * (i + 1) for i in range(num_frames)]

    frame_paths = []
    for i, ts in enumerate(timestamps):
        frame_path = frame_dir / f"frame_{i:02d}.jpg"
        extract_cmd = [
            "ffmpeg",
            "-y",
            "-ss", str(ts),
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(frame_path),
        ]
        result = subprocess.run(extract_cmd, capture_output=True, timeout=30)
        if result.returncode == 0 and frame_path.exists():
            frame_paths.append(str(frame_path))
        else:
            logger.warning(f"Failed to extract frame at {ts}s")

    return frame_paths


def get_video_duration(video_path: str) -> Optional[float]:
    """Get the duration of a video file in seconds."""
    try:
        probe_cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            video_path
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=30)
        import json
        data = json.loads(result.stdout)
        return float(data["format"].get("duration", 0))
    except Exception:
        return None


def cleanup_tmp_files(*paths: str) -> None:
    """Delete temporary files from the server after upload is complete."""
    for path in paths:
        try:
            p = Path(path)
            if p.is_file():
                p.unlink()
                logger.info(f"Cleaned up file: {path}")
            elif p.is_dir():
                import shutil
                shutil.rmtree(path)
                logger.info(f"Cleaned up directory: {path}")
        except Exception as e:
            logger.warning(f"Could not clean up {path}: {e}")
