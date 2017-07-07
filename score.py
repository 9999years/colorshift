import Image
import math
import sys

def main():
	filename = sys.argv[1]
	color_size = int(sys.argv[2])

	input_image = Image.open(filename).convert()
	width, height = input_image.size
	c_mult = float(256.0 / float(color_size)) # typecasting is hard

	# Init input pixel list, and modify it to only use appropriate colors
	input_pixels = input_image.load()
	transform_pixels = {}
	for x in range(width):
		for y in range(height):
			a = int(input_pixels[x, y][0] / c_mult)
			b = int(input_pixels[x, y][1] / c_mult)
			c = int(input_pixels[x, y][2] / c_mult)

			transform_pixels[x, y] = (a, b, c)

	# Init 3d 'color' space, where we will do the smoothing
	# each point in this space is a list of (x,y) coordinates
	transform_colorspace = {}
	for a in range(color_size):
		for b in range(color_size):
			for c in range(color_size):
				transform_colorspace[(a, b, c)] = []

	for x in range(width):
		for y in range(height):
			c = transform_pixels[x, y]
			transform_colorspace[c].append((x, y))

	# Now do the actual color smoothing
	print ""
	print "Higher score indicates output will take longer and be more distorted."
	print "For example, a score of ~500,000 could take 2 to 4 hours."
	print "Score:", color_size * len(transform_colorspace[[x for x in sorted(transform_colorspace, key=lambda x: len(transform_colorspace[x])) if len(transform_colorspace[x]) > 1][-1]]) # MY MAX LINE LENGTH IS INFINITY

if __name__ == '__main__':
	main()
