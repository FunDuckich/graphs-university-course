# быстрый запуск визуализации

1. создать виртуальное окружение из корня проекта:

```powershell
python -m venv .venv
```

2. установить зависимости python:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

3. установить зависимости фронтенда:

```powershell
cd frontend
npm install
```

4. запустить бэк из корня проекта:

```powershell
.\.venv\Scripts\python.exe -m uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

5. запустить фронт в другом терминале:

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

6. открыть:

```text
http://127.0.0.1:5173
```
