import os
import re
from typing import List, Tuple

class TextProcessor:
    def __init__(self):
        self.words_per_page = 50  # Giảm số từ mỗi trang để tránh đánh vần
        self.sentences_per_page = 5  # Giảm số câu mỗi trang
        
    def extract_text(self, file_path: str) -> str:
        """Trích xuất text từ file txt hoặc epub"""
        file_extension = file_path.split('.')[-1].lower()
        
        if file_extension == 'txt':
            return self._extract_from_txt(file_path)
        elif file_extension == 'epub':
            return self._extract_from_epub(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
    
    def _extract_from_txt(self, file_path: str) -> str:
        """Trích xuất text từ file .txt"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            return self._clean_text(content)
        except UnicodeDecodeError:
            # Thử với encoding khác
            with open(file_path, 'r', encoding='cp1252') as file:
                content = file.read()
            return self._clean_text(content)
    
    def _extract_from_epub(self, file_path: str) -> str:
        """Trích xuất text từ file .epub (đơn giản)"""
        # Trong thực tế sẽ cần thư viện như ebooklib
        # Tạm thời xử lý như txt
        return self._extract_from_txt(file_path)
    
    def _clean_text(self, text: str) -> str:
        """Làm sạch text"""
        # Loại bỏ ký tự đặc biệt
        text = re.sub(r'[^\w\s.,!?;:()\-]', '', text)
        # Chuẩn hóa khoảng trắng
        text = re.sub(r'\s+', ' ', text)
        # Loại bỏ dòng trống
        text = re.sub(r'\n\s*\n', '\n', text)
        return text.strip()
    
    def split_into_pages(self, text: str) -> List[str]:
        """Chia text thành các trang"""
        # Tách thành câu
        sentences = self._split_into_sentences(text)
        
        pages = []
        current_page = []
        current_word_count = 0
        
        for sentence in sentences:
            word_count = len(sentence.split())
            
            # Nếu thêm câu này vượt quá giới hạn, tạo trang mới
            if current_word_count + word_count > self.words_per_page and current_page:
                pages.append(' '.join(current_page))
                current_page = [sentence]
                current_word_count = word_count
            else:
                current_page.append(sentence)
                current_word_count += word_count
        
        # Thêm trang cuối nếu còn text
        if current_page:
            pages.append(' '.join(current_page))
        
        return pages
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Tách text thành câu"""
        # Pattern để tách câu tiếng Việt
        sentence_endings = r'[.!?]+'
        sentences = re.split(sentence_endings, text)
        
        # Làm sạch và lọc câu rỗng
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence.split()) > 2:  # Ít nhất 3 từ
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences
    
    def get_page_info(self, pages: List[str]) -> List[dict]:
        """Lấy thông tin chi tiết về các trang"""
        page_info = []
        for i, page in enumerate(pages):
            page_info.append({
                'page_number': i,
                'word_count': len(page.split()),
                'char_count': len(page),
                'preview': page[:100] + '...' if len(page) > 100 else page
            })
        return page_info
