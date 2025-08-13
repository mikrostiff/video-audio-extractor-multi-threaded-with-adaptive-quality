#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video Audio Extraction Script
Batch extract audio from video files using ffmpeg, with resume support and parallel processing
"""

import os
import subprocess
import sys
import json
import shutil
import re
from pathlib import Path
import argparse
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
import time
import signal
import atexit
import logging
import threading


# Thread-safe print lock
print_lock = threading.Lock()

# Monkey patch print function for thread-safe output
import builtins
original_print = builtins.print

def safe_print(*args, **kwargs):
    """Thread-safe print function"""
    with print_lock:
        original_print(*args, **kwargs)

# Replace the built-in print with our safe version
builtins.print = safe_print

# Configure logging for clean, thread-safe output
logging.basicConfig(
    level=logging.INFO,
    format='[%(threadName)s] %(message)s',
    datefmt='%H:%M:%S'
)

# Global variables for signal handling
current_record_file = None
current_record = {}


def signal_handler(signum, frame):
    """Signal handler to ensure records are saved"""
    if current_record_file and current_record:
        logging.info(f"\nSaving interrupt record to {current_record_file}...")
        save_extraction_record(current_record_file, current_record)
    sys.exit(0)


def atexit_handler():
    """Handler function when program exits"""
    if current_record_file and current_record:
        save_extraction_record(current_record_file, current_record)


def get_video_audio_bitrate(video_path):
    """Get audio bitrate from video file"""
    try:
        # Use ffprobe to get audio information
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_streams', '-select_streams', 'a:0', video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if 'streams' in data and len(data['streams']) > 0:
                stream = data['streams'][0]
                
                # Try to get bitrate information
                if 'bit_rate' in stream:
                    # Direct bitrate
                    bitrate = int(stream['bit_rate'])
                    return bitrate
                elif 'tags' in stream and 'BPS' in stream['tags']:
                    # Get bitrate from tags
                    bitrate = int(stream['tags']['BPS'])
                    return bitrate
                elif 'tags' in stream and 'bit_rate' in stream['tags']:
                    # Get bitrate from tags
                    bitrate = int(stream['tags']['bit_rate'])
                    return bitrate
                
                # If no bitrate info, try to estimate from sample rate and channels
                if 'sample_rate' in stream and 'channels' in stream:
                    sample_rate = int(stream['sample_rate'])
                    channels = int(stream['channels'])
                    # Estimate bitrate (assuming 16-bit sampling)
                    estimated_bitrate = sample_rate * channels * 16
                    return estimated_bitrate
        
        # If unable to get, return None
        return None
        
    except Exception as e:
        logging.info(f"Failed to get audio bitrate for {os.path.basename(video_path)}: {e}")
        return None


def get_adaptive_quality(video_path, target_quality, audio_format, worker_id=None, log_message=None):
    """Adaptively set extraction quality based on video audio bitrate"""
    print(f"[Worker {worker_id}] Analyzing video: {os.path.basename(video_path)}")
    print(f"[Worker {worker_id}] Target quality: {target_quality}, Audio format: {audio_format}")
    
    original_bitrate = get_video_audio_bitrate(video_path)
    
    if original_bitrate is None:
        print(f"[Worker {worker_id}] Cannot detect audio bitrate, using target quality: {target_quality}")
        return target_quality
    
    print(f"[Worker {worker_id}] Detected original audio bitrate: {original_bitrate} bps ({original_bitrate//1000}k)")
    
    # Convert target quality to bps
    target_bps = parse_quality_to_bps(target_quality)
    
    if target_bps is None:
        print(f"[Worker {worker_id}] Cannot parse target quality '{target_quality}', using target quality")
        return target_quality
    
    print(f"[Worker {worker_id}] Target quality converted to: {target_bps} bps")
    
    # If target bitrate is higher than original audio bitrate, use original audio bitrate
    if target_bps > original_bitrate:
        print(f"[Worker {worker_id}] Target bitrate {target_bps} bps is higher than original audio bitrate {original_bitrate} bps, will adjust")
        
        # Choose appropriate bitrate based on audio format
        if audio_format == 'mp3':
            # MP3 bitrate selection
            if original_bitrate <= 66000:
                adaptive_quality = '64k'
            elif original_bitrate <= 98000:
                adaptive_quality = '96k'
            elif original_bitrate <= 130000:
                adaptive_quality = '128k'
            elif original_bitrate <= 196000:
                adaptive_quality = '192k'
            else:
                adaptive_quality = '256k'
        elif audio_format == 'aac':
            # AAC bitrate selection
            if original_bitrate <= 66000:
                adaptive_quality = '64k'
            elif original_bitrate <= 98000:
                adaptive_quality = '96k'
            elif original_bitrate <= 130000:
                adaptive_quality = '128k'
            elif original_bitrate <= 196000:
                adaptive_quality = '192k'
            else:
                adaptive_quality = '256k'
        else:
            # Keep original bitrate for other formats
            adaptive_quality = f"{original_bitrate // 1000}k"
        
        print(f"[Worker {worker_id}] Adaptive quality adjusted to: {adaptive_quality}")
        return adaptive_quality
    else:
        print(f"[Worker {worker_id}] Target bitrate {target_bps} bps is appropriate, keeping target quality: {target_quality}")
        return target_quality


def parse_quality_to_bps(quality_str):
    """Convert quality string to bps value"""
    try:
        # Match common quality formats: 64k, 128k, 192k, 320k, etc.
        match = re.match(r'(\d+)k?', quality_str.lower())
        if match:
            value = int(match.group(1))
            if quality_str.lower().endswith('k'):
                return value * 1000
            else:
                return value * 1000
        return None
    except:
        return None


def load_extraction_record(record_file):
    """Load extraction record"""
    if os.path.exists(record_file):
        try:
            with open(record_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_extraction_record(record_file, record):
    """Save extraction record"""
    try:
        with open(record_file, 'w', encoding='utf-8') as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
            # pass
    except Exception as e:
        logging.error(f"Failed to save record: {e}")


def move_video_files_to_original(video_files, original_dir):
    """Move video files from root directory to original folder"""
    moved_files = []
    
    for video_file in video_files:
        # Check if file is in root directory (using absolute path comparison)
        current_dir = os.getcwd()
        file_dir = os.path.dirname(video_file)
        
        if file_dir == current_dir:
            # File is in root directory, need to move
            filename = os.path.basename(video_file)
            new_path = os.path.join(original_dir, filename)
            
            try:
                shutil.move(video_file, new_path)
                moved_files.append(new_path)
                logging.info(f"Moved: {filename} -> {original_dir}/")
            except Exception as e:
                logging.info(f"Failed to move file {filename}: {e}")
                # If move fails, use original path
                moved_files.append(video_file)
        else:
            # File is not in root directory, keep original path
            moved_files.append(video_file)
    
    return moved_files


def move_completed_file_to_done(video_file, original_dir, log_message=None):
    """Move completed video files to original/done folder"""
    try:
        filename = os.path.basename(video_file)
        done_dir = os.path.join(original_dir, 'done')
        
        # Ensure done folder exists
        os.makedirs(done_dir, exist_ok=True)
        
        # Move file
        new_path = os.path.join(done_dir, filename)
        shutil.move(video_file, new_path)
        print(f"Moved completed file: {filename} -> {done_dir}/")
        return True
    except Exception as e:
        print(f"Failed to move completed file {filename}: {e}")
        return False


def check_existing_audio_files(video_files, output_dir, audio_format):
    """Check existing audio files, even without JSON records"""
    existing_files = {}
    
    for video_file in video_files:
        video_name = Path(video_file).stem
        if audio_format == 'mp3':
            audio_file = os.path.join(output_dir, f"{video_name}.mp3")
        elif audio_format == 'aac':
            audio_file = os.path.join(output_dir, f"{video_name}.aac")
        elif audio_format == 'wav':
            audio_file = os.path.join(output_dir, f"{video_name}.wav")
        elif audio_format == 'flac':
            audio_file = os.path.join(output_dir, f"{video_name}.flac")
        else:
            continue
            
        if os.path.exists(audio_file) and os.path.getsize(audio_file) > 0:
            existing_files[os.path.basename(video_file)] = {
                'status': 'completed',
                'output_file': audio_file,
                'audio_format': audio_format,
                'detected': 'auto',  # Mark as auto-detected
                'timestamp': str(Path(audio_file).stat().st_mtime)
            }
    
    return existing_files


def extract_audio_from_video_worker(args):
    """Worker process function for parallel processing"""
    video_path, output_dir, audio_format, quality, record_file, worker_id, original_dir, use_adaptive = args
    
    try:
        video_name = Path(video_path).stem
        original_quality = quality  # Save original quality for record
        
        # If adaptive quality is enabled, get appropriate bitrate
        if use_adaptive:
            print(f"[Worker {worker_id}] Analyzing audio bitrate for {video_name}...")
            adaptive_quality = get_adaptive_quality(video_path, quality, audio_format, worker_id, None)
            if adaptive_quality != quality:
                print(f"[Worker {worker_id}] Detected original audio bitrate, adjusting quality: {quality} -> {adaptive_quality}")
            quality = adaptive_quality
        else:
            print(f"[Worker {worker_id}] Using fixed quality: {quality}")
        
        if audio_format == 'mp3':
            output_file = os.path.join(output_dir, f"{video_name}.mp3")
            cmd = [
                'ffmpeg', '-i', video_path,
                '-vn', '-acodec', 'libmp3lame', '-ab', quality, '-y', output_file
            ]
        elif audio_format == 'aac':
            output_file = os.path.join(output_dir, f"{video_name}.aac")
            cmd = [
                'ffmpeg', '-i', video_path, '-vn', '-acodec', 'aac', '-b:a', quality, '-y', output_file
            ]
        elif audio_format == 'wav':
            output_file = os.path.join(output_dir, f"{video_name}.wav")
            cmd = [
                'ffmpeg', '-i', video_path, '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-y', output_file
            ]
        elif audio_format == 'flac':
            output_file = os.path.join(output_dir, f"{video_name}.flac")
            cmd = [
                'ffmpeg', '-i', video_path, '-vn', '-acodec', 'flac', '-y', output_file
            ]
        else:
            return False, f"Unsupported audio format: {audio_format}"
        
        print(f"[Worker {worker_id}] Extracting: {video_name} (Final quality: {quality})")
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        
        if result.returncode == 0:
            print(f"[Worker {worker_id}] ✓ Successfully extracted: {video_name}")
            # Move file to done folder after successful extraction
            # move_completed_file_to_done(video_path, original_dir, None)
            # Return success status and actual quality used
            return True, (video_name, quality, original_quality)
        else:
            error_msg = f"Extraction failed: {video_name}"
            if result.stderr:
                error_msg += f" - {result.stderr}"
            print(f"[Worker {worker_id}] ✗ {error_msg}")
            return False, error_msg
            
    except Exception as e:
        error_msg = f"Error processing file {video_path}: {str(e)}"
        print(f"[Worker {worker_id}] ✗ {error_msg}")
        return False, error_msg


def extract_audio_from_video(video_path, output_dir, audio_format='mp3', quality='192k', record_file=None, original_dir=None, use_adaptive=False):
    """Extract audio from video file (single process version, backward compatible)"""
    result = extract_audio_from_video_worker((video_path, output_dir, audio_format, quality, record_file, 0, original_dir, use_adaptive))
    if isinstance(result, tuple) and len(result) == 2:
        success, data = result
        if success and isinstance(data, tuple) and len(data) == 3:
            return success, data[1]  # Return success status and actual quality used
        return success, None
    return result, None


def get_video_files(directory):
    """Get all video files in directory"""
    video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
    video_files = []
    
    if not os.path.exists(directory):
        logging.info(f"Directory {directory} does not exist")
        return []
    
    for file_path in Path(directory).iterdir():
        if file_path.is_file() and file_path.suffix.lower() in video_extensions:
            video_files.append(str(file_path))
    
    return video_files


def get_video_files_from_root():
    """Get all video files in root directory"""
    video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
    video_files = []
    
    current_dir = os.getcwd()
    for file_path in Path(current_dir).iterdir():
        if file_path.is_file() and file_path.suffix.lower() in video_extensions:
            # Use absolute path
            video_files.append(str(file_path.absolute()))
    
    return video_files


def main():
    global current_record_file, current_record
    
    parser = argparse.ArgumentParser(description='Batch extract audio from video files with resume support and parallel processing')
    parser.add_argument('-d', '--directory', default='./original', 
                       help='Video files directory (default: ./original)')
    parser.add_argument('-o', '--output', default='./extracted_audio',
                       help='Audio output directory (default: ./extracted_audio)')
    parser.add_argument('-f', '--format', default='mp3', 
                       choices=['mp3', 'aac', 'wav', 'flac'],
                       help='Audio format (default: mp3)')
    parser.add_argument('-q', '--quality', default='192k',
                       help='Audio quality (default: 192k)')
    parser.add_argument('--adaptive', action='store_true',
                       help='Enable adaptive quality: automatically adjust extraction quality based on original video audio bitrate')
    parser.add_argument('--no-resume', action='store_true',
                       help='Disable resume functionality')
    parser.add_argument('-j', '--jobs', type=int, default=0,
                       help='Number of parallel jobs (default: auto-detect CPU cores)')
    parser.add_argument('--sequential', action='store_true',
                       help='Use sequential processing mode (disable parallel)')
    
    args = parser.parse_args()
    
    # 设置信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    atexit.register(atexit_handler)
    
    # Check if ffmpeg is installed
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logging.error("Error: ffmpeg or ffprobe not found. Please ensure ffmpeg is installed and added to system PATH.")
        sys.exit(1)
    
    # Ensure original folder exists
    os.makedirs(args.directory, exist_ok=True)
    
    # Check if there are video files in root directory, if so move them to original folder
    root_video_files = get_video_files_from_root()
    if root_video_files:
        logging.info(f"Found {len(root_video_files)} video files in root directory, moving to {args.directory} folder...")
        moved_files = move_video_files_to_original(root_video_files, args.directory)
        logging.info(f"File move completed!")
    
    # Get video file list
    video_files = get_video_files(args.directory)
    
    if not video_files:
        logging.error(f"No video files found in directory {args.directory}")
        logging.error("Please ensure video files are placed in this directory")
        sys.exit(1)
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Resume functionality - record file saved in root directory
    record_file = None
    pending_files = video_files
    completed_files = []
    
    if not args.no_resume:
        # Record file saved in root directory
        record_file = f"extraction_record_{args.format}.json"
        current_record_file = record_file
        
        # Load JSON record
        record = load_extraction_record(record_file)
        current_record = record.copy()
        
        # Detect existing audio files (even without JSON records)
        auto_detected = check_existing_audio_files(video_files, args.output, args.format)
        
        # Merge records
        for filename, info in auto_detected.items():
            if filename not in record:
                record[filename] = info
                current_record[filename] = info
        
        # Filter completed files
        pending_files = []
        for video_file in video_files:
            video_name = os.path.basename(video_file)
            if video_name in record and record[video_name]['status'] == 'completed':
                completed_files.append(video_file)
            else:
                pending_files.append(video_file)
    
    logging.info(f"Found {len(video_files)} video files:")
    logging.info(f"  - Completed: {len(completed_files)}")
    logging.info(f"  - Pending: {len(pending_files)}")
    
    if completed_files:
        logging.info("\nCompleted files:")
        for video_file in completed_files:
            video_name = os.path.basename(video_file)
            info = current_record.get(video_name, {})
            if info.get('detected') == 'auto':
                logging.info(f"  ✓ {video_name} (auto-detected)")
            else:
                logging.info(f"  ✓ {video_name}")
    
    if pending_files:
        logging.info("\nPending files:")
        for video_file in pending_files:
            video_name = os.path.basename(video_file)
            logging.info(f"  - {video_name}")
    
    logging.info(f"\nAudio will be saved to: {args.output}")
    logging.info(f"Audio format: {args.format}")
    logging.info(f"Audio quality: {args.quality}")
    
    if args.adaptive:
        logging.info("Adaptive quality: Enabled (automatically adjust based on original video audio bitrate)")
    else:
        logging.info("Adaptive quality: Disabled (use fixed quality)")
    
    if not args.no_resume:
        logging.info(f"Resume functionality: Enabled (record file: {record_file})")
        logging.info("Smart detection: Automatically detect existing audio files")
    else:
        logging.info("Resume functionality: Disabled")
    
    # Determine parallel task count
    if args.sequential:
        max_workers = 1
        logging.info("Parallel processing: Disabled (sequential mode)")
    else:
        if args.jobs > 0:
            max_workers = args.jobs
        else:
            max_workers = min(multiprocessing.cpu_count(), len(pending_files))
        logging.info(f"Parallel processing: Enabled (using {max_workers} parallel tasks)")
    
    if not pending_files:
        logging.info("\nAll files have been processed!")
        return
    
    # Confirm whether to continue
    # response = input(f"\nStart processing {len(pending_files)} pending files? (y/N): ").strip().lower()
    # if response not in ['y', 'yes']:
    #     print("Operation cancelled")
    #     sys.exit(0)
    
    # Batch extract audio
    logging.info("\nStarting audio extraction...")
    start_time = time.time()
    
    if max_workers == 1:
        # Sequential processing
        success_count = 0
        total_count = len(pending_files)
        
        for i, video_file in enumerate(pending_files, 1):
            logging.info(f"\n[{i}/{total_count}] ", end="")
            success, actual_quality = extract_audio_from_video(video_file, args.output, args.format, args.quality, record_file, args.directory, args.adaptive)
            if success:
                success_count += 1
                # Update record in real-time
                if record_file:
                    video_name = os.path.basename(video_file)
                    # Use actual quality used, not original set quality
                    quality_for_record = actual_quality if actual_quality else args.quality
                    current_record[video_name] = {
                        'status': 'completed',
                        'output_file': os.path.join(args.output, f"{Path(video_file).stem}.{args.format}"),
                        'audio_format': args.format,
                        'quality': quality_for_record,
                        'timestamp': str(time.time())
                    }
                    save_extraction_record(record_file, current_record)
    else:
        # Parallel processing
        success_count = 0
        total_count = len(pending_files)
        
        tasks = []
        for i, video_file in enumerate(pending_files):
            tasks.append((video_file, args.output, args.format, args.quality, record_file, i + 1, args.directory, args.adaptive))
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_to_task = {executor.submit(extract_audio_from_video_worker, task): task for task in tasks}
            
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    success, result = future.result()
                    if success:
                        success_count += 1
                        # Update record in real-time
                        if record_file:
                            video_name = os.path.basename(task[0])
                            # Get actual quality used from result
                            actual_quality = args.quality  # Default to original quality
                            if isinstance(result, tuple) and len(result) == 3:
                                actual_quality = result[1]  # Get actual quality used
                            
                            current_record[video_name] = {
                                'status': 'completed',
                                'output_file': os.path.join(args.output, f"{Path(task[0]).stem}.{args.format}"),
                                'audio_format': args.format,
                                'quality': actual_quality,
                                'timestamp': str(time.time())
                            }
                            save_extraction_record(record_file, current_record)
                except Exception as e:
                    logging.error(f"Task execution exception: {e}")
    
    # Calculate processing time
    end_time = time.time()
    processing_time = end_time - start_time
    
    # Output result statistics
    logging.info(f"\n=== Extraction Complete! ===")
    logging.info(f"This run successful: {success_count}/{total_count}")
    logging.info(f"Total completed: {len(completed_files) + success_count}/{len(video_files)}")
    logging.info(f"Processing time: {processing_time:.2f} seconds")
    if max_workers > 1:
        logging.info(f"Average per file: {processing_time/len(pending_files):.2f} seconds")
    logging.info(f"Audio files saved to: {os.path.abspath(args.output)}")
    logging.info(f"Completed video files moved to: {os.path.abspath(os.path.join(args.directory, 'done'))}")
    
    if record_file:
        logging.info(f"Extraction record saved to: {os.path.abspath(record_file)}")


if __name__ == "__main__":
    main() 