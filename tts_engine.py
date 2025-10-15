import os
import pyttsx3
import threading
import time
from typing import Optional
import wave
import struct
import re
import subprocess
import platform

class TTSEngine:
    def __init__(self):
        self.engine = None
        self.voices = {}
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Khởi tạo TTS engine"""
        try:
            self.engine = pyttsx3.init()
            self._setup_voices()
        except Exception as e:
            print(f"Error initializing TTS engine: {e}")
            self.engine = None
    
    def _setup_voices(self):
        """Thiết lập các giọng nói"""
        if not self.engine:
            return
        
        try:
            voices = self.engine.getProperty('voices')
            
            # Tìm giọng nói tốt nhất cho tiếng Việt
            best_voice = None
            if voices:
                # Ưu tiên giọng nói có tên chứa "Vietnamese" hoặc "Microsoft"
                for voice in voices:
                    if 'vietnamese' in voice.name.lower() or 'microsoft' in voice.name.lower():
                        best_voice = voice
                        break
                
                # Nếu không tìm thấy, dùng giọng đầu tiên
                if not best_voice:
                    best_voice = voices[0]
            
            # Mapping giọng nói theo vùng miền
            self.voices = {
                'north': {
                    'voice_id': best_voice.id if best_voice else None,
                    'rate': 180,  # Tăng tốc độ để đọc tự nhiên hơn
                    'volume': 0.9
                },
                'central': {
                    'voice_id': best_voice.id if best_voice else None,
                    'rate': 170,
                    'volume': 0.9
                },
                'south': {
                    'voice_id': best_voice.id if best_voice else None,
                    'rate': 190,
                    'volume': 0.9
                }
            }
            
            print(f"Available voices: {len(voices)}")
            for i, voice in enumerate(voices):
                print(f"Voice {i}: {voice.name} - {voice.languages}")
            
            if best_voice:
                print(f"Selected voice: {best_voice.name}")
                
        except Exception as e:
            print(f"Error setting up voices: {e}")
    
    def _preprocess_text(self, text: str) -> str:
        """Xử lý text trước khi đọc để tránh đánh vần"""
        # Loại bỏ ký tự đặc biệt có thể gây đánh vần
        text = re.sub(r'[^\w\s.,!?;:()\-]', '', text)
        
        # Chuẩn hóa khoảng trắng
        text = re.sub(r'\s+', ' ', text)
        
        # Thêm dấu chấm câu nếu thiếu
        if text and text[-1] not in '.!?':
            text += '.'
        
        # Chia thành câu ngắn để đọc tự nhiên hơn
        sentences = re.split(r'[.!?]+', text)
        processed_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                # Giới hạn độ dài câu để tránh đánh vần
                if len(sentence) > 50:  # Giảm từ 100 xuống 50
                    # Chia câu dài thành các phần nhỏ
                    words = sentence.split()
                    for i in range(0, len(words), 10):  # Giảm từ 15 xuống 10
                        chunk = ' '.join(words[i:i+10])
                        processed_sentences.append(chunk)
                else:
                    processed_sentences.append(sentence)
        
        return '. '.join(processed_sentences) + '.'
    
    def _convert_to_phonetic(self, text: str) -> str:
        """Chuyển đổi text tiếng Việt sang dạng phonetic để TTS đọc tốt hơn"""
        # Mapping các ký tự tiếng Việt sang dạng đơn giản
        vietnamese_map = {
            'à': 'a', 'á': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
            'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
            'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
            'è': 'e', 'é': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
            'ê': 'e', 'ề': 'e', 'ế': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
            'ì': 'i', 'í': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
            'ò': 'o', 'ó': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
            'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
            'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
            'ù': 'u', 'ú': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
            'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
            'ỳ': 'y', 'ý': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
            'đ': 'd'
        }
        
        # Chuyển đổi từng ký tự
        converted_text = ""
        for char in text:
            if char.lower() in vietnamese_map:
                converted_text += vietnamese_map[char.lower()]
            else:
                converted_text += char
        
        return converted_text
    
    def generate_audio(self, text: str, output_path: str, dialect: str = 'north') -> bool:
        """Tạo file audio từ text"""
        if not self.engine:
            print("TTS engine not initialized")
            return False
        
        try:
            # Xử lý text trước khi đọc
            processed_text = self._preprocess_text(text)
            
            # Chuyển đổi sang dạng phonetic để TTS đọc tốt hơn
            phonetic_text = self._convert_to_phonetic(processed_text)
            
            print(f"Original text: {text[:50]}...")
            print(f"Processed text: {processed_text[:50]}...")
            print(f"Phonetic text: {phonetic_text[:50]}...")
            
            # Thiết lập giọng nói theo vùng miền
            voice_config = self.voices.get(dialect, self.voices['north'])
            
            if voice_config['voice_id']:
                self.engine.setProperty('voice', voice_config['voice_id'])
            
            self.engine.setProperty('rate', voice_config['rate'])
            self.engine.setProperty('volume', voice_config['volume'])
            
            # Tạo file audio với text đã xử lý
            self.engine.save_to_file(phonetic_text, output_path)
            self.engine.runAndWait()
            
            # Kiểm tra file đã được tạo
            if os.path.exists(output_path):
                print(f"Audio generated: {output_path}")
                return True
            else:
                print(f"Failed to generate audio: {output_path}")
                return False
                
        except Exception as e:
            print(f"Error generating audio: {e}")
            return False
    
    def get_audio_duration(self, audio_path: str) -> float:
        """Lấy thời lượng của file audio (giây)"""
        try:
            if not os.path.exists(audio_path):
                return 0.0
            
            with wave.open(audio_path, 'rb') as audio_file:
                frames = audio_file.getnframes()
                sample_rate = audio_file.getframerate()
                duration = frames / float(sample_rate)
                return duration
        except Exception as e:
            print(f"Error getting audio duration: {e}")
            return 0.0
    
    def speak_text(self, text: str, dialect: str = 'north'):
        """Đọc text trực tiếp (không lưu file)"""
        if not self.engine:
            return False
        
        try:
            # Xử lý text trước khi đọc
            processed_text = self._preprocess_text(text)
            
            # Chuyển đổi sang dạng phonetic để TTS đọc tốt hơn
            phonetic_text = self._convert_to_phonetic(processed_text)
            
            voice_config = self.voices.get(dialect, self.voices['north'])
            
            if voice_config['voice_id']:
                self.engine.setProperty('voice', voice_config['voice_id'])
            
            self.engine.setProperty('rate', voice_config['rate'])
            self.engine.setProperty('volume', voice_config['volume'])
            
            self.engine.say(phonetic_text)
            self.engine.runAndWait()
            return True
            
        except Exception as e:
            print(f"Error speaking text: {e}")
            return False
    
    def stop_speaking(self):
        """Dừng đọc"""
        if self.engine:
            self.engine.stop()
    
    def get_available_voices(self) -> dict:
        """Lấy danh sách giọng nói có sẵn"""
        return self.voices
    
    def test_voice(self, dialect: str) -> bool:
        """Test giọng nói của vùng miền"""
        test_text = "Xin chào, đây là giọng nói vùng miền"
        return self.speak_text(test_text, dialect)
    
    def test_short_text(self, text: str = "Xin chào") -> bool:
        """Test với text ngắn để kiểm tra TTS"""
        print(f"Testing TTS with text: '{text}'")
        return self.speak_text(text, 'north')
    
    def test_long_text(self, text: str = "Đây là một câu chuyện dài về một cô gái tên Lan sống trong ngôi làng nhỏ") -> bool:
        """Test với text dài để kiểm tra xử lý"""
        print(f"Testing TTS with long text: '{text[:50]}...'")
        return self.speak_text(text, 'north')
    
    def cleanup(self):
        """Dọn dẹp tài nguyên"""
        if self.engine:
            self.engine.stop()
            del self.engine
            self.engine = None
