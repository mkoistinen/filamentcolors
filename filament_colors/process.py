from functools import lru_cache
import logging
from math import sqrt
from pathlib import Path
import sys

from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
import requests
import sqlalchemy as db
from sqlalchemy.orm import sessionmaker

from .logging.formatters import ExtraFormatter
from .swatch import Base, Swatch


BASE_URL = 'https://filamentcolors.xyz/api'
DB_FILE_NAME = Path('filamentcolors.sqlite3')
DB_URL = f'sqlite:///{DB_FILE_NAME}'

logger = logging.getLogger(f'filamentcolors.{__name__}')


def get_swatches_from_api(page=1):
    """
    Fetch swatch data from the filamentcolors.xyz API.

    :param page: int
    :return: None
    """
    url = f'{BASE_URL}/swatch/'
    if page > 1:
        url += f'?page={int(page)}'
    req = requests.get(url)
    if req.status_code == 200:
        return req.json()
    else:
        logger.error('Error on GET')


def populate_db(results, engine, session, force=False):
    """
    Save given swatches (dict form) into the database.

    Given a set of results (dict with keys id, hex_color), construct the Lab
    color, and store all of the above into a local database.

    :param engine: sqlalchemy.orm.engine.Engine
    :param session: sqlalchemy.orm.session.Session
    :param results: dict[str, Any]
    :param force: bool
    :return: None
    """
    meta = Base.metadata

    if force:
        # If `force` is set, drop and rebuild the DB
        meta.drop_all(engine, checkfirst=True)
        meta.create_all(engine, checkfirst=True)
        session.commit()

    records = list()
    for swatch in results:
        id = swatch.get('id', None)
        hex_color = swatch.get('hex_color', '')
        lab_color = construct_lab_color_from_hex(hex_color)
        lab_l, lab_a, lab_b = lab_color.get_value_tuple()
        records.append({
            'id': id,
            'hex_color': hex_color,
            'lab_l': lab_l,
            'lab_a': lab_a,
            'lab_b': lab_b,
        })
    Swatch.populate_table_with_records(session=session, records=records)


@lru_cache()
def construct_lab_color_from_hex(color):
    """
    Compute a LabColor from a given RGB color in hexadecimal format.

    :param color: str
    :return: colormath.color_objects.LabColor
    """
    components = [int(color[i * 2:][:2], 16) for i in range(3)]
    a = sRGBColor(*components, is_upscaled=True)
    return convert_color(a, LabColor)


def get_swatches_from_db(session):
    """
    Return a list of dicts representing the rows of the DB.

    :param session: sqlalchemy.orm.session.Session
    :return: list[dict[str, any]] or None
    """
    # If the DB doesn't exist, return None
    if not DB_FILE_NAME.is_file():
        return None
    return session.query(Swatch).all()


def compute_lab_color_distance(color_a, color_b, scale=None):
    """
    Compute the Euclidean LabColor distance between input hex RGB colors.

    :param color_a: str or colormath.color_objects.LabColor
    :param color_b: str or colormath.color_objects.LabColor
    :param scale: iterable of float or None
    :return: float
    """
    if not isinstance(color_a, LabColor):
        # If not LabColor, assume it is a hex-formatted RGB color
        color_a = construct_lab_color_from_hex(color_a)
    if not isinstance(color_b, LabColor):
        # If not LabColor, assume it is a hex-formatted RGB color
        color_b = construct_lab_color_from_hex(color_b)

    a_parts = color_a.get_value_tuple()
    b_parts = color_b.get_value_tuple()

    if scale is None:
        scale = [1.0, 1.0, 1.0]
    deltas = [(a_parts[i] - b_parts[i]) ** 2 * scale[i] for i in range(3)]
    return sqrt(sum(deltas))


def find_closest_by_lab(swatches, hex_color, top_num=1, excluded=None,
                        scale=None):
    """
    Return the closest color to the given hex_color.

    NOTE: This is probably fine for swatch collection sizes < 1000, but look
    into better ways of getting the top-N items if there are many more. Also
    consider doing the comparison and sorting in the DB!

    :param swatches: list[Swatch]
    :param hex_color: str
    :param scale: list[float]
    :return: list[Swatch] or None
    """
    # The largest possible distance between 2 (Colormath) Lab colors is 300.0
    if excluded is None:
        excluded = []
    if scale is None:
        scale = [1.0, 1.0, 1.0]

    compare_color = construct_lab_color_from_hex(hex_color)
    computed = dict()

    for swatch in swatches:
        # Don't even check excluded colors.
        if swatch.id in excluded:
            continue
        dist = compute_lab_color_distance(compare_color,
                                          swatch.get_lab_color(),
                                          scale=scale)
        computed[swatch] = dist
    ordered = sorted(computed.items(), key=lambda i: i[1])
    return [k for k, v in ordered[:top_num]]


def process(**kwargs):
    """
    Perform the requested command.

    :param kwargs: dict
    :return:
    """
    console_handler = logging.StreamHandler(sys.stdout)
    verbose = kwargs.get('verbose', False)
    if verbose:
        logger.setLevel(logging.DEBUG)
        console_handler.setFormatter(ExtraFormatter())
    logger.addHandler(console_handler)

    engine = db.create_engine(DB_URL, echo=False)
    session = sessionmaker(bind=engine)()

    db_exists = DB_FILE_NAME.is_file()

    # Update swatches mode
    update_swatches = kwargs.get('update_swatches', False)
    if update_swatches:
        page = 1
        while page:
            data = get_swatches_from_api(page=page)
            results = data.get('results', [])
            # Force the creation of the schema if the DB file doesn't exist,
            # but only for the first batch.
            populate_db(results=results, engine=engine, session=session,
                        force=(not db_exists and page == 1))

            # process_results(results)
            if data.get('next', None):
                page += 1
            else:
                page = None
        print(f'There are now {Swatch.get_count_records(session)} swatches '
              f'available.')
        return

    # Color search mode
    swatches = get_swatches_from_db(session)

    if swatches:
        print(f'There are currently {len(swatches)} swatches available.')
    else:
        print('There is no local database yet.')

    if not swatches:
        print('No swatches were found.')

    hex_color = kwargs.get('hex_color', '')
    if hex_color and swatches:
        excluded = []
        try:
            excluded = [int(x) for x in kwargs.get('excluded_colors')]
        except TypeError:
            # The option wasn't used, ignore...
            pass
        except ValueError:
            logger.error('Excluded colors must be parsable as integers.')
            return
        top_num = int(kwargs.get('top_num', 1))
        method = kwargs.get('method', 'hue')
        scale = [0.01, 1.0, 1.0] if method == 'hue' else None
        best_matches = find_closest_by_lab(swatches, hex_color,
                                           top_num=top_num, excluded=excluded,
                                           scale=scale)

        digits = len(str(top_num))
        template = 'ID: {id} ({url}) color: #{hex_color}.'
        if top_num == 1:
            swatch = best_matches[0]
            print(('The visually closest swatch (by {method}) to '
                   '#{input_color} is ' + template).format(
                input_color=hex_color,
                method=method,
                id=swatch.id,
                url=swatch.get_absolute_url(),
                hex_color=swatch.hex_color,
            ))
        else:
            print(f'The top-{top_num} visually closest swatches '
                  f'(by {method}) to #{hex_color} are:')
            for i, swatch in enumerate(best_matches):
                print(f'  {i+1:>{digits}}. ' + template.format(
                    id=swatch.id,
                    url=swatch.get_absolute_url(),
                    hex_color=swatch.hex_color,
                ))
