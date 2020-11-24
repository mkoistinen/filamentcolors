import argparse

from .process import process


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='FilamentColors.xyz Data Collector'
    )
    parser.add_argument(
        '--verbose', '-v', dest='verbose', action='store_const', const=True,
        default=False, required=False, help='More detailed logging to console.'
    )
    parser.add_argument(
        '--update-swatches', dest='update_swatches', action='store_const',
        const=True, default=False, required=False,
        help='Load color swatches from filamentcolor.xyz.',
    )
    parser.add_argument(
        '--color', '-c', dest='hex_color', action='store', required=False,
        help='Provide a color in hexadecimal (without preceeding #).'
    )
    parser.add_argument(
        '--method', '-m', dest='method', action='store', required=False,
        choices=['hue', 'absolute'], default='hue',
        help='Provide the method that should be used; `hue` only (default), '
             'or `absolute` closest, which includes hue and lightness.'
    )
    parser.add_argument(
        '--exclude', '-x', dest='excluded_colors', nargs='+', action='store',
        required=False,
        help='Provide one or more color IDs to exclude from results when '
             'using the --color/-c option.'
    )
    parser.add_argument(
        '--top_n', '-t', dest='top_num', action='store', default='1',
        required=False,
        help='Display the top N closest filaments in color (default is 1).'
    )

    options = parser.parse_args()
    kwargs = vars(options)

    # Exactly one of these options is required, else we print_help()
    required_options = {
        'update_swatches',
        'hex_color',
    }
    # Count the number of required options that are used (not Falsy).
    if sum([bool(v) for k, v in kwargs.items() if k in required_options]) != 1:
        parser.print_help()
    else:
        process(**vars(options))
