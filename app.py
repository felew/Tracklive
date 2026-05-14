from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import os
import database

app = Flask(__name__)
CORS(app)

# ── PASTA BASE (onde está este ficheiro) ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── TESSERACT (só activo se instalado) ──
try:
    import pytesseract
    from PIL import Image
    TESSERACT_OK = True
except:
    TESSERACT_OK = False

# ── SERVIR O SITE (ficheiro único) ──
@app.route('/')
def home():
    return send_from_directory(BASE_DIR, 'tracklife.html')

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({'status': 'online', 'sistema': 'TrackLife'})

# ── SERVIR UPLOADS (fotos dos desaparecidos) ──
@app.route('/uploads/desaparecidos/<filename>')
def foto_desaparecido(filename):
    return send_from_directory(
        os.path.join(BASE_DIR, 'uploads', 'desaparecidos'), filename
    )

# ── REGISTAR ──
@app.route('/api/registar', methods=['POST'])
def registar():
    try:
        nome      = request.form.get('nome')
        email     = request.form.get('email')
        password  = request.form.get('password')
        bi_file   = request.files.get('bi_file')
        provincia = request.form.get('provincia')
        municipio = request.form.get('municipio')
        morada    = request.form.get('morada')

        if not nome or not email or not password:
            return jsonify({'status': 'erro', 'message': 'Preencha todos os campos'}), 400

        hashed_password = generate_password_hash(password)

        # Guardar BI se enviado
        bi = email.split('@')[0]  # fallback
        if bi_file and bi_file.filename:
            pasta_bi = os.path.join(BASE_DIR, 'uploads', 'bi')
            os.makedirs(pasta_bi, exist_ok=True)
            caminho = os.path.join(pasta_bi, bi_file.filename)
            bi_file.save(caminho)

            # Tentar OCR se Tesseract disponível
            if TESSERACT_OK:
                try:
                    import cv2, re
                    img_cv = cv2.imread(caminho)
                    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
                    gray = cv2.GaussianBlur(gray, (3, 3), 0)
                    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    try:
                        texto = pytesseract.image_to_string(thresh, lang='por').upper()
                    except:
                        texto = pytesseract.image_to_string(thresh).upper()

                    if "REPUBLICA DE ANGOLA" not in texto and "BILHETE DE IDENTIDADE" not in texto:
                        return jsonify({'status': 'erro', 'message': 'Documento inválido. Use o seu BI de Angola'}), 400

                    bi_numero = re.search(r'\b\d{9}[A-Z]{2}\d{3}\b', texto)
                    if bi_numero:
                        bi = bi_numero.group()
                except Exception as ocr_err:
                    print(f"OCR falhou (não crítico): {ocr_err}")

        conn = database.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM cidadaos WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close(); conn.close()
            return jsonify({'status': 'erro', 'message': 'Email já registado'}), 400

        cursor.execute("""
            INSERT INTO cidadaos (nome, bi, email, password, tipo, provincia, municipio, morada)
            VALUES (%s, %s, %s, %s, 'cidadao', %s, %s, %s)
        """, (nome, bi, email, hashed_password, provincia, municipio, morada))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'status': 'success', 'message': f'Cidadão {nome} registado com sucesso!'})

    except Exception as e:
        return jsonify({'status': 'erro', 'message': str(e)}), 500

# ── LOGIN ──
@app.route('/api/login', methods=['POST'])
def login():
    try:
        email    = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            return jsonify({'status': 'erro', 'message': 'Preencha todos os campos'}), 400

        conn = database.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM cidadaos WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user:
            return jsonify({'status': 'erro', 'message': 'Email não encontrado'}), 401

        if not check_password_hash(user['password'], password):
            return jsonify({'status': 'erro', 'message': 'Password incorrecta'}), 401

        return jsonify({
            'status': 'success',
            'message': 'Login efectuado com sucesso!',
            'user': {
                'id': user['id'],
                'nome': user['nome'],
                'email': user['email'],
                'tipo': user['tipo']
            }
        })

    except Exception as e:
        return jsonify({'status': 'erro', 'message': str(e)}), 500

# ── PUBLICAR DESAPARECIDO ──
@app.route('/api/desaparecidos', methods=['POST'])
def publicar_desaparecido():
    try:
        nome       = request.form.get('nome')
        idade      = request.form.get('idade')
        localizacao= request.form.get('localizacao')
        descricao  = request.form.get('descricao')
        contacto   = request.form.get('contacto')
        data_desap = request.form.get('data')
        foto       = request.files.get('foto')
        doc_bi     = request.files.get('doc_bi')
        doc_cedula = request.files.get('doc_cedula')
        doc_vacina = request.files.get('doc_vacina')

        if not nome or not localizacao:
            return jsonify({'status': 'erro', 'message': 'Nome e localização obrigatórios'}), 400

        pasta_fotos = os.path.join(BASE_DIR, 'uploads', 'desaparecidos')
        pasta_docs  = os.path.join(BASE_DIR, 'uploads', 'documentos')
        os.makedirs(pasta_fotos, exist_ok=True)
        os.makedirs(pasta_docs,  exist_ok=True)

        foto_path = None
        if foto and foto.filename:
            foto.save(os.path.join(pasta_fotos, foto.filename))
            foto_path = f'uploads/desaparecidos/{foto.filename}'

        for doc, nome_doc in [(doc_bi,'doc_bi'),(doc_cedula,'doc_cedula'),(doc_vacina,'doc_vacina')]:
            if doc and doc.filename:
                doc.save(os.path.join(pasta_docs, doc.filename))

        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO desaparecidos (nome, idade, localizacao, descricao, foto, status)
            VALUES (%s, %s, %s, %s, %s, 'desaparecido')
        """, (nome, idade, localizacao, descricao, foto_path))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'status': 'success', 'message': f'{nome} publicado com sucesso!'})

    except Exception as e:
        return jsonify({'status': 'erro', 'message': str(e)}), 500

# ── LISTAR DESAPARECIDOS ──
@app.route('/api/desaparecidos', methods=['GET'])
def listar_desaparecidos():
    try:
        limit  = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        conn = database.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM desaparecidos ORDER BY criado_em DESC LIMIT %s OFFSET %s",
            (limit, offset)
        )
        data = cursor.fetchall()
        cursor.close()
        conn.close()

        for d in data:
            if d.get('criado_em'):
                d['criado_em'] = str(d['criado_em'])

        return jsonify({'status': 'success', 'desaparecidos': data})

    except Exception as e:
        return jsonify({'status': 'erro', 'message': str(e)}), 500

# ── LOCALIZAR CIDADÃO ──
@app.route('/api/localizar', methods=['POST'])
def localizar():
    try:
        dados = request.get_json()
        cidadao_id = dados.get('cidadao_id')
        lat = dados.get('latitude')
        lng = dados.get('longitude')

        if not cidadao_id or not lat or not lng:
            return jsonify({'status': 'erro', 'message': 'Dados incompletos'}), 400

        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE cidadaos SET latitude=%s, longitude=%s WHERE id=%s",
            (lat, lng, cidadao_id)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'status': 'success', 'message': 'Localização guardada'})

    except Exception as e:
        return jsonify({'status': 'erro', 'message': str(e)}), 500

# ── LOGIN INSTITUIÇÃO ──
@app.route('/api/login/instituicao', methods=['POST'])
def login_instituicao():
    try:
        email   = request.form.get('email', '').strip()
        password= request.form.get('password', '').strip()
        codigo  = request.form.get('codigo', '').strip()

        CODIGOS_VALIDOS = {
            'PNA2025':   'Polícia Nacional',
            'MINSA2025': 'Hospital / Clínica',
            'ONG2025':   'ONG',
            'GUARD2025': 'Guarda Fronteira',
        }

        if not email or not password or not codigo:
            return jsonify({'status': 'error', 'message': 'Campos obrigatórios em falta'}), 400

        if codigo not in CODIGOS_VALIDOS:
            return jsonify({'status': 'error', 'message': 'Código de acesso inválido'}), 401

        return jsonify({
            'status': 'success',
            'user': {
                'nome': email.split('@')[0],
                'tipo': CODIGOS_VALIDOS[codigo],
                'email': email
            }
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ── LISTAR DOCUMENTOS ──
@app.route('/api/documentos', methods=['GET'])
def listar_documentos():
    try:
        pasta_docs = os.path.join(BASE_DIR, 'uploads', 'documentos')
        if not os.path.exists(pasta_docs):
            return jsonify({'status': 'success', 'documentos': []})

        documentos = []
        for filename in os.listdir(pasta_docs):
            caminho = os.path.join(pasta_docs, filename)
            tamanho = os.path.getsize(caminho)
            documentos.append({
                'nome': filename,
                'filename': filename,
                'tipo': 'BI' if 'bi' in filename.lower() else 'Cédula' if 'cedula' in filename.lower() else 'Documento',
                'tamanho': f'{round(tamanho/1024, 1)} KB',
                'path': f'uploads/documentos/{filename}'
            })

        return jsonify({'status': 'success', 'documentos': documentos})

    except Exception as e:
        return jsonify({'status': 'erro', 'message': str(e)}), 500

if __name__ == '__main__':
    print("--- INICIANDO TRACKLIFE ---")
    try:
        database.init_db()
    except Exception as db_err:
        print(f"Erro no Banco: {db_err}")

port = int(os.environ.get('PORT', 8080))
app.run(debug=False, host='0.0.0.0', port=port)
