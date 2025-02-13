'''Dictonaries of arguments to be the volume_creation_args when
initalizing a BirefringentVolume.
'''

plane_args = {
    'init_mode' : '1planes',
    'init_args' : {
        }
    }

voxel_args = {
    'init_mode' : 'single_voxel',
    'init_args' : {
        'delta_n' : 0.05,
        'offset' : [0, 0, 0]
        }
    }

ellisoid_init_args = {
    'init_mode' : 'ellipsoid',
    }

planes_init_args = {
    'init_mode' : '1planes',
    }

random_args = {
    'init_mode' : 'random',
    'init_args' : {
        'Delta_n_range' : [0, 0.02],
        'axes_range' : [-1,1]
        }
    }

sphere_args2 = {
    'init_mode' : 'ellipsoid',
    'init_args' : {
    'radius' : [2.5, 2.5, 2.5],
    'center' : [0.5, 0.5, 0.5],
    'delta_n' : 0.01,
    'border_thickness' : 1
        }
    }

sphere_args3 = {
    'init_mode' : 'ellipsoid',
    'init_args' : {
    'radius' : [3.5, 3.5, 3.5],
    'center' : [0.5, 0.5, 0.5],
    'delta_n' : 0.01,
    'border_thickness' : 1
        }
    }

sphere_args4 = {
    'init_mode' : 'ellipsoid',
    'init_args' : {
    'radius' : [4.5, 4.5, 4.5],
    'center' : [0.5, 0.5, 0.5],
    'delta_n' : 0.01,
    'border_thickness' : 1
        }
    }

sphere_args5 = {
    'init_mode' : 'ellipsoid',
    'init_args' : {
    'radius' : [5.5, 5.5, 5.5],
    'center' : [0.5, 0.5, 0.5],
    'delta_n' : 0.01,
    'border_thickness' : 1
        }
    }

sphere_args6 = {
    'init_mode' : 'ellipsoid',
    'init_args' : {
    'radius' : [6.5, 6.5, 6.5],
    'center' : [0.5, 0.5, 0.5],
    'delta_n' : 0.01,
    'border_thickness' : 1
        }
    }


sphere_shifted = {
    'init_mode' : 'ellipsoid',
    'init_args' : {
    'radius' : [6.5, 6.5, 6.5],
    'center' : [0.4, 0.4, 0.4],
    'delta_n' : 0.01,
    'border_thickness' : 1
        }
    }

sphere_shifted45 = {
    'init_mode' : 'ellipsoid',
    'init_args' : {
    'radius' : [6.5, 6.5, 6.5],
    'center' : [0.45, 0.45, 0.45],
    'delta_n' : 0.01,
    'border_thickness' : 1
        }
    }

shell_args = {
    'init_mode' : 'ellipsoid',
    'init_args' : {
    'radius' : [5.5, 9.5, 5.5],
    'center' : [0.5, 0.5, 0.5],
    'delta_n' : -0.01,
    'border_thickness' : 1
        }
    }

shell1_args = {
    'init_mode' : 'ellipsoid',
    'init_args' : {
    'radius' : [10.5, 15.5, 10.5],
    'center' : [0.5, 0.5, 0.5],
    'delta_n' : -0.01,
    'border_thickness' : 1
        }
    }

ellipsoid_large_args = {
    'init_mode' : 'ellipsoid',
    'init_args' : {
    'radius' : [5.5, 9.5, 5.5],
    'center' : [0.5, 0.5, 0.5],
    'delta_n' : -0.01,
    'border_thickness' : 1
        }
    }

ellipsoid_args1 = {
    'init_mode' : 'ellipsoid',
    'init_args' : {
    'radius' : [3.5, 9.5, 5.5],
    'center' : [0.5, 0.5, 0.5],
    'delta_n' : 0.01,
    'border_thickness' : 1
        }
    }

ellipsoid_args2 = {
    'init_mode' : 'ellipsoid',
    'init_args' : {
    'radius' : [3.5, 6.5, 4.5],
    'center' : [0.5, 0.5, 0.5],
    'delta_n' : 0.01,
    'border_thickness' : 1.5
        }
    }
