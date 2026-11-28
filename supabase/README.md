# Supabase

The project utilizes **Supabase PostgreSQL** for collection and storage of Kafkaesque occurrences.

## Database Schema

| Table | Description |
|---|---|
| `environments` | Environments in which occurrences are observed |
| `subjects` | Subjects associated with occurrences |
| `modalities` | Interaction modalities, such as meetings, calls, and messages |
| `occurrences` | Timestamped observations, Kafkaesque scores, and contributor references |
| `testimonies` | Descriptions associated with individual occurrences |
| `presences` | Confirmed presence intervals for individual subjects |

The view `occurrences_v` consolidates occurrence records.

The PostgreSQL function `submit_occurrences()` validates authenticated submissions, resolves reference IDs, and atomically inserts occurrences and testimonies.

## Database Management

The database schema is maintained through versioned SQL migrations in `supabase/migrations/`, managed using the Supabase CLI.
