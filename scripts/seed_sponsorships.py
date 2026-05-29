"""
Creates sponsorships in a realistic mix of states:
  active   — student has an account and is enrolled
  pending  — invitation sent to an email with no LMS account yet
  grace    — sponsorship removed, student has until end-of-month access
  expired  — grace period passed, access ended

Depends on seed_users.py and seed_institutions.py having run first.
"""
import calendar
from datetime import date, timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from student_sponsorship.models import (
    Institution, Sponsorship, SponsorshipInvitation,
    InstitutionManager, TeacherStudentAssignment,
)

User = get_user_model()


def get_inst(slug):
    return Institution.objects.get(slug=slug)


def get_user(username):
    return User.objects.get(username=username)


def end_of_month(d=None):
    d = d or date.today()
    last_day = calendar.monthrange(d.year, d.month)[1]
    return d.replace(day=last_day)


def make_active(inst, email, username):
    if Sponsorship.objects.filter(institution=inst, invited_email=email,
                                   status__in=["active", "pending", "grace"]).exists():
        return None
    student = get_user(username)
    sp = Sponsorship.objects.create(
        institution=inst,
        student=student,
        invited_email=email,
        status=Sponsorship.STATUS_ACTIVE,
    )
    print(f"    + active  {email}")
    return sp


def make_pending(inst, email):
    if Sponsorship.objects.filter(institution=inst, invited_email=email,
                                   status__in=["active", "pending", "grace"]).exists():
        return None
    sp = Sponsorship.objects.create(
        institution=inst,
        invited_email=email,
        status=Sponsorship.STATUS_PENDING,
    )
    SponsorshipInvitation.objects.create(
        sponsorship=sp,
        expires_at=timezone.now() + timedelta(days=7),
    )
    print(f"    + pending {email}")
    return sp


def make_grace(inst, email, username, removed_by_username, days_ago=5):
    if Sponsorship.objects.filter(institution=inst, invited_email=email,
                                   status__in=["active", "pending", "grace"]).exists():
        return None
    student = get_user(username)
    removed_by = get_user(removed_by_username)
    sp = Sponsorship.objects.create(
        institution=inst,
        student=student,
        invited_email=email,
        status=Sponsorship.STATUS_GRACE,
        grace_end=end_of_month(),
        removed_at=timezone.now() - timedelta(days=days_ago),
        removed_by=removed_by,
    )
    print(f"    + grace   {email}  (until {sp.grace_end})")
    return sp


def make_expired(inst, email, username, removed_by_username):
    if Sponsorship.objects.filter(institution=inst, invited_email=email,
                                   status="expired").exists():
        return None
    student = get_user(username)
    removed_by = get_user(removed_by_username)
    past_month = date.today().replace(day=1) - timedelta(days=1)
    sp = Sponsorship.objects.create(
        institution=inst,
        student=student,
        invited_email=email,
        status=Sponsorship.STATUS_EXPIRED,
        grace_end=end_of_month(past_month),
        removed_at=timezone.now() - timedelta(days=45),
        removed_by=removed_by,
    )
    print(f"    + expired {email}")
    return sp


def assign(teacher_username, sponsorship):
    if sponsorship is None:
        return
    try:
        mgr = InstitutionManager.objects.get(user__username=teacher_username)
        TeacherStudentAssignment.objects.get_or_create(teacher=mgr, sponsorship=sponsorship)
    except InstitutionManager.DoesNotExist:
        print(f"    ! manager '{teacher_username}' not found")


# ── TechCorp ──────────────────────────────────────────────────────────────────
print("\n  TechCorp Learning")
tc = get_inst("techcorp")

sp_alex  = make_active(tc, "alex.johnson@example.local",  "alex_johnson")
sp_maria = make_active(tc, "maria.garcia@example.local",  "maria_garcia")
sp_ryan  = make_active(tc, "ryan.patel@example.local",    "ryan_patel")

make_pending(tc, "pending1@techcorp-client.local")
make_pending(tc, "pending2@techcorp-client.local")

sp_grace = make_grace(tc, "sophia.martinez@example.local", "sophia_martinez", "techcorp_admin")

# An expired sponsorship from a previous employee
make_expired(tc, "former.employee@techcorp-client.local", "morgan_clark", "techcorp_admin")

# Teacher assignments
assign("techcorp_t1", sp_alex)
assign("techcorp_t1", sp_maria)
assign("techcorp_t2", sp_ryan)

# ── GreenTech ─────────────────────────────────────────────────────────────────
print("\n  Green Technology Institute")
gt = get_inst("greentech")

sp_olivia = make_active(gt, "olivia.smith@example.local", "olivia_smith")
sp_noah   = make_active(gt, "noah.brown@example.local",   "noah_brown")

make_pending(gt, "incoming@greentech-client.local")

assign("greentech_t1", sp_olivia)
assign("greentech_t1", sp_noah)

# ── HorizonEdu ────────────────────────────────────────────────────────────────
print("\n  Horizon Education Partners")
he = get_inst("horizonedu")

make_active(he, "emma.davis@example.local", "emma_davis")
make_active(he, "liam.wilson@example.local", "liam_wilson")

# Pending cohort invite — two people haven't claimed yet
make_pending(he, "cohort.member1@horizonedu-client.local")
make_pending(he, "cohort.member2@horizonedu-client.local")

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"""
Sponsorships seeded:
  Active:  {Sponsorship.objects.filter(status='active').count()}
  Pending: {Sponsorship.objects.filter(status='pending').count()}
  Grace:   {Sponsorship.objects.filter(status='grace').count()}
  Expired: {Sponsorship.objects.filter(status='expired').count()}
""")
