from flask import Flask, request, send_file, jsonify
from pylatex import Document, Section, Package
from pylatex.utils import NoEscape
import os
import subprocess
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import logging
import logging.handlers
from datetime import datetime

load_dotenv()

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'temp'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Configure logging
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(process)d] - %(message)s')
log_handler = logging.handlers.RotatingFileHandler('latex_converter.log', maxBytes=1024*1024, backupCount=5)
log_handler.setFormatter(log_formatter)

logger = logging.getLogger('latex_converter')
logger.setLevel(logging.DEBUG)
logger.addHandler(log_handler)

@app.route('/convert-code', methods=['POST'])
def convert_latex_code_to_pdf():
    try:
        logger.info('Starting new LaTeX conversion request')
        # Get LaTeX code from request body
        data = request.get_json()
        if not data or 'latex_code' not in data:
            logger.error('Missing latex_code in request body')
            return jsonify({'error': 'latex_code is required in request body'}), 400
            
        latex_code = data['latex_code'].replace("```latex", "").replace("```", "")
        if not latex_code.strip():
            logger.error('Empty latex_code provided')
            return jsonify({'error': 'latex_code cannot be empty'}), 400
        
        file_name = data['file_name']
        if not file_name.strip():
            logger.error('Empty file_name provided')
            return jsonify({'error': 'file_name cannot be empty'}), 400

        # Create a temporary directory for compilation
        temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        logger.debug(f'Using temporary directory: {temp_dir}')

        # Generate unique filename
        filename = secure_filename(f'latex_{os.urandom(8).hex()}')
        filepath = os.path.join(temp_dir, filename)
        logger.debug(f'Generated unique filename: {filename}')

        # Write the LaTeX content to a .tex file
        with open(f'{filepath}.tex', 'w', encoding='utf-8') as f:
            f.write(latex_code)
        logger.info(f'LaTeX content written to {filepath}.tex')

        # Generate PDF using pdflatex
        try:
            logger.info('Starting first pdflatex compilation')
            process = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', '-output-directory', temp_dir, f'{filepath}.tex'],
                capture_output=True,
                text=True,
                check=True
            )
            logger.debug(f'First compilation output: {process.stdout}')
            
            # Run twice for references and table of contents
            logger.info('Starting second pdflatex compilation')
            process = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', '-output-directory', temp_dir, f'{filepath}.tex'],
                capture_output=True,
                text=True,
                check=True
            )
            logger.debug(f'Second compilation output: {process.stdout}')
        except subprocess.CalledProcessError as e:
            logger.error(f'LaTeX compilation failed: {e.stderr}')
            return jsonify({
                'error': f'LaTeX compilation failed: {e.stderr}'
            }), 500

        # Send the PDF file
        if not os.path.exists(f'{filepath}.pdf'):
            logger.error('PDF file not found after compilation')
            return jsonify({'error': 'PDF generation failed - output file not found'}), 500
            
        logger.info('PDF generated successfully')
        return send_file(f'{filepath}.pdf', as_attachment=True)

    except Exception as e:
        logger.error(f'Unexpected error: {str(e)}', exc_info=True)
        return jsonify({'error': str(e)}), 500

    finally:
        # Cleanup all temporary files
        try:
            logger.info('Starting cleanup of temporary files')
            # Add a small delay to ensure file handles are released
            import time
            time.sleep(2.0)  # 2000ms delay
            
            # List of common LaTeX auxiliary file extensions
            aux_extensions = ['.aux', '.log', '.out', '.toc', '.lof', '.lot', '.bbl', '.blg']
            
            # Remove the main output files with retry mechanism
            for ext in ['.pdf', '.tex'] + aux_extensions:
                temp_file = f'{filepath}{ext}'
                max_retries = 3
                retry_delay = 0.5
                
                for attempt in range(max_retries):
                    try:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                            logger.debug(f'Successfully removed {temp_file}')
                        break
                    except Exception as e:
                        if attempt == max_retries - 1:  # Last attempt
                            logger.error(f'Failed to remove {temp_file} after {max_retries} attempts: {str(e)}')
                        else:
                            logger.debug(f'Retry {attempt + 1} to remove {temp_file}')
                            time.sleep(retry_delay)
                            continue
        except Exception as e:
            logger.error(f'Error during cleanup: {str(e)}', exc_info=True)
            pass

@app.route('/convert-file', methods=['POST'])
def convert_latex_file_to_pdf():
    try:
        # Read LaTeX code from input.tex file
        input_file = os.path.join(os.path.dirname(__file__), 'input.tex')
        if not os.path.exists(input_file):
            return jsonify({'error': 'input.tex file not found'}), 404

        with open(input_file, 'r', encoding='utf-8') as f:
            latex_code = f.read()

        if not latex_code.strip():
            return jsonify({'error': 'input.tex file is empty'}), 400

        # Create a temporary directory for compilation
        temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
        os.makedirs(temp_dir, exist_ok=True)

        # Generate unique filename
        filename = secure_filename(f'latex_{os.urandom(8).hex()}')
        filepath = os.path.join(temp_dir, filename)

        # Write the LaTeX content to a .tex file
        with open(f'{filepath}.tex', 'w', encoding='utf-8') as f:
            f.write(latex_code)

        # Generate PDF using pdflatex
        try:
            process = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', '-output-directory', temp_dir, f'{filepath}.tex'],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Run twice for references and table of contents
            subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', '-output-directory', temp_dir, f'{filepath}.tex'],
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            return jsonify({
                'error': f'LaTeX compilation failed: {e.stderr}'
            }), 500

        # Send the PDF file
        if not os.path.exists(f'{filepath}.pdf'):
            return jsonify({'error': 'PDF generation failed - output file not found'}), 500
            
        return send_file(f'{filepath}.pdf', as_attachment=True)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        # Cleanup all temporary files
        try:
            # Add a small delay to ensure file handles are released
            import time
            time.sleep(2.0)  # 2000ms delay
            
            # List of common LaTeX auxiliary file extensions
            aux_extensions = ['.aux', '.log', '.out', '.toc', '.lof', '.lot', '.bbl', '.blg']
            
            # Remove the main output files with retry mechanism
            for ext in ['.pdf', '.tex'] + aux_extensions:
                temp_file = f'{filepath}{ext}'
                max_retries = 3
                retry_delay = 0.5
                
                for attempt in range(max_retries):
                    try:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                        break
                    except Exception as e:
                        if attempt == max_retries - 1:  # Last attempt
                            print(f'Failed to remove {temp_file} after {max_retries} attempts: {str(e)}')
                        else:
                            time.sleep(retry_delay)
                            continue
        except Exception as e:
            print(f'Error during cleanup: {str(e)}')
            pass

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5678)