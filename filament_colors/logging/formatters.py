import logging


class ExtraFormatter(logging.Formatter):
    """
    Render extra items in printed logs.

    A formatter that also exposes anything provided to the log event as
    `extra`.
    """

    def __init__(self, *args, **kwargs):
        """
        Instantiate an ExtraFormatter.

        :param args: any
        :param kwargs: any
        """
        super().__init__(*args, **kwargs)
        self._normal_keys = vars(
            logging.LogRecord('', 0, '', 0, '', {}, None)
        ).keys()

    def get_extra(self, record):
        """
        Return a dictionary of "extra" key/value pairs.

        :param record: LogRecord
        :return: dict
        """
        extra = {
            k: v for k, v in vars(record).items()
            if k not in self._normal_keys
        }
        return extra

    def format(self, record):
        """
        Format a string that includes the extra values.

        :param record: LogRecord
        :return: dict
        """
        extra = self.get_extra(record)
        if extra:
            extras = [f'{k}="{str(v)}"' for k, v in extra.items()]
            record.msg = f"{record.msg} [{', '.join(extras)}]"
        return super().format(record)
