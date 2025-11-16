@echo off
chcp 65001 >nul
setlocal DisableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
set "ZIP_FILE=%SCRIPT_DIR%pandoc-download.zip"

:: === 1. Получаем версию ===
for /f "delims=" %%G in ('powershell -Command "try { $r = Invoke-WebRequest -Uri 'https://github.com/jgm/pandoc/releases/latest' -MaximumRedirection 0 -ErrorAction Ignore; if ($r.StatusCode -eq 302) { $r.Headers.Location -match '/tag/([^/]+)$' | Out-Null; Write-Output $matches[1] } } catch {}" 2^>nul') do (
    set "VERSION=%%G"
)

setlocal EnableDelayedExpansion
if not defined VERSION (
    echo [-] Не удалось определить версию. Используем 3.8.2.1.
    set "VERSION=3.8.2.1"
)
echo [+] Версия: !VERSION!

:: === 2. Скачиваем ===
set "URL=https://github.com/jgm/pandoc/releases/download/!VERSION!/pandoc-!VERSION!-windows-x86_64.zip"
set "TEMP_ZIP=!TEMP!\pandoc-!VERSION!.zip"

powershell -Command "try { [Net.ServicePointManager]::SecurityProtocol = 'Tls12'; (New-Object Net.WebClient).DownloadFile('!URL!', '!TEMP_ZIP!'); Write-Host '[+] Скачано.' } catch { Write-Host '[-] Ошибка: ' $_.Exception.Message; exit 1 }"
if !errorlevel! neq 0 exit /b 1

move /Y "!TEMP_ZIP!" "!ZIP_FILE!" >nul
if !errorlevel! neq 0 (
    echo [-] Не удалось переместить архив.
    exit /b 1
)

:: === 3. Распаковываем ===
set "EXTRACT_TO=!SCRIPT_DIR!_pandoc_unzip"
if exist "!EXTRACT_TO!" rd /s /q "!EXTRACT_TO!"
mkdir "!EXTRACT_TO!" >nul

tar -xf "!ZIP_FILE!" -C "!EXTRACT_TO!" >nul
if !errorlevel! neq 0 (
    echo [-] Ошибка распаковки. Возможно, антивирус удалил архив.
    rd /s /q "!EXTRACT_TO!" >nul
    del "!ZIP_FILE!" >nul
    pause
    exit /b 1
)

:: === 4. Копируем pandoc.exe из ожидаемой папки ===
set "SOURCE_EXE=!EXTRACT_TO!\pandoc-!VERSION!\pandoc.exe"
if exist "!SOURCE_EXE!" (
    copy "!SOURCE_EXE!" "!SCRIPT_DIR!" >nul
    echo [+] pandoc.exe успешно скопирован.
) else (
    echo [-] Ошибка: файл не найден по пути:
    echo     !SOURCE_EXE!
    echo     Убедитесь, что структура архива не изменилась.
    rd /s /q "!EXTRACT_TO!" >nul
    del "!ZIP_FILE!" >nul
    pause
    exit /b 1
)

:: === 5. Очистка ===
rd /s /q "!EXTRACT_TO!" >nul
del "!ZIP_FILE!" >nul

:: === 6. Проверка ===
"!SCRIPT_DIR!pandoc.exe" --version | findstr /r /c:"^pandoc "
echo [+] Готово! pandoc.exe находится рядом с этим скриптом.

pause
exit /b 0