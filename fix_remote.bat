@echo off
title Correction URL GitHub
color 0B

echo.
echo  ================================================
echo    Correction de l'URL GitHub
echo    Depot : FayraYTB/Steak-Optimisation
echo  ================================================
echo.

set GITHUB_USER=FayraYTB
set REPO_NAME=Steak-Optimisation
set REPO_URL=https://github.com/%GITHUB_USER%/%REPO_NAME%.git

echo  [1/5] Mise a jour de l'URL du depot...
git remote remove origin >nul 2>&1
git remote add origin %REPO_URL%
echo  [OK] URL mise a jour : %REPO_URL%

echo.
echo  [2/5] Mise a jour du nom dans les fichiers...
powershell -Command "(Get-Content updater.py)      -replace 'SteakOptimisation|TON_USERNAME', '%GITHUB_USER%' | Set-Content updater.py"
powershell -Command "(Get-Content version.json)    -replace 'SteakOptimisation|TON_USERNAME', '%GITHUB_USER%' | Set-Content version.json"
powershell -Command "(Get-Content docs\index.html) -replace 'SteakOptimisation|TON_USERNAME', '%GITHUB_USER%' | Set-Content docs\index.html"

:: Correction du nom du dépôt dans les URLs
powershell -Command "(Get-Content updater.py)      -replace 'pc-optimizer', '%REPO_NAME%' | Set-Content updater.py"
powershell -Command "(Get-Content version.json)    -replace 'pc-optimizer', '%REPO_NAME%' | Set-Content version.json"
powershell -Command "(Get-Content docs\index.html) -replace 'pc-optimizer', '%REPO_NAME%' | Set-Content docs\index.html"
echo  [OK] Fichiers mis a jour.

echo.
echo  [3/5] Ajout des fichiers modifies...
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
echo  [4/5] Commit...
git commit -m "Fix: URL GitHub corrigee - FayraYTB/Steak-Optimisation" >nul 2>&1
echo  [OK] Commit effectue.

echo.
echo  [5/5] Push vers GitHub...
git branch -M main
git push -u origin main

if %errorlevel% neq 0 (
    echo.
    echo  [ERREUR] Push echoue. Assure-toi d'etre connecte a GitHub.
    pause
    exit /b 1
)

echo.
echo  ================================================
echo    SUCCES !
echo.
echo    Depot    : https://github.com/FayraYTB/Steak-Optimisation
echo    Site web : https://FayraYTB.github.io/Steak-Optimisation
echo.
echo    ACTIVE GITHUB PAGES :
echo    https://github.com/FayraYTB/Steak-Optimisation/settings/pages
echo    Branch : main  /  Folder : /docs  /  Save
echo  ================================================
echo.
pause
