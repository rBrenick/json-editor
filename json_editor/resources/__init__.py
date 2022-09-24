import os

CURRENT_DIR = os.path.dirname(__file__)


def get_image_path(image_name, extension=".png"):
    image_path = "{}/{}{}".format(CURRENT_DIR, image_name, extension)
    return image_path




