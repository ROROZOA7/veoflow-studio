"""
Video Processor Service - FFmpeg operations for video stitching
"""

import subprocess
import os
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Handles video processing with FFmpeg"""
    
    def stitch_scenes(
        self,
        scene_paths: List[str],
        output_path: str,
        transition: str = "fade",
        transition_duration: float = 0.5
    ) -> str:
        """
        Stitch multiple scene videos into one final video.
        
        Args:
            scene_paths: List of paths to scene video files
            output_path: Output file path
            transition: Transition type (fade, cut, slide, etc.)
            transition_duration: Transition duration in seconds
        
        Returns:
            Path to output video file
        """
        if transition == "cut":
            return self.concat_videos(scene_paths, output_path)
        elif transition == "fade":
            return self.concat_with_fade(scene_paths, output_path, transition_duration)
        else:
            return self.concat_videos(scene_paths, output_path)
    
    def concat_videos(self, scene_paths: List[str], output_path: str) -> str:
        """Simple video concatenation without transitions."""
        concat_file = self._create_concat_file(scene_paths)
        
        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
            output_path
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            os.remove(concat_file)
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr.decode()}")
            raise
    
    def concat_with_fade(
        self,
        scene_paths: List[str],
        output_path: str,
        fade_duration: float
    ) -> str:
        """Concatenate videos with fade transitions."""
        # For simplicity, use concat with fade filter
        # This is a basic implementation - can be enhanced
        
        # First, get video durations
        durations = [self.get_video_duration(path) for path in scene_paths]
        
        # Build filter complex for fade transitions
        filter_parts = []
        inputs = []
        
        for i, path in enumerate(scene_paths):
            inputs.extend(["-i", path])
            
            if i == 0:
                # First video: fade out
                filter_parts.append(
                    f"[{i}:v]fade=t=out:st={durations[i]-fade_duration}:d={fade_duration}[v{i}out]"
                )
            elif i == len(scene_paths) - 1:
                # Last video: fade in
                filter_parts.append(
                    f"[{i}:v]fade=t=in:st=0:d={fade_duration}[v{i}in]"
                )
            else:
                # Middle videos: fade in and out
                filter_parts.append(
                    f"[{i}:v]fade=t=in:st=0:d={fade_duration},"
                    f"fade=t=out:st={durations[i]-fade_duration}:d={fade_duration}[v{i}]"
                )
        
        # Concatenate
        concat_inputs = "".join([f"[v{i}]" for i in range(len(scene_paths))])
        filter_parts.append(f"{concat_inputs}concat=n={len(scene_paths)}:v=1[outv]")
        
        filter_complex = ";".join(filter_parts)
        
        cmd = [
            "ffmpeg",
            *inputs,
            "-filter_complex", filter_complex,
            "-map", "[outv]",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            output_path
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg fade error: {e.stderr.decode()}")
            # Fallback to simple concat
            return self.concat_videos(scene_paths, output_path)
    
    def _create_concat_file(self, scene_paths: List[str]) -> str:
        """Create FFmpeg concat file."""
        concat_file = "/tmp/concat_list.txt"
        with open(concat_file, "w") as f:
            for path in scene_paths:
                abs_path = os.path.abspath(path)
                f.write(f"file '{abs_path}'\n")
        return concat_file
    
    def get_video_duration(self, video_path: str) -> float:
        """Get video duration in seconds."""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except:
            return 5.0  # Default duration if can't detect

