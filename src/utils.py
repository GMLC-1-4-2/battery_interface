import os
import logging


# def setup_logging(level=logging.DEBUG):
#     root = logging.getLogger()
#     if not root.handlers:
#         handler = logging.StreamHandler()
#         if isapipe(sys.stderr) and '_LAUNCHED_BY_PLATFORM' in os.environ:
#             handler.setFormatter(JsonFormatter())
#         else:
#             fmt = '%(asctime)s %(name)s %(levelname)s: %(message)s'
#             handler.setFormatter(logging.Formatter(fmt))
#
#         root.addHandler(handler)
#     root.setLevel(level)


def format_timestamp(time_stamp):
    """Create a consistent datetime string representation based on
    ISO 8601 format.

    YYYY-MM-DDTHH:MM:SS.mmmmmm for unaware datetime objects.
    YYYY-MM-DDTHH:MM:SS.mmmmmm+HH:MM for aware datetime objects

    :param time_stamp: value to convert
    :type time_stamp: datetime
    :returns: datetime in string format
    :rtype: str
    """

    time_str = time_stamp.strftime("%Y-%m-%dT%H:%M:%S.%f")

    if time_stamp.tzinfo is not None:
        sign = '+'
        td = time_stamp.tzinfo.utcoffset(time_stamp)
        if td.days < 0:
            sign = '-'
            td = -td

        seconds = td.seconds
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        time_str += "{sign}{HH:02}:{MM:02}".format(sign=sign,
                                                   HH=hours,
                                                   MM=minutes)

    return time_str


def month_abbr_to_num(abbr):
    abbr_dict = {
        'Jan': 1,
        'Feb': 2,
        'Mar': 3,
        'Apr': 4,
        'May': 5,
        'Jun': 6,
        'Jul': 7,
        'Aug': 8,
        'Sep': 9,
        'Oct': 10,
        'Nov': 11,
        'Dec': 12
    }
    return abbr_dict[abbr]


def ensure_fdir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)


def ensure_ddir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

