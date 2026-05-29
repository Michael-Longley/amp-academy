#!/usr/bin/env bash
# Import all course .tar.gz files from scripts/sample-data/courses into Open edX,
# then wire them into the institution course-access table.
#
# Usage:  bash scripts/seed_courses.sh
# Env:    LMS_CONTAINER  (default: tutor_local-lms-1)
#         CMS_CONTAINER  (default: tutor_local-cms-1)

set -euo pipefail

LMS_CONTAINER="${LMS_CONTAINER:-tutor_local-lms-1}"
CMS_CONTAINER="${CMS_CONTAINER:-tutor_local-cms-1}"
COURSES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/sample-data/courses" && pwd)"

if [ -z "$(ls "$COURSES_DIR"/*.tar.gz 2>/dev/null)" ]; then
  echo "No .tar.gz files found in $COURSES_DIR — nothing to import."
  exit 0
fi

# ── Step 1: extract course IDs from each archive before importing ─────────────
COURSE_IDS=()

for archive in "$COURSES_DIR"/*.tar.gz; do
  name="$(basename "$archive")"
  echo "Reading: $name"

  # Pull out the top-level course.xml to get org/course/run
  course_xml=$(python3 - "$archive" <<'PYEOF'
import sys, tarfile
with tarfile.open(sys.argv[1], "r:gz") as t:
    # find the root course.xml (one directory deep)
    target = next(
        (m for m in t.getmembers()
         if m.name.count("/") == 1 and m.name.endswith("/course.xml")),
        None,
    )
    if not target:
        raise SystemExit(f"No course.xml found in {sys.argv[1]}")
    print(t.extractfile(target).read().decode())
PYEOF
  )

  org=$(echo "$course_xml"    | python3 -c "import sys,re; m=re.search(r'org=\"([^\"]+)\"',    sys.stdin.read()); print(m.group(1))")
  course=$(echo "$course_xml" | python3 -c "import sys,re; m=re.search(r'course=\"([^\"]+)\"', sys.stdin.read()); print(m.group(1))")
  run=$(echo "$course_xml"    | python3 -c "import sys,re; m=re.search(r'url_name=\"([^\"]+)\"', sys.stdin.read()); print(m.group(1))")

  course_id="course-v1:${org}+${course}+${run}"
  echo "  → $course_id"
  COURSE_IDS+=("$course_id")
done

# ── Step 2: import each archive via the CMS ───────────────────────────────────
docker exec "$CMS_CONTAINER" mkdir -p /tmp/course_imports

for archive in "$COURSES_DIR"/*.tar.gz; do
  name="$(basename "$archive")"
  folder="${name%.tar.gz}"

  echo ""
  echo "Importing: $name"
  # Detect the actual top-level folder name inside the archive
  folder=$(python3 - "$archive" <<'PYEOF'
import sys, tarfile
with tarfile.open(sys.argv[1], "r:gz") as t:
    top = next(m.name.split("/")[0] for m in t.getmembers() if "/" in m.name)
    print(top)
PYEOF
  )

  docker cp "$archive" "$CMS_CONTAINER:/tmp/$name"

  docker exec "$CMS_CONTAINER" bash -c "
    mkdir -p /tmp/course_imports
    cd /tmp/course_imports
    rm -rf '$folder'
    tar xzf '/tmp/$name' -C /tmp/course_imports
    cd /openedx/edx-platform
    ./manage.py cms import /tmp/course_imports '$folder' 2>&1 \
      | grep -v '^20[0-9][0-9]-' \
      | grep -v 'DeprecationWarning\|pkg_resources\|casbin\|BLOCK_STRUCT' \
      || true
  "
  echo "  done."
done

# ── Step 3: wire courses into institution course-access via LMS shell ─────────
echo ""
echo "Wiring courses into institutions..."

# Build a Python list literal from the collected course IDs
ids_literal=$(python3 -c "
import sys
ids = sys.argv[1:]
print('[' + ', '.join(repr(i) for i in ids) + ']')
" "${COURSE_IDS[@]}")

docker exec "$LMS_CONTAINER" bash -c "
cd /openedx/edx-platform
./manage.py lms shell -c \"
from student_sponsorship.models import Institution, InstitutionCourseAccess

course_ids = ${ids_literal}

# Assign all imported courses to every institution.
# Edit this mapping to be more selective once you have multiple courses.
for inst in Institution.objects.filter(is_active=True):
    for cid in course_ids:
        obj, created = InstitutionCourseAccess.objects.get_or_create(
            institution=inst, course_id=cid
        )
        if created:
            print(f'  + {inst.name} → {cid}')
        else:
            print(f'  ~ {inst.name} → {cid} (already mapped)')

print('Done.')
\" 2>&1 | grep -v '^20[0-9][0-9]-' | grep -v 'DeprecationWarning\|pkg_resources\|casbin\|BLOCK_STRUCT\|objects imported\|could not be'
" 2>&1

echo ""
echo "Courses seeded: ${COURSE_IDS[*]}"
