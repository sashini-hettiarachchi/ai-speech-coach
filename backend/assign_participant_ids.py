"""
Utility script to assign participant IDs (P1-P7) to users

This script helps assign participant IDs to existing users in the database.
Run this script from the backend directory.

Usage:
    python assign_participant_ids.py
"""

from app import app, db
from models import User
from sqlalchemy import and_

def list_users():
    """List all users in the database with their current participant_id"""
    with app.app_context():
        users = User.query.all()
        
        if not users:
            print("No users found in the database.")
            return []
        
        print("\n" + "="*80)
        print("Current Users in Database:")
        print("="*80)
        print(f"{'ID':<5} {'Participant ID':<15} {'Auth0 User ID':<40} {'Created At'}")
        print("-"*80)
        
        for user in users:
            participant_id = user.participant_id or "Not assigned"
            created_at = user.created_at.strftime("%Y-%m-%d %H:%M") if user.created_at else "N/A"
            auth0_id = user.auth0_user_id[:37] + "..." if len(user.auth0_user_id) > 40 else user.auth0_user_id
            print(f"{user.id:<5} {participant_id:<15} {auth0_id:<40} {created_at}")
        
        print("="*80 + "\n")
        return users

def assign_participant_id(user_id, participant_id):
    """Assign a participant ID to a user"""
    with app.app_context():
        # Validate participant_id
        valid_ids = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7']
        if participant_id not in valid_ids:
            print(f"❌ Error: Participant ID must be one of {valid_ids}")
            return False
        
        # Check if participant_id is already assigned
        existing = User.query.filter_by(participant_id=participant_id).first()
        if existing and existing.id != user_id:
            print(f"❌ Error: Participant ID '{participant_id}' is already assigned to user {existing.id}")
            return False
        
        # Get user
        user = User.query.get(user_id)
        if not user:
            print(f"❌ Error: User with ID {user_id} not found")
            return False
        
        # Assign participant_id
        user.participant_id = participant_id
        db.session.commit()
        
        print(f"✅ Successfully assigned '{participant_id}' to user {user_id} ({user.auth0_user_id})")
        return True

def bulk_assign():
    """Interactively assign participant IDs to users"""
    with app.app_context():
        users = list_users()
        
        if not users:
            return
        
        print("Bulk Assignment Mode")
        print("Enter participant IDs for each user (P1-P7), or 'skip' to skip a user")
        print("Enter 'done' to finish, or 'list' to show users again\n")
        
        while True:
            cmd = input("Command (list/assign/done): ").strip().lower()
            
            if cmd == 'done':
                print("\n✅ Assignment complete!")
                break
            elif cmd == 'list':
                list_users()
            elif cmd == 'assign':
                try:
                    user_id = int(input("Enter user ID: ").strip())
                    participant_id = input("Enter participant ID (P1-P7): ").strip().upper()
                    assign_participant_id(user_id, participant_id)
                except ValueError:
                    print("❌ Invalid user ID. Please enter a number.")
                except Exception as e:
                    print(f"❌ Error: {str(e)}")
            else:
                print("Invalid command. Use 'list', 'assign', or 'done'")

def auto_assign_sequential():
    """Automatically assign P1-P7 to users without participant_id in creation order"""
    with app.app_context():
        # Get users without participant_id
        users_without_id = User.query.filter(
            User.participant_id.is_(None)
        ).order_by(User.created_at.asc()).limit(7).all()
        
        if not users_without_id:
            print("✅ All users already have participant IDs assigned.")
            return
        
        print(f"\nFound {len(users_without_id)} users without participant IDs")
        print("Auto-assigning P1-P7 in creation order...\n")
        
        for idx, user in enumerate(users_without_id, start=1):
            participant_id = f"P{idx}"
            user.participant_id = participant_id
            print(f"  {participant_id} → User {user.id} ({user.auth0_user_id[:30]}...)")
        
        confirm = input("\nProceed with auto-assignment? (yes/no): ").strip().lower()
        if confirm == 'yes':
            db.session.commit()
            print("\n✅ Auto-assignment complete!")
            list_users()
        else:
            db.session.rollback()
            print("\n❌ Auto-assignment cancelled.")

if __name__ == "__main__":
    print("\n" + "="*80)
    print("Participant ID Assignment Utility")
    print("="*80)
    
    while True:
        print("\nOptions:")
        print("1. List all users")
        print("2. Assign participant ID to a user")
        print("3. Bulk assign (interactive)")
        print("4. Auto-assign P1-P7 sequentially to unassigned users")
        print("5. Exit")
        
        choice = input("\nSelect an option (1-5): ").strip()
        
        if choice == '1':
            list_users()
        elif choice == '2':
            try:
                user_id = int(input("Enter user ID: ").strip())
                participant_id = input("Enter participant ID (P1-P7): ").strip().upper()
                assign_participant_id(user_id, participant_id)
            except ValueError:
                print("❌ Invalid user ID. Please enter a number.")
            except Exception as e:
                print(f"❌ Error: {str(e)}")
        elif choice == '3':
            bulk_assign()
        elif choice == '4':
            auto_assign_sequential()
        elif choice == '5':
            print("\n👋 Goodbye!\n")
            break
        else:
            print("❌ Invalid option. Please select 1-5.")
