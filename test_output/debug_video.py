# -*- coding: utf-8 -*-
"""
调试特定视频文件的脚本
"""

import os
import subprocess
import json
from pathlib import Path

def debug_video_file(video_path):
    """详细调试视频文件的音频信息"""
    print(f"=== 调试视频文件: {os.path.basename(video_path)} ===")
    
    # 检查文件是否存在
    if not os.path.exists(video_path):
        print(f"❌ 文件不存在: {video_path}")
        return
    
    print(f"✅ 文件存在，大小: {os.path.getsize(video_path)} 字节")
    
    # 使用ffprobe获取详细信息
    cmd = [
        'ffprobe', '-v', 'info', '-print_format', 'json',
        '-show_format', '-show_streams', video_path
    ]
    
    print(f"\n执行命令: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    
    print(f"返回码: {result.returncode}")
    
    if result.returncode != 0:
        print(f"❌ ffprobe 执行失败")
        print(f"错误信息: {result.stderr}")
        return
    
    try:
        data = json.loads(result.stdout)
        print(f"✅ JSON 解析成功")
        
        # 显示格式信息
        if 'format' in data:
            print(f"\n📁 格式信息:")
            format_info = data['format']
            print(f"  格式名称: {format_info.get('format_name', 'N/A')}")
            print(f"  时长: {format_info.get('duration', 'N/A')} 秒")
            print(f"  比特率: {format_info.get('bit_rate', 'N/A')} bps")
            print(f"  标签: {format_info.get('tags', {})}")
        
        # 显示流信息
        if 'streams' in data:
            print(f"\n🎵 音频流信息:")
            audio_streams = [s for s in data['streams'] if s.get('codec_type') == 'audio']
            
            if not audio_streams:
                print("❌ 未找到音频流")
                return
            
            for i, stream in enumerate(audio_streams):
                print(f"\n  音频流 {i+1}:")
                print(f"    编码器: {stream.get('codec_name', 'N/A')}")
                print(f"    编码器长名称: {stream.get('codec_long_name', 'N/A')}")
                print(f"    比特率: {stream.get('bit_rate', 'N/A')} bps")
                print(f"    采样率: {stream.get('sample_rate', 'N/A')} Hz")
                print(f"    声道数: {stream.get('channels', 'N/A')}")
                print(f"    声道布局: {stream.get('channel_layout', 'N/A')}")
                print(f"    标签: {stream.get('tags', {})}")
                
                # 检查是否有码率信息
                if 'bit_rate' in stream and stream['bit_rate']:
                    try:
                        bitrate = int(stream['bit_rate'])
                        print(f"    ✅ 检测到码率: {bitrate} bps ({bitrate//1000}k)")
                    except:
                        print(f"    ❌ 码率格式错误: {stream['bit_rate']}")
                else:
                    print(f"    ❌ 未找到码率信息")
                    
                    # 尝试从标签获取
                    if 'tags' in stream:
                        tags = stream['tags']
                        for tag_name in ['BPS', 'bit_rate', 'BitRate']:
                            if tag_name in tags:
                                try:
                                    tag_bitrate = int(tags[tag_name])
                                    print(f"    ✅ 从标签 {tag_name} 获取到码率: {tag_bitrate} bps")
                                    break
                                except:
                                    print(f"    ❌ 标签 {tag_name} 格式错误: {tags[tag_name]}")
                    
                    # 尝试估算码率
                    if 'sample_rate' in stream and 'channels' in stream:
                        try:
                            sample_rate = int(stream['sample_rate'])
                            channels = int(stream['channels'])
                            # 假设16位采样
                            estimated_bitrate = sample_rate * channels * 16
                            print(f"    📊 估算码率: {sample_rate}Hz × {channels}声道 × 16bit = {estimated_bitrate} bps ({estimated_bitrate//1000}k)")
                        except:
                            print(f"    ❌ 无法估算码率")
        
        # 尝试获取音频码率
        print(f"\n🔍 尝试获取音频码率...")
        audio_cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_streams', '-select_streams', 'a:0', video_path
        ]
        
        audio_result = subprocess.run(audio_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        
        if audio_result.returncode == 0:
            try:
                audio_data = json.loads(audio_result.stdout)
                if 'streams' in audio_data and len(audio_data['streams']) > 0:
                    stream = audio_data['streams'][0]
                    if 'bit_rate' in stream and stream['bit_rate']:
                        bitrate = int(stream['bit_rate'])
                        print(f"✅ 成功获取音频码率: {bitrate} bps ({bitrate//1000}k)")
                    else:
                        print(f"❌ 音频流中未找到码率信息")
                else:
                    print(f"❌ 未找到音频流")
            except:
                print(f"❌ 音频信息解析失败")
        else:
            print(f"❌ 音频信息获取失败")
            
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败: {e}")
        print(f"原始输出: {result.stdout}")

def main():
    print("🔧 视频文件调试工具")
    print("=" * 50)
    
    # 检查ffprobe
    try:
        subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
        print("✅ ffprobe 可用")
    except:
        print("❌ 未找到 ffprobe，请确保已安装 ffmpeg")
        return
    
    # 查找视频文件
    video_files = []
    for file_path in Path('.').iterdir():
        if file_path.is_file() and file_path.suffix.lower() in {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'}:
            video_files.append(str(file_path))
    
    if not video_files:
        print("❌ 当前目录下没有找到视频文件")
        return
    
    print(f"\n📁 找到 {len(video_files)} 个视频文件:")
    for i, video_file in enumerate(video_files, 1):
        print(f"  {i}. {os.path.basename(video_file)}")
    
    # 让用户选择要调试的文件
    try:
        choice = input(f"\n请选择要调试的文件 (1-{len(video_files)}) 或按回车调试第一个文件: ").strip()
        
        if not choice:
            choice = 1
        else:
            choice = int(choice)
        
        if 1 <= choice <= len(video_files):
            selected_file = video_files[choice - 1]
            debug_video_file(selected_file)
        else:
            print("❌ 无效的选择")
            
    except (ValueError, KeyboardInterrupt):
        print("\n❌ 输入无效或操作取消")

if __name__ == "__main__":
    main() 