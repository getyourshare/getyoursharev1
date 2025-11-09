"""
MIGRATION SIMPLE - Utilise test_database_setup.py existant
Copie données mockées et les garde en BDD
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'tests'))

import asyncio
try:
    from backend.tests.test_database_setup import TestDatabase
except ImportError:
    # Fallback pour exécution directe
    from test_database_setup import TestDatabase  # type: ignore

async def migrate_and_keep():
    """Crée données de test et les GARDE en BDD (pas de cleanup)"""
    print("=" * 70)
    print("MIGRATION DONNEES MOCKS -> VRAIE BDD SUPABASE")
    print("=" * 70)
    print()
    
    db = TestDatabase()
    
    try:
        # Créer toutes les données
        print(" Creation de toutes les donnees de test...")
        test_data = await db.setup()
        
        print()
        print("=" * 70)
        print(" MIGRATION REUSSIE!")
        print("=" * 70)
        print()
        print(" DONNEES CREEES EN BASE:")
        print(f"   - Users: {len([k for k in test_data.keys() if 'user_' in k])}")
        print(f"   - Products: {len([k for k in test_data.keys() if 'product_' in k])}")
        print(f"   - Links: {len([k for k in test_data.keys() if 'tracking_link' in k])}")
        print(f"   - Sales: {len([k for k in test_data.keys() if 'sale_' in k])}")
        print(f"   - Commissions: {len([k for k in test_data.keys() if 'commission_' in k])}")
        print()
        print(" IDs CREES:")
        for key, value in test_data.items():
            if isinstance(value, dict) and 'id' in value:
                print(f"   {key}: {value['id']}")
        print()
        print("=" * 70)
        print(" DONNEES DISPONIBLES POUR LES TESTS!")
        print(" Pas de cleanup automatique - donnees conservees")
        print("=" * 70)
        
        return test_data
        
    except Exception as e:
        print(f"\n ERREUR: {e}")
        import traceback
        traceback.print_exc()
        raise

async def cleanup_data():
    """Cleanup manuel des données si nécessaire"""
    print("=" * 70)
    print("CLEANUP DONNEES DE TEST")
    print("=" * 70)
    
    db = TestDatabase()
    await db.cleanup()
    
    print(" Cleanup termine")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--cleanup":
        # Mode cleanup
        asyncio.run(cleanup_data())
    else:
        # Mode migration (creation sans cleanup)
        asyncio.run(migrate_and_keep())
