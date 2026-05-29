"""
Creates institutions, their course access lists, and manager/teacher assignments.
Depends on seed_users.py having run first.
"""
from datetime import date
from django.contrib.auth import get_user_model
from student_sponsorship.models import Institution, InstitutionCourseAccess, InstitutionManager

User = get_user_model()

INSTITUTIONS = [
    {
        "slug": "techcorp",
        "name": "TechCorp Learning",
        "contact_name": "Sarah Chen",
        "contact_email": "admin@techcorp.local",
        "seat_limit": 20,
        "contract_start": date(2024, 1, 1),
        "contract_end": date(2026, 12, 31),
        "notes": "Corporate training partner since 2024. Focus on Python and cloud skills.",
        "courses": [
            "course-v1:TechCorp+PY101+2024",
            "course-v1:TechCorp+DS201+2024",
            "course-v1:TechCorp+CLD301+2025",
        ],
        "managers": [
            ("techcorp_admin", InstitutionManager.ROLE_ADMIN,   True),
            ("techcorp_t1",    InstitutionManager.ROLE_TEACHER, False),
            ("techcorp_t2",    InstitutionManager.ROLE_TEACHER, False),
        ],
    },
    {
        "slug": "greentech",
        "name": "Green Technology Institute",
        "contact_name": "Marcus Williams",
        "contact_email": "admin@greentech.local",
        "seat_limit": 10,
        "contract_start": date(2024, 6, 1),
        "contract_end": date(2025, 12, 31),
        "notes": "Focused on sustainability and renewable energy curriculum.",
        "courses": [
            "course-v1:GreenTech+RE101+2024",
            "course-v1:GreenTech+SU201+2024",
        ],
        "managers": [
            ("greentech_admin", InstitutionManager.ROLE_ADMIN,   True),
            ("greentech_t1",    InstitutionManager.ROLE_TEACHER, False),
        ],
    },
    {
        "slug": "horizonedu",
        "name": "Horizon Education Partners",
        "contact_name": "Priya Patel",
        "contact_email": "admin@horizonedu.local",
        "seat_limit": 0,
        "contract_start": date(2025, 1, 1),
        "contract_end": None,
        "notes": "New partner. Unlimited seats during onboarding period.",
        "courses": [
            "course-v1:HorizonEdu+BIZ101+2025",
            "course-v1:HorizonEdu+PM201+2025",
        ],
        "managers": [
            ("horizonedu_admin", InstitutionManager.ROLE_ADMIN,   True),
            ("horizonedu_t1",    InstitutionManager.ROLE_TEACHER, False),
        ],
    },
]

for data in INSTITUTIONS:
    inst, created = Institution.objects.get_or_create(
        slug=data["slug"],
        defaults={k: v for k, v in data.items() if k not in ("slug", "courses", "managers")},
    )
    print(f"  {'+ ' if created else '~ '}{inst.name}")

    for course_id in data["courses"]:
        InstitutionCourseAccess.objects.get_or_create(institution=inst, course_id=course_id)

    for username, role, is_primary in data["managers"]:
        try:
            user = User.objects.get(username=username)
            InstitutionManager.objects.get_or_create(
                institution=inst,
                user=user,
                defaults={"role": role, "is_primary": is_primary},
            )
        except User.DoesNotExist:
            print(f"    ! user '{username}' not found — run seed_users first")

print("\nInstitutions seeded.")
