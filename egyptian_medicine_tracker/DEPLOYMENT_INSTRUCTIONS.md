
# 🚀 DEPLOYMENT DATABASE SETUP

## Option 1: Copy Local Database (Recommended)
1. Copy your local `src/database/app.db` to your deployment server
2. The database contains 51,441 medicines ready to use

## Option 2: Recreate Database on Server
1. Download DailyMed ZIP files to server
2. Run extraction scripts on server
3. This will take time but ensures fresh data

## Option 3: Use Database Backup
1. Create a backup of your local database
2. Upload backup to deployment server
3. Restore database on server

## Quick Commands:
```bash
# Copy database to server (replace with your server details)
scp src/database/app.db user@your-server:/path/to/app/

# Or use rsync
rsync -avz src/database/app.db user@your-server:/path/to/app/
```

## Database Location:
- Local: `src/database/app.db`
- Server: Same path in your deployed app
