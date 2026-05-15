# 📖 Guide Rapide - Utilisation du Rapport LaTeX Amélioré

## 🚀 Démarrage Rapide

### Étape 1 : Fichiers Requis
```
votre-projet/
├── RAPPORT_PFE_IMPROVED.tex      ← Fichier principal
├── macros_personnalisees.sty     ← (Optionnel) Macros additionnelles
├── image/                        ← Dossier des images
│   ├── FARM_AI_login.png
│   ├── dashboard.png
│   └── ...
└── images/                       ← Alternative
    └── ...
```

### Étape 2 : Compilation
```bash
# Méthode 1 : Compilation simple (recommandée)
pdflatex -interaction=nonstopmode RAPPORT_PFE_IMPROVED.tex

# Méthode 2 : Avec génération de bibliographie
pdflatex RAPPORT_PFE_IMPROVED.tex
bibtex RAPPORT_PFE_IMPROVED
pdflatex RAPPORT_PFE_IMPROVED.tex
pdflatex RAPPORT_PFE_IMPROVED.tex

# Méthode 3 : Utiliser Makefile
latexmk -pdf RAPPORT_PFE_IMPROVED.tex
```

---

## 📝 Utilisation des Boxes Personnalisées

### Box d'Information
```latex
\begin{infobox}
  Information importante à mettre en évidence
\end{infobox}
```

### Box d'Attention
```latex
\begin{warningbox}
  ⚠ Points critiques ou limitations du système
\end{warningbox}
```

### Box Optionnelles (avec macros_personnalisees.sty)

#### Box de Définition
```latex
\usepackage{macros_personnalisees}

\begin{definitionbox}
  L'IA est l'intelligence simulée par des machines
\end{definitionbox}
```

#### Box de Résultat
```latex
\begin{resultbox}
  Le système a atteint 97.2\% de précision
\end{resultbox}
```

#### Box de Conseil
```latex
\begin{tipsbox}
  Utilisez toujours une authentification JWT sécurisée
\end{tipsbox}
```

---

## 🖼️ Insertion d'Images

### Méthode Simple
```latex
\begin{figure}[H]
  \centering
  \includegraphics[width=0.9\textwidth]{FARM_AI_login.png}
  \caption{Interface d'authentification}
  \label{fig:login}
\end{figure}
```

### Avec Macro (si macros_personnalisees.sty utilisé)
```latex
\myfigure{FARM_AI_login.png}{0.9\textwidth}{Interface d'authentification}{login}
```

### Deux Images Côte à Côte
```latex
\doublefigure{image1.png}{Légende 1}{ref1}{image2.png}{Légende 2}{ref2}
```

---

## 📊 Tableaux Professionnels

### Tableau Simple
```latex
\begin{table}[H]
  \centering
  \caption{Besoins fonctionnels}
  \label{tab:besoins}
  \begin{tabularx}{\textwidth}{|l|X|}
    \hline
    \tableheader{Fonction} & \tableheader{Description} \\
    \hline
    Gestion des employés & Ajout et modification \\
    \hline
    Reconnaissance faciale & Identification temps réel \\
    \hline
  \end{tabularx}
\end{table}
```

### Avec Macro (macros_personnalisees.sty)
```latex
\tabheader{Colonne 1} & \tabheader{Colonne 2} \\
...
Dernière ligne & \tabtotal{Total}
```

---

## 📚 Références et Renvois

### Référencer une Figure
```latex
Comme shown in \ref{fig:login}, l'interface...
```

### Référencer un Tableau
```latex
Voir le \ref{tab:besoins} pour les détails.
```

### Référencer une Section
```latex
D'après la \ref{sec:introduction}, nous...
```

---

## 🔗 Lien Hypertexte

### Lien Web
```latex
Plus d'info sur \url{https://angular.io/}
```

### Lien Interne
```latex
\hyperref[fig:login]{Cliquez ici}
```

---

## 📜 Listes Améliorées

### Liste à Puces
```latex
\begin{itemize}
  \item Premier point
  \item Deuxième point
  \item Troisième point
\end{itemize}
```

### Liste Ordonnée
```latex
\begin{enumerate}
  \item Première étape
  \item Deuxième étape
  \item Troisième étape
\end{enumerate}
```

### Avec Macros (macros_personnalisees.sty)
```latex
% Points clés
\begin{keypoints}
  \item Avantage 1
  \item Avantage 2
\end{keypoints}

% Objectifs
\begin{objectives}
  \item Objectif 1
  \item Objectif 2
\end{objectives}
```

---

## ✍️ Formatage du Texte

### Avec Macros (macros_personnalisees.sty)

#### Surligné
```latex
\highlight{texte important}
```

#### Terme Technique
```latex
Les \tech{CNN} sont utilisés...
```

#### Très Important (Rouge + Gras)
```latex
\important{Ce point est critique !}
```

#### Avec Indexation
```latex
\indexterm{YOLO} est un algorithme...
```

---

## 📋 Ajouter une Citation

### Citation Simple
```latex
\begin{quotation}
  \textit{« La citation ici »}
  \linebreak
  \hspace*{\fill}--- Auteur
\end{quotation}
```

### Avec Macro (macros_personnalisees.sty)
```latex
\citation{L'IA change le monde}{Steve Jobs}
```

---

## 🏷️ Acronymes (macros_personnalisees.sty)

```latex
% Raccourcis disponibles
\AI      → Intelligence Artificielle (IA)
\ML      → Machine Learning (ML)
\CV      → Vision par ordinateur (CV)
\API     → Interface de programmation...
\JWT     → JSON Web Token (JWT)
\SPA     → Application mono-page (SPA)
\REST    → Transfert d'état représentatif...
```

Exemple d'utilisation :
```latex
Les modèles de \ML sont intégrés via une \API REST.
```

---

## 🌐 Personnalisation du Rapport

### Modifier le Titre
```latex
\title{Votre titre ici}
\author{Votre nom}
\date{\today}
```

### Modifier les En-têtes
```latex
\fancyhead[C]{%
  \fontsize{10}{12}\selectfont\itshape%
  Votre titre personnalisé%
}
```

### Modifier les Couleurs des Boxes
```latex
% Dans le préambule :
\newtcolorbox{infobox}{
  colback=green!5!white,    ← Couleur de fond
  colframe=green!75!black,  ← Couleur bordure
  ...
}
```

---

## 🎨 Codes Couleurs LaTeX

| Couleur | Code |
|---------|------|
| Rouge | `red` ou `red!30!white` (pâle) |
| Bleu | `blue` ou `blue!20!white` |
| Vert | `green` ou `green!10!white` |
| Orange | `orange!75!black` |
| Violet | `violet` |
| Jaune | `yellow!30` |
| Gris | `gray` |

---

## 🛠️ Dépannage Courant

### Erreur : "Package not found"
**Solution** : Installer le package
```bash
# Sous Windows
miktex-console  # Interface graphique
# Sous Linux
sudo apt-get install texlive-full
```

### Erreur : "Undefined control sequence"
**Solution** : Vérifiez l'orthographe et les accolades
```latex
% ✗ Mauvais
\textbf{texte
% ✓ Correct
\textbf{texte}
```

### Les images ne s'affichent pas
**Solution** : Vérifiez le chemin
```latex
% ✓ Correct (relatif)
\includegraphics{./image/logo.png}
% ✓ Avec graphicspath
\graphicspath{{./image/}{./figures/}}
\includegraphics{logo.png}
```

### La table de matières est vide
**Solution** : Compiler plusieurs fois
```bash
pdflatex rapport.tex  # 1ère fois
pdflatex rapport.tex  # 2ème fois (génère TOC)
```

---

## 💾 Fichiers Générés Après Compilation

| Fichier | Utilité |
|---------|---------|
| `.pdf` | Le rapport final |
| `.aux` | Références croisées |
| `.toc` | Table des matières (source) |
| `.lof` | Liste des figures (source) |
| `.lot` | Liste des tableaux (source) |
| `.bbl` | Bibliographie compilée |
| `.log` | Journal de compilation |

✅ **À garder** : `.pdf`  
❌ **À supprimer** : `.aux`, `.log`, `.bbl`

---

## 📱 Conseils Professionnels

### 1. **Optimiser les Images**
```bash
# Réduire la taille des images (ImageMagick)
convert -density 150 input.pdf -quality 85 output.jpg

# Compresser PNG
pngquant 256 input.png -o output.png
```

### 2. **Vérifier Avant Remise**
- [ ] PDF génère sans erreurs
- [ ] Table de matières correcte
- [ ] Tous les liens fonctionnent
- [ ] Images bien intégrées
- [ ] Pas de pages orphelines

### 3. **Sauvegarder Régulièrement**
```bash
git add RAPPORT_PFE_IMPROVED.tex
git commit -m "Mise à jour du rapport v1.2"
```

---

## 🎓 Structure Recommandée

```
Mon_PFE/
├── rapport_main.tex           ← Fichier maître
├── chapitres/
│   ├── 01_introduction.tex
│   ├── 02_contexte.tex
│   ├── 03_specifications.tex
│   └── 04_realisation.tex
├── images/
│   ├── screenshots/
│   ├── diagrams/
│   └── charts/
├── annexes/
│   ├── code_listings/
│   └── data/
└── macros_personnalisees.sty
```

### Fichier Maître (rapport_main.tex)
```latex
\documentclass[12pt,a4paper]{report}
\input{macros_personnalisees}

\begin{document}
  \input{chapitres/01_introduction}
  \input{chapitres/02_contexte}
  % ... etc
\end{document}
```

---

## 📞 Support Supplémentaire

### Documentation Officielle
- **Overleaf** : https://www.overleaf.com/learn
- **CTAN** : https://www.ctan.org/
- **TikZ** : https://pgfplots.sourceforge.net/

### Outils Utiles
- **Overleaf** : Éditeur LaTeX en ligne (gratuit)
- **Texmaker** : Éditeur LaTeX (gratuit)
- **MiKTeX** : Distribution LaTeX (gratuit)

---

**Document créé pour Farm AI - PFE ISET Siliana 2025-2026**
