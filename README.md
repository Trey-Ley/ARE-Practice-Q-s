# ARE 5.0 Daily Flashcard Email — free, no API

Every weekday at 7:45 AM you get three exam-style questions, alternating:

- **Set A:** PcM, PjM, CE
- **Set B:** PA, PDD, PPD

All three questions come first. Then a screen of blank space. Then the answer key, with
why the right answer is right, why each wrong answer is wrong, and the governing
document or code section. Nothing to click or reply to.

**20 weekdays of questions (60 total, 10 per division) are baked into
`are_questions.json`.** No API key, no cost. The script works through the bank one day
per weekday and remembers its place in `are_progress.json`.

**Running-out warnings.** With 3, 2 and 1 days left you get a yellow warning at the top
of the email. On the final day the subject line reads "⚠️ LAST SET" and the warning tells
you what to do. If you run past the end, it recycles from day 1 and labels the email as
repeats, so you never get silence.

## Setup (about 10 minutes)

1. **Create a new private repo** on GitHub, e.g. `are-flashcards`. Runtime is about 15
   seconds a day, so private is free.
2. **Upload `are_flashcards.py` and `are_questions.json`** to the repo root.
3. **Add file → Create new file**, name it `.github/workflows/are_flashcards.yml`, and
   paste in `are_flashcards.yml`.
4. **Add secrets** (Settings → Secrets and variables → Actions):

   | Name | Value |
   |---|---|
   | `GMAIL_ADDRESS` | `tr3y.l3hman@gmail.com` |
   | `GMAIL_APP_PASSWORD` | the same 16-letter app password from the Metra setup |
   | `EMAIL_TO` | only if you want it sent elsewhere |

   Secrets don't carry between repos, so paste the Gmail ones in again. The same app
   password works in both.
5. **Test:** Actions → ARE flashcards → Run workflow → **test**. An email arrives within
   a minute or two and advances you to day 2. Use **preview** to see a day's text in the
   log without sending or advancing, and **status** to see how many days remain.

## When the bank runs out

Ask me for a fresh 20-day set. Then replace `are_questions.json` and delete
`are_progress.json` (Actions → the file → trash icon), which restarts at day 1.

To reset early, just delete `are_progress.json`.

## Good to know
- **Scheduling.** Two cron entries fire at 7:45 AM Chicago time year-round; only the one
  matching the current daylight-saving offset runs. GitHub sometimes starts scheduled
  jobs a few minutes late.
- **Weekends and holidays** don't consume a day. The bank advances only when an email is
  actually sent, so a skipped day never desyncs the A/B alternation.
- **Verify what surprises you.** These are practice questions, not NCARB items, and each
  cites its source. If an answer seems wrong, check the citation, since that check is
  itself good studying. Confirm code figures against the edition your jurisdiction has
  adopted, and contract language against the current AIA documents.
- **Topics covered.** PcM: additional services, claims-made coverage, standard of care,
  overhead and multipliers, instruments of service, firm structure, title laws, statute
  of repose, fee methods, QA programs. PjM: float, earned value, flow-down, RFIs, change
  authority, nonconforming work, fast-track, resource leveling, record documents,
  suspension. CE: correction period, payment certification, submittals, substitutions,
  final payment waiver, initial decisions, retainage, site visits, CCD pricing, POE.
  PA: efficiency ratios, zoning envelope, load factor, allowable area, mixed occupancy,
  soils, existing building code, orientation, parking, budget reconciliation. PPD: egress
  capacity, common path, ramps, HVAC selection, glazing trade-offs, escalation, lateral
  systems, acoustics, site slopes, thermal bridging. PDD: vapor retarders, cavity wall
  flashing, tapered roofing, masonry joints, rebar cover, firestopping, rainscreen
  drainage, specification types, wood shrinkage, door clearances.
