import os
import mysql.connector
from urllib.parse import urlparse

def get_connection():
    # Railway fornece DATABASE_URL automaticamente
    # Formato: mysql://user:password@host:port/database
    db_url = os.environ.get('DATABASE_URL')

    if db_url:
        # Usar a URL do Railway
        parsed = urlparse(db_url)
        return mysql.connector.connect(
            host=parsed.hostname,
            port=parsed.port or 3306,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path.lstrip('/'),
            connection_timeout=10,
            use_pure=True
        )
    else:
        # Fallback local (desenvolvimento no teu PC)
        return mysql.connector.connect(
            host=os.environ.get('DB_HOST', '127.0.0.1'),
            port=int(os.environ.get('DB_PORT', 3306)),
            user=os.environ.get('DB_USER', 'root'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tracklife'),
            connection_timeout=10,
            use_pure=True
        )

def criar_tabelas():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cidadaos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            bi VARCHAR(20) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            tipo VARCHAR(20) DEFAULT 'cidadao',
            provincia VARCHAR(100),
            municipio VARCHAR(100),
            morada VARCHAR(255),
            latitude DECIMAL(10,8),
            longitude DECIMAL(11,8),
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    colunas_novas = [
        "ALTER TABLE cidadaos ADD COLUMN IF NOT EXISTS provincia VARCHAR(100)",
        "ALTER TABLE cidadaos ADD COLUMN IF NOT EXISTS municipio VARCHAR(100)",
        "ALTER TABLE cidadaos ADD COLUMN IF NOT EXISTS morada VARCHAR(255)",
        "ALTER TABLE cidadaos ADD COLUMN IF NOT EXISTS latitude DECIMAL(10,8)",
        "ALTER TABLE cidadaos ADD COLUMN IF NOT EXISTS longitude DECIMAL(11,8)",
    ]
    for sql in colunas_novas:
        try:
            cursor.execute(sql)
        except:
            pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS desaparecidos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            idade INT,
            genero VARCHAR(10),
            localizacao VARCHAR(200),
            latitude_desap DECIMAL(10,8),
            longitude_desap DECIMAL(11,8),
            descricao TEXT,
            foto VARCHAR(255),
            status VARCHAR(20) DEFAULT 'desaparecido',
            registado_por INT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (registado_por) REFERENCES cidadaos(id)
        )
    """)

    colunas_desap = [
        "ALTER TABLE desaparecidos ADD COLUMN IF NOT EXISTS latitude_desap DECIMAL(10,8)",
        "ALTER TABLE desaparecidos ADD COLUMN IF NOT EXISTS longitude_desap DECIMAL(11,8)",
    ]
    for sql in colunas_desap:
        try:
            cursor.execute(sql)
        except:
            pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS avistamentos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            desaparecido_id INT,
            descricao TEXT,
            localizacao VARCHAR(200),
            foto VARCHAR(255),
            reportado_por INT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (desaparecido_id) REFERENCES desaparecidos(id),
            FOREIGN KEY (reportado_por) REFERENCES cidadaos(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS autoridades (
            id INT AUTO_INCREMENT PRIMARY KEY,
            cidadao_id INT UNIQUE,
            badge VARCHAR(50) UNIQUE NOT NULL,
            departamento VARCHAR(100),
            nivel_acesso INT DEFAULT 1,
            FOREIGN KEY (cidadao_id) REFERENCES cidadaos(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notificacoes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            cidadao_id INT,
            desaparecido_id INT,
            mensagem TEXT,
            distancia_km DECIMAL(6,2),
            lida BOOLEAN DEFAULT FALSE,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cidadao_id) REFERENCES cidadaos(id),
            FOREIGN KEY (desaparecido_id) REFERENCES desaparecidos(id)
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Todas as tabelas criadas com sucesso!", flush=True)

def init_db():
    criar_tabelas()
    print("✅ Banco de dados iniciado com sucesso!", flush=True)

# Criar tabelas ao importar
try:
    criar_tabelas()
except Exception as e:
    print(f"⚠️ Aviso ao criar tabelas: {e}", flush=True)
