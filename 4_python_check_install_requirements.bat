@echo off
chcp 65001 >nul
setlocal

set "INSTALL_DIR=%CD%\winpython"
set "PYTHON_EXE="

:: Поиск python.exe
echo [Поиск] Поиск python.exe в "%INSTALL_DIR%"...
for /r "%INSTALL_DIR%" %%F in (python.exe) do (
    if exist "%%F" (
        set "PYTHON_EXE=%%F"
        goto :found_python
    )
)
:found_python

if not defined PYTHON_EXE (
    echo Ошибка: не найден python.exe в папке winpython.
    echo Сначала запустите install_python.bat
    pause
    exit /b 1
)

if not exist "requirements.txt" (
    echo Ошибка: файл requirements.txt не найден в текущей директории.
    pause
    exit /b 1
)

:: Получаем список установленных пакетов
echo.
echo [Анализ] Получение списка установленных пакетов...
"%PYTHON_EXE%" -m pip list --format=freeze > "%TEMP%\installed_packages.txt"

:: Отключаем delayed expansion для безопасного чтения строк с "!"
setlocal DisableDelayedExpansion

echo.
echo [Проверка] Анализ требуемых пакетов из requirements.txt...

for /f "usebackq eol=# tokens=* delims=" %%L in ("requirements.txt") do (
    set "line=%%L"
    setlocal EnableDelayedExpansion
    set "pkg=!line!"
    for /f "tokens=* delims= " %%A in ("!pkg!") do set "pkg=%%A"
    if defined pkg (
        call :check_package "!pkg!"
    )
    endlocal
)

echo.
echo Проверка завершена.
pause
exit /b 0

:: =============== ФУНКЦИЯ ПРОВЕРКИ ПАКЕТА ===============
:check_package
set "req=%~1"

:: Извлекаем имя пакета до первого оператора: ==, >=, <=, !=, ~=, ^
set "pkg_name=%req%"
for /f "delims==>!~<^" %%P in ("%req%") do set "pkg_name=%%P"

:: Убираем завершающие пробелы
for /f "tokens=* delims= " %%A in ("%pkg_name%") do set "pkg_name=%%A"

if not defined pkg_name (
    echo ❓ Не удалось определить имя пакета: %req%
    goto :eof
)

:: Ищем установленную версию в файле
set "found_version="
for /f "usebackq tokens=2 delims==" %%V in (`findstr /i /r /c:"^%pkg_name%==" "%TEMP%\installed_packages.txt" 2^>nul`) do (
    set "found_version=%%V"
)

if defined found_version (
    echo ✅ Установлен: %pkg_name% ^(%found_version%^)
) else (
    echo ❌ Не установлен: %pkg_name%
)
goto :eof