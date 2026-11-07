@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "FOUND_PYTHON="

for /d %%D in ("%~dp0winpython\WPy64-*") do (
    if exist "%%D\python\python.exe" (
        set "FOUND_PYTHON=%%D\python\python.exe"
        goto :found_python
    )
)

:found_python
if not defined FOUND_PYTHON (
    echo Ошибка: python.exe не найден в winpython\WPy64-*
    pause
    exit /b 1
)

set "PYTHON_EXE=!FOUND_PYTHON!"

if not exist "requirements.txt" (
    echo Ошибка: requirements.txt не найден
    pause
    exit /b 1
)

echo [1/3] Очистка pip-кэша...
"%PYTHON_EXE%" -m pip cache purge

echo.
echo [2/3] Обновление pip...
"%PYTHON_EXE%" -m pip install --upgrade pip --no-user --force-reinstall

echo.
echo [3/3] Установка пакетов БЕЗ кэша и БЕЗ пользовательского каталога...
"%PYTHON_EXE%" -m pip install -r requirements.txt --no-cache-dir --no-user --force-reinstall


echo.
echo Готово!
pause