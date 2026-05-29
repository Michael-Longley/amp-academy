"""
Creates all seed users with Open edX UserProfiles.
All test accounts use password: TestPass123!
Superuser uses: Admin1234!
"""
from django.contrib.auth import get_user_model
from common.djangoapps.student.models import UserProfile

User = get_user_model()

USERS = [
    # (username, email, full_name, password, is_staff, is_superuser)
    ("admin",            "admin@localhost.local",            "Platform Admin",  "Admin1234!",   True,  True),
    # Institution admins
    ("techcorp_admin",   "admin@techcorp.local",            "Sarah Chen",      "TestPass123!", False, False),
    ("greentech_admin",  "admin@greentech.local",           "Marcus Williams", "TestPass123!", False, False),
    ("horizonedu_admin", "admin@horizonedu.local",          "Priya Patel",     "TestPass123!", False, False),
    # Teachers
    ("techcorp_t1",      "james.rodriguez@techcorp.local",  "James Rodriguez", "TestPass123!", False, False),
    ("techcorp_t2",      "emily.nguyen@techcorp.local",     "Emily Nguyen",    "TestPass123!", False, False),
    ("greentech_t1",     "david.kim@greentech.local",       "David Kim",       "TestPass123!", False, False),
    ("horizonedu_t1",    "lisa.thompson@horizonedu.local",  "Lisa Thompson",   "TestPass123!", False, False),
    # Active sponsored students — TechCorp
    ("alex_johnson",     "alex.johnson@example.local",      "Alex Johnson",    "TestPass123!", False, False),
    ("maria_garcia",     "maria.garcia@example.local",      "Maria Garcia",    "TestPass123!", False, False),
    ("ryan_patel",       "ryan.patel@example.local",        "Ryan Patel",      "TestPass123!", False, False),
    # Active sponsored students — GreenTech
    ("olivia_smith",     "olivia.smith@example.local",      "Olivia Smith",    "TestPass123!", False, False),
    ("noah_brown",       "noah.brown@example.local",        "Noah Brown",      "TestPass123!", False, False),
    # Active sponsored students — HorizonEdu
    ("emma_davis",       "emma.davis@example.local",        "Emma Davis",      "TestPass123!", False, False),
    ("liam_wilson",      "liam.wilson@example.local",       "Liam Wilson",     "TestPass123!", False, False),
    # Grace-period students (accounts exist, sponsorship being wound down)
    ("sophia_martinez",  "sophia.martinez@example.local",   "Sophia Martinez", "TestPass123!", False, False),
    # Unaffiliated users (registered but not sponsored)
    ("jordan_taylor",    "jordan.taylor@example.local",     "Jordan Taylor",   "TestPass123!", False, False),
    ("casey_white",      "casey.white@example.local",       "Casey White",     "TestPass123!", False, False),
    ("morgan_clark",     "morgan.clark@example.local",      "Morgan Clark",    "TestPass123!", False, False),
]

created = 0
for username, email, full_name, password, is_staff, is_superuser in USERS:
    # Skip if email is already taken by a different username
    if User.objects.filter(email=email).exclude(username=username).exists():
        print(f"  ~ {username} (email {email} already in use, skipping)")
        continue
    try:
        user, new = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_staff": is_staff, "is_superuser": is_superuser},
        )
    except Exception as e:
        print(f"  ! {username}: {e}")
        continue
    if new:
        user.set_password(password)
        user.save()
        created += 1
        print(f"  + {username}")
    # Ensure profile exists even for pre-existing users
    UserProfile.objects.get_or_create(user=user, defaults={"name": full_name})

print(f"\nUsers: {created} created, {len(USERS) - created} already existed.")
