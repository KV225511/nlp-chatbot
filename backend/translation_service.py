"""
Multi-language translation service for CosmosBot.
Uses googletrans for translating user input and bot responses.
"""

try:
    from googletrans import Translator, LANGUAGES
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False


class TranslationService:
    """
    Handles multi-language support:
    - Detects input language
    - Translates user input to English for model processing
    - Translates bot response back to user's preferred language
    """
    
    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'hi': 'Hindi',
        'ta': 'Tamil',
        'te': 'Telugu',
        'bn': 'Bengali',
        'mr': 'Marathi',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'ja': 'Japanese',
        'ko': 'Korean',
        'zh-cn': 'Chinese (Simplified)'
    }
    
    def __init__(self):
        if TRANSLATOR_AVAILABLE:
            try:
                self.translator = Translator()
            except Exception:
                self.translator = None
                print("⚠️ Google Translate init failed. Translation disabled.")
        else:
            self.translator = None
            print("⚠️ googletrans not available. Translation disabled.")
    
    def translate_to_english(self, text, source_lang='auto'):
        """
        Translate text to English for model processing.
        
        Args:
            text: Input text in any language
            source_lang: Source language code (or 'auto' for detection)
            
        Returns:
            dict: { translated_text, detected_lang, original_text }
        """
        if not self.translator or source_lang == 'en':
            return {
                'translated_text': text,
                'detected_lang': 'en',
                'original_text': text
            }
        
        try:
            result = self.translator.translate(text, dest='en', src=source_lang if source_lang != 'auto' else 'auto')
            return {
                'translated_text': result.text,
                'detected_lang': result.src,
                'original_text': text
            }
        except Exception as e:
            print(f"Translation error: {e}")
            return {
                'translated_text': text,
                'detected_lang': 'en',
                'original_text': text
            }
    
    def translate_from_english(self, text, target_lang):
        """
        Translate English bot response to target language.
        
        Args:
            text: English text to translate
            target_lang: Target language code
            
        Returns:
            str: Translated text
        """
        if not self.translator or target_lang == 'en':
            return text
        
        try:
            result = self.translator.translate(text, dest=target_lang, src='en')
            return result.text
        except Exception as e:
            print(f"Translation error: {e}")
            return text
    
    def detect_language(self, text):
        """
        Detect the language of input text.
        
        Returns:
            str: Language code
        """
        if not self.translator:
            return 'en'
        
        try:
            detected = self.translator.detect(text)
            return detected.lang
        except Exception:
            return 'en'
    
    def get_supported_languages(self):
        """Return dict of supported language codes and names."""
        return self.SUPPORTED_LANGUAGES


if __name__ == '__main__':
    ts = TranslationService()
    print("Supported languages:", ts.get_supported_languages())
    
    if ts.translator:
        # Test Hindi
        result = ts.translate_to_english("ब्लैक होल क्या है", source_lang='hi')
        print(f"Hindi → English: {result}")
        
        # Test English to Hindi
        translated = ts.translate_from_english("Black holes are fascinating!", 'hi')
        print(f"English → Hindi: {translated}")
