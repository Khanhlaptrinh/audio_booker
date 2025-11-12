# 📚 Audio Book Reader

Ứng dụng web đọc truyện bằng giọng nói vùng miền (Bắc/Trung/Nam) với giao diện lật trang đẹp mắt.

## ✨ Tính năng

- **Upload truyện**: Hỗ trợ file .txt và .epub
- **Giọng đọc vùng miền**: Bắc, Trung, Nam với từ điển mapping
- **Giao diện lật trang**: Hiệu ứng flip book mượt mà
- **Real-time streaming**: SocketIO để đồng bộ audio và UI
- **Responsive design**: Tương thích mobile và desktop

## 🚀 Cài đặt

### 1. Clone repository
```bash
git clone <repository-url>
cd audio-book-reader
```

### 2. Tạo virtual environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 4. Chạy ứng dụng
```bash
python app.py
```

Truy cập: http://localhost:5001

## 📁 Cấu trúc dự án

```
audio-book-reader/
├── app.py                 # Flask app chính
├── text_processor.py      # Xử lý text và chia trang
├── tts_engine.py         # TTS engine với giọng vùng miền
├── dialect_mapper.py     # Mapping từ vùng miền
├── templates/
│   └── index.html        # Giao diện chính
├── static/
│   ├── css/
│   │   └── style.css     # CSS styling
│   ├── js/
│   │   └── app.js        # JavaScript frontend
│   └── audio/            # Thư mục lưu audio files
├── uploads/              # Thư mục lưu file upload
└── requirements.txt      # Python dependencies
```

## 🎯 Cách sử dụng

1. **Upload truyện**: Kéo thả hoặc chọn file .txt/.epub
2. **Chọn giọng đọc**: Bắc/Trung/Nam
3. **Bắt đầu đọc**: Nhấn nút "Phát"
4. **Điều khiển**: Tạm dừng, dừng, lật trang tự động

## 🔧 Tính năng kỹ thuật

### Text Processing
- Tự động chia text thành trang (200 từ/trang)
- Xử lý encoding UTF-8 và CP1252
- Làm sạch text và chuẩn hóa

### TTS Engine
- Sử dụng pyttsx3 (offline)
- 3 giọng nói vùng miền
- Tùy chỉnh tốc độ và âm lượng

### Dialect Mapping
- Rule-based transformation
- Từ điển Bắc/Trung/Nam
- Tự động phát hiện vùng miền

### Frontend
- Responsive design
- Page flip animation
- Real-time audio streaming
- SocketIO communication

## 🚧 Roadmap

### Giai đoạn 1 (Hiện tại) - MVP
- ✅ Upload file txt/epub
- ✅ TTS với giọng vùng miền
- ✅ Giao diện lật trang
- ✅ SocketIO streaming

### Giai đoạn 2 - Nâng cao
- [ ] Lưu lịch sử đọc
- [ ] Chọn giọng nhân vật
- [ ] Mobile app (React Native)
- [ ] Cloud TTS (FPT.AI, Viettel)

### Giai đoạn 3 - AI Enhancement
- [ ] AI voice cloning
- [ ] Emotion detection
- [ ] Smart page splitting
- [ ] Multi-language support

## 🛠️ Development

### Chạy development server
```bash
python app.py
```

### Debug mode
```bash
export FLASK_DEBUG=1
python app.py
```

### Test TTS
```python
from tts_engine import TTSEngine
tts = TTSEngine()
tts.test_voice('north')  # Test giọng Bắc
```

## 📝 API Endpoints

- `POST /upload` - Upload file truyện
- `GET /start_reading/<session_id>` - Bắt đầu đọc
- `GET /` - Giao diện chính

### SocketIO Events
- `join_session` - Tham gia session
- `new_page` - Trang mới
- `error` - Lỗi

## 🐛 Troubleshooting

### Lỗi TTS
```bash
# Cài đặt TTS dependencies
pip install pyttsx3
```

### Lỗi SocketIO
```bash
# Cài đặt eventlet
pip install eventlet
```

### Lỗi encoding
- Đảm bảo file .txt là UTF-8
- Hoặc sử dụng file .epub

## 📄 License

MIT License - Xem file LICENSE để biết thêm chi tiết.

## 🤝 Contributing

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push to branch
5. Tạo Pull Request

## 📞 Support

Nếu gặp vấn đề, hãy tạo issue trên GitHub hoặc liên hệ qua email.

---

**Lưu ý**: Đây là phiên bản prototype. Để sử dụng trong production, cần cải thiện bảo mật, performance và error handling.
