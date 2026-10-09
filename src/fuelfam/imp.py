from PIL import Image

IMAGE_NAME = "IMG_9253.jpeg"

def imp() -> None: 
    im = Image.open(IMAGE_NAME)
    exif = im.getexif()
    for k,v in exif.items():
        print(f"{k}: {v}")
