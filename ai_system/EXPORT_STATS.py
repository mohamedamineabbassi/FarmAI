#!/usr/bin/env python3
"""
📊 EXPORT STATISTIQUES - Générer des rapports en JSON, CSV, HTML
Parfait pour archiver et analyser les performances de l'IA
"""

import mysql.connector
import json
import csv
from datetime import datetime
from mysql.connector import Error

class StatsExporter:
    def __init__(self):
        self.db = None
        self.cursor = None
        self.connect_db()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def connect_db(self):
        """Connecter à MySQL"""
        try:
            self.db = mysql.connector.connect(
                host="localhost",
                user="root",
                password="root123",
                database="attendance_db"
            )
            self.cursor = self.db.cursor(dictionary=True)
            return True
        except Error as e:
            print(f"✗ Erreur MySQL: {e}")
            return False
    
    def get_all_stats(self):
        """Récupérer toutes les statistiques"""
        stats = {
            'timestamp': datetime.now().isoformat(),
            'employees': {},
            'attendance': {},
            'summary': {}
        }
        
        try:
            # SECTION 1: EMPLOYÉS
            self.cursor.execute("SELECT COUNT(*) as total FROM employees")
            total_employees = self.cursor.fetchone()['total']
            
            self.cursor.execute("SELECT COUNT(*) as total FROM employees WHERE embedding IS NOT NULL")
            with_face = self.cursor.fetchone()['total']
            
            self.cursor.execute("SELECT COUNT(*) as total FROM employees WHERE status = 'APPROVED'")
            approved = self.cursor.fetchone()['total']
            
            # Détail des employés
            self.cursor.execute("""
                SELECT id, name, email, status, 
                       IF(embedding IS NOT NULL, 1, 0) as has_face
                FROM employees
                ORDER BY id
            """)
            
            employees_list = []
            for emp in self.cursor.fetchall():
                employees_list.append({
                    'id': emp['id'],
                    'name': emp['name'],
                    'email': emp['email'],
                    'status': emp['status'],
                    'face_registered': bool(emp['has_face'])
                })
            
            stats['employees'] = {
                'total': total_employees,
                'with_face': with_face,
                'approved': approved,
                'list': employees_list
            }
            
            # SECTION 2: RECONNAISSANCES
            try:
                self.cursor.execute("""
                    SELECT COUNT(*) as total FROM attendance 
                    WHERE DATE(timestamp) = CURDATE()
                """)
                today_count = self.cursor.fetchone()['total']
                
                # Top reconnus
                self.cursor.execute("""
                    SELECT e.name, COUNT(*) as count
                    FROM attendance a
                    JOIN employees e ON a.employee_id = e.id
                    WHERE DATE(a.timestamp) = CURDATE()
                    GROUP BY e.id, e.name
                    ORDER BY count DESC
                    LIMIT 10
                """)
                
                top_recognized = []
                for row in self.cursor.fetchall():
                    top_recognized.append({
                        'name': row['name'],
                        'count': row['count']
                    })
                
                stats['attendance'] = {
                    'today': today_count,
                    'top_recognized': top_recognized
                }
            except:
                stats['attendance'] = {
                    'today': 0,
                    'top_recognized': []
                }
            
            # SECTION 3: RÉSUMÉ
            pct_face = (with_face * 100) // max(1, total_employees)
            pct_approved = (approved * 100) // max(1, total_employees)
            
            stats['summary'] = {
                'total_employees': total_employees,
                'pct_with_face': pct_face,
                'pct_approved': pct_approved,
                'recognitions_today': today_count if 'today_count' in locals() else 0,
                'system_ready': with_face > 0 and approved > 0
            }
            
        except Error as e:
            print(f"Erreur: {e}")
        
        return stats
    
    def export_json(self):
        """Exporter en JSON"""
        stats = self.get_all_stats()
        filename = f"ai_stats_{self.timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Exporté: {filename}")
        return filename
    
    def export_csv(self):
        """Exporter les employés en CSV"""
        filename = f"employees_{self.timestamp}.csv"
        
        try:
            self.cursor.execute("""
                SELECT id, name, email, status, 
                       IF(embedding IS NOT NULL, 'OUI', 'NON') as visage
                FROM employees
                ORDER BY id
            """)
            
            employees = self.cursor.fetchall()
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'name', 'email', 'status', 'visage'])
                writer.writeheader()
                writer.writerows(employees)
            
            print(f"✓ Exporté: {filename}")
            return filename
        except Exception as e:
            print(f"✗ Erreur CSV: {e}")
            return None
    
    def export_html(self):
        """Exporter en HTML"""
        stats = self.get_all_stats()
        filename = f"rapport_ai_{self.timestamp}.html"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Rapport IA Farm-AI</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #3498db;
            margin-top: 30px;
        }}
        .stat-box {{
            display: inline-block;
            background-color: #ecf0f1;
            padding: 15px 25px;
            margin: 10px;
            border-radius: 5px;
            border-left: 4px solid #3498db;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }}
        .stat-label {{
            font-size: 12px;
            color: #7f8c8d;
            text-transform: uppercase;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th {{
            background-color: #3498db;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: bold;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #ecf0f1;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .status-approved {{
            color: #27ae60;
            font-weight: bold;
        }}
        .status-pending {{
            color: #f39c12;
            font-weight: bold;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #7f8c8d;
            font-size: 12px;
        }}
        .progress-bar {{
            width: 100%;
            height: 20px;
            background-color: #ecf0f1;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }}
        .progress-fill {{
            height: 100%;
            background-color: #3498db;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Rapport Statistiques - AI Farm-AI</h1>
        <p>Généré le: {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}</p>
        
        <h2>📊 Statistiques Résumé</h2>
        <div class="stat-box">
            <div class="stat-label">Total Employés</div>
            <div class="stat-value">{stats['summary']['total_employees']}</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Avec Visage</div>
            <div class="stat-value">{stats['employees']['with_face']}</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Approuvés</div>
            <div class="stat-value">{stats['employees']['approved']}</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Reconnaissances Aujourd'hui</div>
            <div class="stat-value">{stats['summary']['recognitions_today']}</div>
        </div>
        
        <h2>📈 Progression</h2>
        <p>Employés avec visage</p>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {stats['summary']['pct_with_face']}%">
                {stats['summary']['pct_with_face']}%
            </div>
        </div>
        
        <p>Employés approuvés</p>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {stats['summary']['pct_approved']}%">
                {stats['summary']['pct_approved']}%
            </div>
        </div>
        
        <h2>👥 Liste Employés</h2>
        <table>
            <tr>
                <th>ID</th>
                <th>Nom</th>
                <th>Email</th>
                <th>Status</th>
                <th>Visage</th>
            </tr>
"""
        
        for emp in stats['employees']['list']:
            status_class = 'status-approved' if emp['status'] == 'APPROVED' else 'status-pending'
            face = '✓' if emp['face_registered'] else '✗'
            html += f"""
            <tr>
                <td>{emp['id']}</td>
                <td>{emp['name']}</td>
                <td>{emp['email']}</td>
                <td class="{status_class}">{emp['status']}</td>
                <td>{face}</td>
            </tr>
"""
        
        html += """
        </table>
"""
        
        if stats['attendance']['top_recognized']:
            html += """
        <h2>🏆 Top Reconnus (Aujourd'hui)</h2>
        <table>
            <tr>
                <th>Rang</th>
                <th>Nom</th>
                <th>Détections</th>
            </tr>
"""
            for i, person in enumerate(stats['attendance']['top_recognized'], 1):
                html += f"""
            <tr>
                <td>{i}</td>
                <td>{person['name']}</td>
                <td>{person['count']}</td>
            </tr>
"""
            html += """
        </table>
"""
        
        html += """
        <div class="footer">
            <p>Rapport généré automatiquement par AI Farm-AI</p>
        </div>
    </div>
</body>
</html>
"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✓ Exporté: {filename}")
        return filename
    
    def export_all(self):
        """Exporter dans tous les formats"""
        print(f"\n📊 Export des statistiques ({self.timestamp})\n")
        
        json_file = self.export_json()
        csv_file = self.export_csv()
        html_file = self.export_html()
        
        print(f"\n✅ Tous les fichiers ont été exportés!")
        print(f"\nFichiers créés:")
        print(f"  - {json_file} (JSON)")
        print(f"  - {csv_file} (CSV)")
        print(f"  - {html_file} (HTML)")
        print(f"\nVous pouvez ouvrir le rapport HTML dans un navigateur")
        
        return json_file, csv_file, html_file
    
    def close(self):
        """Fermer la connexion"""
        if self.cursor:
            self.cursor.close()
        if self.db:
            self.db.close()

if __name__ == "__main__":
    import sys
    
    exporter = StatsExporter()
    
    if len(sys.argv) > 1:
        format_type = sys.argv[1].lower()
        
        if format_type == 'json':
            exporter.export_json()
        elif format_type == 'csv':
            exporter.export_csv()
        elif format_type == 'html':
            exporter.export_html()
        else:
            print(f"Format inconnu: {format_type}")
            print("Usage: python EXPORT_STATS.py [json|csv|html|all]")
    else:
        # Exporter tout par défaut
        exporter.export_all()
    
    exporter.close()
