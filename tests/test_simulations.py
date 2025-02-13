import pytest
import numpy as np
from VolumeRaytraceLFM.simulations import ForwardModel, BackEnds, BirefringentRaytraceLFM, BirefringentVolume

@pytest.fixture(scope="module")
def backend(request):
    if request.param == 'numpy':
        return BackEnds.NUMPY
    elif request.param == 'pytorch':
        return BackEnds.PYTORCH
    else:
        raise Exception("Invalid backend")

@pytest.fixture
def forward_model(backend):
    optical_system = {
        "optical_info": {
        "volume_shape"      : [3, 5, 5],
        "axial_voxel_size_um"     : 1.0,
        "cube_voxels"       : True,
        "pixels_per_ml"     : 17,
        "n_micro_lenses"    : 1,
        "n_voxels_per_ml"   : 1,
        "M_obj"             : 60,
        "na_obj"            : 1.2,
        "n_medium"          : 1.35,
        "wavelength"        : 0.550,
        "camera_pix_pitch"  : 6.5,
        "polarizer"         : [[1, 0], [0, 1]],
        "analyzer"          : [[1, 0], [0, 1]],
        "polarizer_swing"   : 0.03
        }
    }
    return ForwardModel(optical_system, backend)

@pytest.mark.parametrize("backend", ['numpy', 'pytorch'], indirect=True)
def test_backend(forward_model, backend):
    assert forward_model.backend == backend

@pytest.mark.parametrize("backend", ['numpy', 'pytorch'], indirect=True)
def test_is_pytorch_backend(forward_model, backend):
    assert forward_model.is_pytorch_backend() == (backend == BackEnds.PYTORCH)

@pytest.mark.parametrize("backend", ['numpy', 'pytorch'], indirect=True)
def test_is_numpy_backend(forward_model, backend):
    assert forward_model.is_numpy_backend() == (backend == BackEnds.NUMPY)

@pytest.mark.parametrize("backend", ['numpy', 'pytorch'], indirect=True)
def test_convert_to_numpy(forward_model, backend):
    data = np.array([1, 2, 3])
    np.testing.assert_array_equal(forward_model.convert_to_numpy(data), data)

@pytest.mark.parametrize("backend", ['numpy', 'pytorch'], indirect=True)
def test_is_pytorch_tensor(forward_model, backend):
    data = np.array([1, 2, 3])
    assert not forward_model.is_pytorch_tensor(data)

@pytest.mark.parametrize("backend", ['numpy', 'pytorch'], indirect=True)
def test_setup_raytracer(forward_model, backend):
    rays = forward_model.setup_raytracer()
    assert isinstance(rays, BirefringentRaytraceLFM)

@pytest.mark.parametrize("backend", ['numpy', 'pytorch'], indirect=True)
def test_forward_model(forward_model, backend):
    assert forward_model.backend == backend
    optical_info = {
        "volume_shape"      : [3, 7, 7],
        "axial_voxel_size_um"     : 1.0,
        "cube_voxels"       : True,
        "pixels_per_ml"     : 17,
        "n_micro_lenses"    : 1,
        "n_voxels_per_ml"   : 1,
        "M_obj"             : 60,
        "na_obj"            : 1.2,
        "wavelength"        : 0.550,
        "n_medium"          : 1.35,
        "camera_pix_pitch"  : 6.5,
        }
    volume = BirefringentVolume(
        backend=backend,
        optical_info=optical_info,
        volume_creation_args={    
            'init_mode' : 'single_voxel',
            'init_args' : {
                'delta_n' : -0.05,
                'offset' : [0, 0, 0]
                }
            }
    )
    forward_model.forward_model(volume, backend)
    assert forward_model.ret_img is not None
    assert forward_model.azim_img is not None
