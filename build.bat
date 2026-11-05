@echo off
title PC Optimizer Pro - Build Script
color 0A

:: Chemin exact vers Python
set PYTHON=C:\Users\matys\AppData\Local\Python\bin\python3.14-64.exe

echo.
echo  ================================================
echo    PC Optimizer Pro - Compilation en .EXE
echo  ================================================
echo.

:: Vérification Python
"%PYTHON%" --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERREUR] Python introuvable.
    pause
    exit /b 1
)

echo  [1/3] Installation de PyInstaller...
"%PYTHON%" -m pip install pyinstaller --quiet
if %errorlevel% neq 0 (
    echo  [ERREUR] Impossible d'installer PyInstaller.
    pause
    exit /b 1
)
echo  [OK] PyInstaller installe.
echo.

echo  [2/3] Compilation de l'application...
"%PYTHON%" -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name "PC_Optimizer_Pro" ^
    --manifest optimizer.manifest ^
    --icon NONE ^
    --clean ^
    optimizer.py

if %errorlevel% neq 0 (
    echo.
    echo  [ERREUR] La compilation a echoue.
    pause
    exit /b 1
)

echo.
echo  [3/3] Nettoyage des fichiers temporaires de build...
if exist build        rmdir /s /q build
if exist __pycache__  rmdir /s /q __pycache__
if exist PC_Optimizer_Pro.spec del /q PC_Optimizer_Pro.spec

echo.
echo  ================================================
echo    SUCCES !
echo    Ton .exe se trouve dans : dist\PC_Optimizer_Pro.exe
echo  ================================================
echo.
pause
