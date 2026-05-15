import re

def process_pdf_text(text):
    lines = text.split('\n')
    latex_lines = []
    in_itemize = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Handle Chapter
        if line.startswith('Chapitre 2 :'):
            latex_lines.append(r'\chapter{État de l\'art}')
            continue
            
        # Handle Sections
        sec_match = re.match(r'^2\.(\d+)\s+(.+)', line)
        if sec_match:
            if in_itemize:
                latex_lines.append(r'\end{itemize}')
                in_itemize = False
            
            num, title = sec_match.groups()
            title = title.replace('Ɵ', 'ti').replace('Ʃ', 'tt')
            if num == '0': # just in case
                pass
            latex_lines.append(fr'\section{{{title}}}')
            continue
            
        # Handle Subsections
        subsec_match = re.match(r'^2\.\d+\.(\d+)\s+(.+)', line)
        if subsec_match:
            if in_itemize:
                latex_lines.append(r'\end{itemize}')
                in_itemize = False
            
            num, title = subsec_match.groups()
            title = title.replace('Ɵ', 'ti').replace('Ʃ', 'tt')
            latex_lines.append(fr'\subsection{{{title}}}')
            continue
            
        # Handle Items
        if line.startswith('') or line.startswith('-'):
            if not in_itemize:
                latex_lines.append(r'\begin{itemize}')
                in_itemize = True
            item_text = line[1:].strip().replace('Ɵ', 'ti').replace('Ʃ', 'tt')
            latex_lines.append(fr'  \item {item_text}')
            continue
            
        # End itemize if normal text
        if in_itemize:
            latex_lines.append(r'\end{itemize}')
            in_itemize = False
            
        # Handle bold headings like "Définition", "Rôle dans le projet", "Avantages"
        if line in ['Définition', 'Défi niƟon', 'Défi nition', 'Rôle dans le projet', 'Avantages', 'Structure u Ɵlisée']:
            line = line.replace('Ɵ', 'ti').replace('Ʃ', 'tt').replace('Défi nition', 'Définition')
            latex_lines.append(fr'\textbf{{{line}}} : \\')
            continue
            
        # Handle Figure
        if line.startswith('Figure :'):
            latex_lines.append(r'\begin{figure}[H]')
            latex_lines.append(r'  \centering')
            latex_lines.append(r'  % \includegraphics[width=0.8\textwidth]{images/...}')
            caption = line.replace('Figure :', '').strip().replace('Ɵ', 'ti').replace('Ʃ', 'tt')
            latex_lines.append(fr'  \caption{{{caption}}}')
            latex_lines.append(r'\end{figure}')
            continue
            
        if line == 'Figure':
            continue
            
        # Normal text
        clean_line = line.replace('Ɵ', 'ti').replace('Ʃ', 'tt')
        latex_lines.append(clean_line)
        
    if in_itemize:
        latex_lines.append(r'\end{itemize}')
        
    return '\n'.join(latex_lines)

# Read the extracted PDF text
with open('ch2_extracted.txt', 'r', encoding='utf-8') as f:
    pdf_text = f.read()

ch2_latex = process_pdf_text(pdf_text)

# Read the RAPPORT_PFE_IMPROVED.tex
with open('RAPPORT_PFE_IMPROVED.tex', 'r', encoding='utf-8') as f:
    report_content = f.read()

# Read the SECTIONS_MANQUANTES.tex
with open('SECTIONS_MANQUANTES.tex', 'r', encoding='utf-8') as f:
    missing_content = f.read()

# Parse SECTIONS_MANQUANTES to extract blocks
blocks = {}
current_block_name = None
current_block_lines = []

for line in missing_content.split('\n'):
    if line.startswith('% 1. REMPLACER la section "Présentation des acteurs"'):
        current_block_name = "acteurs"
        current_block_lines = []
    elif line.startswith('% 2. TABLEAU DES BESOINS'):
        blocks[current_block_name] = '\n'.join(current_block_lines).strip()
        current_block_name = "besoins"
        current_block_lines = []
    elif line.startswith('% 3. SECTION GMAIL'):
        blocks[current_block_name] = '\n'.join(current_block_lines).strip()
        current_block_name = "gmail"
        current_block_lines = []
    elif line.startswith('% 4. SECTION GESTION DES GESTIONNAIRES'):
        blocks[current_block_name] = '\n'.join(current_block_lines).strip()
        current_block_name = "cu_managers"
        current_block_lines = []
    elif line.startswith('% 5. SECTION GESTION DES DÉPARTEMENTS'):
        blocks[current_block_name] = '\n'.join(current_block_lines).strip()
        current_block_name = "cu_departments"
        current_block_lines = []
    elif line.startswith('% 6. SECTION ACTIVATION'):
        blocks[current_block_name] = '\n'.join(current_block_lines).strip()
        current_block_name = "cu_activation"
        current_block_lines = []
    elif line.startswith('% 7. SECTION SUGGESTION'):
        blocks[current_block_name] = '\n'.join(current_block_lines).strip()
        current_block_name = "cu_team"
        current_block_lines = []
    elif line.startswith('% 8. ENTRÉES DU BACKLOG'):
        blocks[current_block_name] = '\n'.join(current_block_lines).strip()
        current_block_name = "backlog"
        current_block_lines = []
    elif line.startswith('% 9. CORRECTION'):
        blocks[current_block_name] = '\n'.join(current_block_lines).strip()
        current_block_name = "mysql"
        current_block_lines = []
    elif line.startswith('% 10. INTERFACES'):
        blocks[current_block_name] = '\n'.join(current_block_lines).strip()
        current_block_name = "interfaces"
        current_block_lines = []
    elif line.startswith('% 11. PLANIFICATION'):
        blocks[current_block_name] = '\n'.join(current_block_lines).strip()
        current_block_name = "sprints"
        current_block_lines = []
    elif line.startswith('\\end{document}'):
        blocks[current_block_name] = '\n'.join(current_block_lines).strip()
        current_block_name = None
    else:
        if current_block_name and not line.startswith('% ========================================'):
            current_block_lines.append(line)

# Clean up blocks
for key in blocks:
    # remove leading comments and empty lines
    lines = blocks[key].split('\n')
    clean_lines = []
    for l in lines:
        if l.startswith('%') and not 'table' in key:
            continue
        clean_lines.append(l)
    blocks[key] = '\n'.join(clean_lines).strip()

# Create the final report
# 1. Update Chapter 1 title and remove its state of the art section
report_content = report_content.replace(r'\chapter{Contexte et État de l\'art}', r'\chapter{Contexte du projet}')
report_content = report_content.replace(r'Ce chapitre présente le contexte général du projet, la problématique liée à la gestion classique', r'Ce chapitre présente le contexte général du projet et la problématique liée à la gestion classique')

# Remove old Section 4 from Chapter 1
old_sec4_pattern = r'\\section\{État de l\'art des solutions technologiques\}.*?\\section\{Solution proposée : Farm AI\}'
report_content = re.sub(old_sec4_pattern, lambda m: r'\\section{Solution proposée : Farm AI}', report_content, flags=re.DOTALL)

# 2. Insert Chapter 2
ch1_end_pattern = r'(\\section\{Conclusion\}.*?Le chapitre suivant précisera les besoins.*?fonctionnels et non fonctionnels du système.)'
new_ch1_end = r'\section{Conclusion}\nCe chapitre a permis d\'identifier les lacunes des systèmes existants et de justifier le choix d\'une solution basée sur l\'intelligence artificielle. Le chapitre suivant présentera l\'état de l\'art des technologies utilisées.\n\n% ===========================================================\n% CHAPITRE 2 : ÉTAT DE L\'ART\n% ===========================================================\n' + ch2_latex + '\n\n'
report_content = re.sub(ch1_end_pattern, lambda m: new_ch1_end, report_content, flags=re.DOTALL)

# Update chapter numbers in comments
report_content = report_content.replace('CHAPITRE 2 : SPÉCIFICATION', 'CHAPITRE 3 : SPÉCIFICATION')
report_content = report_content.replace('CHAPITRE 3 : ENVIRONNEMENT', 'CHAPITRE 4 : ENVIRONNEMENT')
report_content = report_content.replace('CHAPITRE 4 : RÉALISATION', 'CHAPITRE 5 : RÉALISATION')

# 3. Replace Besoins fonctionnels table
old_besoins_func = r'\\begin\{table\}\[H\].*?\\caption\{Besoins fonctionnels.*?\\end\{table\}'
report_content = re.sub(old_besoins_func, lambda m: blocks['besoins'], report_content, flags=re.DOTALL)

# Also remove old besoins non fonctionnels
old_besoins_nf = r'\\subsection\{Besoins non fonctionnels\}.*?\\end\{table\}'
report_content = re.sub(old_besoins_nf, lambda m: '', report_content, flags=re.DOTALL)

# Add the CU sections at the end of Chapter 3 (old Chapter 2)
cu_content = "\n\n" + blocks['cu_managers'] + "\n\n" + blocks['cu_departments'] + "\n\n" + blocks['cu_activation'] + "\n\n" + blocks['cu_team']
report_content = report_content.replace(r'\subsection{Architecture globale du système}', cu_content + '\n\n' + r'\subsection{Architecture globale du système}')

# Add Gmail section in Chapter 4 (old Chapter 3)
gmail_content = "\n\n" + blocks['gmail']
report_content = report_content.replace(r'\section{Technologies Backend (Java)}', r'\section{Technologies Backend (Java)}' + gmail_content)

# Correct PostgreSQL to MySQL
report_content = report_content.replace(r'\subsection{Base de données PostgreSQL}', blocks['mysql'])
report_content = report_content.replace('PostgreSQL', 'MySQL')

# Save to RAPPORT_FINAL.tex
with open('RAPPORT_FINAL.tex', 'w', encoding='utf-8') as f:
    f.write(report_content)

print("Report successfully merged into RAPPORT_FINAL.tex")
