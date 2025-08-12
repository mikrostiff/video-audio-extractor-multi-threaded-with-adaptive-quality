# -*- coding: utf-8 -*-
"""
测试单个文件的自适应质量功能
"""

import os
import subprocess
import json
import re
from pathlib import Path

def get_video_audio_bitrate(video_path):
    """获取视频文件的音频码率"""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_streams', '-select_streams', 'a:0', video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if 'streams' in data and len(data['streams']) > 0:
                stream = data['streams'][0]
                
                if 'bit_rate' in stream:
                    bitrate = int(stream['bit_rate'])
                    return bitrate
                elif 'tags' in stream and 'BPS' in stream['tags']:
                    bitrate = int(stream['tags']['BPS'])
                    return bitrate
                elif 'tags' in stream and 'bit_rate' in stream['tags']:
                    bitrate = int(stream['tags']['bit_rate'])
                    return bitrate
                
                if 'sample_rate' in stream and 'channels' in stream:
                    sample_rate = int(stream['sample_rate'])
                    channels = int(stream['channels'])
                    estimated_bitrate = sample_rate * channels * 16
                    return estimated_bitrate
        
        return None
        
    except Exception as e:
        print(f"获取音频码率失败: {e}")
        return None

def parse_quality_to_bps(quality_str):
    """将质量字符串转换为bps数值"""
    try:
        match = re.match(r'(\d+)k?', quality_str.lower())
        if match:
            value = int(match.group(1))
            return value * 1000
        return None
    except:
        return None

def get_adaptive_quality(video_path, target_quality, audio_format):
    """根据视频音频码率自适应设置提取质量"""
    print(f"正在分析视频: {os.path.basename(video_path)}")
    print(f"目标质量: {target_quality}, 音频格式: {audio_format}")
    
    original_bitrate = get_video_audio_bitrate(video_path)
    
    if original_bitrate is None:
        print(f"无法检测到音频码率，使用目标质量: {target_quality}")
        return target_quality
    
    print(f"检测到原音频码率: {original_bitrate} bps ({original_bitrate//1000}k)")
    
    target_bps = parse_quality_to_bps(target_quality)
    
    if target_bps is None:
        print(f"无法解析目标质量 '{target_quality}'，使用目标质量")
        return target_quality
    
    print(f"目标质量转换为: {target_bps} bps")
    
    if target_bps > original_bitrate:
        print(f"目标码率 {target_bps} bps 高于原音频码率 {original_bitrate} bps，将进行调整")
        
        if audio_format == 'mp3':
            if original_bitrate <= 64000:
                adaptive_quality = '64k'
            elif original_bitrate <= 96000:
                adaptive_quality = '96k'
            elif original_bitrate <= 128000:
                adaptive_quality = '128k'
            elif original_bitrate <= 192000:
                adaptive_quality = '192k'
            else:
                adaptive_quality = '256k'
        elif audio_format == 'aac':
            if original_bitrate <= 64000:
                adaptive_quality = '64k'
            elif original_bitrate <= 96000:
                adaptive_quality = '96k'
            elif original_bitrate <= 128000:
                adaptive_quality = '128k'
            elif original_bitrate <= 192000:
                adaptive_quality = '192k'
            else:
                adaptive_quality = '256k'
        else:
            adaptive_quality = f"{original_bitrate // 1000}k"
        
        print(f"自适应调整后的质量: {adaptive_quality}")
        return adaptive_quality
    else:
        print(f"目标码率 {target_bps} bps 合适，保持目标质量: {target_quality}")
        return target_quality

def test_extraction(video_path, output_dir, audio_format, quality, use_adaptive):
    """测试音频提取过程"""
    print(f"\n{'='*60}")
    print(f"测试音频提取")
    print(f"{'='*60}")
    
    video_name = Path(video_path).stem
    original_quality = quality
    
    print(f"视频文件: {video_name}")
    print(f"音频格式: {audio_format}")
    print(f"原始质量设置: {quality}")
    print(f"启用自适应: {use_adaptive}")
    
    # 自适应质量调整
    if use_adaptive:
        print(f"\n--- 自适应质量分析 ---")
        adaptive_quality = get_adaptive_quality(video_path, quality, audio_format)
        if adaptive_quality != quality:
            print(f"✅ 质量已调整: {quality} -> {adaptive_quality}")
            quality = adaptive_quality
        else:
            print(f"ℹ️ 质量无需调整: {quality}")
    else:
        print(f"\n--- 固定质量模式 ---")
        print(f"使用固定质量: {quality}")
    
    # 构建ffmpeg命令
    print(f"\n--- FFmpeg命令构建 ---")
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
    else:
        print(f"❌ 不支持的格式: {audio_format}")
        return False
    
    print(f"输出文件: {output_file}")
    print(f"FFmpeg命令: {' '.join(cmd)}")
    
    # 执行提取
    print(f"\n--- 执行音频提取 ---")
    print(f"正在提取: {video_name} (最终质量: {quality})")
    
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    
    if result.returncode == 0:
        print(f"✅ 提取成功!")
        
        # 检查输出文件
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"输出文件大小: {file_size} 字节")
            
            # 验证提取的音频质量
            print(f"\n--- 验证输出质量 ---")
            verify_cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_streams', '-select_streams', 'a:0', output_file
            ]
            
            verify_result = subprocess.run(verify_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            if verify_result.returncode == 0:
                try:
                    verify_data = json.loads(verify_result.stdout)
                    if 'streams' in verify_data and len(verify_data['streams']) > 0:
                        stream = verify_data['streams'][0]
                        if 'bit_rate' in stream:
                            actual_bitrate = int(stream['bit_rate'])
                            print(f"实际输出码率: {actual_bitrate} bps ({actual_bitrate//1000}k)")
                            
                            # 比较预期和实际
                            expected_bps = parse_quality_to_bps(quality)
                            if expected_bps:
                                if abs(actual_bitrate - expected_bps) <= 5000:  # 允许5k的误差
                                    print(f"✅ 码率匹配: 预期 {quality}, 实际 {actual_bitrate//1000}k")
                                else:
                                    print(f"⚠️ 码率不匹配: 预期 {quality}, 实际 {actual_bitrate//1000}k")
                        else:
                            print(f"ℹ️ 无法获取输出文件码率信息")
                except:
                    print(f"ℹ️ 无法解析输出文件信息")
        else:
            print(f"❌ 输出文件未找到")
        
        return True
    else:
        print(f"❌ 提取失败!")
        print(f"错误信息: {result.stderr}")
        return False

def main():
    print("🎵 单个文件自适应质量测试工具")
    print("=" * 60)
    
    # 检查ffprobe
    try:
        subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
        print("✅ ffprobe 可用")
    except:
        print("❌ 未找到 ffprobe")
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
    
    # 选择文件
    try:
        choice = input(f"\n请选择要测试的文件 (1-{len(video_files)}) 或按回车测试第一个文件: ").strip()
        
        if not choice:
            choice = 1
        else:
            choice = int(choice)
        
        if not (1 <= choice <= len(video_files)):
            print("❌ 无效的选择")
            return
            
        selected_file = video_files[choice - 1]
        
        # 选择音频格式
        print(f"\n🎵 音频格式选择:")
        print("  1. MP3 (推荐)")
        print("  2. AAC")
        format_choice = input("请选择格式 (1-2) 或按回车使用MP3: ").strip()
        
        if not format_choice or format_choice == '1':
            audio_format = 'mp3'
        elif format_choice == '2':
            audio_format = 'aac'
        else:
            print("❌ 无效的选择，使用MP3")
            audio_format = 'mp3'
        
        # 选择质量
        print(f"\n🎚️ 质量选择:")
        print("  1. 64k (低质量)")
        print("  2. 128k (标准质量)")
        print("  3. 192k (高质量)")
        print("  4. 320k (最高质量)")
        quality_choice = input("请选择质量 (1-4) 或按回车使用128k: ").strip()
        
        quality_map = {'1': '64k', '2': '128k', '3': '192k', '4': '320k'}
        if quality_choice in quality_map:
            quality = quality_map[quality_choice]
        else:
            quality = '128k'
        
        # 选择是否启用自适应
        print(f"\n🔄 自适应模式:")
        print("  1. 启用自适应 (推荐)")
        print("  2. 禁用自适应 (固定质量)")
        adaptive_choice = input("请选择模式 (1-2) 或按回车启用自适应: ").strip()
        
        if not adaptive_choice or adaptive_choice == '1':
            use_adaptive = True
        elif adaptive_choice == '2':
            use_adaptive = False
        else:
            print("❌ 无效的选择，启用自适应")
            use_adaptive = True
        
        # 创建输出目录
        output_dir = './test_output'
        os.makedirs(output_dir, exist_ok=True)
        
        # 开始测试
        print(f"\n🚀 开始测试...")
        success = test_extraction(selected_file, output_dir, audio_format, quality, use_adaptive)
        
        if success:
            print(f"\n✅ 测试完成!")
        else:
            print(f"\n❌ 测试失败!")
            
    except (ValueError, KeyboardInterrupt):
        print("\n❌ 输入无效或操作取消")

if __name__ == "__main__":
    main() 