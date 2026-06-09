DATABASE_PATH         = "database/attendance.db"
CAMERA_INDEX          = 0

# ── Recognition thresholds ─────────────────────────────────────────────────────
# InsightFace ArcFace uses cosine similarity (higher = more similar, range 0-1)
# MATCH_THRESHOLD: minimum similarity to accept as a match
#   0.35 = strict  (fewer false positives, more "Unknown")
#   0.40 = balanced (recommended default)
#   0.45 = lenient  (more matches, more false positives)
MATCH_THRESHOLD       = 0.40

# CONFIDENCE_MARGIN: the winning match must be this much better than the
# second-best match. Prevents misidentification when two embeddings are close.
# e.g. 0.08 means the best match must beat second-best by at least 8 points.
CONFIDENCE_MARGIN     = 0.08

# ── Registration ───────────────────────────────────────────────────────────────
REGISTER_PHOTO_COUNT  = 7    # 7 diverse captures → robust averaged embedding

# ── Camera ─────────────────────────────────────────────────────────────────────
RECOGNITION_INTERVAL  = 4    # process every Nth frame in the stream

# ── App ────────────────────────────────────────────────────────────────────────
SECRET_KEY            = "attendai-secret-change-in-prod"
