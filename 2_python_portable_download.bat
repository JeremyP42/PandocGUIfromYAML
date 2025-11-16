@echo off
:: Устанавливаем кодировку UTF-8 для корректного отображения кириллицы
chcp 65001 >nul

setlocal 

:: Настройки
set "PYTHON_URL=https://github.com/winpython/winpython/releases/download/17.2.20251012/WinPython64-3.13.8.0dotb1.zip"
set "ARCHIVE_NAME= WinPython64-3.13.8.0dotb1.zip"
set "INSTALL_DIR=%CD%\winpython"

:: Проверяем, существует ли уже установленный Python
if exist "%INSTALL_DIR%" (
    echo [Проверка] Установленная директория Python уже существует: %INSTALL_DIR%
    echo Удалите её или продолжите использование существующей.
    goto :find_python_path
)

:: Создаем папку для установки
mkdir "%INSTALL_DIR%"

:: 1. Скачивание WinPython
echo [1/3] Скачивание WinPython...
powershell -Command "Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%ARCHIVE_NAME%'"

:: 2. Распаковка ZIP-архива
echo [2/3] Распаковка архива...
powershell -Command "Expand-Archive -Path '%ARCHIVE_NAME%' -DestinationPath '%INSTALL_DIR%' -Force"

:: Чистим временные файлы
del /q "%ARCHIVE_NAME%"

:: Глубокий поиск python.exe
:find_python_path
set "PYTHON_EXE="

echo [Поиск] Поиск python.exe во всех подкаталогах...

for /r "%INSTALL_DIR%" %%F in (python.exe) do (
    if exist "%%F" (
        set "PYTHON_EXE=%%F"
        set "SCRIPTS_DIR=%%~dpFscripts"
        goto :found_python
    )
)

:found_python
if not defined PYTHON_EXE (
    echo Ошибка: Не найден python.exe внутри директории:
    echo     %INSTALL_DIR%
    echo Возможно, структура архива изменилась или произошла ошибка при распаковке.
    pause
    exit /b 1
)

:: Вывод найденного пути
echo Найден Python по пути:
echo     %PYTHON_EXE%

:: Обновляем pip
echo [3/3] Обновление pip и установка библиотек...
"%PYTHON_EXE%" -c "import sys; print('Тест кириллицы: успешно')"
"%PYTHON_EXE%" -m ensurepip --upgrade
"%PYTHON_EXE%" -m pip install --upgrade pip

echo.
echo Установка завершена!
echo.
echo Для запуска Python используйте:
echo     "%PYTHON_EXE%"
echo.
pause