@echo off
title Push vers GitHub
color 0A

echo.
echo  ================================================
echo    Envoi des fichiers vers GitHub
echo  ================================================
echo.

cd /d "%~dp0"

echo  [1/4] Configuration du depot...
git remote remove origin >nul 2>&1
git remote add origin https://github.com/FayraYTB/SteakOptimisation.git
git branch -M main
echo  [OK] Depot configure.

echo.
echo  [2/4] Ajout de tous les fichiers...
git add optimizer.py
git add updater.py
git add version.json
git add optimizer.manifest
git add build.bat
git add SETUP_GITHUB.md
git add docs\index.html
git add docs\style.css
echo  [OK] Fichiers ajoutes.

echo.
echo  [3/4] Commit...
git commit -m "PC Optimizer Pro v2.0 - Initial release" >nul 2>&1
echo  [OK] Commit effectue.

echo.
echo  [4/4] Envoi vers GitHub...
git push -u origin main

if %errorlevel% neq 0 (
    echo.
    echo  [ERREUR] Echec du push.
    echo  Une fenetre de connexion GitHub va peut-etre s'ouvrir.
    echo  Connecte-toi puis relance ce script.
    pause
    exit /b 1
)

echo.
echo  ================================================
echo    SUCCES ! Fichiers envoyes sur GitHub.
echo.
echo    Depot : https://github.com/FayraYTB/SteakOptimisation
echo.
echo    MAINTENANT active GitHub Pages :
echo    1. Va sur ce lien :
echo       https://github.com/FayraYTB/SteakOptimisation/settings/pages
echo    2. Source : Deploy from a branch
echo    3. Branch : main    Folder : /docs
echo    4. Clique Save
echo.
echo    Ton site sera en ligne sur :
echo    https://FayraYTB.github.io/SteakOptimisation
echo  ================================================
echo.
pause
