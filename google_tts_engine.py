import os
import tempfile
import time
import urllib.request
import urllib.parse
from typing import Optional

class GoogleTTSEngine:
    def __init__(self):
        self.available = False
        self.base_url = "https://translate.google.com/translate_tts"
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Khởi tạo Google TTS engine"""
        try:
            # Test kết nối
            req = urllib.request.Request("https://www.google.com")
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    self.available = True
                    print("✅ Google TTS engine initialized")
                else:
                    print("❌ No internet connection")
        except Exception as e:
            print(f"❌ Error initializing Google TTS: {e}")
    
    def _preprocess_text(self, text: str) -> str:
        """Xử lý text trước khi đọc"""
        import re
        # Giữ nguyên ký tự tiếng Việt
        # Chỉ loại bỏ ký tự đặc biệt không cần thiết
        text = re.sub(r'[^\w\s.,!?;:()\-àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴĐ]', '', text)
        
        # Chuẩn hóa khoảng trắng
        text = re.sub(r'\s+', ' ', text)
        
        # Thêm dấu chấm câu nếu thiếu
        if text and text[-1] not in '.!?':
            text += '.'
        
        return text.strip()
    
    def generate_audio(self, text: str, output_path: str, dialect: str = 'north') -> bool:
        """Tạo file audio từ text"""
        if not self.available:
            print("❌ Google TTS engine not available")
            return False
        
        try:
            # Xử lý text
            processed_text = self._preprocess_text(text)
            print(f"Generating audio for: {processed_text[:50]}...")
            
            # Chia text thành các phần nhỏ (Google TTS có giới hạn)
            if len(processed_text) > 200:
                # Chia thành các câu
                sentences = processed_text.split('.')
                audio_files = []
                
                for i, sentence in enumerate(sentences):
                    if sentence.strip():
                        temp_file = f"temp_audio_{i}.wav"
                        if self._generate_single_audio(sentence.strip(), temp_file):
                            audio_files.append(temp_file)
                
                # Gộp các file audio
                if audio_files:
                    self._merge_audio_files(audio_files, output_path)
                    # Xóa file tạm
                    for temp_file in audio_files:
                        try:
                            os.unlink(temp_file)
                        except:
                            pass
                    return True
            else:
                return self._generate_single_audio(processed_text, output_path)
            
            return False
            
        except Exception as e:
            print(f"❌ Error generating audio: {e}")
            return False
    
    def _generate_single_audio(self, text: str, output_path: str) -> bool:
        """Tạo audio cho một đoạn text ngắn"""
        try:
            # Sử dụng Google TTS API
            params = {
                'ie': 'UTF-8',
                'q': text,
                'tl': 'vi',  # Tiếng Việt
                'client': 'tw-ob'
            }
            
            # Tạo URL với parameters
            url = self.base_url + '?' + urllib.parse.urlencode(params)
            
            # Tạo request với headers
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            # Gửi request
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    with open(output_path, 'wb') as f:
                        f.write(response.read())
                    
                    if os.path.exists(output_path):
                        print(f"✅ Audio generated: {output_path}")
                        return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error generating single audio: {e}")
            return False
    
    def _merge_audio_files(self, audio_files: list, output_path: str):
        """Gộp các file audio thành một file"""
        try:
            import wave
            
            # Đọc file đầu tiên
            with wave.open(audio_files[0], 'rb') as first_file:
                params = first_file.getparams()
                frames = first_file.readframes(first_file.getnframes())
            
            # Gộp các file còn lại
            for audio_file in audio_files[1:]:
                with wave.open(audio_file, 'rb') as file:
                    frames += file.readframes(file.getnframes())
            
            # Ghi file kết quả
            with wave.open(output_path, 'wb') as output_file:
                output_file.setparams(params)
                output_file.writeframes(frames)
                
        except Exception as e:
            print(f"❌ Error merging audio files: {e}")
    
    def speak_text(self, text: str, dialect: str = 'north') -> bool:
        """Đọc text trực tiếp (không lưu file)"""
        if not self.available:
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
            'north': 'Vietnamese (Google TTS)',
            'central': 'Vietnamese (Google TTS)', 
            'south': 'Vietnamese (Google TTS)'
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
