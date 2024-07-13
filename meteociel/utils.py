"""
Manages the functionalities required by other modules.
"""

from datetime import datetime

import bs4
import numpy as np
import requests
from bs4 import BeautifulSoup


def get_seconds(
    date: datetime,
    ref_string: str = "1970-01-01 01:00",
    ref_fmt: str = "%Y-%m-%d %H:%M",
):
    """
    Compute the elapsed seconds since a given reference time (by default epoch).

    Parameters
    ----------
    date : ``datetime``
        Date up to which the number of elapsed seconds is to be calculated.
    ref_string : ``str``, optionnal
        By default: ``"1970-01-01 01:00"`` (epoch). The time to be used as reference for
        calculations.
    ref_fmt : ``str``, optionnal
        By default: ``"%Y-%m-%d %H:%M"``. The format to be used to read ``ref_string``. For more
        information on format codes, please see the ``datetime``
        `documentation <https://docs.python.org/3/library/datetime.html#format-codes>`_

    Returns
    -------
    out : ``int``
        The number of elapsed seconds between the reference and the given time.

    Exemples
    --------
    This exemple computes the number of elapsed seconds between epoch and 2022/08/18 00h GMT::

        >>> from datetime import datetime
        >>> from meteociel import utils
        >>> utils.get_seconds(datetime.strptime("2022-08-18 00", "%Y-%m-%d %H"))
        1660777200

    """
    # Calculate the time of reference
    time_ref = datetime.strptime(ref_string, ref_fmt)
    return int((date - time_ref).total_seconds())


def get_separator(elmnt: str, separators, default_sep: str = " "):
    """Return the separator to use in order to split ``elmnt``."""
    for sep in separators:
        if sep in elmnt:
            return sep
    return default_sep


def conv(
    data: np.array,
    separators: tuple = (),
    multi_value_sep: tuple = (),
    strip_char: tuple = (),
):
    """
    Convert the given array of strings into an array of floats. The input strings should be
    formatted as follow: ``value SEP unit`` where ``SEP`` is a separator character. You can also
    pass two values in one string by separate them with a char from ``multi_value_sep``, The
    returned array will a tuple that contains the arrays.

    .. warning::
        If an element of ``data`` isn't a string, it will result in a ``np.nan`` into the
        converted array.

    Parameters
    ----------
    data : ``np.array``
        The array of strings to convert.
    separators : ``tuple``, optionnal
        By default only spaces are managed. A tuple of strings that allows to split strings beetween
        value and units. Spaces are automatically managed so no need to add them.
    multi_value_sep : ``tuple``, optionnal
        By default, this feature is disabled, to enable it, pass a tuple of characters. A tuple of
        strings that allows to split strings that contain two couples ``(value, unit)``.
    strip_char : ``tuple``, optionnal
        By default, this feature is disabled. A tuple of characters that will be deleted when trying
        to convert a string into a float.

    Returns
    -------
    out : ``list``
        The converted array of floats.

    Exemples
    --------

        >>> import numpy as np
        >>> from meteociel import utils
        >>> utils.conv(np.array(["1 m", "2 m", "3 m"]))
        [1.0, 2.0, 3.0]
        >>> utils.conv(
        ...     np.array(["40° / 5 km/h", "50° / 10 km/h", "45° / 7 km/h"]),
        ...     separators=("°", ),
        ...     multi_value_sep=(" / ", )
        ... )
        (array([40., 50., 45.]), array([ 5., 10.,  7.]))

    """

    def conv_elmnt(elmnt: str):
        """Split ``elmnt`` in a float value and a unit."""
        # If elemnt isn't an str, ignore it
        if not isinstance(elmnt, str) or not elmnt:
            return np.nan

        # Split elmnt if there's two value in it
        if sep := get_separator(elmnt, multi_value_sep, ""):
            elmnt1, elmnt2 = elmnt.split(sep)
            return conv_elmnt(elmnt1), conv_elmnt(elmnt2)

        # Split elmnt into a value and a second part (ignored here)
        sep = get_separator(elmnt, separators)
        elmnt = elmnt.split(sep)[0]

        # Delete character before and after the value
        for stp_char in strip_char:
            elmnt = elmnt.strip(stp_char).rstrip(stp_char)

        # Try converting the value into a float
        try:
            return float(elmnt)
        # If it failed, return np.nan
        except ValueError:
            return np.nan

    converted_data = [conv_elmnt(elmnt) for elmnt in data]
    if any(isinstance(elmnt, tuple) for elmnt in converted_data):
        converted_data = np.array(
            [elmnt if isinstance(elmnt, tuple) else (elmnt, np.nan) for elmnt in converted_data]
        )
        return converted_data[:, 0], converted_data[:, 1]

    return converted_data


def extract_data(html_data: bs4.element.Tag, *, skiprows: int = 0):
    """
    Extract data from html table into a lists of lists.

    Parameters
    ----------
    html_data: bs4.element.Tag
        The html table to be parsed.
    skiprows : ``int``, keyword-only, optionnal
        The number of row to skip at the begenning of the table.

    Returns
    -------
    data : list
        The list of lists that contains the data extracted from the html table.
    """
    data = []

    # For each line of the table
    for rowindex, line in enumerate(html_data.find_all("tr")):
        # Skip the line
        if rowindex < skiprows:
            continue

        # For each value in the line
        for index, value in enumerate(line.find_all("td")):
            # Add a new column if necessary
            if len(data) <= index:
                data.append([])

            # Add the value into the right column
            if text := value.text:
                data[index].append(text)
            elif img := value.find("img"):
                if "alt" in img.attrs:
                    data[index].append(img.attrs["alt"])
                elif "onmouseover" in img.attrs:
                    data[index].append(img.attrs["onmouseover"])
                else:
                    data[index].append("")
            else:
                data[index].append("")

    return data


def get_data_from_html(response: requests.models.Response, conditions: dict = None, **kwargs):
    """
    Search in the given ``response`` for a table that meet the given conditions and return the
    parsed data in a list where each element is a column of the html tabular.

    Parameters
    ----------
    response : ``requests.models.Response``
        The response of the request.
    conditions : ``dict``, optionnal
        The conditions to meet. This dictionnary will be passed to ``BeautifulSoup.find``.
    kwargs
        The keyword-only arguments to be passed to ``extract_data``.

    Returns
    -------
    out : ``list``
        A list that contains all the column of the given html code.

    Raises
    ------
    ConnectionError
        This exception is raised in the case of the connection failed, the HTTP error code is given.
    ValueError
        This exception is raised in the case of unavailable data. The URL is given so the user can
        get the data by hand if needed.
    """
    if not conditions:
        conditions = {}
    # Raise an error in case of fail
    if not response.ok:
        raise ConnectionError(f"connection failed with code: {response.status_code}")

    # Analyse the source code and extract the data from the table
    soup = BeautifulSoup(response.text, features="html5lib")

    if not (html_data := soup.find("table", conditions)):
        raise ValueError(
            f"the data seems to be unavailable, you can check the following URL to see the data: "
            f"'{response.url}'"
        )

    return extract_data(html_data, **kwargs)
