# Use uma imagem base do Python
FROM python:3.11-slim

# Define o diretório de trabalho
WORKDIR /app

# Copia o arquivo de requisitos e instala as dependências
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copia o restante do código para o container
COPY . .

# Expõe a porta (no nosso caso, 8000)
EXPOSE 8000

# Comando para iniciar o servidor Uvicorn com FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
