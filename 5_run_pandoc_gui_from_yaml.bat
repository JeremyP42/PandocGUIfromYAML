@echo off
setlocal

set "WINPYTHON_DIR=%~dp0winpython"
set "SCRIPT_PATH=%~dp0pandoc_gui_from_yaml.py"

if not exist "%WINPYTHON_DIR%\" (
    echo Ошибка: папка 'winpython' не найдена.
    echo Ожидалась: "%WINPYTHON_DIR%"
    pause
    exit /b 1
)

REM Ищем WPy* без использования enabledelayedexpansion
set "PYTHON_EXE="

for /d %%D in ("%WINPYTHON_DIR%\WPy*") do (
    if exist "%%D\python\python.exe" (
        set "PYTHON_EXE=%%D\python\python.exe"
        goto :found
    )
)

REM Если не найдено — проверяем альтернативные места
for /d %%D in ("%WINPYTHON_DIR%\WPy*") do (
    if exist "%%D\python.exe" (
        set "PYTHON_EXE=%%D\python.exe"
        goto :found
    )
)

if exist "%WINPYTHON_DIR%\python.exe" (
    set "PYTHON_EXE=%WINPYTHON_DIR%\python.exe"
    goto :found
)

echo Ошибка: не найден python.exe в подпапках WPy* или в winpython\.
echo Проверьте структуру папки "%WINPYTHON_DIR%"
pause
exit /b 1

:found
REM На этом этапе PYTHON_EXE установлен, и мы можем его использовать
if not exist "%SCRIPT_PATH%" (
    echo Ошибка: не найден скрипт "%SCRIPT_PATH%"
    pause
    exit /b 1
)

"%PYTHON_EXE%" "%SCRIPT_PATH%"

if errorlevel 1 (
    echo.
    echo Скрипт завершился с ошибкой.
    pause
)