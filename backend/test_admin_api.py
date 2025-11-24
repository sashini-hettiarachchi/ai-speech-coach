"""
Test script to verify what the admin API endpoints are returning
"""

from app import app, db
from models import User

def test_admin_users_query():
    """Test what the admin users endpoint query returns"""
    
    with app.app_context():
        print("\n" + "="*80)
        print("TESTING ADMIN /api/v1/admin/users QUERY")
        print("="*80)
        
        # This is the exact query from the endpoint
        valid_participant_ids = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7']
        users = User.query.filter(User.participant_id.in_(valid_participant_ids)).all()
        
        print(f"\nQuery: User.query.filter(User.participant_id.in_({valid_participant_ids})).all()")
        print(f"\nResults: {len(users)} users found")
        print("-"*80)
        
        for user in sorted(users, key=lambda x: x.participant_id if x.participant_id else 'Z'):
            print(f"  User ID: {user.id:<3} | Participant ID: {user.participant_id:<5} | Auth0: {user.auth0_user_id[:30]}")
        
        print("\n" + "="*80)
        print("CONCLUSION")
        print("="*80)
        
        # Check if any excluded users are present
        excluded_ids = [1, 3, 4, 12, 13]
        found_excluded = [u for u in users if u.id in excluded_ids]
        
        if found_excluded:
            print("❌ ERROR: Found excluded users in results!")
            for u in found_excluded:
                print(f"   - User ID {u.id} with participant_id '{u.participant_id}' should NOT be included")
        else:
            print("✅ SUCCESS: Only P1-P7 users are in the results")
            print(f"   Expected 7 users, found {len(users)} users")
        
        print("="*80 + "\n")

if __name__ == "__main__":
    test_admin_users_query()
