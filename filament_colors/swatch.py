import logging

import sqlalchemy as db
from colormath.color_objects import LabColor
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()
logger = logging.getLogger(f'filamentcolors.{__name__}')


class TableBase(object):
    """
    Encapsulate helpful logic for the ORM.
    """

    @classmethod
    def get_count_records(cls, session):
        """
        Query the number of available swatches.

        :param session: sqlalchemy.orm.session.Session
        :return: int
        """
        return session.query(cls).count()

    @classmethod
    def populate_table_with_records(cls, session, records):
        """
        Populate the table with records as rows.

        Insert the given records into the table and return the IDs assigned to
        Each row.

        :param session: sqlalchemy.orm.session.Session
        :param records: list[dict[str, any]]
        :return: list[any]
        """
        for record in records:
            swatch_id = record.get('id')

            # Try to get this swatch from the DB
            swatch = session.query(cls).filter_by(id=swatch_id).first()
            if swatch:
                # Updates the Swatch instance with current values
                for key, value in record.items():
                    setattr(swatch, key, value)
                logger.info(f'swatch ({swatch_id}) updated.')
            else:
                # Object doesn't exist in the DB, let's create it
                swatch = Swatch(**record)
                session.add(swatch)
                logger.info(f'swatch ({swatch_id}) added.')
            # session.commit()
        ids = []
        for record in session.execute(db.select([cls])):
            ids.append(record.id)
        session.commit()
        return ids


class Swatch(TableBase, Base):
    """
    Represent a Swatch instance within the ORM.

    This is a simple DB that holds the ID of a swatch from filamentcolors.xyz
    and its RGB color value (in hexadecimal format).
    """

    __tablename__ = 'swatch'

    id = db.Column(db.Integer, primary_key=True)
    hex_color = db.Column(db.String)
    lab_l = db.Column(db.Float)
    lab_a = db.Column(db.Float)
    lab_b = db.Column(db.Float)

    def get_lab_color(self):
        """
        Return the Lab color instance for this swatch.

        :return: colormath.color_objects.LabColor
        """
        return LabColor(self.lab_l, self.lab_a, self.lab_b)

    def get_absolute_url(self):
        """
        Return the URL for this swatch at filamentcolors.xyz.

        :return: str
        """
        return f'https://filamentcolors.xyz/swatch/{self.id}/'

    def __str__(self):
        """
        Return a string representation for this Swatch instance.

        :return: str
        """
        return f'FilamentColors.xyz swatch ({self.id})'
