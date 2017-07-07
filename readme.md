# ColorShift

A “program that makes each pixel in an image a unique color,” written by
[/u/RedHotChiliRocket][1] on Reddit.

Inspired by [a CodeGolf.SE post for images with all colors][2].

[Post on /r/glitch_art, with discussion][3]

This branch has ported the original code to Python 3 — if you’d *really* like
to use Python 2, there’s a [`python_2`][5] branch that I will **not
maintain.**

# Usage

```
usage: colorshift.py [-h] [--order ORDER ORDER ORDER] [--hsv] [--sort]
                     filename colorsize

Fuck up an image

positional arguments:
  filename              File to fuck
  colorsize             Minimum: ceil(cbrt(width*height)) - color resolution

optional arguments:
  -h, --help            show this help message and exit
  --order ORDER ORDER ORDER
                        Order to check cells in, default 0 1 2
  --hsv                 Use HSV instead of RGB
  --sort                Sort a thing. Time consuming, but cool
```

# Dependencies

ColorShift requires (at least) [Pillow][4] (`pip install Pillow` or whatever).

[1]: https://www.reddit.com/user/RedHotChiliRocket
[2]: https://codegolf.stackexchange.com/questions/22144/images-with-all-colors
[3]: https://www.reddit.com/r/glitch_art/comments/6ltv7m/i_wrote_a_program_that_makes_each_pixel_in_an/
[4]: https://pillow.readthedocs.io/en/latest/index.html
[5]: /9999years/colorshift/tree/master
