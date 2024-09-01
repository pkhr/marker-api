import os
import tempfile
import warnings
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import shutil

# Suppress specific warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers.tokenization_utils_base")
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers.models.auto.image_processing_auto")

from marker.convert import convert_single_pdf
from marker.models import load_all_models

model_lst = load_all_models()
app = Flask(__name__)

@app.route('/convert', methods=['POST'])
def convert_pdf_to_markdown():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected for uploading'}), 400
    
    if file and file.filename.lower().endswith('.pdf'):
        filename = secure_filename(file.filename)
        temp_dir = tempfile.mkdtemp()
        try:
            pdf_path = os.path.join(temp_dir, filename)
            file.save(pdf_path)
            full_text, images, out_meta = convert_single_pdf(pdf_path, model_lst, ocr_all_pages='')
            # return jsonify({'markdown': full_text, 'images':images, 'out_meta':out_meta}), 200
            return jsonify({'markdown': full_text}), 200
        
        except Exception as e:
            return jsonify({'error': f'Conversion failed: {str(e)}'}), 500
        
        finally:
            # Clean up temporary directory and its contents
            shutil.rmtree(temp_dir, ignore_errors=True)
    else:
        return jsonify({'error': 'Allowed file type is PDF'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)