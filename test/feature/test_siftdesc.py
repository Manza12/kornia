import pytest
from torch.autograd import gradcheck
from torch.testing import assert_allclose

import kornia.testing as utils  # test utils
from kornia.feature.siftdesc import *


@pytest.mark.parametrize("ksize", [5, 13, 25])
def test_get_sift_pooling_kernel(ksize):
    kernel = get_sift_pooling_kernel(ksize)
    assert kernel.shape == (ksize, ksize)


@pytest.mark.parametrize("ps,n_bins,ksize,stride,pad", [(41, 3, 20, 13, 5), (32, 4, 12, 8, 3)])
def test_get_sift_bin_ksize_stride_pad(ps, n_bins, ksize, stride, pad):
    out = get_sift_bin_ksize_stride_pad(ps, n_bins)
    assert out == (ksize, stride, pad)


class TestSIFTDescriptor:
    def test_shape(self, device):
        inp = torch.ones(1, 1, 32, 32, device=device)
        sift = SIFTDescriptor(32).to(device)
        out = sift(inp)
        assert out.shape == (1, 128)

    def test_batch_shape(self, device):
        inp = torch.ones(2, 1, 15, 15, device=device)
        sift = SIFTDescriptor(15).to(device)
        out = sift(inp)
        assert out.shape == (2, 128)

    def test_batch_shape_non_std(self, device):
        inp = torch.ones(3, 1, 19, 19, device=device)
        sift = SIFTDescriptor(19, 5, 3).to(device)
        out = sift(inp)
        assert out.shape == (3, (3 ** 2) * 5)

    def test_print(self, device):
        sift = SIFTDescriptor(41)
        sift.__repr__()

    def test_toy(self, device):
        patch = torch.ones(1, 1, 6, 6, device=device).float()
        patch[0, 0, :, 3:] = 0
        sift = SIFTDescriptor(6, num_ang_bins=4, num_spatial_bins=1, clipval=0.2, rootsift=False).to(device)
        out = sift(patch)
        expected = torch.tensor([[0, 0, 1.0, 0]], device=device)
        assert_allclose(out, expected, atol=1e-3, rtol=1e-3)

    @pytest.mark.xfail(reason='May raise checkIfNumericalAnalyticAreClose.')
    def test_gradcheck(self, device):
        batch_size, channels, height, width = 1, 1, 13, 13
        patches = torch.rand(batch_size, channels, height, width, device=device)
        patches = utils.tensor_to_gradcheck_var(patches)  # to var
        assert gradcheck(sift_describe, (patches, 13), raise_exception=True, nondet_tol=1e-4)

    @pytest.mark.jit
    @pytest.mark.skip("Compiled functions can't take variable number")
    def test_jit(self, device, dtype):
        B, C, H, W = 2, 1, 41, 41
        patches = torch.ones(B, C, H, W, device=device, dtype=dtype)
        model = SIFTDescriptor(41).to(patches.device, patches.dtype).eval()
        model_jit = torch.jit.script(SIFTDescriptor(41).to(patches.device, patches.dtype).eval())
        assert_allclose(model(patches), model_jit(patches))
