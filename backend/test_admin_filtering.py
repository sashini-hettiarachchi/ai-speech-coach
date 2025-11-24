"""
Test script to verify admin dashboard filters only P1-P7 participants

This script tests the filtering logic to confirm only P1-P7 users are shown.
"""

from app import app, db
from models import User, Speech, Session, UserPRPSAAssessment

def test_admin_filtering():
    """Test that admin endpoints only return P1-P7 users"""
    
    with app.app_context():
        print("\n" + "="*80)
        print("ADMIN DASHBOARD FILTERING TEST")
        print("="*80)
        
        # Get all users in database
        all_users = User.query.all()
        print(f"\n📊 Total users in database: {len(all_users)}")
        
        # Show all users
        print("\n" + "-"*80)
        print("All Users in Database:")
        print("-"*80)
        for user in all_users:
            pid = user.participant_id or "NULL"
            print(f"  ID: {user.id:<3} | Participant: {pid:<5} | Name: {user.auth0_user_id[:30]}")
        
        # Filter for P1-P7 (what admin dashboard will show)
        valid_participant_ids = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7']
        filtered_users = User.query.filter(User.participant_id.in_(valid_participant_ids)).all()
        
        print("\n" + "="*80)
        print("ADMIN DASHBOARD WILL SHOW (P1-P7 only):")
        print("="*80)
        print(f"Total participants shown: {len(filtered_users)}")
        print("-"*80)
        
        for user in sorted(filtered_users, key=lambda x: x.participant_id):
            # Get stats
            speech_count = Speech.query.filter_by(user_id=user.id).count()
            session_count = db.session.query(Session).join(Speech).filter(
                Speech.user_id == user.id
            ).count()
            
            # Get PRPSA
            initial = UserPRPSAAssessment.query.filter_by(
                user_id=user.id, assessment_type='initial'
            ).first()
            post = UserPRPSAAssessment.query.filter_by(
                user_id=user.id, assessment_type='post_experimental'
            ).first()
            
            initial_score = initial.total_score if initial else "N/A"
            post_score = post.total_score if post else "N/A"
            
            print(f"\n  {user.participant_id} - {user.auth0_user_id[:30]}")
            print(f"    User ID: {user.id}")
            print(f"    Speeches: {speech_count} | Sessions: {session_count}")
            print(f"    PRPSA: Initial={initial_score}, Post={post_score}")
        
        # Show excluded users
        excluded_users = [u for u in all_users if u not in filtered_users]
        if excluded_users:
            print("\n" + "="*80)
            print("EXCLUDED FROM ADMIN DASHBOARD:")
            print("="*80)
            for user in excluded_users:
                pid = user.participant_id or "NULL"
                print(f"  ID: {user.id:<3} | Participant: {pid:<5} | {user.auth0_user_id[:30]}")
                print(f"    Reason: {'No participant_id assigned' if not user.participant_id else f'Outside P1-P7 range ({user.participant_id})'}")
        
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"  Total users in database: {len(all_users)}")
        print(f"  Shown in admin dashboard: {len(filtered_users)} (P1-P7)")
        print(f"  Excluded from dashboard: {len(excluded_users)}")
        print("="*80 + "\n")
        
        # Verify the expected 7 participants
        if len(filtered_users) == 7:
            print("✅ SUCCESS: Exactly 7 participants (P1-P7) will be shown in admin dashboard")
        elif len(filtered_users) < 7:
            missing = set(['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7']) - set([u.participant_id for u in filtered_users])
            print(f"⚠️  WARNING: Only {len(filtered_users)} participants found. Missing: {missing}")
        else:
            print(f"⚠️  WARNING: Found {len(filtered_users)} participants (expected 7)")

if __name__ == "__main__":
    test_admin_filtering()
