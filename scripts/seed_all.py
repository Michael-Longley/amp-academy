"""
Master seed script — runs all seed steps in order.

Copy into container and run via manage.py shell:
  See run_seeds.ps1 in this directory.
"""
import os

SEEDS_DIR = "/tmp/amp_seeds"


def run(filename):
    path = os.path.join(SEEDS_DIR, filename)
    print(f"\n{'=' * 55}")
    print(f"  {filename}")
    print(f"{'=' * 55}")
    with open(path) as f:
        exec(compile(f.read(), path, "exec"), {"__name__": "__main__"})


run("seed_users.py")
run("seed_institutions.py")
run("seed_sponsorships.py")

print("\n" + "=" * 55)
print("  All seeds complete.")
print("=" * 55)
print("""
Credentials
  Superuser:       admin / Admin1234!
  Institution admin: techcorp_admin / TestPass123!
  Teacher:         techcorp_t1 / TestPass123!
  Active student:  alex_johnson / TestPass123!
  Unaffiliated:    jordan_taylor / TestPass123!

Portal: http://100.77.129.85/sponsorship/
Admin:  http://100.77.129.85/admin/
""")
