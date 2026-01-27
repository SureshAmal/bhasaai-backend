# Learning Service API

The Learning Service manages the gamified Gujarati learning experience, including Spaced Repetition (SM-2) vocabulary lessons, user profiles (XP, streaks), and audio generation.

## Base URL
`/api/v1/learning`

## Endpoints

### 1. Get User Profile
Get learning statistics and gamification status.

- **URL**: `/profile`
- **Method**: `GET`
- **Auth Required**: Yes

#### Response (`LearningProfileResponse`)
```json
{
  "success": true,
  "data": {
    "total_xp": 1500,
    "streak_days": 5,
    "current_level": "Beginner II",
    "vocabulary_mastered": 42,
    "last_activity_date": "2024-01-26T..."
  }
}
```

### 2. Get Daily Vocabulary
Get a daily lesson mix of new words and review items (due for repetition).

- **URL**: `/vocabulary/daily`
- **Method**: `GET`
- **Auth Required**: Yes

#### Query Parameters
| Param | Type | Default | Description |
|---|---|---|---|
| `limit` | int | 10 | Max words to fetch |

#### Response
List of items, where `type` is `new` or `review`.

```json
{
  "success": true,
  "data": [
    {
      "type": "new",
      "word": {
        "id": "uuid",
        "gujarati_word": "નમસ્તે",
        "english_translation": "Hello",
        "transliteration": "Namaste",
        "audio_url": "..."
      }
    }
  ]
}
```

### 3. Submit Progress (SM-2)
Record the result of a flashcard review. This updates the scheduling interval.

- **URL**: `/vocabulary/{word_id}/progress`
- **Method**: `POST`
- **Auth Required**: Yes

#### Request Body (`VocabularyProgressSubmit`)
| Field | Type | Required | Description |
|---|---|---|---|
| `quality` | int | Yes | 0 (Blackout) - 5 (Perfect Recall) |

#### Response (`ProgressResponse`)
```json
{
  "success": true,
  "data": {
    "vocabulary_item_id": "uuid",
    "next_review_date": "2024-01-27...",
    "interval_days": 1.0,
    "is_mastered": false
  }
}
```

### 4. Generate Audio (TTS)
Generate pronunciation audio.

- **URL**: `/audio/tts`
- **Method**: `POST`
- **Auth Required**: Yes

#### Request Body (`TTSRequest`)
| Field | Type | Required | Description |
|---|---|---|---|
| `text` | string | Yes | Text to speak |
| `language` | string | No | `gu` or `en` (default `gu`) |

#### Response
```json
{
  "success": true,
  "data": {
    "audio_url": "https://storage..."
  }
}
```
