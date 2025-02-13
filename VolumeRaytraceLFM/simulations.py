import os
import time
import matplotlib.pyplot as plt
from VolumeRaytraceLFM.abstract_classes import BackEnds
from VolumeRaytraceLFM.birefringence_implementations import BirefringentVolume, BirefringentRaytraceLFM
from VolumeRaytraceLFM.visualization.plotting_ret_azim import plot_retardance_orientation
from VolumeRaytraceLFM.jones_calculus import JonesMatrixGenerators

class ForwardModel:
    def __init__(self, optical_system, backend, device='cpu'):
        self.backend = backend
        # Linking with the optical system
        self.optical_info = optical_system['optical_info']
        self.rays = self.setup_raytracer(device=device)
        self.ret_img = None  # placeholder
        self.azim_img = None  # placeholder
        self.volume_GT = None  # placeholder
        self.savedir = None  # placeholder
        self.forward_img_dir = None  # placeholder
        self.base_dir = ""   # placeholder
        
        # Set up directories
        if False:
            self.create_savedir()

    def to_device(self, device):
        """Move all tensors to the specified device."""
        if self.is_pytorch_backend():
            if self.ret_img is not None:
                self.ret_img = self.ret_img.to(device)
            if self.azim_img is not None:
                self.azim_img = self.azim_img.to(device)
            if self.volume_GT is not None:
                self.volume_GT = self.volume_GT.to(device)
            self.rays.to(device)
        return self

    def is_pytorch_backend(self):
        return self.backend == BackEnds.PYTORCH

    def is_numpy_backend(self):
        return self.backend == BackEnds.NUMPY

    def convert_to_numpy(self, data):
        # Alternative is to use self.is_pytorch_backend()
        # This method avoid importing the torch module
        if self.is_pytorch_tensor(data):
            return data.detach().cpu().numpy()
        return data

    def is_pytorch_tensor(self, obj):
        return "torch.Tensor" in str(type(obj))

    def setup_raytracer(self, device='cpu'):
        """Initialize Birefringent Raytracer."""
        print(f'For raytracing, using computing device {device}')
        rays = BirefringentRaytraceLFM(backend=self.backend, optical_info=self.optical_info)
        if self.is_pytorch_backend():
            rays.to(device)  # Move the rays to the specified device
        start_time = time.time()
        rays.compute_rays_geometry()
        self.ray_geometry_computation_time = time.time() - start_time
        print(f'Raytracing time in seconds: {self.ray_geometry_computation_time:.4f}')
        return rays

    def view_images(self, azimuth_plot_type='hsv'):
        """View the simulated images,
        and pause until the user closes the figure.
        Args:
            azimuth_plot_type (str): 'hsv' or 'lines'
        """
        ret_image = self.convert_to_numpy(self.ret_img)
        azim_image = self.convert_to_numpy(self.azim_img)
        my_fig = plot_retardance_orientation(
            ret_image, azim_image, azimuth_plot_type, include_labels=True
            )
        my_fig.tight_layout()
        plt.pause(0.2)
        plt.show(block=True)
    
    def view_intensity_image(self):
        pass

    def save_images(self, savedir):
        self.create_savedir(savedir)
        ret_image = self.convert_to_numpy(self.ret_img)
        azim_image = self.convert_to_numpy(self.azim_img)
        my_fig = plot_retardance_orientation(ret_image, azim_image, 'hsv', include_labels=True)
        my_fig.savefig(savedir + '/ret_azim.png', bbox_inches='tight', dpi=300)

    def save_intensity_image(self):
        pass

    def add_polscope_components(self):
        # Create non-identity polarizers and analyzers
        # LC-PolScope setup
        self.optical_info['polarizer'] = JonesMatrixGenerators.polscope_analyzer()
        self.optical_info['analyzer'] = JonesMatrixGenerators.universal_compensator_modes(setting=0, swing=0)

    def plot_rays(self):
        self.rays.plot_rays()

    def create_savedir(self):
        """
        Create the directory where the forward images and possibly other results will be saved.
        """
        # Here's a basic structure; customize as needed
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
        self.savedir = os.path.join(self.base_dir, "forward_images")
        if not os.path.exists(self.savedir):
            os.makedirs(self.savedir)

    def forward_model(self, volume: BirefringentVolume, intensity=False):
        """
        Compute the forward model. Uses self.optical_info and other attributes 
        of the optical system.
        """
        
        ret_image, azim_image = self.rays.ray_trace_through_volume(volume)
        self.ret_img = ret_image
        self.azim_img = azim_image

        if intensity and self.is_numpy_backend():
            self.img_list = self.rays.ray_trace_through_volume(volume, intensity=True)
