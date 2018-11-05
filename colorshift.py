import math
import argparse
from collections import deque
import os
import sys
from datetime import datetime

import colorsys

from PIL import Image

def iso_now():
    """iso-formatted utc time"""
    return datetime.utcnow().strftime('%Y-%m-%dT%H_%M_%S')

_timer = datetime.utcnow()
def start_timer(txt=None):
    global _timer
    if txt:
        print(txt, end='... ')
        sys.stdout.flush()
    _timer = datetime.utcnow()

def end_timer():
    end = datetime.utcnow()
    delta = end - _timer
    print(delta)
    return delta

def argparser():
    parser = argparse.ArgumentParser(description="Fuck up an image")
    parser.add_argument('filename', type=str, help="File to fuck")
    parser.add_argument('colorsize', type=int, nargs='?', default=64,
        help='''Minimum: ceil(cbrt(width*height)) - color resolution. Default:
        64. Note that image processing time grows cubically with proportion to
        this.''')
    parser.add_argument('--order', type=int, nargs=3, default=[0,1,2],
        help="Order to check cells in, default 0 1 2")
    parser.add_argument('--hsv', action='store_true', default=False,
        help="Use HSV instead of RGB")
    parser.add_argument('--sort', action='store_true', default=False,
        help="Sort a thing. Time consuming, but cool")
    return parser

def convert_output_image(input_image, transform_colorspace, color_size=2, unconvert_color=lambda a, b, c: (a, b, c)):
    # Transform back to 256 colors
    output_image = Image.new(input_image.mode, input_image.size)
    for key, point in transform_colorspace.items():
        a, b, c = map(lambda x: int(x * 255),
                unconvert_color(
                    *map(lambda x: float(x) / (color_size - 1),
                        key)))

        for pos in point:
            x, y = pos
            output_image.putpixel((x, y), (a, b, c))

    return output_image

def main():
    args = argparser().parse_args()

    filename = args.filename
    color_size = args.colorsize

    if color_size < 2:
        print('WARNING: A colorsize of 0 or 1 will trigger 0-divide error, and '
            'a negative colorsize makes no sense. Defaulting to 2.')
        color_size = 2
    elif color_size >= 128:
        print('WARNING: large color sizes (>128 or so) will take a very long time to run')

    if args.hsv:
        get_adj = get_adj_HSB
        convert_color = colorsys.rgb_to_hsv
        unconvert_color = colorsys.hsv_to_rgb
    else:
        get_adj = get_adj_RGB
        convert_color   = lambda a, b, c: (a, b, c)
        unconvert_color = lambda a, b, c: (a, b, c)

    input_image = Image.open(filename).convert()
    width, height = input_image.size

    # Init input pixel list, and modify it to only use appropriate colors
    input_pixels = input_image.load()
    start_timer('Converting image')
    transform_pixels = {}
    for x in range(width):
        for y in range(height):
            transform_pixels[x, y] = tuple(map(lambda x: int(x * (color_size - 1)),
                    convert_color(*map(lambda x: x / 255.0,
                        input_pixels[x, y]))))
    end_timer()

    start_timer('Initializing 3d color space')
    # Init 3d 'color' space, where we will do the smoothing
    # each point in this space is a list of (x,y) coordinates
    transform_colorspace = {}
    for a in range(color_size):
        for b in range(color_size):
            for c in range(color_size):
                transform_colorspace[(a, b, c)] = deque()

    for x in range(width):
        for y in range(height):
            c = transform_pixels[x, y]
            transform_colorspace[c].append((x, y))
    end_timer()

    start_timer('Smoothing color')
    # Now do the actual color smoothing
    start_keys = filter(lambda x: len(transform_colorspace[x]) > 1,
            sorted(transform_colorspace,
                   key=lambda x: len(transform_colorspace[x])))

    print()
    _prev = 0
    queue = deque()
    for i, start_key in enumerate(start_keys):
        transform_colorspace[start_key] = (
            deque(sorted(
            transform_colorspace[start_key],
            # √((w/2 - x₀)² + (h/2 - x₁)²)
            # pythagorean sum of... something
            key=lambda x:
                ((width/2 - x[0]) ** 2 + (height/2 - x[1]) ** 2) ** 0.5
        )))

        if len(transform_colorspace[start_key]) != _prev:
            _prev = len(transform_colorspace[start_key])
            print(_prev, end='\r')
            sys.stdout.flush()
        # Declare shit
        end_keys = []
        # Use a dict for searched keys because hash maps are fast
        searched = {}
        prev = {}
        queue.clear()

        # Init shit
        start_key_size = len(transform_colorspace[start_key])
        queue.append(start_key)
        # We only care if the key exists, not it's value
        searched[start_key] = None
        prev[start_key] = None

        # Breadth first search for a viable spot to flatten to
        while queue:
            current_key = queue.popleft()
            # If the size of the point here is zero (ie there are no points
            # that are this color), it's an end point
            if len(transform_colorspace[current_key]) == 0:
                end_keys.append(current_key)
                # We need to find start_key_size - 1 open spots
                if(len(end_keys) >= start_key_size - 1):
                    break

            # Search the nodes that are adjacent to this one
            for adj in get_adj(
                    current_key, searched, args.order, color_size
                ):
                searched[adj] = None
                prev[adj] = current_key
                queue.append(adj)

        # For each end point we found, slide along the path and move the
        # tail of one point to the head of the next.
        for end_key in end_keys:
            if prev[end_key] is None:
                raise ValueError('prev[end_key] is None')

            current_key = end_key
            while prev[current_key] is not None:
                transform_colorspace[current_key].append(
                    transform_colorspace[prev[current_key]].popleft()
                )
                current_key = prev[current_key]

    print()
    end_timer()

    print('Converting image')
    output_image = convert_output_image(input_image, transform_colorspace, color_size, unconvert_color)
    end_timer()
    basename = os.path.splitext(filename)[0]
    outname = basename + '_output_' + iso_now() + '.png'
    print('Saving image as', outname)
    output_image.save(outname)
    print('Opening image')
    output_image.show()

def calc_channel(color, searched, color_size, channel, adj):
    cs = color_size - 1
    if color[channel] > 0:
        c = color[:channel] + (color[channel] - 1,) + color[channel + 1:]
        if c not in searched:
            adj.append(c)
    if color[channel] < cs:
        c = color[:channel] + (color[channel] + 1,) + color[channel + 1:]
        if c not in searched:
            adj.append(c)

def get_adj_RGB(color, searched, order, color_size):
    # color is an rgb 3-tuple
    cs = color_size - 1
    adj = []
    for channel in order:
        # yikes
        calc_channel(color, searched, color_size, channel, adj)
    return adj

def get_adj_HSB(color, searched, order, color_size):
    # color is an hsb 3-tuple
    cs = color_size - 1
    adj = []
    for channel in order:
        if channel == 0:
            # hue loops so we have to *slightly* modify the calc_channel
            # logic
            c = (color[:channel]
                + ((color[channel] + 1) % color_size,)
                + color[channel + 1:])
            if c not in searched:
                adj.append(c)
            c = (color[:channel]
                + ((color[channel] - 1) % color_size,)
                + color[channel + 1:])
            if c not in searched:
                adj.append(c)
        else:
            # same logic as rgb
            calc_channel(color, searched, color_size, channel, adj)
    return adj

if __name__ == '__main__':
    try:
        main()
    except:
        print()
        raise
