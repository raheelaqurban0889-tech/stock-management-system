@echo off
echo Starting Web-based Stock, Inventory and Sales Management System...

:: Yeh line current folder par switch kar degi
cd /d %~dp0

:: Agar venv folder mojood hai toh usay activate karo
IF EXIST venv\Scripts\activate (
    echo Activating Virtual Environment...
    call venv\Scripts\activate
) ELSE (
    echo Virtual environment not found. Running with system Python...
)

:: Start the Django development server
python manage.py runserver

pause