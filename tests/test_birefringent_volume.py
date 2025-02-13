'''Tests for BirefringentVolume class'''
import numpy as np
import torch
import pytest
import h5py
from plotly.graph_objs import Figure
from VolumeRaytraceLFM.birefringence_implementations import *

@pytest.fixture(scope="module")
def optical_info():
    # Fetch default optical info
    optical_info = OpticalElement.get_optical_info_template()

    optical_info['volume_shape'] = [11, 11, 11]
    optical_info['axial_voxel_size_um'] = 1.0
    optical_info['pixels_per_ml'] = 5
    optical_info['na_obj'] = 1.2
    optical_info['n_medium'] = 1.52
    optical_info['wavelength'] = 0.550
    optical_info['n_micro_lenses'] = 1
    optical_info['n_voxels_per_ml'] = 1
    optical_info['polarizer'] = np.array([[1, 0], [0, 1]])
    optical_info['analyzer'] = np.array([[1, 0], [0, 1]])

    return optical_info

@pytest.mark.parametrize("backend", [BackEnds.NUMPY, BackEnds.PYTORCH])
def test_init(optical_info, backend):
    bv = BirefringentVolume(backend=backend, optical_info=optical_info)
    assert bv.backend == backend, f"Expected backend to be {backend}, but got {bv.backend}"
    assert bv.optical_info == optical_info, "Unexpected optical_info"

@pytest.mark.parametrize("backend", [BackEnds.NUMPY, BackEnds.PYTORCH])
def test_get_delta_n(optical_info, backend):
    bv = BirefringentVolume(backend=backend, optical_info=optical_info, Delta_n=0.2)
    delta_n = bv.get_delta_n()
    # Convert to numpy if it's a torch tensor
    if backend == BackEnds.PYTORCH:
        delta_n = delta_n.detach().cpu().numpy() if delta_n.requires_grad else delta_n.cpu().numpy()
    assert np.isclose(delta_n.max(), 0.2), f"Expected maximum delta_n to be 0.2, but got {delta_n.max()}"

def generate_random_idx(vol_shape):
    import random
    return [random.randint(0, vol_shape[i] - 1) for i in range(len(vol_shape))]

@pytest.mark.parametrize("backend", [BackEnds.NUMPY, BackEnds.PYTORCH])
def test_get_optic_axis(optical_info, backend):
    bv = BirefringentVolume(backend=backend, optical_info=optical_info, optic_axis=[1.0, 0.0, 0.0])
    optic_axis = bv.get_optic_axis()
    # Convert to numpy if it's a torch tensor
    if backend == BackEnds.PYTORCH:
        optic_axis = optic_axis.detach().cpu().numpy() if optic_axis.requires_grad else optic_axis.cpu().numpy()
    idx = generate_random_idx(optical_info['volume_shape'])
    assert np.array_equal(optic_axis[:, idx[0], idx[1], idx[2]], [1.0, 0.0, 0.0]), f"Expected optic_axis to be [1.0, 0.0, 0.0], but got {optic_axis[:, idx[0], idx[1], idx[2]]}"

@pytest.mark.parametrize("backend", [BackEnds.NUMPY, BackEnds.PYTORCH])
def test_plot_lines_plotly(optical_info, backend):
    bv = BirefringentVolume(backend=backend, optical_info=optical_info, Delta_n=0.2, optic_axis=[1.0, 0.0, 0.0])
    fig = bv.plot_lines_plotly()
    assert isinstance(fig, Figure), f"Expected a plotly Figure, but got {type(fig)}"
    assert len(fig.data) == 2, f"Expected 2 data elements (spheres and lines), but got {len(fig.data)}"

@pytest.mark.parametrize("backend", [BackEnds.NUMPY, BackEnds.PYTORCH])
def test_plot_volume_plotly(optical_info, backend):
    bv = BirefringentVolume(backend=backend, optical_info=optical_info, Delta_n=0.2, optic_axis=[1.0, 0.0, 0.0])
    fig = bv.plot_volume_plotly(optical_info, bv.get_delta_n())
    assert isinstance(fig, Figure), f"Expected a plotly Figure, but got {type(fig)}"

@pytest.mark.parametrize("backend", [BackEnds.NUMPY, BackEnds.PYTORCH])
def test_get_vox_params(optical_info, backend):
    bv = BirefringentVolume(backend=backend, optical_info=optical_info, Delta_n=0.2, optic_axis=[1.0, 0.0, 0.0])
    if backend == BackEnds.NUMPY:
        vox_idx = (1,1,1)
    else:
        vox_idx = 5
    delta_n, optic_axis = bv.get_vox_params(vox_idx)
    if backend == BackEnds.PYTORCH:
        delta_n = delta_n.detach().cpu().numpy() if delta_n.requires_grad else delta_n.cpu().numpy()
        optic_axis = optic_axis.detach().cpu().numpy() if optic_axis.requires_grad else optic_axis.cpu().numpy()
    assert np.isclose(delta_n, 0.2), f"Expected delta_n to be 0.2, but got {delta_n}"
    assert np.array_equal(optic_axis, [1.0, 0.0, 0.0]), f"Expected optic_axis to be [1.0, 0.0, 0.0], but got {optic_axis}"

def create_data(shape, backend):
    if backend == BackEnds.NUMPY:
        return np.random.rand(*shape)
    elif backend == BackEnds.PYTORCH:
        return torch.rand(*shape)
    else:
        raise ValueError(f"Unknown backend: {backend}")

def to_numpy(data):
    if isinstance(data, torch.Tensor):
        return data.cpu().numpy()
    return data

@pytest.mark.parametrize("backend", [BackEnds.NUMPY, BackEnds.PYTORCH])
def test_crop_to_region_shape(backend):
    delta_n = create_data((10, 10, 10), backend)
    optic_axis = create_data((3, 10, 10, 10), backend)
    volume_shape = np.array([10, 10, 10])
    region_shape = np.array([5, 5, 5])

    cropped_delta_n, cropped_optic_axis = BirefringentVolume.crop_to_region_shape(delta_n, optic_axis, volume_shape, region_shape)

    assert to_numpy(cropped_delta_n).shape == tuple(region_shape)
    assert to_numpy(cropped_optic_axis).shape == (3, *region_shape)

@pytest.mark.parametrize("backend", [BackEnds.NUMPY, BackEnds.PYTORCH])
def test_pad_to_region_shape(backend):
    delta_n = create_data((5, 5, 5), backend)
    optic_axis = create_data((3, 5, 5, 5), backend)
    volume_shape = np.array([5, 5, 5])
    region_shape = np.array([10, 10, 10])

    padded_delta_n, padded_optic_axis = BirefringentVolume.pad_to_region_shape(delta_n, optic_axis, volume_shape, region_shape)

    assert to_numpy(padded_delta_n).shape == tuple(region_shape)
    assert to_numpy(padded_optic_axis).shape == (3, *region_shape)

def test_init_from_file(optical_info, tmp_path):  # tmp_path is a pytest fixture providing a temporary directory unique to this test invocation
    # Creating a sample h5 file
    file_path = tmp_path / "sample.h5"
    with h5py.File(file_path, 'w') as f:
        f.create_dataset("data/delta_n", data=np.random.rand(5, 5, 5))
        f.create_dataset("data/optic_axis", data=np.random.rand(3, 5, 5, 5))

    optical_info['volume_shape'] = [10, 10, 10]
    bv = BirefringentVolume.init_from_file(file_path, backend=BackEnds.NUMPY, optical_info=optical_info)

    assert bv.get_delta_n().shape == tuple(optical_info['volume_shape'])
    assert bv.get_optic_axis().shape == (3, *optical_info['volume_shape'])


def main():
    test_get_vox_params(optical_info(), BackEnds.PYTORCH)
    test_get_optic_axis(optical_info(), BackEnds.NUMPY)

if __name__ == '__main__':
    main()