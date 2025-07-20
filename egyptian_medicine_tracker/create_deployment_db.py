#!/usr/bin/env python3
"""
Create a deployment-ready database file for Render free tier
"""

import sqlite3
import os
import shutil
from pathlib import Path

def create_deployment_database():
    """Create a deployment database file"""
    
    print("🚀 CREATING DEPLOYMENT DATABASE FOR RENDER")
    print("=" * 60)
    
    # Source database
    source_db = "egyptian_medicine_tracker/src/database/app.db"
    # Deployment database (smaller, for Git)
    deploy_db = "egyptian_medicine_tracker/deployment_database.db"
    
    if not os.path.exists(source_db):
        print("❌ Source database not found!")
        return False
    
    try:
        # Get source database size
        source_size = os.path.getsize(source_db) / (1024 * 1024)
        print(f"📁 Source database size: {source_size:.1f} MB")
        
        # Create a copy for deployment
        shutil.copy2(source_db, deploy_db)
        
        # Verify copy
        deploy_size = os.path.getsize(deploy_db) / (1024 * 1024)
        print(f"📁 Deployment database size: {deploy_size:.1f} MB")
        
        # Check medicine count
        conn = sqlite3.connect(deploy_db)
        cursor = conn.cursor()
        
        # Check main table
        cursor.execute("SELECT COUNT(*) FROM medicine_dailymed_complete_all")
        main_count = cursor.fetchone()[0]
        
        # Check resume table
        try:
            cursor.execute("SELECT COUNT(*) FROM medicine_dailymed_resume")
            resume_count = cursor.fetchone()[0]
        except:
            resume_count = 0
        
        total_count = main_count + resume_count
        conn.close()
        
        print(f"💊 Total medicines: {total_count:,}")
        print(f"✅ Deployment database created: {deploy_db}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating deployment database: {e}")
        return False

def update_gitignore_for_deployment():
    """Temporarily allow database in Git for deployment"""
    
    print("\n📝 UPDATING .GITIGNORE FOR DEPLOYMENT")
    print("=" * 60)
    
    gitignore_path = ".gitignore"
    
    # Read current .gitignore
    with open(gitignore_path, 'r') as f:
        content = f.read()
    
    # Add comment and allow deployment database
    deployment_content = content + "\n# TEMPORARY: Allow deployment database for Render\n!deployment_database.db\n"
    
    # Write updated .gitignore
    with open(gitignore_path, 'w') as f:
        f.write(deployment_content)
    
    print("✅ Updated .gitignore to allow deployment database")
    print("⚠️  Remember to revert this after deployment!")

def create_deployment_instructions():
    """Create deployment instructions for Render free tier"""
    
    instructions = """
# 🚀 RENDER FREE TIER DEPLOYMENT

## 🎯 Problem Solved
Render free tier doesn't have Shell access, so we need alternative methods.

## 📋 Solution: Include Database in Git

### Step 1: Add Database to Git
```bash
git add deployment_database.db
git commit -m "Add deployment database for Render"
git push origin main
```

### Step 2: Update Your App Code
Modify your database path in your app to use the deployment database:

```python
# In your main.py or database connection code
import os

# Use deployment database if available
if os.path.exists('deployment_database.db'):
    db_path = 'deployment_database.db'
else:
    db_path = 'src/database/app.db'
```

### Step 3: Deploy to Render
1. Push code to GitHub (includes database)
2. Render will automatically deploy
3. Your app will have all 51,441 medicines!

## 🔧 Alternative: Manual Upload
If Git method doesn't work:
1. Go to Render dashboard
2. Look for "Files" or "Upload" option
3. Upload deployment_database.db
4. Restart your app

## ⚠️ Important Notes
- Database file is ~50-100 MB
- Git repository will be larger
- After deployment, you can remove database from Git
- Revert .gitignore changes after deployment

## 🎯 Expected Result
- ✅ App loads with all medicines
- ✅ Search works immediately
- ✅ 51,441 medicines available
"""
    
    with open("RENDER_FREE_TIER_GUIDE.md", "w") as f:
        f.write(instructions)
    
    print("📝 Created RENDER_FREE_TIER_GUIDE.md")

def main():
    """Main function"""
    
    print("🔧 RENDER FREE TIER DEPLOYMENT SETUP")
    print("=" * 60)
    
    # Create deployment database
    success = create_deployment_database()
    
    if success:
        # Update gitignore
        update_gitignore_for_deployment()
        
        # Create instructions
        create_deployment_instructions()
        
        print(f"\n🎯 SETUP COMPLETE!")
        print("=" * 60)
        print("📋 Next steps:")
        print("1. Add deployment_database.db to Git")
        print("2. Update your app code to use deployment database")
        print("3. Push to GitHub")
        print("4. Deploy to Render")
        print("\n📖 Check RENDER_FREE_TIER_GUIDE.md for detailed instructions")
    else:
        print("❌ Setup failed!")

if __name__ == "__main__":
    main() 