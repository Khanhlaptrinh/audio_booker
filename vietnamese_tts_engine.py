import os
import tempfile
import time
import subprocess
from typing import Optional

class VietnameseTTSEngine:
    def __init__(self):
        self.available = False
        self.voices = {}
        self.has_vietnamese_voice = False
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Khởi tạo TTS engine với giọng tiếng Việt"""
        try:
            # Thử sử dụng Windows SAPI với giọng tiếng Việt
            import win32com.client
            
            self.sapi = win32com.client.Dispatch("SAPI.SpVoice")
            self.available = True
            
            # Lấy danh sách giọng nói
            voices = self.sapi.GetVoices()
            print(f"Available voices: {voices.Count}")
            
            # Tìm giọng tiếng Việt (có thể ép qua biến môi trường APP_VI_VOICE)
            preferred_name = os.environ.get('APP_VI_VOICE')
            vietnamese_voice = None
            for i in range(voices.Count):
                voice = voices.Item(i)
                voice_name = voice.GetDescription()
                print(f"Voice {i}: {voice_name}")
                
                # Tìm giọng tiếng Việt
                if preferred_name and preferred_name.lower() in voice_name.lower():
                    vietnamese_voice = voice
                    break
                if 'vietnamese' in voice_name.lower() or 'viet nam' in voice_name.lower():
                    vietnamese_voice = voice
                    break
            
            if vietnamese_voice:
                self.sapi.Voice = vietnamese_voice
                print(f"Using Vietnamese voice: {vietnamese_voice.GetDescription()}")
                self.has_vietnamese_voice = True
            else:
                print("No Vietnamese voice found, using default")
                self.has_vietnamese_voice = False
            
            # Thiết lập tốc độ và âm lượng
            self.sapi.Rate = 0  # Tốc độ bình thường
            self.sapi.Volume = 100  # Âm lượng tối đa
            
        except ImportError:
            print("win32com not available, trying alternative method")
            self._try_alternative_method()
        except Exception as e:
            print(f"Error initializing TTS: {e}")
            self._try_alternative_method()
    
    def _try_alternative_method(self):
        """Thử phương pháp thay thế"""
        try:
            # Sử dụng PowerShell với Windows TTS
            result = subprocess.run([
                'powershell', '-Command', 
                'Add-Type -AssemblyName System.Speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.GetInstalledVoices() | ForEach-Object { $_.VoiceInfo.Name }'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                voices = result.stdout.strip().split('\n')
                print(f"Available voices: {voices}")
                
                # Tìm giọng tiếng Việt (có thể ép qua biến môi trường APP_VI_VOICE)
                preferred_name = os.environ.get('APP_VI_VOICE')
                vietnamese_voice = None
                for voice in voices:
                    if preferred_name and preferred_name.lower() in voice.lower():
                        vietnamese_voice = voice
                        break
                    if 'vietnamese' in voice.lower() or 'viet nam' in voice.lower():
                        vietnamese_voice = voice
                        break
                
                if vietnamese_voice:
                    self.powershell_voice = vietnamese_voice
                    self.available = True
                    print(f"Using PowerShell TTS with voice: {vietnamese_voice}")
                    self.has_vietnamese_voice = True
                else:
                    print("No Vietnamese voice found in PowerShell TTS")
                    self.available = True  # PowerShell is available but not Vietnamese voice
                    self.has_vietnamese_voice = False
            else:
                print("PowerShell TTS not available")
                
        except Exception as e:
            print(f"Alternative method failed: {e}")
    
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
            print("TTS engine not available")
            return False

        try:
            # Đảm bảo thư mục tồn tại
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Xử lý text và escape cho PowerShell
            processed_text = self._preprocess_text(text)
            # Escape dấu nháy kép cho PowerShell
            safe_text = processed_text.replace('"', '`"')

            print(f"Generating audio for: {processed_text[:80]}...")

            # Ưu tiên sử dụng PowerShell System.Speech để ghi WAV ổn định
            ps_script = (
                f"Add-Type -AssemblyName System.Speech; "
                f"$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                f"$speak.SetOutputToWaveFile(\"{output_path}\"); "
                f"$speak.Speak(\"{safe_text}\"); "
                f"$speak.Dispose();"
            )

            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0 and os.path.exists(output_path):
                print(f"Audio generated with PowerShell: {output_path}")
                return True

            # Fallback: nếu có SAPI object, thử nói trực tiếp (không lưu file)
            if hasattr(self, 'sapi'):
                try:
                    self.sapi.Speak(processed_text)
                    # Không lưu được file với API này; coi như thất bại tạo file
                except Exception:
                    pass

            print("Failed to generate audio")
            if result.stderr:
                print(f"PowerShell error: {result.stderr}")
            return False

        except Exception as e:
            print(f"Error generating audio: {e}")
            return False
    
    def speak_text(self, text: str, dialect: str = 'north') -> bool:
        """Đọc text trực tiếp (không lưu file)"""
        if not self.available:
            return False
        
        try:
            # Xử lý text
            processed_text = self._preprocess_text(text)
            
            # Sử dụng Windows SAPI
            if hasattr(self, 'sapi'):
                self.sapi.Speak(processed_text)
                return True
            
            # Sử dụng PowerShell TTS
            elif hasattr(self, 'powershell_voice'):
                ps_command = f'''
                Add-Type -AssemblyName System.Speech
                $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer
                $speak.Speak("{processed_text}")
                '''
                
                subprocess.run([
                    'powershell', '-Command', ps_command
                ], timeout=30)
                
                return True
            
            return False
            
        except Exception as e:
            print(f"Error speaking text: {e}")
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
        if hasattr(self, 'sapi'):
            del self.sapi
