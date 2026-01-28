# Dictionary Service API

The Dictionary Service provides a bilingual English-Gujarati / Gujarati-English dictionary with LLM-powered translations, meanings, parts of speech, and example sentences.

## Base URL
`/api/v1/dictionary`

## Features
- Bidirectional translation (EN→GU, GU→EN)
- Part of speech tagging (noun, verb, adjective, etc.)
- Example sentences with translations
- Synonyms and antonyms
- Search history tracking
- Automatic caching of LLM translations

## Endpoints

### 1. Lookup/Translate Word
Lookup a word and get full dictionary entry.

- **URL**: `/lookup`
- **Method**: `POST`
- **Auth Required**: Yes

#### Request Body (`DictionaryLookupRequest`)
| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `word` | string | Yes | - | Word to translate (1-100 chars) |
| `direction` | string | No | `en_to_gu` | `en_to_gu` or `gu_to_en` |
| `include_examples` | boolean | No | true | Include example sentences |
| `include_audio` | boolean | No | false | Generate TTS audio |

#### Response (`DictionaryEntryResponse`)
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "word": "hello",
    "language": "en",
    "translation": "નમસ્તે",
    "transliteration": "namaste",
    "part_of_speech": "interjection",
    "meaning": "A greeting used when meeting someone",
    "meaning_gujarati": "કોઈને મળતી વખતે વપરાતું શુભેચ્છા શબ્દ",
    "example_sentence": "Hello, how are you?",
    "example_sentence_translation": "નમસ્તે, તમે કેમ છો?",
    "synonyms": ["hi", "greetings"],
    "antonyms": ["goodbye"],
    "audio_url": null,
    "lookup_count": 42,
    "created_at": "2024-01-26T..."
  }
}
```

---

### 2. Get Dictionary Entry
Get a cached dictionary entry by ID.

- **URL**: `/{entry_id}`
- **Method**: `GET`
- **Auth Required**: Yes

#### Path Parameters
| Param | Type | Description |
|---|---|---|
| `entry_id` | UUID | Dictionary entry ID |

#### Response
Same as lookup response.

---

### 3. Get Search History
Get user's word lookup history.

- **URL**: `/history`
- **Method**: `GET`
- **Auth Required**: Yes

#### Query Parameters
| Param | Type | Default | Description |
|---|---|---|---|
| `page` | int | 1 | Page number |
| `per_page` | int | 50 | Items per page (max 100) |

#### Response (`SearchHistoryResponse`)
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "word": "hello",
        "translation": "નમસ્તે",
        "part_of_speech": "interjection",
        "lookup_count": 5,
        "last_looked_up": "2024-01-26T..."
      }
    ],
    "total": 42,
    "page": 1,
    "per_page": 50
  }
}
```

---

### 4. Delete History Item
Remove a word from search history.

- **URL**: `/history/{history_id}`
- **Method**: `DELETE`
- **Auth Required**: Yes

#### Path Parameters
| Param | Type | Description |
|---|---|---|
| `history_id` | UUID | History item ID |

#### Response
```json
{
  "success": true,
  "data": { "deleted": true },
  "message": "History item removed"
}
```

---

### 5. Get Popular Words
Get most frequently looked up words.

- **URL**: `/popular`
- **Method**: `GET`
- **Auth Required**: No

#### Query Parameters
| Param | Type | Default | Description |
|---|---|---|---|
| `limit` | int | 10 | Number of words (max 50) |

#### Response
```json
{
  "success": true,
  "data": [
    { "id": "...", "word": "hello", "translation": "નમસ્તે", ... },
    { "id": "...", "word": "thank you", "translation": "આભાર", ... }
  ]
}
```

---

## Translation Direction

| Direction | Source | Target |
|---|---|---|
| `en_to_gu` | English | Gujarati |
| `gu_to_en` | Gujarati | English |

## Parts of Speech

Supported values:
- `noun`
- `verb`
- `adjective`
- `adverb`
- `pronoun`
- `preposition`
- `conjunction`
- `interjection`

## Caching Strategy

1. Words are cached in the database after first LLM translation
2. Subsequent lookups hit the cache for instant response
3. Lookup counts are tracked for popularity metrics
4. Cache entries persist indefinitely (no TTL)
