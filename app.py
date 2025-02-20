# app.py

from flask import Flask, request, jsonify, send_file, render_template
import os
# ... (기존 import 유지)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'  # 임시 폴더 경로 변경
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

from flask import Flask, request, jsonify, send_file, render_template
import docx2txt
import re
from googletrans import Translator
import pandas as pd
import io
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'  # 업로드 폴더 설정
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 메인 페이지 - 파일 업로드 폼
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/translate', methods=['POST'])
def translate_document():
    try:
        if 'file' not in request.files:
            return '파일을 선택해주세요'
            
        file = request.files['file']
        if not file.filename.endswith('.docx'):
            return 'Word 문서(.docx)만 지원합니다'

        # 파일 저장
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # 문서에서 텍스트 추출
        text = docx2txt.process(filepath)
        
        # 문장 단위로 분리 
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # 번역기 초기화
        translator = Translator()
        
        # 번역 결과를 저장할 리스트
        translations = []
        
        # 각 문장 번역
        for sentence in sentences:
            if sentence.strip():
                eng, kor = translate_text(translator, sentence.strip())
                translations.append({
                    '원문': sentence.strip(),
                    '영어': eng,
                    '한국어': kor
                })
        
        # DataFrame 생성
        df = pd.DataFrame(translations)
        
        # Excel 파일로 변환
        output = io.BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        
        # 임시 파일 삭제
        os.remove(filepath)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='translations.xlsx'
        )
        
    except Exception as e:
        return str(e)

def translate_text(translator, text):
    try:
        detected = translator.detect(text)
        
        if detected.lang != 'en':
            eng_trans = translator.translate(text, dest='en').text
        else:
            eng_trans = text
            
        if detected.lang != 'ko':
            kor_trans = translator.translate(text, dest='ko').text
        else:
            kor_trans = text
            
        return eng_trans, kor_trans
    except Exception as e:
        return text, text


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)