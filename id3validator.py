"""Audio file metadata validator for Trent Radio's Libretime implementation."""


from enum import Enum
from typing import List, Tuple
from dataclasses import dataclass

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
    CATEGORY_WRONG_POSITION = "Category in wrong position"


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

ALL_GENRE_ITEMS = ("cancon", "local")


@dataclass
class TrackType:
    """Class to hold data for a track type, including validation rules

    Attributes
    ----------
    name:
        Name of the track type
    valid_categories: optional
        Valid CRTC content categories for the track type, defaults to all valid CRTC categories.
    valid_genre_items: optional
        Other entries that are valid to appear in the "genre" tag. Defaulst to ALL_GENRE_ITEMS
    artist_mandatory: optional
        Whether the artist field is mandatory for this track type, defaults to False
    album_mandatory: optional
        Whether the album field is mandatory for this track type, defaults to False
    """

    name: str
    valid_categories: Tuple[int] = ALL_CATEGORIES
    valid_genre_items: Tuple[str] = ALL_GENRE_ITEMS
    artist_mandatory: bool = False
    album_mandatory: bool = False


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

    def __validate_genre(self) -> bool:
        genre_valid = True
        if "genre" in self.metadata:
            genres = []
            for i in self.metadata["genre"]:
                j = i.split(", ")
                genres.extend(j)

            # verify cat is present
            contains_category = False
            category_index = None
            category = 0
            for i, item in enumerate(genres):
                if item[0:3] == "cat":
                    contains_category = True
                    category_index = i
                    category = int(item[3:])
                    break

            if not contains_category:
                self.__errors.append(ValidationMessages.MISSING_CATEGORY.value)
                genre_valid = False

            if contains_category:
                # verify cat is in first position
                if category_index is not 0:
                    self.__warnings.append(
                        ValidationMessages.CATEGORY_WRONG_POSITION.value
                    )

                # verify cat is valid
                if category not in self.type.valid_categories:
                    self.__errors.append(ValidationMessages.INVALID_CATEGORY.value)

            # verify other genre items are acceptable
            for i, item in enumerate(genres):
                if i is not category_index:
                    if item not in self.type.valid_genre_items:
                        self.__errors.append(
                            f"{ValidationMessages.INVALID_GENRE.value}: {item}"
                        )
                        genre_valid = False

        else:
            self.__errors.append(ValidationMessages.MISSING_CATEGORY.value)
            genre_valid = False

        return genre_valid

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
            self.__errors.append(ValidationMessages.MISSING_TITLE.value)
            valid_check = False

        if "album" not in self.metadata:
            if self.type.album_mandatory:
                self.__errors.append(ValidationMessages.MISSING_ALBUM.value)
                valid_check = False
            else:
                self.__warnings.append(ValidationMessages.MISSING_ALBUM.value)

        if "artist" not in self.metadata:
            if self.type.artist_mandatory:
                self.__errors.append(ValidationMessages.MISSING_ARTIST.value)
                valid_check = False
            else:
                self.__warnings.append(ValidationMessages.MISSING_ARTIST.value)

        if "date" not in self.metadata:
            self.__warnings.append(ValidationMessages.MISSING_YEAR.value)

        if not self.__validate_genre():
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

    while True:
        input_file = input("File?")
        input_file = input_file.strip("\"'")

        track = Track(input_file)

        print("Errors: ", track.errors)
        print("Warnings: ", track.warnings)
        print("Valid: ", track.valid)
