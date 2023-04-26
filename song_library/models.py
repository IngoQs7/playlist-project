from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Song:
    _id: str
    title: str
    band: str
    album: str
    year: int = None
    last_played: datetime = None
    rating: int = 0
    tags: list[str] = field(default_factory=list)
    description: str = None
    video_link: str = None
    date_added: datetime = None


@dataclass
class User:
    _id: str
    email: str
    password: str
    songs: list[str] = field(default_factory=list)
