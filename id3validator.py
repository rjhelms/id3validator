"""Audio file metadata validator for Trent Radio's Libretime implementation."""


from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple

import mutagen
import wx
import ObjectListView
from mutagen.easyid3 import EasyID3


class ValidationMessages(Enum):
    """Enumerator to hold validation messages."""

    NO_METADATA = "No metadata found"
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
    24,
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
            try:
                self.metadata = EasyID3(file_obj)
            except mutagen.id3._util.ID3NoHeaderError:
                self.__errors.append(ValidationMessages.NO_METADATA.value)
                self.__valid = False
                self.__validated = True

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
                if category_index != 0:
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

    def summary(self) -> str:
        """
        Returns a string representation of the validation results, for logging or UI display.
        """
        summary = ""
        summary += f"{self.filename}: "
        if self.valid:
            summary += "Valid\n"
        else:
            summary += "Invalid\n"

        if self.errors:
            summary += "Errors:\n"
            for error in self.errors:
                summary += f"    - {error}\n"

        if self.warnings:
            summary += "Warnings:\n"
            for warning in self.warnings:
                summary += f"    - {warning}\n"

        return summary

    @property
    def title(self) -> str:
        """String representation of the title tag, if present. Read-only"""
        if "title" in self.metadata:
            return self.metadata["title"][0]
        return ""

    @property
    def artist(self) -> str:
        """String representation of the artist tag, if present. Read-only"""
        if "artist" in self.metadata:
            return self.metadata["artist"][0]
        return ""

    @property
    def album(self) -> str:
        """String representation of the album tag, if present. Read-only"""
        if "album" in self.metadata:
            return self.metadata["album"][0]
        return ""

    @property
    def date(self) -> str:
        """String representation of the date tag, if present. Read-only"""
        if "date" in self.metadata:
            return self.metadata["date"][0]
        return ""

    @property
    def error_count(self) -> int:
        """Returns count of validation errors. If validation has not yet been performed, runs
        validate() before returning. Read-only."""
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        """
        Returns count of validation warnings. If validation has not yet been performed, runs
        validate() before returning. Read-only.
        """
        return len(self.warnings)

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


class MainWindow(wx.Frame):
    """Main window for application."""

    def __init__(self, parent, title):
        self.track_list = []
        wx.Frame.__init__(self, parent, title=title, size=(640, 480))
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.list = ObjectListView.ObjectListView(self, style=wx.LC_REPORT)
        self.list.SetColumns(
            [
                ObjectListView.ColumnDefn(
                    "Valid", "left", 24, "valid", checkStateGetter="valid"
                ),
                ObjectListView.ColumnDefn("E", "left", 24, "error_count"),
                ObjectListView.ColumnDefn("W", "left", 24, "warning_count"),
                ObjectListView.ColumnDefn("Title", "left", -1, "title"),
                ObjectListView.ColumnDefn("Artist", "left", -1, "artist"),
                ObjectListView.ColumnDefn("Album", "left", -1, "album"),
                ObjectListView.ColumnDefn("Date", "left", -1, "date"),
                ObjectListView.ColumnDefn("Filename", "left", -1, "filename"),
            ]
        )
        self.list.SetObjects(self.track_list)
        self.text_box = wx.TextCtrl(
            self, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(-1, 150)
        )
        self.text_box.SetMinSize(wx.Size(-1, 150))
        sizer.Add(self.list, 3, wx.EXPAND, 0)
        sizer.Add(self.text_box, 1, wx.EXPAND, 0)
        self.SetSizer(sizer)
        file_drop_target = ValidationDropper(self)
        self.SetDropTarget(file_drop_target)
        self.Show()


class ValidationDropper(wx.FileDropTarget):
    """File drop target class for receiving files for metadata validation."""

    def __init__(self, window: MainWindow):
        wx.FileDropTarget.__init__(self)
        self.window = window

    def OnDropFiles(self, x, y, filenames):
        """Receives dropped files, and runs validation on them."""
        self.window.text_box.SetValue("")
        for i in filenames:
            track = Track(i)
            self.window.text_box.write(track.summary())
            self.window.text_box.write("\n")
            self.window.list.AddObject(track)
        return True


if __name__ == "__main__":
    app = wx.App()
    frame = MainWindow(None, "id3validator")
    app.MainLoop()
