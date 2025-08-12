# 🎵 Video Audio Extraction Tool

A batch video audio extraction tool with support for multiple audio formats, resume functionality, parallel processing, and adaptive quality.

## ✨ Main Features

### 🎯 Core Features
- **Multi-format Support**: MP3, AAC, WAV, FLAC
- **Batch Processing**: Support for processing large numbers of video files simultaneously
- **Resume Functionality**: Support for continuing processing after interruption
- **Parallel Processing**: Multi-process parallel extraction, significantly improving speed
- **Smart File Management**: Automatic file organization

### 🚀 New Features
- **Adaptive Quality**: Automatically adjust extraction quality based on original video audio bitrate
- **Automatic File Organization**: Automatically move video files from root directory to specified folders
- **Completed File Management**: Automatically move files to done folder after processing
- **Smart Bitrate Detection**: Automatically detect video audio bitrate and optimize extraction parameters

## 🛠️ System Requirements

- **Python 3.6+**
- **FFmpeg** (must be installed and added to system PATH)
- **FFprobe** (part of FFmpeg)

## 📦 Installation

1. Clone or download project files
2. Ensure FFmpeg is installed
3. Run the program

## 🚀 Usage

### 📁 **Where to Place Your Videos**

**Important**: Place your video files in the **project root directory** (same folder as `extract_audio.py`), or in ./original folder

### Method 1: Using Batch Files (Recommended)

#### **Step-by-Step Process:**
1. **Place video files** in the project root directory
2. **Double-click to run** one of these batch files:
   - `extract_audio.bat` - Default 192k + adaptive
   - `extract_audio_128k.bat` - 128k quality + adaptive  
   - `extract_audio_320k.bat` - 320k quality + adaptive
3. **Videos automatically move** to `./original/` folder
4. **Audio extracted** to `./extracted_audio/` folder
5. **Completed videos move** to `./original/done/` folder

#### Quick Start:
```bash
# Double-click to run
extract_audio.bat
```

### Method 2: Command Line

#### **Step-by-Step Process:**
1. **Place video files** in the project root directory
2. **Run command**:
   ```bash
   python extract_audio.py --adaptive
   ```
3. **Same automatic workflow** as batch files

#### Basic Usage:
```bash
# Default 192k quality + adaptive
python extract_audio.py --adaptive

# Specify 128k quality + adaptive
python extract_audio.py -q 128k --adaptive

# Specify 320k quality + adaptive
python extract_audio.py -q 320k --adaptive
```

#### Full Parameters:
```bash
python extract_audio.py \
    -d ./original \           # Video files directory
    -o ./extracted_audio \    # Audio output directory
    -f mp3 \                  # Audio format (mp3/aac/wav/flac)
    -q 128k \                 # Audio quality
    --adaptive \              # Enable adaptive quality
    --sequential              # Sequential processing mode
```

## 🎚️ Adaptive Quality Explanation

### How It Works
The program automatically detects the original video's audio bitrate and intelligently adjusts extraction quality:

- **Target Bitrate > Original Audio Bitrate** → Automatically downgrade to appropriate bitrate
- **Target Bitrate ≤ Original Audio Bitrate** → Maintain target bitrate

### Quality Selection Algorithm
| Original Audio Bitrate | MP3/AAC Output | Description |
|------------------------|----------------|-------------|
| ≤ 66k | 64k | Avoid meaningless high bitrate |
| ≤ 98k | 96k | Suitable for voice content |
| ≤ 130k | 128k | Standard music quality |
| ≤ 196k | 192k | High quality music |
| > 196k | 256k | Highest quality |

### Usage Examples
```bash
# Original audio 96k, target 320k → Automatically adjust to 96k
python extract_audio.py -q 320k --adaptive

# Original audio 256k, target 128k → Maintain 128k
python extract_audio.py -q 128k --adaptive
```

## 📁 File Structure Management

### Automatic File Organization
1. **On Startup**: Automatically detect video files in root directory
2. **Auto Move**: Move video files to `./original` folder
3. **After Processing**: Automatically move to `./original/done` folder

### Directory Structure
```
Project Root/
├── extract_audio.py          # Main program
├── extract_audio.bat         # Default configuration batch file
├── extract_audio_128k.bat    # 128k quality batch file
├── extract_audio_320k.bat    # 320k quality batch file
├── original/                 # Video files directory
│   ├── video1.mp4
│   ├── video2.avi
│   └── done/                 # Completed video files
├── extracted_audio/          # Audio output directory
│   ├── video1.mp3
│   └── video2.mp3
└── extraction_record_mp3.json # Extraction record file
```

## ⚙️ Advanced Options

### Parallel Processing
```bash
# Auto-detect CPU cores
python extract_audio.py --adaptive

# Specify parallel task count
python extract_audio.py --adaptive -j 4

# Sequential processing mode
python extract_audio.py --adaptive --sequential
```

### Resume Functionality
```bash
# Enable resume functionality (default)
python extract_audio.py --adaptive

# Disable resume functionality
python extract_audio.py --adaptive --no-resume
```

### Custom Directories
```bash
# Custom video directory and output directory
python extract_audio.py \
    -d ./my_videos \
    -o ./my_audio \
    --adaptive
```

## 🔍 Debugging and Troubleshooting

### Enable Debug Mode
Use VS Code debug configuration:

1. Create `.vscode/launch.json`
2. Set breakpoints
3. Press F5 to start debugging

### Common Issues

#### 1. FFmpeg Not Found
```bash
Error: ffmpeg or ffprobe not found
```
**Solution**: Ensure FFmpeg is installed and added to system PATH

#### 2. Adaptive Function Not Working
**Check Points**:
- Whether `--adaptive` parameter is used
- Whether correct batch file is used
- Check output for "Adaptive quality: Enabled"

#### 3. File Move Failed
**Possible Causes**:
- File is occupied by other programs
- Insufficient permissions
- Insufficient disk space

## 📊 Performance Optimization

### Parallel Processing Recommendations
- **Small Files (< 100MB)**: Use default parallel count
- **Large Files (> 100MB)**: Reduce parallel count to avoid memory issues
- **SSD Hard Drive**: Can increase parallel count
- **Mechanical Hard Drive**: Recommend reducing parallel count

### Quality Selection Recommendations
- **Voice/Podcast**: 64k-96k
- **General Music**: 128k-192k
- **High Quality Music**: 256k-320k
- **Lossless Archive**: WAV/FLAC

## 🎉 Update Log

### v2.0.0 (Latest)
- ✨ New adaptive quality functionality
- 🗂️ Automatic file organization and management
- 🚀 Performance optimization and parallel processing improvements
- 📝 Comprehensive error handling and logging

### v1.0.0
- 🎵 Basic audio extraction functionality
- 📁 Resume functionality support
- 🔄 Batch processing support

## 🤝 Contributing

Welcome to submit Issues and Pull Requests to improve this tool!

## 📄 License

This project uses MIT License.

---

**Enjoy high-quality audio extraction experience!** 🎵✨ 