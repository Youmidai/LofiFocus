from sqlalchemy import Table, Column, ForeignKey

from app.models.Base import Base


# Track <-> Mood
track_mood = Table(
    "TrackMood",
    Base.metadata,
    Column("track_id", ForeignKey("Track.id", ondelete="CASCADE"), primary_key=True),
    Column("mood_id", ForeignKey("Mood.id", ondelete="CASCADE"), primary_key=True),
)


# Playlist <-> Track
playlist_track = Table(
    "PlaylistTrack",
    Base.metadata,
    Column("playlist_id", ForeignKey("Playlist.id", ondelete="CASCADE"), primary_key=True),
    Column("track_id", ForeignKey("Track.id", ondelete="CASCADE"), primary_key=True),
)


# Listener <-> Track
favourite = Table(
    "Favourite",
    Base.metadata,
    Column("listener_id", ForeignKey("Listener.id", ondelete="CASCADE"), primary_key=True),
    Column("track_id", ForeignKey("Track.id", ondelete="CASCADE"), primary_key=True),
)