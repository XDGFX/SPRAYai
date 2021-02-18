#!/usr/bin/env python3

"""
mask_separate.py

Separate masks containing more than one object into different mask files.
Will overwrite images in the directory! Make sure you have a backup

@input
dataset/subdir/annotations/[unique images].[jpg / png]

@output
# New images appended with [annotation id]
dataset/subdir/annotations/[unique images]_[annotation id].[jpg / png]

# Renames original images with .orig
.../[unique images].[jpg / png] >> .../[unique images].[jpg / png].orig

Callum Morrison, 2020
"""

import fnmatch
import os
import re

import numpy as np
from PIL import Image
from scipy.ndimage import label


# VARIABLES
# dataset:      root directory for files
# subdir:       the collection (e.g. 'test', 'train' or 'validate')
# category:     the main category that individual objects belong to
# year:         the year of the dataset
# threshold:    for B&W conversion of masks, pixels must be brighter

dataset = 'dandelions_v2'
subdir = 'validate'
category = 'plants'
year = 2021
threshold = 191
image_dir = os.path.join(dataset, subdir, f"{category}_{subdir}{year}")
annotation_dir = os.path.join(dataset, subdir, "annotations")


def filter_filetype(root, files):
    """
    Search for files within `root` which have a supported image extension
    """
    # Supported file extensions
    file_types = ['*.png', '*.jpeg', '*.jpg']

    # Generate regex to match files with supported extensions
    file_types = r'|'.join([fnmatch.translate(x) for x in file_types])

    # Select all files in root dir
    files = [os.path.join(root, f) for f in files]

    # Filter based on regex
    files = [f for f in files if re.match(file_types, f)]

    return files


def main():
    # Filter images
    for root, _, files in os.walk(annotation_dir):
        image_files = filter_filetype(root, files)

        for annotation_filename in image_files:
            print(annotation_filename)

            # Open image
            image = Image.open(annotation_filename)

            # Rename original image
            os.rename(annotation_filename, annotation_filename + ".orig")

            # Threshold and convert to black and white
            image = image.point(lambda p: p > threshold and 255).convert('1')

            # Convert to np array
            image = np.array(image)

            # Divide into continous regions
            label_image = label(image)[0]

            annotation_id = 1
            annotation_name_split = os.path.splitext(annotation_filename)

            for i in range(1, label_image.max() + 1):
                # Select only active annotation
                current_annotation = (label_image == i)

                # Remove groups with a low number of pixels
                if sum(sum(current_annotation)) < 50:
                    continue

                # Convert back to image
                current_annotation_image = Image.fromarray(
                    np.uint8(current_annotation * 255))

                current_annotation_name = f"{annotation_name_split[0]}_{annotation_id:03}{annotation_name_split[1]}"

                # Save image and increment annotation count
                current_annotation_image.save(current_annotation_name)

                annotation_id += 1


if __name__ == "__main__":
    main()
