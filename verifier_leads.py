#!/usr/bin/env python3
"""
Script de vérification du système LEADS
Vérifie que tous les composants sont correctement installés
"""

import sys
import os
from pathlib import Path

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def check_mark(condition):
    return "✅" if condition else "❌"

def main():
    print_header("🔍 VÉRIFICATION SYSTÈME LEADS")
    
    all_checks = []
    
    # 1. Vérifier les dépendances Python
    print("1️⃣ Vérification des dépendances Python...")
    dependencies = {
        'fastapi': 'FastAPI',
        'supabase': 'Supabase Client',
        'apscheduler': 'APScheduler',
        'stripe': 'Stripe SDK',
        'reportlab': 'ReportLab (PDF)',
        'pydantic': 'Pydantic'
    }
    
    for module, name in dependencies.items():
        try:
            __import__(module)
            print(f"   ✅ {name}")
            all_checks.append(True)
        except ImportError:
            print(f"   ❌ {name} - MANQUANT")
            print(f"      → pip install {module}")
            all_checks.append(False)
    
    # 2. Vérifier les fichiers backend
    print("\n2️⃣ Vérification des fichiers backend...")
    backend_files = {
        'services/lead_service.py': 'LeadService',
        'services/deposit_service.py': 'DepositService',
        'services/notification_service.py': 'NotificationService',
        'services/analytics_service.py': 'AnalyticsService',
        'services/payment_automation_service.py': 'PaymentAutomationService',
        'repositories/lead_repositories.py': 'Lead Repositories',
        'endpoints/leads_endpoints.py': 'Leads Endpoints',
        'scheduler/leads_scheduler.py': 'Leads Scheduler'
    }
    
    backend_path = Path('backend')
    for file, name in backend_files.items():
        file_path = backend_path / file
        exists = file_path.exists()
        print(f"   {check_mark(exists)} {name}")
        all_checks.append(exists)
    
    # 3. Vérifier les fichiers frontend
    print("\n3️⃣ Vérification des composants frontend...")
    frontend_files = {
        'src/components/leads/DepositBalanceCard.js': 'DepositBalanceCard',
        'src/components/leads/PendingLeadsTable.js': 'PendingLeadsTable',
        'src/components/leads/CreateLeadForm.js': 'CreateLeadForm'
    }
    
    frontend_path = Path('frontend')
    for file, name in frontend_files.items():
        file_path = frontend_path / file
        exists = file_path.exists()
        print(f"   {check_mark(exists)} {name}")
        all_checks.append(exists)
    
    # 4. Vérifier le fichier SQL
    print("\n4️⃣ Vérification de la migration SQL...")
    sql_file = Path('database/migrations/leads_system.sql')
    sql_exists = sql_file.exists()
    print(f"   {check_mark(sql_exists)} leads_system.sql")
    all_checks.append(sql_exists)
    
    if sql_exists:
        with open(sql_file, 'r', encoding='utf-8') as f:
            content = f.read()
            tables = ['leads', 'company_deposits', 'deposit_transactions', 
                     'lead_validation', 'influencer_agreements', 'campaign_settings']
            for table in tables:
                has_table = f'CREATE TABLE IF NOT EXISTS {table}' in content
                print(f"      {check_mark(has_table)} Table '{table}'")
                all_checks.append(has_table)
    
    # 5. Vérifier la documentation
    print("\n5️⃣ Vérification de la documentation...")
    docs = {
        'INSTALLATION_RAPIDE_LEADS.md': 'Installation rapide',
        'RECAPITULATIF_FINAL_LEADS.md': 'Récapitulatif',
        'SYSTEME_LEADS_FINAL_COMPLET.md': 'Documentation complète',
        'INDEX_DOCUMENTATION_LEADS.md': 'Index documentation'
    }
    
    for file, name in docs.items():
        file_path = Path(file)
        exists = file_path.exists()
        print(f"   {check_mark(exists)} {name}")
        all_checks.append(exists)
    
    # 6. Vérifier l'intégration server.py
    print("\n6️⃣ Vérification de l'intégration server.py...")
    server_file = Path('backend/server.py')
    if server_file.exists():
        with open(server_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            checks = {
                'scheduler import': 'from scheduler.leads_scheduler import' in content,
                'endpoints import': 'from endpoints.leads_endpoints import' in content,
                'scheduler start': 'start_scheduler()' in content,
                'routes leads': 'app.add_api_route("/api/leads/' in content
            }
            
            for check_name, result in checks.items():
                print(f"   {check_mark(result)} {check_name}")
                all_checks.append(result)
    else:
        print(f"   ❌ server.py non trouvé")
        all_checks.append(False)
    
    # 7. Résumé final
    print_header("📊 RÉSUMÉ")
    
    total = len(all_checks)
    passed = sum(all_checks)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"Tests réussis: {passed}/{total} ({percentage:.1f}%)")
    
    if percentage == 100:
        print("\n✅ TOUS LES COMPOSANTS SONT INSTALLÉS!")
        print("\n🚀 Prochaines étapes:")
        print("   1. Exécuter la migration SQL dans Supabase")
        print("   2. Configurer .env (STRIPE_SECRET_KEY, etc.)")
        print("   3. Démarrer le serveur: python backend/server.py")
        print("   4. Vérifier: http://localhost:8001/docs")
        return 0
    else:
        print(f"\n⚠️  {total - passed} composant(s) manquant(s)")
        print("\n📖 Consultez: INSTALLATION_RAPIDE_LEADS.md")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Vérification interrompue")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        sys.exit(1)
