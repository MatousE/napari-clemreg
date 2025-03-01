#!/usr/bin/env python3
# coding: utf-8
from scipy.ndimage import gaussian_filter1d
import numpy as np
from skimage import feature, exposure
from napari.layers import Image
from napari.qt.threading import thread_worker
import time
from napari.layers import Labels


def _min_max_scaling(data):
    """

    Parameters
    ----------
    data

    Returns
    -------

    """
    n = data - np.min(data)
    d = np.max(data) - np.min(data)

    return n / d


def _diff_of_gauss(img, sigma_1=2.5, sigma_2=4):
    """ Calculates difference of gaussian of an inputted image
    with two sigma values._

    Parameters
    ----------
    img : napari.layers.Image
        Image to apply difference of gaussian to
    sigma_1 : float
        float Sigma of the first Gaussian filter
    sigma_2 : float
        float Sigma of the second Gaussian filter
    Returns
    -------
    diff_of_gauss : Image
        Difference of gaussian of image
    """
    gauss_img_0_e = gaussian_filter1d(img, sigma_1, axis=0)
    gauss_img_1_e = gaussian_filter1d(gauss_img_0_e, sigma_1, axis=1)
    gauss_img_2_e = gaussian_filter1d(gauss_img_1_e, sigma_1, axis=2)

    gauss_img_0_i = gaussian_filter1d(img, sigma_2, axis=0)
    gauss_img_1_i = gaussian_filter1d(gauss_img_0_i, sigma_2, axis=1)
    gauss_img_2_i = gaussian_filter1d(gauss_img_1_i, sigma_2, axis=2)

    diff_of_gauss = gauss_img_2_e - gauss_img_2_i

    return diff_of_gauss


def _slice_adaptive_thresholding(img, thresh):
    """ Apply adaptive thresholding to the user inputted image stack
    based on the threshold value.

    Parameters
    ----------
    img : napari.layers.Image
        Image to apply adaptive thresholding to.
    thresh : float
        Threshold value to be applied to Image.
    Returns
    -------
    thresh_img : np.array
        Segmented image
    """
    thresh_img = []
    for i in range(img.shape[0]):
        slice = exposure.rescale_intensity(img[i], out_range='uint8')
        slice_thresh = np.sum(slice) / (slice.shape[0] * slice.shape[1]) * thresh
        slice[slice < slice_thresh] = 0
        slice[slice >= slice_thresh] = 1
        thresh_img.append(slice)

    return np.asarray(thresh_img)


# @thread_worker
def log_segmentation(input: Image,
                     sigma: float = 3,
                     threshold: float = 1.2):
    """ Apply log segmentation to user input.

    Parameters
    ----------
    input : napari.layers.Image
        Image to be segmented as napari Image layer
    sigma : float
        Sigma value for 1D gaussian filter to be applied oto image before segmentation
    threshold : float
        Threshold value to apply to image
    Returns
    -------
    Labels : napari.layers.Labels
        Labels of the segmented moving image
    """
    print(f'Segmenting {input.name} with sigma={sigma} and threshold={threshold}...')
    start_time = time.time()

    volume = _min_max_scaling(input.data)
    sigma_2 = sigma * 1.6
    log_iso_volume = _diff_of_gauss(volume, sigma, sigma_2)
    seg_volume = _slice_adaptive_thresholding(log_iso_volume, threshold)

    kwargs = dict(
        name=input.name + '_seg'
    )

    print(f'Finished segmenting after {time.time() - start_time}s!')

    return Labels(seg_volume, **kwargs)
