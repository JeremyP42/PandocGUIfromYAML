@echo off
:: Устанавливаем кодировку UTF-8 для корректного отображения кириллицы

chcp 65001 >nul

setlocal 

set "INSTALL_DIR=%CD%\winpython"
set "PYTHON_EXE="

:: Поиск python.exe
echo [Поиск] Поиск установленного python.exe...

for /r "%INSTALL_DIR%" %%F in (python.exe) do (
    if exist "%%F" (
        set "PYTHON_EXE=%%F"
        goto :found
    )
)

:found
if not defined PYTHON_EXE (
    echo Ошибка: Не найден python.exe в %INSTALL_DIR%
    echo Сначала запустите python_portable_download.bat
    pause
    exit /b 1
)

:: Проверяем наличие requirements.txt
if not exist "requirements.txt" (
    echo Ошибка: Файл requirements.txt не найден в текущей директории.
    pause
    exit /b 1
)

:: Обновляем pip и устанавливаем зависимости
echo Обновление pip...
"%PYTHON_EXE%" -m pip install --upgrade pip

echo Установка зависимостей из requirements.txt...
"%PYTHON_EXE%" -m pip install -r requirements.txt

echo.
echo Все зависимости успешно установлены!
echo.
pause