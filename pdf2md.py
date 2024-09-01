import os
import tempfile
import warnings
import base64
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import shutil
from io import BytesIO

# Suppress specific warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers.tokenization_utils_base")
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers.models.auto.image_processing_auto")

from marker.convert import convert_single_pdf
from marker.models import load_all_models
from marker.settings import settings

model_lst = load_all_models()
app = Flask(__name__)

def encode_image(image):
    """
    Encode a PIL Image object to a base64 PNG string.
    
    Args:
    image (PIL.Image.Image): The PIL Image object to encode.
    
    Returns:
    str: A base64-encoded string of the PNG image.
    """
    # Create a BytesIO object to store the image data
    buffered = BytesIO()
    
    # Save the image as PNG to the BytesIO object
    image.save(buffered, format="PNG")
    
    # Get the byte string from the BytesIO object
    img_str = buffered.getvalue()
    
    # Encode the byte string to base64
    base64_encoded = base64.b64encode(img_str)
    
    # Convert bytes to string and return
    return base64_encoded.decode('utf-8')
    

@app.route('/convert', methods=['POST'])
def convert_pdf_to_markdown():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'success': False, 'error': 'No file part in the request'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'status': 'error', 'success': False, 'error': 'No file selected for uploading'}), 400
    
    if file and file.filename.lower().endswith(('.pdf')):
        filename = secure_filename(file.filename)
        temp_dir = tempfile.mkdtemp()
        try:
            file_path = os.path.join(temp_dir, filename)
            file.save(file_path)

            # Get parameters from the request
            max_pages = request.form.get('max_pages', type=int)
            langs = request.form.get('langs', {'en'})
            force_ocr = request.form.get('force_ocr', 'false').lower() == 'true'
            settings.PAGINATE_OUTPUT = request.form.get('paginate', 'false').lower() == 'true'
            settings.EXTRACT_IMAGES = request.form.get('extract_images', 'true').lower() == 'true'

            full_text, images, out_meta = convert_single_pdf(
                file_path, 
                model_lst, 
                ocr_all_pages=force_ocr,
                max_pages=max_pages,
                langs=langs
            )

            # Encode images in base64
            encoded_images = {}
            for img_name, img_path in images.items():
                encoded_images[img_name] = encode_image(img_path)

            response = {
                'status': 'success',
                'markdown': full_text,
                'images': encoded_images,
                'success': True,
                'error': "",
                'page_count': out_meta.get('page_count', 0)
            }
            return jsonify(response), 200
        
        except Exception as e:
            return jsonify({
                'status': 'error',
                'markdown': "",
                'images': {},
                'success': False,
                'error': f'Conversion failed: {str(e)}',
                'page_count': 0
            }), 500
        
        finally:
            # Clean up temporary directory and its contents
            shutil.rmtree(temp_dir, ignore_errors=True)
    else:
        return jsonify({
            'status': 'error',
            'markdown': "",
            'images': {},
            'success': False,
            'error': 'Allowed file types are PDF',
            'page_count': 0
        }), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)