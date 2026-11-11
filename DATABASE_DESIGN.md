# Database Design

## Storage and scope

Use SQLite through SQLAlchemy, with the database file in the Flask `instance\` directory. The application is a single-user annotation workspace: there is one editable profile and no account, cloud sync, or remote database. Clip references are plain text; no video or other media files are stored.

Tables use integer primary keys and UTC creation/update timestamps where relevant. Text is stored as entered after server-side trimming and length validation. Controlled values are checked in application validation and, where practical, database constraints.

## Tables and relationships

### `user_profiles`

One profile row for the annotation workspace.

- `id` — primary key, restricted to `1` to enforce one profile
- `name` — optional display name
- `introduction` — optional professional introduction
- `experience` — optional relevant experience
- `technical_interests` — optional interests
- `skills` — optional skills text
- `contact_information` — optional contact text
- `created_at`, `updated_at`

Personal details are never hardcoded. Contact information is included in a report only when the user has entered it.

### `exercises`

An exercise/clip context that can own multiple observations.

- `id` — primary key
- `title` — required exercise title
- `clip_reference` — optional text-only reference
- `created_at`, `updated_at`

Relationships: one exercise has many object/action observations, movement observations, quality assessments, and quality issues. Deleting an exercise deletes its dependent assessment records.

### `object_action_observations`

- `id` — primary key
- `exercise_id` — required foreign key to `exercises`
- `timestamp` — required `MM:SS` or `HH:MM:SS` text, optionally a nondecreasing range
- `identified_object` — required text
- `observed_action` — required text
- `additional_observations` — optional text
- `created_at`, `updated_at`

### `movement_observations`

- `id` — primary key
- `exercise_id` — required foreign key to `exercises`
- `timestamp` — required timestamp/range text
- `movement_description` — required text
- `visibility` — required enum: `clearly_visible`, `partially_visible`, `obstructed`, `unclear`
- `plausibility` — required enum: `plausible`, `uncertain`, `implausible`
- `inconsistencies` — optional text
- `reasoning` — required explanation text
- `created_at`, `updated_at`

### `quality_assessments`

One assessment per exercise; only a complete assessment is considered complete for dashboard/report scoring.

- `id` — primary key
- `exercise_id` — required unique foreign key to `exercises`
- `created_at`, `updated_at`

### `quality_ratings`

Normalized rating rows under a quality assessment.

- `id` — primary key
- `assessment_id` — required foreign key to `quality_assessments`
- `category` — required enum, unique per assessment: `visual_clarity`, `camera_angle`, `object_visibility`, `movement_visibility`, `overall_footage_quality`
- `score` — required integer from 1 through 10
- `explanation` — required text

An assessment is complete only when it has exactly one valid row for each of the five categories. Partial drafts may contain one to four category rows but have no overall score. The overall score is the arithmetic mean of all five scores and is not independently editable or stored as a separate user-entered value.

### `quality_issues`

Attention-to-detail findings, also supporting an explicit reviewed-with-no-issues state.

- `id` — primary key
- `exercise_id` — required foreign key to `exercises`
- `timestamp` — required `MM:SS` or `HH:MM:SS` timestamp/range
- `category` — required enum: `missing_objects`, `unexpected_object_movement`, `unclear_actions`, `visual_obstruction`, `inconsistent_frames`, `other`
- `description` — required text
- `severity` — required enum selected from a documented set (`low`, `medium`, `high`)
- `explanation` — required text
- `suggested_correction` — optional text
- `created_at`, `updated_at`

### `section_reviews`

Explicit review state per exercise. This lets a user complete Attention to Detail after checking a clip and finding no issues, without creating a misleading dummy issue.

- `id` — primary key
- `exercise_id` — required foreign key to `exercises`
- `section_key` — required enum: `object_action`, `movement`, `quality`, `attention_to_detail`
- `reviewed_at` — nullable UTC timestamp

`(exercise_id, section_key)` is unique. The app must not let a review state override missing required data: object/action and movement require at least one valid saved observation, and quality requires a complete assessment. Attention to Detail can be reviewed with zero issues. If a change makes a section's required data invalid, the dashboard and report treat it as incomplete regardless of any prior review timestamp.

The Phase 1 prototype used a global `section_reviews` table without an exercise association. On startup, the app renames that table to `legacy_section_reviews` before creating the exercise-scoped table. Existing rows are preserved but not applied to any assessment because their original exercise cannot be determined safely.

## Integrity and validation

- Foreign keys are enabled for SQLite connections.
- Numeric quality scores are constrained to integers 1–10.
- Category/status values are allow-listed and constrained; unknown values are rejected with a visible validation message.
- Required text is trimmed and cannot be blank; field lengths are bounded.
- Unique constraints prevent duplicate quality categories per assessment and duplicate assessment per exercise.
- Deletes use SQLAlchemy relationships with deliberate cascade behavior so child rows cannot become orphaned.
- Database errors are logged locally and surfaced as an actionable error; errors do not produce success-shaped responses.
- The initial schema is created by the app factory. The targeted Phase 2 SQLite schema change preserves the former global review table as `legacy_section_reviews`; broader migrations will be added when needed.
- The Phase 6 SQLite migration adds insert/update triggers to existing `quality_issues` tables so required timestamps are enforced without rebuilding or discarding existing records.

## Relationships

```text
user_profiles (single local profile)

exercises
  ├── object_action_observations (one-to-many)
  ├── movement_observations (one-to-many)
  ├── quality_assessments (one-to-zero-or-one)
  │     └── quality_ratings (one-to-five, complete only with all five)
  └── quality_issues (one-to-many)

section_reviews (one row per section per exercise)
```
