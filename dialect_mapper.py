import re
from typing import Dict, List

class DialectMapper:
    def __init__(self):
        # Từ điển mapping cho các vùng miền
        self.dialect_mappings = {
            'north': {
                # Giọng Bắc - giữ nguyên hoặc thay đổi nhẹ
                'rứa': 'vậy',
                'hắn': 'nó',
                'mần chi': 'làm gì',
                'răng': 'sao',
                'mô': 'đâu',
                'tê': 'kia',
                'ni': 'này',
                'rồi': 'rồi',
                'mô răng': 'sao vậy',
                'chi rứa': 'gì vậy'
            },
            'central': {
                # Giọng Trung - giữ nguyên từ địa phương
                'rứa': 'rứa',
                'hắn': 'hắn', 
                'mần chi': 'mần chi',
                'răng': 'răng',
                'mô': 'mô',
                'tê': 'tê',
                'ni': 'ni',
                'rồi': 'rồi',
                'mô răng': 'mô răng',
                'chi rứa': 'chi rứa'
            },
            'south': {
                # Giọng Nam - chuyển đổi sang từ Nam Bộ
                'rứa': 'vậy',
                'hắn': 'ổng/bả',
                'mần chi': 'làm chi',
                'răng': 'sao',
                'mô': 'đâu',
                'tê': 'kia',
                'ni': 'này',
                'rồi': 'rồi',
                'mô răng': 'sao vậy',
                'chi rứa': 'gì vậy'
            }
        }
        
        # Pattern để nhận diện từ địa phương
        self.dialect_patterns = {
            'central': [
                r'\brứa\b', r'\bhắn\b', r'\bmần chi\b', r'\brăng\b',
                r'\bmô\b', r'\btê\b', r'\bni\b', r'\bchi rứa\b'
            ],
            'north': [
                r'\bvậy\b', r'\bnó\b', r'\blàm gì\b', r'\bsao\b',
                r'\bđâu\b', r'\bkia\b', r'\bnày\b', r'\bgì vậy\b'
            ],
            'south': [
                r'\bvậy\b', r'\bổng\b', r'\bbả\b', r'\blàm chi\b',
                r'\bsao\b', r'\bđâu\b', r'\bkia\b', r'\bnày\b'
            ]
        }
    
    def transform_text(self, text: str, target_dialect: str) -> str:
        """Chuyển đổi text theo vùng miền"""
        if target_dialect not in self.dialect_mappings:
            return text
        
        mapping = self.dialect_mappings[target_dialect]
        transformed_text = text
        
        # Áp dụng mapping từng từ
        for original, replacement in mapping.items():
            # Sử dụng word boundary để tránh thay thế nhầm
            pattern = r'\b' + re.escape(original) + r'\b'
            transformed_text = re.sub(pattern, replacement, transformed_text, flags=re.IGNORECASE)
        
        return transformed_text
    
    def detect_dialect(self, text: str) -> str:
        """Tự động phát hiện vùng miền của text"""
        dialect_scores = {'north': 0, 'central': 0, 'south': 0}
        
        for dialect, patterns in self.dialect_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                dialect_scores[dialect] += len(matches)
        
        # Trả về dialect có điểm cao nhất
        return max(dialect_scores, key=dialect_scores.get)
    
    def get_dialect_features(self, text: str) -> Dict[str, List[str]]:
        """Lấy các đặc điểm vùng miền trong text"""
        features = {
            'central_words': [],
            'north_words': [],
            'south_words': []
        }
        
        # Tìm từ Trung
        for pattern in self.dialect_patterns['central']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            features['central_words'].extend(matches)
        
        # Tìm từ Bắc
        for pattern in self.dialect_patterns['north']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            features['north_words'].extend(matches)
        
        # Tìm từ Nam
        for pattern in self.dialect_patterns['south']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            features['south_words'].extend(matches)
        
        return features
    
    def add_custom_mapping(self, dialect: str, original: str, replacement: str):
        """Thêm mapping tùy chỉnh"""
        if dialect not in self.dialect_mappings:
            self.dialect_mappings[dialect] = {}
        
        self.dialect_mappings[dialect][original] = replacement
    
    def get_available_dialects(self) -> List[str]:
        """Lấy danh sách các vùng miền có sẵn"""
        return list(self.dialect_mappings.keys())
