# TrackLife — Guia de Deploy no Railway

## Estrutura final do projecto

```
tracklife/
├── app.py              ✅ Backend Flask (corrigido)
├── database.py         ✅ Banco MySQL (corrigido)
├── tracklife.html      ✅ Site completo (HTML+CSS+JS num ficheiro)
├── requirements.txt    ✅ Dependências Python
├── Procfile            ✅ Comando de arranque
├── nixpacks.toml       ✅ Instala o Tesseract no servidor
└── uploads/            (criado automaticamente)
    ├── desaparecidos/
    ├── documentos/
    └── bi/
```

---

## Passo 1 — Colocar o tracklife.html na pasta

Copia o ficheiro `tracklife.html` (gerado anteriormente) para esta mesma pasta.

---

## Passo 2 — Subir para o GitHub

1. Cria uma conta em github.com (se não tiveres)
2. Cria um repositório novo chamado `tracklife`
3. Faz upload de todos os ficheiros desta pasta

---

## Passo 3 — Deploy no Railway

1. Acede a **railway.app** e cria conta (grátis)
2. Clica em **"New Project"**
3. Escolhe **"Deploy from GitHub repo"**
4. Selecciona o teu repositório `tracklife`

---

## Passo 4 — Adicionar MySQL

1. No projecto Railway, clica em **"+ New"**
2. Escolhe **"Database" → "MySQL"**
3. O Railway cria automaticamente a variável `DATABASE_URL`
4. O teu `database.py` já a lê automaticamente ✅

---

## Passo 5 — O site fica disponível

O Railway dá-te um URL tipo:
```
https://tracklife-production.up.railway.app
```

Este URL é o teu site! Partilha com quem quiseres.

---

## Melhorias futuras (sem perder nada)

Para actualizar o site depois:
1. Edita os ficheiros localmente
2. Faz upload para o GitHub
3. O Railway faz o deploy automaticamente ✅
