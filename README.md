# What is this?

The website [filamentcolors.xyz](https://filamentcolors.xyz) is a great 
resource of filament colors. However, the policy of the site's owner is that 
color-matching isn't good enough to allow such a feature on the website itself.
This is reasonable, as "color is hard" to capture absolutely and real-world
comparisons will be different for different people in different lighting
conditions, etc.

However, the site's database of filament swatches and their RGB colors as
measured by the site's author in his lighting conditions using his equipment
is, in this author's opinion, still useful.

**This program attempts to enable this utility, by identifying 
   filamentcolors.xyz swatches that are closest to an input RGB color.**
   
This program uses a device independent color system (Lab) for computing color-
distance. It is clearly not going to produce absolutely accurate results, but
it should still be useful for identifying good filaments for projects based on
their color.

## Usage

### Quick start

```bash
> cd filamentcolors
> python -m filament_colors --update-swatches
There are now 487 swatches available.

> python -m filament_colors --color BADA55
There are currently 487 swatches available.
The visually closest swatch (by hue) to #BADA55 is ID: 36 (https://filamentcolors.xyz/swatch/36/) color: #B6D448.
```

There are two modes of operation:

1. Update Local Database Mode
2. Search Filaments Mode

Exactly one of these options must be used when running this program, otherwise
the program will display a help page, and exit.

### Update Local Database Mode

   Use the `--update-swatches` to update the local database from via the
   filamentcolors.xyz public API. This will locally store swatch ID and color
   for searching later.

   > **NOTE:** There is no shortcut for this option, it must be spelled out 
               since this is a rather expensive operation that produces traffic
               on the remote website.

   This operation has to be used at least once to have data to use with the
   "search filaments" mode.
   
### Filament Swatch Color Search Mode

   Use `--color` or the shortcut `-c` followed by a 6-character hexadecimal
   RGB color to search the local database for the closest filament swatch(es)
   to the given color.
   
   There are additional options when in this mode of operation:
   
   - `--method` or `-m` allows one to choose between two algorithms used during
     filament searches:
     
     - `hue` (default) will reduce the weight of the lightness and prioritize
       the filament hue during the searching.
     - `absolute` will weigh the lightness and the hue the same during the
       searching.

   - `--exclude` or `-x` followed by one or more swatch IDs will exclude these
     swatches from the search. This is useful if one or more swatches have
     undesirable effects (transparency, glow-in-the-dark, glitter, etc.) which
     may render them inappropriate for your needs.

   - `--top_num` or `-t` followed by a positive integer (default 1) declares
     how many filament swatches to return (ordered by closeness to the input
     color).

### Global Options

- `--verbose` or `-v` can be used to display more information about the
  progress of the code. This is typically used for debugging the code.
- `--help` or `-h` will output a description of the program and its options
  then promptly exit.
