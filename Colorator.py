import Image
import math
import argparse
import colorsys
from collections import deque

def main():
	parser = argparse.ArgumentParser(description="Fuck up an image")
	parser.add_argument('filename', type=str, help="File to fuck")
	parser.add_argument('colorsize', type=int, help="Minimum: ceil(cbrt(width*height)) - color resolution")
	parser.add_argument('--order', type=int, nargs=3, default=[0,1,2], help="Order to check cells in, default 0 1 2")
	parser.add_argument('--hsv', action='store_true', default=False, help="Use HSV instead of RGB")
	parser.add_argument('--sort', action='store_true', default=False, help="Sort a thing. Time consuming, but cool")
	args = parser.parse_args()

	filename = args.filename
	color_size = args.colorsize

	if args.hsv:
		get_adj = get_adj_HSB
		convert_color = colorsys.rgb_to_hsv
		unconvert_color = colorsys.hsv_to_rgb
	else:
		get_adj = get_adj_RGB
		convert_color = lambda a, b, c : (a, b, c)
		unconvert_color = lambda a, b, c : (a, b, c)

	input_image = Image.open(filename).convert()
	width, height = input_image.size

	# Init input pixel list, and modify it to only use appropriate colors
	input_pixels = input_image.load()
	transform_pixels = {}
	for x in range(width):
		for y in range(height):
			a = input_pixels[x, y][0] / 255.0
			b = input_pixels[x, y][1] / 255.0
			c = input_pixels[x, y][2] / 255.0

			a, b, c = convert_color(a, b, c)

			a = a * (color_size - 1)
			b = b * (color_size - 1)
			c = c * (color_size - 1)

			transform_pixels[x, y] = (int(a), int(b), int(c))

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

	# Now do the actual color smoothing
	start_keys = [x for x in sorted(transform_colorspace, key=lambda x: len(transform_colorspace[x])) if len(transform_colorspace[x]) > 1] # MY MAX LINE LENGTH IS INFINITY
	_prev = 0
	queue = deque()
	for start_key in start_keys:
		transform_colorspace[start_key]= deque(sorted(transform_colorspace[start_key], key=lambda x: ((width/2 - x[0]) ** 2 + (height/2 - x[1]) ** 2) ** 0.5))
		if len(transform_colorspace[start_key]) != _prev:
			_prev = len(transform_colorspace[start_key])
			print _prev
		# Declare shit
		end_keys = []
		searched = {} # Use a dict for searched keys because hash maps are fast
		prev = {}
		queue.clear()

		# Init shit
		start_key_size = len(transform_colorspace[start_key])
		queue.append(start_key)
		searched[start_key] = None # We only care if the key exists, not it's value
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
			for adj in get_adj(current_key, searched, args.order, color_size):
				searched[adj] = None
				prev[adj] = current_key
				queue.append(adj)

		# For each end point we found, slide along the path and move the 
		# tail of one point to the head of the next.
		for end_key in end_keys:
			if prev[end_key] is None:
				print "OH FUCK SOMETHIN BAD HAPPENED"

			current_key = end_key
			while prev[current_key] is not None:
				transform_colorspace[current_key].append(transform_colorspace[prev[current_key]].popleft())
				current_key = prev[current_key]


	# Transform back to 256 colors
	print "Converting image..."
	output_image = Image.new(input_image.mode, input_image.size)
	for key, point in transform_colorspace.iteritems():
		a = float(key[0]) / (color_size - 1)
		b = float(key[1]) / (color_size - 1)
		c = float(key[2]) / (color_size - 1)

		a, b, c = unconvert_color(a, b, c)

		a = int(a * 255)
		b = int(b * 255)
		c = int(c * 255)

		for pos in point:
			x, y = pos
			output_image.putpixel((x, y), (a, b, c))

	output_image.save(filename + '_output.bmp')
	output_image.show()


def get_adj_RGB(color, searched, order, color_size):
	cs = color_size - 1
	adj = []
	for channel in order:
		if color[channel] > 0:
			c = color[:channel] + (color[channel]-1,) + color[channel+1:]
			if c not in searched:
				adj.append(c)
		if color[channel] < cs:
			c = color[:channel] + (color[channel]+1,) + color[channel+1:]
			if c not in searched:
				adj.append(c)
	return adj

def get_adj_HSB(color, searched, order, color_size):
	cs = color_size - 1
	adj = []
	for channel in order:
		if channel == 0:
			c = color[:channel] + ((color[channel]+1)%color_size,) + color[channel+1:]	
			if c not in searched:
				adj.append(c)
			c = color[:channel] + ((color[channel]-1)%color_size,) + color[channel+1:]	
			if c not in searched:
				adj.append(c)
		else:
			if color[channel] > 0:
				c = color[:channel] + (color[channel]-1,) + color[channel+1:]	
				if c not in searched:
					adj.append(c)
			if color[channel] < cs:
				c = color[:channel] + (color[channel]+1,) + color[channel+1:]
				if c not in searched:
					adj.append(c)
	return adj

if __name__ == '__main__':
	main()
