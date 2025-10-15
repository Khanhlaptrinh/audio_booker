import os
import tempfile
import time
from typing import Optional

class HybridTTSEngine:
    def __init__(self):
        self.coqui_available = False
        self.pyttsx3_available = False
        self.coqui_tts = None
        self.pyttsx3_engine = None
        
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Khởi tạo các TTS engines"""
        # Thử Coqui TTS trước
        try:
            from TTS.api import TTS
            self.coqui_tts = TTS("tts_models/vi/vivos/vits")
            self.coqui_available = True
            print("✅ Coqui TTS initialized")
        except Exception as e:
            print(f"❌ Coqui TTS not available: {e}")
            self.coqui_available = False
            self.coqui_tts = None
        
        # Fallback với pyttsx3
        try:
            import pyttsx3
            self.pyttsx3_engine = pyttsx3.init()
            self.pyttsx3_available = True
            print("✅ pyttsx3 initialized")
        except Exception as e:
            print(f"❌ pyttsx3 not available: {e}")
            self.pyttsx3_available = False
            self.pyttsx3_engine = None
    
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
        # Xử lý text
        processed_text = self._preprocess_text(text)
        print(f"Generating audio for: {processed_text[:50]}...")
        
        # Thử Coqui TTS trước
        if self.coqui_available:
            try:
                self.coqui_tts.tts_to_file(
                    text=processed_text,
                    file_path=output_path
                )
                
                if os.path.exists(output_path):
                    print(f"✅ Audio generated with Coqui TTS: {output_path}")
                    return True
            except Exception as e:
                print(f"❌ Coqui TTS failed: {e}")
        
        # Fallback với pyttsx3
        if self.pyttsx3_available:
            try:
                self.pyttsx3_engine.save_to_file(processed_text, output_path)
                self.pyttsx3_engine.runAndWait()
                
                if os.path.exists(output_path):
                    print(f"✅ Audio generated with pyttsx3: {output_path}")
                    return True
            except Exception as e:
                print(f"❌ pyttsx3 failed: {e}")
        
        print("❌ All TTS engines failed")
        return False
    
    def speak_text(self, text: str, dialect: str = 'north') -> bool:
        """Đọc text trực tiếp (không lưu file)"""
        # Xử lý text
        processed_text = self._preprocess_text(text)
        
        # Thử Coqui TTS trước
        if self.coqui_available:
            try:
                # Tạo file tạm
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    temp_path = temp_file.name
                
                # Tạo audio
                self.coqui_tts.tts_to_file(
                    text=processed_text,
                    file_path=temp_path
                )
                
                # Phát audio
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
                
                print("✅ Spoke with Coqui TTS")
                return True
                
            except Exception as e:
                print(f"❌ Coqui TTS failed: {e}")
        
        # Fallback với pyttsx3
        if self.pyttsx3_available:
            try:
                self.pyttsx3_engine.say(processed_text)
                self.pyttsx3_engine.runAndWait()
                print("✅ Spoke with pyttsx3")
                return True
            except Exception as e:
                print(f"❌ pyttsx3 failed: {e}")
        
        print("❌ All TTS engines failed")
        return False
    
    def get_available_voices(self) -> dict:
        """Lấy danh sách giọng nói có sẵn"""
        voices = {}
        
        if self.coqui_available:
            voices['coqui'] = 'Vietnamese (Coqui TTS)'
        
        if self.pyttsx3_available:
            voices['pyttsx3'] = 'English (pyttsx3)'
        
        return voices
    
    def test_voice(self, dialect: str) -> bool:
        """Test giọng nói của vùng miền"""
        test_text = "Xin chào, đây là test giọng nói"
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
        if self.pyttsx3_engine:
            self.pyttsx3_engine.stop()
            del self.pyttsx3_engine
            self.pyttsx3_engine = None
