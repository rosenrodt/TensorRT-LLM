#!/usr/bin/env python3
"""Analyze fusion performance from nsys profiling data."""

import re
import subprocess
import sys

batch_sizes = [4096, 1024, 512, 256, 128, 64, 32, 4]

def extract_avg_time(nsys_output: str, kernel_pattern: str) -> float:
    """Extract average time in ns for a kernel matching the pattern."""
    for line in nsys_output.split('\n'):
        if kernel_pattern in line:
            # Format: Time (%)  Total Time (ns)  Instances  Avg (ns)  ...
            # The Avg (ns) is the 4th numeric column
            parts = line.split()
            for i, part in enumerate(parts):
                if part == 'Avg':
                    # Next part after header would be the value
                    break
            # Find numeric values - avg is at index 3 of numeric columns
            nums = re.findall(r'[\d.]+', line)
            if len(nums) >= 4:
                return float(nums[3])
    return 0.0

def get_kernel_times(nsys_rep_file: str) -> dict:
    """Run nsys stats and extract kernel times."""
    try:
        result = subprocess.run(
            ['nsys', 'stats', '--force-export=true', nsys_rep_file],
            capture_output=True, text=True, timeout=60
        )
        output = result.stdout + result.stderr
    except Exception as e:
        print(f"Error running nsys stats on {nsys_rep_file}: {e}")
        return {}
    
    times = {}
    times['doActivation'] = extract_avg_time(output, 'doActivationKernel')
    times['apply_per_channel'] = extract_avg_time(output, 'apply_per_channel_scale')
    return times

def main():
    print("=" * 80)
    print("Fusion Performance Analysis")
    print("=" * 80)
    print()
    print(f"{'Batch':<8} {'No-Fuse (ns)':<30} {'Fuse (ns)':<15} {'Savings (ns)':<15} {'Speedup':<10}")
    print("-" * 80)
    
    total_no_fuse = 0
    total_fuse = 0
    
    for bs in batch_sizes:
        no_fuse_file = f"bs{bs}-no-fuse.nsys-rep"
        fuse_file = f"bs{bs}-fuse.nsys-rep"
        
        no_fuse_times = get_kernel_times(no_fuse_file)
        fuse_times = get_kernel_times(fuse_file)
        
        if not no_fuse_times or not fuse_times:
            print(f"BS {bs}: Missing data")
            continue
        
        no_fuse_total = no_fuse_times['doActivation'] + no_fuse_times['apply_per_channel']
        fuse_total = fuse_times['doActivation']
        
        savings = no_fuse_total - fuse_total
        speedup = (savings / no_fuse_total) * 100 if no_fuse_total > 0 else 0
        
        total_no_fuse += no_fuse_total
        total_fuse += fuse_total
        
        no_fuse_str = f"{no_fuse_times['doActivation']:.1f} + {no_fuse_times['apply_per_channel']:.1f} = {no_fuse_total:.1f}"
        
        print(f"{bs:<8} {no_fuse_str:<30} {fuse_total:<15.1f} {savings:<15.1f} {speedup:.1f}%")
    
    print("-" * 80)
    total_savings = total_no_fuse - total_fuse
    total_speedup = (total_savings / total_no_fuse) * 100 if total_no_fuse > 0 else 0
    print(f"{'TOTAL':<8} {total_no_fuse:<30.1f} {total_fuse:<15.1f} {total_savings:<15.1f} {total_speedup:.1f}%")
    print()

if __name__ == "__main__":
    main()

