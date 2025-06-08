import os
import sys
import sqlite3
from datetime import datetime

def create_student_groups_tables():
    print("\n[1/3] u041fu0440u043eu0432u0435u0440u043au0430 u0431u0430u0437u044b u0434u0430u043du043du044bu0445...")
    
    # u041fu0443u0442u044c u043a u0431u0430u0437u0435 u0434u0430u043du043du044bu0445
    instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'instance')
    site_db_path = os.path.join(instance_dir, 'site.db')
    
    if not os.path.exists(site_db_path):
        print(f"u041eu0448u0438u0431u043au0430: u0431u0430u0437u0430 u0434u0430u043du043du044bu0445 {site_db_path} u043du0435 u043du0430u0439u0434u0435u043du0430!")
        return
    
    try:
        # u041fu043eu0434u043au043bu044eu0447u0430u0435u043cu0441u044f u043a u0431u0430u0437u0435 u0434u0430u043du043du044bu0445
        conn = sqlite3.connect(site_db_path)
        cursor = conn.cursor()
        
        # u041fu0440u043eu0432u0435u0440u044fu0435u043c u0441u0443u0449u0435u0441u0442u0432u043eu0432u0430u043du0438u0435 u0442u0430u0431u043bu0438u0446u044b student_groups
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='student_groups';")
        student_groups_exists = cursor.fetchone() is not None
        
        # u041fu0440u043eu0432u0435u0440u044fu0435u043c u0441u0443u0449u0435u0441u0442u0432u043eu0432u0430u043du0438u0435 u0442u0430u0431u043bu0438u0446u044b group_access_rules
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='group_access_rules';")
        group_access_rules_exists = cursor.fetchone() is not None
        
        # u041fu0440u043eu0432u0435u0440u044fu0435u043c u043du0430u043bu0438u0447u0438u0435 u043fu043eu043bu044f group_id u0432 u0442u0430u0431u043bu0438u0446u0435 users
        cursor.execute("PRAGMA table_info(users);")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        group_id_exists = 'group_id' in column_names
        
        print("\n[2/3] u0421u043eu0437u0434u0430u043du0438u0435 u043du0435u043eu0431u0445u043eu0434u0438u043cu044bu0445 u0442u0430u0431u043bu0438u0446...")
        
        # u0421u043eu0437u0434u0430u0435u043c u0442u0430u0431u043bu0438u0446u0443 student_groups, u0435u0441u043bu0438 u043eu043du0430 u043du0435 u0441u0443u0449u0435u0441u0442u0432u0443u0435u0442
        if not student_groups_exists:
            cursor.execute("""
            CREATE TABLE student_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """)
            print("u0422u0430u0431u043bu0438u0446u0430 student_groups u0443u0441u043fu0435u0448u043du043e u0441u043eu0437u0434u0430u043du0430.")
        else:
            print("u0422u0430u0431u043bu0438u0446u0430 student_groups u0443u0436u0435 u0441u0443u0449u0435u0441u0442u0432u0443u0435u0442.")
        
        # u0421u043eu0437u0434u0430u0435u043c u0442u0430u0431u043bu0438u0446u0443 group_access_rules, u0435u0441u043bu0438 u043eu043du0430 u043du0435 u0441u0443u0449u0435u0441u0442u0432u0443u0435u0442
        if not group_access_rules_exists:
            cursor.execute("""
            CREATE TABLE group_access_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                content_type VARCHAR(20) NOT NULL,
                content_id INTEGER NOT NULL,
                access_type VARCHAR(20) NOT NULL DEFAULT 'allow',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES student_groups(id) ON DELETE CASCADE,
                UNIQUE (group_id, content_type, content_id)
            );
            """)
            print("u0422u0430u0431u043bu0438u0446u0430 group_access_rules u0443u0441u043fu0435u0448u043du043e u0441u043eu0437u0434u0430u043du0430.")
        else:
            print("u0422u0430u0431u043bu0438u0446u0430 group_access_rules u0443u0436u0435 u0441u0443u0449u0435u0441u0442u0432u0443u0435u0442.")
        
        # u0414u043eu0431u0430u0432u043bu044fu0435u043c u043fu043eu043bu0435 group_id u0432 u0442u0430u0431u043bu0438u0446u0443 users, u0435u0441u043bu0438 u043eu043du043e u043du0435 u0441u0443u0449u0435u0441u0442u0432u0443u0435u0442
        if not group_id_exists:
            cursor.execute("ALTER TABLE users ADD COLUMN group_id INTEGER REFERENCES student_groups(id);")
            print("u041fu043eu043bu0435 group_id u0434u043eu0431u0430u0432u043bu0435u043du043e u0432 u0442u0430u0431u043bu0438u0446u0443 users.")
        else:
            print("u041fu043eu043bu0435 group_id u0443u0436u0435 u0441u0443u0449u0435u0441u0442u0432u0443u0435u0442 u0432 u0442u0430u0431u043bu0438u0446u0435 users.")
        
        # u0421u043eu0437u0434u0430u0435u043c u0438u043du0434u0435u043au0441u044b u0434u043bu044f u0443u0441u043au043eu0440u0435u043du0438u044f u0437u0430u043fu0440u043eu0441u043eu0432
        print("\n[3/3] u0421u043eu0437u0434u0430u043du0438u0435 u0438u043du0434u0435u043au0441u043eu0432...")
        
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_student_groups_name ON student_groups(name);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_group_access_rules_group_id ON group_access_rules(group_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_group_access_rules_content ON group_access_rules(content_type, content_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_group_id ON users(group_id);")
            print("u0418u043du0434u0435u043au0441u044b u0443u0441u043fu0435u0448u043du043e u0441u043eu0437u0434u0430u043du044b.")
        except sqlite3.OperationalError as e:
            print(f"u041eu0448u0438u0431u043au0430 u043fu0440u0438 u0441u043eu0437u0434u0430u043du0438u0438 u0438u043du0434u0435u043au0441u043eu0432: {str(e)}")
        
        # u0421u043eu0445u0440u0430u043du044fu0435u043c u0438u0437u043cu0435u043du0435u043du0438u044f
        conn.commit()
        conn.close()
        
        print("\nu041cu0438u0433u0440u0430u0446u0438u044f u0443u0441u043fu0435u0448u043du043e u0437u0430u0432u0435u0440u0448u0435u043du0430. u0422u0430u0431u043bu0438u0446u044b u0434u043bu044f u0433u0440u0443u043fu043f u0441u0442u0443u0434u0435u043du0442u043eu0432 u0441u043eu0437u0434u0430u043du044b.")
        
    except Exception as e:
        print(f"\nu041eu0448u0438u0431u043au0430 u043fu0440u0438 u0441u043eu0437u0434u0430u043du0438u0438 u0442u0430u0431u043bu0438u0446 u0434u043bu044f u0433u0440u0443u043fu043f u0441u0442u0443u0434u0435u043du0442u043eu0432: {str(e)}")

if __name__ == "__main__":
    create_student_groups_tables()
