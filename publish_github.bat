@echo off
title PC Optimizer Pro - Publication GitHub
color 0B

echo.
echo  ================================================
echo    Publication sur GitHub
echo  ================================================
echo.

:: Vérification Git
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERREUR] Git n'est pas installe.
    echo  Telecharge-le sur https://git-scm.com/download/win
    pause
    exit /b 1
)

:: Demande le nom d'utilisateur GitHub
set /p GITHUB_USER="Entre ton nom d'utilisateur GitHub : "
if "%GITHUB_USER%"=="" (
    echo  [ERREUR] Nom d'utilisateur vide.
    pause
    exit /b 1
)

set REPO_URL=https://github.com/%GITHUB_USER%/pc-optimizer.git

echo.
echo  [1/5] Initialisation Git...
git init >nul 2>&1

:: Création du .gitignore
echo build/         > .gitignore
echo dist/          >> .gitignore
echo __pycache__/   >> .gitignore
echo *.spec         >> .gitignore
echo *.pyc          >> .gitignore

echo  [OK] Git initialise.

echo.
echo  [2/5] Mise a jour de TON_USERNAME dans les fichiers...

:: Remplacement dans updater.py
powershell -Command "(Get-Content updater.py)     -replace 'TON_USERNAME', '%GITHUB_USER%' | Set-Content updater.py"
:: Remplacement dans version.json
powershell -Command "(Get-Content version.json)   -replace 'TON_USERNAME', '%GITHUB_USER%' | Set-Content version.json"
:: Remplacement dans la page web
powershell -Command "(Get-Content docs\index.html) -replace 'TON_USERNAME', '%GITHUB_USER%' | Set-Content docs\index.html"

echo  [OK] Nom d'utilisateur mis a jour : %GITHUB_USER%

echo.
echo  [3/5] Ajout des fichiers...

:: Fichiers de l'application
git add optimizer.py
git add updater.py
git add version.json
git add optimizer.manifest
git add build.bat
git add publish_github.bat
git add SETUP_GITHUB.md

:: Fichiers du site web (GitHub Pages)
git add docs\index.html
git add docs\style.css

echo  [OK] Fichiers ajoutes.

echo.
echo  [4/5] Commit...
git commit -m "PC Optimizer Pro v2.0 - Interface + site de telechargement"
if %errorlevel% neq 0 (
    echo  [ERREUR] Le commit a echoue. Verifie que les fichiers sont bien ajoutes.
    pause
    exit /b 1
)
echo  [OK] Commit effectue.

echo.
echo  [5/5] Push vers GitHub...
git branch -M main
git remote remove origin >nul 2>&1
git remote add origin %REPO_URL%
git push -u origin main

if %errorlevel% neq 0 (
    echo.
    echo  [INFO] GitHub va peut-etre te demander de te connecter
    echo  dans une fenetre de navigateur. Reconnecte-toi et relance.
    pause
    exit /b 1
)

echo.
echo  ================================================
echo    SUCCES !
echo.
echo    Depot GitHub  : https://github.com/%GITHUB_USER%/pc-optimizer
echo    Site web      : https://%GITHUB_USER%.github.io/pc-optimizer
echo.
echo    PROCHAINE ETAPE — Activer GitHub Pages :
echo    1. Va sur https://github.com/%GITHUB_USER%/pc-optimizer/settings/pages
echo    2. Source : "Deploy from a branch"
echo    3. Branch : main   Folder : /docs
echo    4. Clique Save
echo.
echo    Ton site sera en ligne en ~2 minutes !
echo  ================================================
echo.
pause
