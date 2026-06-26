# Linux/Mac
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

cp .env.sample .env

python run.py

# docker
docker build -t mini-collaborator .
docker run -p 8000:8000 --env-file .env mini-collaborator