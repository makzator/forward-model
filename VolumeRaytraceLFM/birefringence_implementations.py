
import torch
import torch.nn as nn
import torch.nn.functional as f

# Waveblocks imports
from waveblocks.blocks.optic_block import OpticBlock
from waveblocks.blocks.optic_config import *

from VolumeRaytraceLFM.abstract_classes import *
from jones_torch import *

############ Implementations

class BirefringentRaytraceLFM(RayTraceLFM):
    """This class extends RayTraceLFM, and implements the forward function, where voxels contribute to ray's Jones-matrices with a retardance and axis in a non-commutative matter"""
    def __init__(
        self, optic_config : OpticConfig, members_to_learn : list =[]
    ):
        # optic_config contains mla_config and volume_config
        super(BirefringentRaytraceLFM, self).__init__(
            optic_config=optic_config, members_to_learn=members_to_learn, simul_type=SimulType.BIREFRINGENT
        )
        # Create tensors to store the Jones-matrices per ray

        # We either define a volume here or use one provided by the user

    def ray_trace_through_volume(self, volume_in : VolumeLFM = None):
        """ This function forward projects a whole volume, by iterating through the volume in front of each micro-lens in the system.
            By computing an offset (current_offset) that shifts the volume indices reached by each ray.
            Then we accumulate the images generated by each micro-lens, and concatenate in a final image"""

        # volume_shape defines the size of the workspace
        # the number of micro lenses defines the valid volume inside the workspace
        volume_shape = volume_in.voxel_parameters.shape[2:]
        n_micro_lenses = self.optic_config.mla_config.n_micro_lenses
        n_voxels_per_ml = self.optic_config.mla_config.n_voxels_per_ml
        n_ml_half = floor(n_micro_lenses / 2.0)

        # Check if the volume_size can fit these micro_lenses.
        # considering that some rays go beyond the volume in front of the micro-lens
        voxel_span_per_ml = self.voxel_span_per_ml * n_micro_lenses
        assert voxel_span_per_ml < volume_shape[0], f"No full micro-lenses fit inside this volume. \
            Decrease the number of micro-lenses defining the active volume area, or increase workspace \
            ({voxel_span_per_ml} > {self.optic_config.volume_config.volume_shape[1]})"
        

        # Traverse volume for every ray, and generate retardance and azimuth images
        full_img_r = None
        full_img_a = None
        # Iterate micro-lenses in y direction
        for ml_ii in range(-n_ml_half, n_ml_half+1):
            full_img_row_r = None
            full_img_row_a = None
            # Iterate micro-lenses in x direction
            for ml_jj in range(-n_ml_half, n_ml_half+1):
                current_offset = [n_voxels_per_ml * ml_ii, n_voxels_per_ml*ml_jj]
                # Compute images for current microlens, by passing an offset to this function depending on the micro lens and the super resolution
                ret_image_torch, azim_image_torch = self.ret_and_azim_images(volume_in, micro_lens_offset=current_offset)
                # If this is the first image, create
                if full_img_row_r is None:
                    full_img_row_r = ret_image_torch
                    full_img_row_a = azim_image_torch
                else: # Concatenate to existing image otherwise
                    full_img_row_r = torch.cat((full_img_row_r, ret_image_torch), 0)
                    full_img_row_a = torch.cat((full_img_row_a, azim_image_torch), 0)
            if full_img_r is None:
                full_img_r = full_img_row_r
                full_img_a = full_img_row_a
            else:
                full_img_r = torch.cat((full_img_r, full_img_row_r), 1)
                full_img_a = torch.cat((full_img_a, full_img_row_a), 1)
        return full_img_r, full_img_a
    
    def calc_cummulative_JM_of_ray(self, voxel_parameters, micro_lens_offset=[0,0]):
        '''This function computes the Jones Matrices of all rays defined in this object.
            It uses pytorch's batch dimension to store each ray, and process them in parallel'''

        # Fetch the voxels traversed per ray and the lengths that each ray travels through every voxel
        voxels_of_segs, ell_in_voxels = self.ray_vol_colli_indexes, self.ray_vol_colli_lengths
        # Fetch the ray's directions
        rays = self.ray_valid_direction
        # Calculate the ray's direction with the two normalized perpendicular directions
        # Returns a list size 3, where each element is a torch tensor shaped [n_rays, 3]
        rayDir = calc_rayDir(rays)
        # Init an array to store the Jones matrices.
        JM_list = []

        # Iterate the interactions of all rays with the m-th voxel
        # Some rays interact with less voxels, so we mask the rays valid
        # for this step with rays_with_voxels
        for m in range(self.ray_vol_colli_lengths.shape[1]):
            # Check which rays still have voxels to traverse
            rays_with_voxels = [len(vx)>m for vx in voxels_of_segs]
            # How many rays at this step
            n_rays_with_voxels = sum(rays_with_voxels)
            # The lengths these rays traveled through the current voxels
            ell = ell_in_voxels[rays_with_voxels,m]
            # The voxel coordinates each ray collides with
            vox = [vx[m] for ix,vx in enumerate(voxels_of_segs) if rays_with_voxels[ix]]

            # Extract the information from the volume
            my_params = voxel_parameters[:, [v[0] for v in vox], [v[1]+micro_lens_offset[0] for v in vox], [v[2]+micro_lens_offset[1] for v in vox]]

            # Initiallize identity Jones Matrices, shape [n_rays_with_voxels, 2, 2]
            JM = torch.tensor([[1.0,0],[0,1.0]], dtype=torch.complex64, device=self.get_device()).unsqueeze(0).repeat(n_rays_with_voxels,1,1)

            if not torch.all(my_params==0):
                # Retardance
                Delta_n = my_params[0]
                # And axis
                opticAxis = my_params[1:].permute(1,0)

                # Grab the subset of precomputed ray directions that have voxels in this step
                filtered_rayDir = [rayDir[0][rays_with_voxels,:], rayDir[1][rays_with_voxels,:], rayDir[2][rays_with_voxels,:]]

                # Only compute if there's an Delta_n
                # Create a mask of the valid voxels
                valid_voxel = Delta_n!=0
                if valid_voxel.sum() > 0:
                    # make sure that everything is in the right computing device
                    # assert 
                    # Compute the interaction from the rays with their corresponding voxels
                    JM[valid_voxel, :, :] = voxRayJM(Delta_n = Delta_n[valid_voxel], 
                                                    opticAxis = opticAxis[valid_voxel, :], 
                                                    rayDir = [filtered_rayDir[0][valid_voxel], filtered_rayDir[1][valid_voxel], filtered_rayDir[2][valid_voxel]], 
                                                    ell = ell[valid_voxel])
            else:
                pass
            # Store current interaction step
            JM_list.append(JM)
        # JM_list contains m steps of rays interacting with voxels
        # Each JM_list[m] is shaped [n_rays, 2, 2]
        # We pass voxels_of_segs to compute which rays have a voxel in each step
        effective_JM = rayJM(JM_list, voxels_of_segs)
        return effective_JM

    def ret_and_azim_images(self, volume_in : VolumeLFM, micro_lens_offset=[0,0]):
        '''This function computes the retardance and azimuth images of the precomputed rays going through a volume'''
        # Include offset to move to the center of the volume, as the ray collisions are computed only for a single micro-lens
        n_micro_lenses = self.optic_config.mla_config.n_micro_lenses
        n_voxels_per_ml = self.optic_config.mla_config.n_voxels_per_ml
        n_ml_half = floor(n_micro_lenses / 2.0)
        micro_lens_offset = np.array(micro_lens_offset) + np.array(self.vox_ctr_idx[1:]) - n_ml_half
        # Fetch needed variables
        pixels_per_ml = self.optic_config.mla_config.n_pixels_per_mla
        # Create output images
        ret_image = torch.zeros((pixels_per_ml, pixels_per_ml), requires_grad=True)
        azim_image = torch.zeros((pixels_per_ml, pixels_per_ml), requires_grad=True)
        
        # Calculate Jones Matrices for all rays
        effective_JM = self.calc_cummulative_JM_of_ray(volume_in.voxel_parameters, micro_lens_offset)
        # Calculate retardance and azimuth
        retardance = calc_retardance(effective_JM)
        azimuth = calc_azimuth(effective_JM)
        ret_image.requires_grad = False
        azim_image.requires_grad = False
        # Assign the computed ray values to the image pixels
        for ray_ix, (i,j) in enumerate(self.ray_valid_indexes):
            ret_image[i, j] = retardance[ray_ix]
            azim_image[i, j] = azimuth[ray_ix]
        return ret_image, azim_image


########### Generate different birefringent volumes 
    def init_volume(self, volume_ref : VolumeLFM = None, init_mode='zeros'):
        # IF the user doesn't provide a volume, let's create one and return it
        if volume_ref is None:
            volume_ref = VolumeLFM(self.optic_config, [], self.simul_type)
        
        if init_mode=='zeros':
            volume_ref.voxel_parameters = torch.zeros([4,] + volume_ref.config.volume_shape)
        elif init_mode=='random':
            volume_ref.voxel_parameters = self.generate_random_volume(volume_ref.config.volume_shape)
        elif 'planes' in init_mode:
            n_planes = int(init_mode[0])
            volume_ref.voxel_parameters = self.generate_planes_volume(volume_ref.config.volume_shape, n_planes) # Perpendicular optic axes each with constant birefringence and orientation 
        elif init_mode=='ellipsoid':
            volume_ref.voxel_parameters = self.generate_ellipsoid_volume(volume_ref.config.volume_shape, radius=[5,7.5,7.5], delta_n=0.1)
        
        # Enable gradients for auto-differentiation 
        volume_ref.voxel_parameters = volume_ref.voxel_parameters.to(self.get_device())
        volume_ref.voxel_parameters = volume_ref.voxel_parameters.detach()
        volume_ref.voxel_parameters.requires_grad = True
        return volume_ref

    
    @staticmethod
    def generate_random_volume(volume_shape):
        Delta_n = torch.FloatTensor(*volume_shape).uniform_(0, .01)
        # Random axis
        a_0 = torch.FloatTensor(*volume_shape).uniform_(-5, 5)
        a_1 = torch.FloatTensor(*volume_shape).uniform_(-5, 5)
        a_2 = torch.FloatTensor(*volume_shape).uniform_(-5, 5)
        norm_A = (a_0**2+a_1**2+a_2**2).sqrt()
        return torch.cat((Delta_n.unsqueeze(0), (a_0/norm_A).unsqueeze(0), (a_1/norm_A).unsqueeze(0), (a_2/norm_A).unsqueeze(0)),0)
    
    @staticmethod
    def generate_planes_volume(volume_shape, n_planes=1):
        vol = torch.zeros([4,] + volume_shape)
        vol.requires_grad = False
        z_size = volume_shape[0]
        z_ranges = np.linspace(0, z_size-1, n_planes*2).astype(int)

        if n_planes==1:
            z_offset = 4
            # Birefringence
            vol[0, z_size//2+z_offset, :, :] = 0.1
            # Axis
            # vol[1, z_size//2, :, :] = 0.5
            vol[1, z_size//2+z_offset, :, :] = 1
            return vol
        random_data = BirefringentRaytraceLFM.generate_random_volume([n_planes])
        for z_ix in range(0,n_planes):
            vol[:,z_ranges[z_ix*2] : z_ranges[z_ix*2+1]] = random_data[:,z_ix].unsqueeze(1).unsqueeze(1).unsqueeze(1).repeat(1,1,volume_shape[1],volume_shape[2])
        
        vol.requires_grad = True
        return vol
    
    @staticmethod
    def generate_ellipsoid_volume(volume_shape, center=[0.5,0.5,0.5], radius=[10,10,10], alpha=0.1, delta_n=0.1):
        vol = torch.zeros([4,] + volume_shape)
        vol.requires_grad = False
        
        kk,jj,ii = np.meshgrid(np.arange(volume_shape[0]), np.arange(volume_shape[1]), np.arange(volume_shape[2]), indexing='ij')
        # shift to center
        kk = floor(center[0]*volume_shape[0]) - kk.astype(float)
        jj = floor(center[1]*volume_shape[1]) - jj.astype(float)
        ii = floor(center[2]*volume_shape[2]) - ii.astype(float)

        ellipsoid_border = (kk**2) / (radius[0]**2) + (jj**2) / (radius[1]**2) + (ii**2) / (radius[2]**2)
        ellipsoid_border_mask = np.abs(ellipsoid_border-alpha) <= 1
        vol[0,...] = torch.from_numpy(ellipsoid_border_mask.astype(float))
        # Compute normals
        kk_normal = 2 * kk / radius[0]
        jj_normal = 2 * jj / radius[1]
        ii_normal = 2 * ii / radius[2]
        norm_factor = np.sqrt(kk_normal**2 + jj_normal**2 + ii_normal**2)
        # Avoid division by zero
        norm_factor[norm_factor==0] = 1
        vol[1,...] = torch.from_numpy(kk_normal / norm_factor) * vol[0,...]
        vol[2,...] = torch.from_numpy(jj_normal / norm_factor) * vol[0,...]
        vol[3,...] = torch.from_numpy(ii_normal / norm_factor) * vol[0,...]
        vol[0,...] *= delta_n
        vol.requires_grad = True
        # vol = vol.permute(0,2,1,3)
        return vol

