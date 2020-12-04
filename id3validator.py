"""Audio file metadata validator for Trent Radio's Libretime implementation."""


from enum import Enum
from typing import List, Tuple

from mutagen.easyid3 import EasyID3


class ValidationMessages(Enum):
    """Enumerator to hold validation messages."""

    MISSING_TITLE = "Missing title"
    MISSING_ARTIST = "Missing artist"
    MISSING_ALBUM = "Missing album"
    MISSING_YEAR = "Missing year"
    MISSING_CATEGORY = "Missing category"
    INVALID_CATEGORY = "Invalid category"
    INVALID_GENRE = "Invalid item in genre"


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
        self.__errors = []
        self.__warnings = []
        self.__valid = False
        self.__validated = False

        with open(filename, "rb") as file_obj:
            self.metadata = EasyID3(file_obj)

    def validate(self) -> bool:
        """Validates the metadata for the audio track.

        Any errors and warnings generated validation can be retrieved from their respective
        properties.

        Returns
        -------
        bool
            True if no validation errors were encountered, false otherwise
        """
        valid_check = True

        if "title" not in self.metadata:
            self.__errors.append(ValidationMessages.MISSING_TITLE)
            valid_check = False

        if "album" not in self.metadata:
            if self.type.album_mandatory:
                self.__errors.append(ValidationMessages.MISSING_ALBUM)
                valid_check = False
            else:
                self.__warnings.append(ValidationMessages.MISSING_ALBUM)

        if "artist" not in self.metadata:
            if self.type.artist_mandatory:
                self.__errors.append(ValidationMessages.MISSING_ARTIST)
                valid_check = False
            else:
                self.__warnings.append(ValidationMessages.MISSING_ARTIST)

        if "date" not in self.metadata:
            self.__warnings.append(ValidationMessages.MISSING_YEAR)

        if "genre" in self.metadata:
            # TODO: implement full genre validation
            pass
        else:
            self.__errors.append(ValidationMessages.MISSING_CATEGORY)
            valid_check = False

        self.__valid = valid_check
        self.__validated = True
        return self.__valid

    @property
    def errors(self) -> List[str]:
        """
        Returns the list of validation errors. If validation has not yet been performed, runs
        validate() before returning. Read-only.
        """
        if not self.__validated:
            self.validate()
        return self.__errors

    @property
    def warnings(self) -> List[str]:
        """
        Returns the list of validation warnings. If validation has not yet been performed, runs
        validate() before returning. Read-only.
        """
        if not self.__validated:
            self.validate()
        return self.__warnings

    @property
    def valid(self) -> bool:
        """
        Returns the stored validation result for the audio track. If validation has not yet been
        performed, runs validate() before returning. Read-only.
        """
        if not self.__validated:
            self.validate()
        return self.__valid


if __name__ == "__main__":

    input_file = input("File?")
    input_file = input_file.strip("\"'")

    track = Track(input_file)

    print("Errors: ", track.errors)
    print("Warnings: ", track.warnings)
    print("Valid: ", track.valid)
