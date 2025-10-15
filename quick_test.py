#!/usr/bin/env python3
"""
Quick test cho TTS
"""

from tts_engine import TTSEngine

def main():
    print("🧪 Quick TTS Test")
    print("=" * 30)
    
    tts = TTSEngine()
    
    if tts.engine is None:
        print("❌ TTS engine not available")
        return
    
    print("✅ TTS engine initialized")
    
    # Test với text ngắn
    test_texts = [
        "Xin chào",
        "Tôi tên là Lan",
        "Đây là một câu chuyện",
        "Tôi thích đọc sách",
        "Hôm nay trời đẹp"
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n📝 Test {i}: '{text}'")
        print("🔊 Playing...")
        tts.speak_text(text, 'north')
        print("✅ Done")
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    main()
