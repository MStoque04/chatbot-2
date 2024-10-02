import openai
import os
import fitz  
from flask import Flask, request, jsonify, render_template, session
from werkzeug.utils import secure_filename
from docx import Document

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Defina a chave da API diretamente no código 
openai.api_key = ""

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True) 
app.config['UPLOAD_FOLDER']=UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message")
    
    if 'file_path' in session:
        file_path = session['file_path']
        file_content = extract_text(file_path)
        
        response = openai.ChatCompletion.create(
            model='gpt-4o',
            messages=[
                {"role": "system", "content": "Você é um assistente útil que responde perguntas baseado no documento fornecido. Quando for dar as respostas, não reescreva o que está no documento, apenas faça um resumo e respoonda de forma objetiva ao que o usuario pedir"},
                {"role": "user", "content": f"O conteúdo do documento é:\n{file_content}"},
                {"role": "user", "content": user_message}
            ]
        )

        response_message = response['choices'][0]['message']['content']
        return jsonify({"response": response_message})
    else:
        return jsonify({"error": "Nenhum arquivo foi enviado ou processado."}), 400

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        session['file_path'] = file_path
        
        return jsonify({"response": "Arquivo carregado e processado com sucesso."})

def extract_text(file_path):
    if file_path.endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    elif file_path.endswith('.docx'):
        return extract_text_from_word(file_path)
    else:
        return ""

def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_text_from_word(file_path):
    doc = Document(file_path)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

if __name__ == '__main__':
    app.run(debug=True)
