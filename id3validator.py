"""Audio file metadata validator for Trent Radio's Libretime implementation."""


from typing import Tuple

from mutagen.easyid3 import EasyID3

ALL_CATEGORIES = (
    11,
    12,
    21,
    22,
    23,
    34,
    31,
    32,
    33,
    34,
    35,
    36,
    41,
    42,
    43,
    44,
    45,
    51,
    52,
    53,
)


class TrackType:
    """Class to hold data for a track type, including validation rules"""

    def __init__(
        self,
        name: str,
        valid_categories: Tuple[int] = ALL_CATEGORIES,
        artist_mandatory: bool = False,
        album_mandatory: bool = False,
    ) -> None:
        """
        Parameters
        ----------
        name:
            Name of the track type
        valid_categories: optional
            Valid CRTC content categories for the track type, defaults to all valid CRTC categories.
        artist_mandatory: optional
            Whether the artist field is mandatory for this track type, defaults to False
        album_mandatory: optional
            Whether the album field is mandatory for this track type, defaults to False
        """
        self.name = name
        self.valid_categories = valid_categories

        self.artist_mandatory = artist_mandatory
        self.album_mandatory = album_mandatory


DEFAULT_TYPE = TrackType("Default")


class Track:
    """An individual audio track to be validated"""

    def __init__(self, filename: str, tracktype: TrackType = DEFAULT_TYPE) -> None:
        """
        Parameters
        ----------
        filename:
            File name of audiotrack
        tracktype:
            TrackType instance to use for validation
        """
        self.filename = filename
        self.type = tracktype

        # TODO: handle file path properly!

        file = open(filename, "rb")
        self.metadata = EasyID3(file)


if __name__ == "__main__":

    input_file = input("File?")
    input_file = input_file.strip('"')

    track = Track(input_file)
    print(track.metadata)
