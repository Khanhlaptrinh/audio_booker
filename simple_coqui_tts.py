import os
import subprocess
import tempfile
import time
from typing import Optional

class SimpleCoquiTTSEngine:
    def __init__(self):
        self.tts_available = False
        self._check_tts_availability()
    
    def _check_tts_availability(self):
        """Kiểm tra xem TTS có sẵn không"""
        try:
            # Thử import TTS
            from TTS.api import TTS
            self.tts_available = True
            print("✅ TTS available")
        except ImportError:
            print("❌ TTS not available, using fallback")
            self.tts_available = False
    
    def _preprocess_text(self, text: str) -> str:
        """Xử lý text trước khi đọc"""
        import re
        # Loại bỏ ký tự đặc biệt
        text = re.sub(r'[^\w\s.,!?;:()\-]', '', text)
        # Chuẩn hóa khoảng trắng
        text = re.sub(r'\s+', ' ', text)
        # Thêm dấu chấm câu nếu thiếu
        if text and text[-1] not in '.!?':
            text += '.'
        return text.strip()
    
    def generate_audio(self, text: str, output_path: str, dialect: str = 'north') -> bool:
        """Tạo file audio từ text"""
        if not self.tts_available:
            print("❌ TTS not available")
            return False
        
        try:
            from TTS.api import TTS
            
            # Xử lý text
            processed_text = self._preprocess_text(text)
            print(f"Generating audio for: {processed_text[:50]}...")
            
            # Sử dụng model tiếng Việt
            tts = TTS("tts_models/vi/vivos/vits")
            
            # Tạo audio
            tts.tts_to_file(
                text=processed_text,
                file_path=output_path
            )
            
            # Kiểm tra file đã được tạo
            if os.path.exists(output_path):
                print(f"✅ Audio generated: {output_path}")
                return True
            else:
                print(f"❌ Failed to generate audio: {output_path}")
                return False
                
        except Exception as e:
            print(f"❌ Error generating audio: {e}")
            return False
    
    def speak_text(self, text: str, dialect: str = 'north') -> bool:
        """Đọc text trực tiếp (không lưu file)"""
        if not self.tts_available:
            return False
        
        try:
            # Xử lý text
            processed_text = self._preprocess_text(text)
            
            # Tạo file tạm
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Tạo audio
            success = self.generate_audio(processed_text, temp_path, dialect)
            
            if success:
                # Phát audio (Windows)
                if os.name == 'nt':  # Windows
                    os.system(f'start /min wmplayer "{temp_path}"')
                else:  # Linux/Mac
                    os.system(f'play "{temp_path}"')
                
                # Xóa file tạm sau 5 giây
                time.sleep(5)
                try:
                    os.unlink(temp_path)
                except:
                    pass
                
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error speaking text: {e}")
            return False
    
    def get_available_voices(self) -> dict:
        """Lấy danh sách giọng nói có sẵn"""
        return {
            'north': 'Vietnamese (Northern)',
            'central': 'Vietnamese (Central)', 
            'south': 'Vietnamese (Southern)'
        }
    
    def test_voice(self, dialect: str) -> bool:
        """Test giọng nói của vùng miền"""
        test_text = "Xin chào, đây là giọng nói tiếng Việt"
        return self.speak_text(test_text, dialect)
    
    def get_audio_duration(self, audio_path: str) -> float:
        """Lấy thời lượng của file audio (giây)"""
        try:
            if not os.path.exists(audio_path):
                return 0.0
            
            import wave
            with wave.open(audio_path, 'rb') as audio_file:
                frames = audio_file.getnframes()
                sample_rate = audio_file.getframerate()
                duration = frames / float(sample_rate)
                return duration
        except Exception as e:
            print(f"Error getting audio duration: {e}")
            return 0.0
    
    def cleanup(self):
        """Dọn dẹp tài nguyên"""
        pass
