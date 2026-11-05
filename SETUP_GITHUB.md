# Guide — Serveur de mises à jour GitHub

## Étape 1 — Créer un compte GitHub
1. Va sur https://github.com
2. Clique "Sign up" et crée ton compte

---

## Étape 2 — Créer le dépôt
1. Clique le "+" en haut à droite → "New repository"
2. Nom du dépôt : `pc-optimizer`
3. Coche "Public"
4. Clique "Create repository"

---

## Étape 3 — Installer Git
Télécharge Git sur https://git-scm.com/download/win et installe-le.

---

## Étape 4 — Publier le projet
Double-clique sur `publish_github.bat` et entre ton nom d'utilisateur GitHub quand demandé.

---

## Étape 5 — Mettre à jour l'URL dans les fichiers

### Dans `updater.py` (ligne VERSION_URL) :
Remplace `TON_USERNAME` par ton vrai nom GitHub :
```
VERSION_URL = "https://raw.githubusercontent.com/TON_USERNAME/pc-optimizer/main/version.json"
```

### Dans `version.json` (download_url) :
```json
"download_url": "https://github.com/TON_USERNAME/pc-optimizer/releases/latest/download/PC_Optimizer_Pro.exe"
```

---

## Étape 6 — Créer une Release (publier un .exe)
1. Va sur ton dépôt GitHub
2. Clique "Releases" à droite → "Create a new release"
3. Tag version : `v2.0`
4. Titre : `PC Optimizer Pro v2.0`
5. Glisse ton `dist/PC_Optimizer_Pro.exe` dans la zone "Attach binaries"
6. Clique "Publish release"

---

## Publier une mise à jour (v3.0 par exemple)

1. Modifie le code dans `optimizer.py`
2. Lance `build.bat` pour compiler le nouveau `.exe`
3. Modifie `version.json` :
   ```json
   {
     "version": "3.0",
     "download_url": "...releases/latest/download/PC_Optimizer_Pro.exe",
     "changelog": ["Nouvelle fonctionnalité X", "Correction bug Y"]
   }
   ```
4. Lance `publish_github.bat` pour pousser les changements
5. Crée une nouvelle Release sur GitHub avec le nouveau `.exe`

L'application des utilisateurs détectera automatiquement la v3.0 au prochain démarrage !
