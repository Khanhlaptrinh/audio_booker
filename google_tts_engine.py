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
            chunks = self._split_text_into_chunks(processed_text, max_len=180)
            if not chunks:
                return False

            # Tải từng chunk dưới dạng mp3 bytes và ghép nối lại
            combined = bytearray()
            for part in chunks:
                mp3_bytes = self._fetch_tts_bytes(part)
                if not mp3_bytes:
                    return False
                combined.extend(mp3_bytes)

            # Ghi file kết quả (mp3)
            with open(output_path, 'wb') as f:
                f.write(combined)
            return os.path.exists(output_path)
            
            return False
            
        except Exception as e:
            print(f"❌ Error generating audio: {e}")
            return False
    
    def _fetch_tts_bytes(self, text: str) -> bytes:
        """Lấy mp3 bytes cho một đoạn text ngắn"""
        try:
            params = {
                'ie': 'UTF-8',
                'q': text,
                'tl': 'vi',  # Tiếng Việt
                'client': 'tw-ob'
            }
            url = self.base_url + '?' + urllib.parse.urlencode(params)
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    return response.read()
            return b''
        except Exception as e:
            print(f"❌ Error fetching tts bytes: {e}")
            return b''

    def _split_text_into_chunks(self, text: str, max_len: int = 180) -> list:
        """Chia text thành các phần <= max_len, cắt theo từ để tránh vỡ chữ"""
        words = text.split()
        chunks = []
        current = []
        current_len = 0
        for w in words:
            if current_len + len(w) + (1 if current else 0) > max_len:
                chunks.append(' '.join(current))
                current = [w]
                current_len = len(w)
            else:
                current.append(w)
                current_len += len(w) + (1 if current_len > 0 else 0)
        if current:
            chunks.append(' '.join(current))
        return chunks
    
    def _merge_audio_files(self, audio_files: list, output_path: str):
        """[Deprecated for MP3] Giữ lại để tương thích, không dùng cho MP3."""
        try:
            combined = bytearray()
            for p in audio_files:
                with open(p, 'rb') as f:
                    combined.extend(f.read())
            with open(output_path, 'wb') as out:
                out.write(combined)
        except Exception as e:
            print(f"❌ Error merging files: {e}")
    
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
