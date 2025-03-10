#!/usr/bin/env python3
# coding: utf-8
from napari.layers import Image
import time
import numpy as np
from scipy import ndimage
from napari.layers.utils._link_layers import get_linked_layers

def get_pixelsize(metadata: dict):
    """ Parse pixel sizes from image metadata

    Parameters
    ----------
    metadata : dict
        Metadata of user inputted image
    Returns
    -------
        Pixel size
    """

    try:
        x_pxlsz = 1 / metadata['XResolution']
        y_pxlsz = 1 / metadata['YResolution']
    # If no metadata, set pixelsize to 1: no effect on output image
    except KeyError:
        x_pxlsz = 1
        y_pxlsz = 1
        print('XResolution and YResolution not recorded in metadata')

    try:
        # Parse ImageJ Metadata to get z pixelsize
        ij_metadata = metadata['ImageDescription'].split('\n')
        ij_metadata = [i for i in ij_metadata if i not in '=']
        ij_dict = dict((k, v) for k, v in (i.rsplit('=') for i in ij_metadata))

        z_pxlsz = ij_dict['spacing']
        unit = ij_dict['unit']
    except KeyError:
        z_pxlsz = 1
        unit = 'micron'
        print('ImageJ metdata not recorded in metadata')

    return (eval(x_pxlsz) if isinstance(x_pxlsz, str) else x_pxlsz,
            eval(y_pxlsz) if isinstance(y_pxlsz, str) else y_pxlsz,
            eval(z_pxlsz) if isinstance(z_pxlsz, str) else z_pxlsz,
            unit)

def _zoom_values(xy, z, xy_ref, z_ref):
    xy_zoom = xy / xy_ref
    z_zoom = z / z_ref

    return xy_zoom, z_zoom

def _make_isotropic(image: Image):
    # Inplace operation
    moving_xy_pixelsize, __, moving_z_pixelsize, __ = get_pixelsize(image.metadata)
    z_zoom = moving_z_pixelsize / moving_xy_pixelsize

    image.data = ndimage.zoom(image.data, (z_zoom, 1, 1))
    return z_zoom

def make_isotropic(input_image: Image):
    # Inplace operation
    if len(get_linked_layers(input_image)) > 0:
        images = get_linked_layers(input_image)
        images.add(input_image)
        for image in images:
            z_zoom = _make_isotropic(image)
    else:
        z_zoom = _make_isotropic(input_image)
    return z_zoom
