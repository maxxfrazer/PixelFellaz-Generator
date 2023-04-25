from flask import escape
import functions_framework
from PIL import Image, ImageOps
import urllib.request
import io

def sprite_sheet_to_gif(request):
	"""HTTP Cloud Function.
	Args:
		request (flask.Request): The request object.
		<https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
	Returns:
		The response text, or any set of values that can be turned into a
		Response object using `make_response`
		<https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
	"""
	# Get the sprite number and sprite size from the query parameters
	sprite_num = request.path.split("/")[-1]
	if not sprite_num.isdigit() or int(sprite_num) < 1 or int(sprite_num) > 10000:
		return ("Invalid sprite number, should be a number between 1 and 10000", 400)
	sprite_num = str(int(sprite_num))

	# sprite_width, sprite_height = map(int, request.args.get("sprite_size").split("x"))
	sprite_width = 48
	sprite_height = 48
	# Extract the animation type from the query parameters
	animation_type = request.args.get("type", "bounce")
	# Extract the animation type from the query parameters
	frame_delay = request.args.get("delay", 100)

	try:
		frame_delay = int(frame_delay)
	except:
		print("invalid frame delay")
		frame_delay = 100

	# Extract the image size from the query parameters
	image_size = request.args.get("size", "small")

	# Construct the sprite sheet URL based on the sprite number
	sprite_sheet_url = f"http://ipfs.io/ipfs/bafybeidjtuaictzkitnkcq2b5zugktj3dnolj7uqbgdwsx5uaiyrxrwdua/{sprite_num}.png"

	try:
		# Open the sprite sheet image from the URL
		sprite_sheet_data = urllib.request.urlopen(sprite_sheet_url).read()
		sprite_sheet = Image.open(io.BytesIO(sprite_sheet_data))
	except urllib.error.HTTPError:
		# Return a 404 error if the sprite sheet URL is not found
		return ('Invalid Sprite Number', 404)

	# Calculate the number of sprites in the sprite sheet
	num_sprites = sprite_sheet.width // 48 * sprite_sheet.height // 48

	# Scale the sprite sheet if the image size is "large"
	if image_size == "large":
		sprite_sheet = sprite_sheet.resize((sprite_sheet.width * 4, sprite_sheet.height * 4), resample=Image.NEAREST)
		sprite_width *= 4
		sprite_height *= 4

	# Create a list to hold each individual sprite
	sprites = []

	# Split the sprite sheet into individual sprites and add them to the list
	for i in range(num_sprites):
		x = (i % (sprite_sheet.width // sprite_width)) * sprite_width
		y = (i // (sprite_sheet.width // sprite_width)) * sprite_height
		sprite = sprite_sheet.crop((x, y, x + sprite_width, y + sprite_height))
		# Add one extra transparent pixel around the edge of the sprite
		padded_sprite = ImageOps.expand(sprite, border=1, fill=(0, 0, 255, 0))
		sprites.append(padded_sprite)

	# Create a dict that maps each animation type to a slice of the sprites list
	animation_slices = {
		"right": slice(0, 8),
		"up": slice(8, 16),
		"left": slice(16, 24),
		"down": slice(24, 32),
	}

	# Get the slice of the sprites list that corresponds to the animation type
	sprite_slice = animation_slices.get(animation_type, slice(32, 36))

	# Get the sprites that correspond to the animation type
	anim_sprites = sprites[sprite_slice]

	# Save the sprites as a GIF animation to a memory buffer
	buffer = io.BytesIO()
	anim_sprites[0].save(buffer, format="GIF", save_all=True, append_images=anim_sprites[1:], duration=frame_delay, loop=0, transparency=0, disposal=2)

	# Set the response headers
	headers = {
		"Content-type": "image/gif",
		"Content-length": str(len(buffer.getvalue()))
	}

	# Return the GIF as the response
	return (buffer.getvalue(), 200, headers)