# Seed Data Credentials

All accounts were created by `run_seeds.sh`. Re-run it anytime to restore missing data.

**Base URL:** http://local.openedx.io

> **Hosts file required:** Add to `C:\Windows\System32\drivers\etc\hosts` (run Notepad as Administrator):
> ```
> 127.0.0.1  local.openedx.io
> 127.0.0.1  studio.local.openedx.io
> ```

## Platform

| Role      | Username | Email                    | Password     | URL                                    |
|-----------|----------|--------------------------|--------------|-----------------------------------------|
| Superuser | `admin`  | `admin@localhost.local`  | `Admin1234!` | http://local.openedx.io/admin/ |

## Institution Admins

| Institution                 | Username          | Email                        | Password       |
|-----------------------------|-------------------|------------------------------|----------------|
| TechCorp Learning           | `techcorp_admin`  | `admin@techcorp.local`       | `TestPass123!` |
| Green Technology Institute  | `greentech_admin` | `admin@greentech.local`      | `TestPass123!` |
| Horizon Education Partners  | `horizonedu_admin`| `admin@horizonedu.local`     | `TestPass123!` |

## Teachers

| Institution                | Username       | Email                             | Password       | Assigned Students          |
|----------------------------|----------------|-----------------------------------|----------------|----------------------------|
| TechCorp Learning          | `techcorp_t1`  | `james.rodriguez@techcorp.local`  | `TestPass123!` | alex_johnson, maria_garcia |
| TechCorp Learning          | `techcorp_t2`  | `emily.nguyen@techcorp.local`     | `TestPass123!` | ryan_patel                 |
| Green Technology Institute | `greentech_t1` | `david.kim@greentech.local`       | `TestPass123!` | olivia_smith, noah_brown   |
| Horizon Education Partners | `horizonedu_t1`| `lisa.thompson@horizonedu.local`  | `TestPass123!` | (unassigned)               |

## Students

| Username          | Email                             | Password       | Status       | Institution                |
|-------------------|-----------------------------------|----------------|--------------|----------------------------|
| `alex_johnson`    | `alex.johnson@example.local`      | `TestPass123!` | Active       | TechCorp Learning          |
| `maria_garcia`    | `maria.garcia@example.local`      | `TestPass123!` | Active       | TechCorp Learning          |
| `ryan_patel`      | `ryan.patel@example.local`        | `TestPass123!` | Active       | TechCorp Learning          |
| `olivia_smith`    | `olivia.smith@example.local`      | `TestPass123!` | Active       | Green Technology Institute |
| `noah_brown`      | `noah.brown@example.local`        | `TestPass123!` | Active       | Green Technology Institute |
| `emma_davis`      | `emma.davis@example.local`        | `TestPass123!` | Active       | Horizon Education Partners |
| `liam_wilson`     | `liam.wilson@example.local`       | `TestPass123!` | Active       | Horizon Education Partners |
| `sophia_martinez` | `sophia.martinez@example.local`   | `TestPass123!` | Grace period | TechCorp Learning          |

## Pending Invitations (no LMS account — register with this email to test the claim flow)

| Email                                  | Institution                |
|----------------------------------------|----------------------------|
| `pending1@techcorp-client.local`       | TechCorp Learning          |
| `pending2@techcorp-client.local`       | TechCorp Learning          |
| `incoming@greentech-client.local`      | Green Technology Institute |
| `cohort.member1@horizonedu-client.local` | Horizon Education Partners |
| `cohort.member2@horizonedu-client.local` | Horizon Education Partners |

## Unaffiliated Users (registered but not sponsored)

| Username       | Email                          | Password       |
|----------------|--------------------------------|----------------|
| `jordan_taylor`| `jordan.taylor@example.local`  | `TestPass123!` |
| `casey_white`  | `casey.white@example.local`    | `TestPass123!` |
| `morgan_clark` | `morgan.clark@example.local`   | `TestPass123!` |

## Courses

| Course ID                                          | Name                  |
|----------------------------------------------------|-----------------------|
| `course-v1:AmpAcademy+NEC2017Journeyman+course`    | NEC 2017 Journeyman   |

Add more courses by dropping `.tar.gz` files into `scripts/sample-data/courses/` and re-running `bash scripts/seed_courses.sh`.

**Studio (course authoring):** http://studio.local.openedx.io

## Sponsorship Portal

| URL                                          | What you see                        |
|----------------------------------------------|-------------------------------------|
| http://local.openedx.io/sponsorship/         | Portal home (login required)        |
| http://local.openedx.io/admin/               | Django admin                        |
| http://local.openedx.io/courses/             | LMS course catalog                  |
