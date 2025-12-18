#!

for bs in 4096 1024 512 256 128 64 32 4; do
    nsys profile -f true -t cuda,nvtx --capture-range-end stop-shutdown -c cudaProfilerApi -o bs${bs}-fuse pytest tests/unittest/_torch/modules/test_fused_moe.py::test_fused_moe_w4afp8[${bs}-MoEWeightLoadingMode.VANILLA-dtype1] -vs
    TRTLLM_DISABLE_FC2_PREQUANT_SCALE=1 nsys profile -f true -t cuda,nvtx --capture-range-end stop-shutdown -c cudaProfilerApi -o bs${bs}-no-fuse pytest tests/unittest/_torch/modules/test_fused_moe.py::test_fused_moe_w4afp8[${bs}-MoEWeightLoadingMode.VANILLA-dtype1] -vs
done

# for bs in 4096 1024 512 256 128 64 32 4; do
#     set -x
#     nsys stats --force-export=true bs${bs}-no-fuse.nsys-rep | grep -P 'doActivation|apply_per_channel|Instances.*Avg.*Range'
#     nsys stats --force-export=true bs${bs}-fuse.nsys-rep | grep -P 'doActivation|apply_per_channel|Instances.*Avg.*Range'
#     set +x
# done

python3 analyze_fusion.py