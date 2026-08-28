# Comparison

Generated directly from JSON result files.

Result differences are calculated as:

- `v032 CPU-GPU` = v032 CPU - v032 GPU
- `v100 CPU-GPU` = v100 CPU - v100 GPU
- `CPU v032-v100` = v032 CPU - v100 CPU
- `GPU v032-v100` = v032 GPU - v100 GPU

Differences are rounded to 7 decimal places (~1e-07), a stand-in for the SCF/GW convergence threshold. Anything smaller is numerical noise and shown as `0`. Energies (`e1b`, `ecorr`, `ehf`) are in Hartree; band/gap quantities (`cbm`, `vbm`, `*_gap*`, `homo`, `lumo`, `ip_koopmans`) are in electronvolts.

Timing ratios are calculated as:

- `CPU v032/v100` = v032 CPU time / v100 CPU time
- `GPU v032/v100` = v032 GPU time / v100 GPU time

For timing ratios, values > 1 mean that v100 is faster than v032.

## aln

### Results differences

| observable | v032 CPU-GPU | v100 CPU-GPU | CPU v032-v100 | GPU v032-v100 |
|---|---:|---:|---:|---:|
| `gw/cbm` | 0 | 0 | 0 | 0 |
| `gw/direct_gap_gamma` | 0 | 0 | 0 | 0 |
| `gw/e1b` | -0.0000333 Ha | 0 | -0.0000333 Ha | 0 |
| `gw/ecorr` | 0.0000005 Ha | 0 | 0.0000005 Ha | 0 |
| `gw/ehf` | 0 | 0 | 0 | 0 |
| `gw/indirect_gap` | 0 | 0 | 0 | 0 |
| `gw/vbm` | 0 | 0 | 0 | 0 |
| `hf/e1b` | — | — | — | -0.0000125 Ha |
| `hf/ecorr` | — | — | — | 0 |
| `hf/ehf` | — | — | — | 0 |

### Timing comparison

| timing | CPU v032/v100 | GPU v032/v100 |
|---|---:|---:|
| `gw/hf` | 1.1923x | — |
| `gw/total` | 1.6774x | 0.8580x |

## c_bn

### Results differences

| observable | v032 CPU-GPU | v100 CPU-GPU | CPU v032-v100 | GPU v032-v100 |
|---|---:|---:|---:|---:|
| `gw/cbm` | 0 | 0 | 0 | 0 |
| `gw/direct_gap_gamma` | 0 | 0 | 0 | 0 |
| `gw/e1b` | 0 | 0 | 0.0000029 Ha | 0.0000029 Ha |
| `gw/ecorr` | 0 | 0 | 0.0000024 Ha | 0.0000024 Ha |
| `gw/ehf` | 0 | 0 | 0 | 0 |
| `gw/indirect_gap` | 0 | 0 | 0 | 0 |
| `gw/vbm` | 0 | 0 | 0 | 0 |
| `hf/e1b` | — | — | — | -0.0000021 Ha |
| `hf/ecorr` | — | — | — | 0 |
| `hf/ehf` | — | — | — | -0.0000010 Ha |

### Timing comparison

| timing | CPU v032/v100 | GPU v032/v100 |
|---|---:|---:|
| `gw/hf` | 0.9406x | — |
| `gw/total` | 2.8653x | 1.7341x |

## diamond

### Results differences

| observable | v032 CPU-GPU | v100 CPU-GPU | CPU v032-v100 | GPU v032-v100 |
|---|---:|---:|---:|---:|
| `gw/cbm` | 0 | 0 | 0 | 0 |
| `gw/direct_gap_gamma` | 0 | 0 | 0 | 0 |
| `gw/e1b` | 0 | 0 | 0 | 0 |
| `gw/ecorr` | 0 | 0 | 0 | 0 |
| `gw/ehf` | 0 | 0 | 0 | 0 |
| `gw/indirect_gap` | 0 | 0 | 0 | 0 |
| `gw/vbm` | 0 | 0 | 0 | 0 |
| `hf/e1b` | — | — | — | -0.0000009 Ha |
| `hf/ecorr` | — | — | — | 0 |
| `hf/ehf` | — | — | — | -0.0000001 Ha |

### Timing comparison

| timing | CPU v032/v100 | GPU v032/v100 |
|---|---:|---:|
| `gw/hf` | 0.7918x | — |
| `gw/total` | 2.8168x | 1.7203x |

## gaas

### Results differences

| observable | v032 CPU-GPU | v100 CPU-GPU | CPU v032-v100 | GPU v032-v100 |
|---|---:|---:|---:|---:|
| `gw/cbm` | -0.3535073 eV | 0.0271929 eV | -0.3535073 eV | 0.0271929 eV |
| `gw/direct_gap_gamma` | -0.0271929 eV | 0.1631572 eV | 0.1631572 eV | 0.3535073 eV |
| `gw/e1b` | 0 | 0 | 0 | 0 |
| `gw/ecorr` | 0 | 0 | 0 | 0 |
| `gw/ehf` | 0 | 0 | 0 | 0 |
| `gw/indirect_gap` | -0.3535073 eV | 0.1631572 eV | -0.1631572 eV | 0.3535073 eV |
| `gw/vbm` | 0 | -0.1359644 eV | -0.1903501 eV | -0.3263145 eV |
| `hf/e1b` | — | — | — | -0.0000016 Ha |
| `hf/ecorr` | — | — | — | 0 |
| `hf/ehf` | — | — | — | -0.0000008 Ha |

### Timing comparison

| timing | CPU v032/v100 | GPU v032/v100 |
|---|---:|---:|
| `gw/hf` | 1.2001x | — |
| `gw/total` | 2.8798x | 1.7281x |

## ge_sfx2c1e

### Results differences

| observable | v032 CPU-GPU | v100 CPU-GPU | CPU v032-v100 | GPU v032-v100 |
|---|---:|---:|---:|---:|
| `gw/cbm` | 0.1087715 eV | -0.2719287 eV | 0.1631572 eV | -0.2175430 eV |
| `gw/direct_gap_gamma` | 0.2447358 eV | -0.0543857 eV | 0.3535073 eV | 0.0543857 eV |
| `gw/e1b` | 0.0004447 Ha | 0.0004447 Ha | 0.0000002 Ha | 0.0000002 Ha |
| `gw/ecorr` | -0.0000026 Ha | -0.0000026 Ha | 0 | 0 |
| `gw/ehf` | 0.0000004 Ha | 0.0000004 Ha | 0 | 0 |
| `gw/indirect_gap` | -0.4078931 eV | -0.4622788 eV | 0.0815786 eV | 0.0271929 eV |
| `gw/vbm` | 0.5166646 eV | 0.1903501 eV | 0.0815786 eV | -0.2447358 eV |
| `hf/e1b` | -1.4962414 Ha | -3.6673794 Ha | 0.0000042 Ha | -2.1711338 Ha |
| `hf/ecorr` | 0 | 0 | 0 | 0 |
| `hf/ehf` | 0.0055467 Ha | 0.0046353 Ha | -0.0000001 Ha | -0.0009115 Ha |

### Timing comparison

| timing | CPU v032/v100 | GPU v032/v100 |
|---|---:|---:|
| `gw/hf` | 2.3669x | — |
| `gw/total` | 3.3616x | 1.7008x |
| `hf/hf` | 3.1582x | — |

## ge_x2c1e

### Results differences

| observable | v032 CPU-GPU | v100 CPU-GPU | CPU v032-v100 | GPU v032-v100 |
|---|---:|---:|---:|---:|
| `gw/cbm` | — | — | — | -0.7614004 eV |
| `gw/direct_gap_gamma` | — | — | — | -1.4684151 eV |
| `gw/e1b` | -2.1896658 Ha | -2.1896616 Ha | -0.0000039 Ha | 0.0000002 Ha |
| `gw/ecorr` | 0.6425008 Ha | 0.6425009 Ha | 0 | 0 |
| `gw/ehf` | -215.2604849 Ha | -215.2604853 Ha | 0.0000003 Ha | 0 |
| `gw/indirect_gap` | — | — | — | -0.6798218 eV |
| `gw/vbm` | — | — | — | -0.0815786 eV |
| `hf/e1b` | 1.4000915 Ha | 1.0882726 Ha | -0.0000211 Ha | -0.3118400 Ha |
| `hf/ecorr` | 0 | 0 | 0 | 0 |
| `hf/ehf` | -214.9513981 Ha | -214.9515056 Ha | 0.0000003 Ha | -0.0001072 Ha |

### Timing comparison

| timing | CPU v032/v100 | GPU v032/v100 |
|---|---:|---:|
| `gw/total` | 4.0406x | 1.3982x |

## lih

### Results differences

| observable | v032 CPU-GPU | v100 CPU-GPU | CPU v032-v100 | GPU v032-v100 |
|---|---:|---:|---:|---:|
| `gw/cbm` | 0 | 0 | 0 | 0 |
| `gw/e1b` | 0 | 0 | 0 | 0 |
| `gw/ecorr` | 0 | 0 | 0 | 0 |
| `gw/ehf` | 0 | 0 | 0 | 0 |
| `gw/indirect_gap` | 0 | 0 | 0 | 0 |
| `gw/vbm` | 0 | 0 | 0 | 0 |
| `hf/e1b` | — | — | — | 0.0000007 Ha |
| `hf/ecorr` | — | — | — | 0 |
| `hf/ehf` | — | — | — | -0.0000002 Ha |

### Timing comparison

| timing | CPU v032/v100 | GPU v032/v100 |
|---|---:|---:|
| `gw/hf` | 0.9525x | — |
| `gw/total` | 2.6770x | 1.9832x |

## mg

### Results differences

| observable | v032 CPU-GPU | v100 CPU-GPU | CPU v032-v100 | GPU v032-v100 |
|---|---:|---:|---:|---:|
| `gw/cbm` | 0.2447358 eV | 0.1359644 eV | -0.1903501 eV | -0.2991216 eV |
| `gw/direct_gap_gamma` | 2.7464800 eV | 0.0543857 eV | -1.0877149 eV | -3.7798091 eV |
| `gw/e1b` | 0 | 0 | 0 | 0 |
| `gw/ecorr` | 0 | 0 | 0 | 0 |
| `gw/ehf` | 0 | 0 | 0 | 0 |
| `gw/indirect_gap` | 0.2175430 eV | 0.2447358 eV | -0.3807002 eV | -0.3535073 eV |
| `gw/vbm` | 0.0271929 eV | -0.1087715 eV | 0.1903501 eV | 0.0543857 eV |
| `hf/e1b` | — | — | — | 0.0000027 Ha |
| `hf/ecorr` | — | — | — | 0 |
| `hf/ehf` | — | — | — | 0 |

### Timing comparison

| timing | CPU v032/v100 | GPU v032/v100 |
|---|---:|---:|
| `gw/hf` | 0.7447x | — |
| `gw/total` | 1.3887x | 0.9915x |

## mgf2

### Results differences

| observable | v032 CPU-GPU | v100 CPU-GPU | CPU v032-v100 | GPU v032-v100 |
|---|---:|---:|---:|---:|
| `gw/cbm` | 0 | 0 | 0 | 0 |
| `gw/direct_gap_gamma` | 0.0271929 eV | 0.0271929 eV | 0 | 0 |
| `gw/e1b` | -0.0233894 Ha | -0.0233894 Ha | 0 | 0 |
| `gw/ecorr` | 0.0010237 Ha | 0.0010237 Ha | 0 | 0 |
| `gw/ehf` | 0.0001542 Ha | 0.0001542 Ha | 0 | 0 |
| `gw/indirect_gap` | 0.0271929 eV | 0.0271929 eV | 0 | 0 |
| `gw/vbm` | -0.0271929 eV | -0.0271929 eV | 0 | 0 |
| `hf/e1b` | — | — | — | -0.0307051 Ha |
| `hf/ecorr` | — | — | — | 0 |
| `hf/ehf` | — | — | — | -0.0000073 Ha |

### Timing comparison

| timing | CPU v032/v100 | GPU v032/v100 |
|---|---:|---:|
| `gw/hf` | 2.4862x | — |
| `gw/total` | 2.2900x | 1.1554x |

## mgh2

### Results differences

| observable | v032 CPU-GPU | v100 CPU-GPU | CPU v032-v100 | GPU v032-v100 |
|---|---:|---:|---:|---:|
| `gw/cbm` | 0 | 0.0271929 eV | -0.0271929 eV | 0 |
| `gw/direct_gap_gamma` | 0 | 0 | 0 | 0 |
| `gw/e1b` | 0 | 0 | -0.0000005 Ha | -0.0000005 Ha |
| `gw/ecorr` | 0 | 0 | 0 | 0 |
| `gw/ehf` | 0 | 0 | 0 | 0 |
| `gw/indirect_gap` | 0.4078931 eV | 0.0271929 eV | -0.0271929 eV | -0.4078931 eV |
| `gw/vbm` | -0.4078931 eV | 0 | 0 | 0.4078931 eV |
| `hf/e1b` | — | — | — | -0.0000002 Ha |
| `hf/ecorr` | — | — | — | 0 |
| `hf/ehf` | — | — | — | 0 |

### Timing comparison

| timing | CPU v032/v100 | GPU v032/v100 |
|---|---:|---:|
| `gw/hf` | 1.3126x | — |
| `gw/total` | 2.0868x | 1.1561x |

## n2

### Results differences

| observable | v032 CPU-GPU | v100 CPU-GPU | CPU v032-v100 | GPU v032-v100 |
|---|---:|---:|---:|---:|
| `gf2/e1b` | — | — | 0 | — |
| `gf2/ecorr` | — | — | 0 | — |
| `gf2/ehf` | — | — | 0 | — |
| `gw/e1b` | 0.0510746 Ha | 0.0510746 Ha | 0 | 0 |
| `gw/ecorr` | -0.0070809 Ha | -0.0070809 Ha | 0 | 0 |
| `gw/ehf` | 0.0037783 Ha | 0.0037783 Ha | 0 | 0 |
| `gw/homo` | 0.6526289 eV | 0.6526289 eV | 0 | 0 |
| `gw/ip_koopmans` | -0.6526289 eV | -0.6526289 eV | 0 | 0 |
| `gw/lumo` | -0.5438574 eV | -0.5438574 eV | 0 | 0 |
| `gw_fullmem/e1b` | — | — | — | 0 |
| `gw_fullmem/ecorr` | — | — | — | 0 |
| `gw_fullmem/ehf` | — | — | — | 0 |
| `hf/e1b` | 0 | 0 | 0 | 0 |
| `hf/ecorr` | 0 | 0 | 0 | 0 |
| `hf/ehf` | 0 | 0 | 0 | 0 |

### Timing comparison

| timing | CPU v032/v100 | GPU v032/v100 |
|---|---:|---:|
| `gf2/hf` | 0.8182x | — |
| `gf2/total` | 1.0005x | — |
| `gw/hf` | 1.1651x | — |
| `gw/total` | 0.9652x | 0.6927x |
| `gw_fullmem/total` | — | 0.6934x |
| `hf/hf` | 0.7811x | — |

## na

### Results differences

| observable | v032 CPU-GPU | v100 CPU-GPU | CPU v032-v100 | GPU v032-v100 |
|---|---:|---:|---:|---:|
| `gw/cbm` | 0 | 0 | 0 | 0 |
| `gw/direct_gap_gamma` | 0.2447358 eV | -0.1359644 eV | -1.2780650 eV | -1.6587652 eV |
| `gw/e1b` | 0 | 0 | 0 | 0 |
| `gw/ecorr` | 0 | 0 | 0 | 0 |
| `gw/ehf` | 0 | 0 | 0 | 0 |
| `gw/indirect_gap` | 0 | 0.0271929 eV | -0.0271929 eV | 0 |
| `gw/vbm` | 0 | -0.0271929 eV | 0.0271929 eV | 0 |
| `hf/e1b` | — | — | — | 0.0000019 Ha |
| `hf/ecorr` | — | — | — | 0 |
| `hf/ehf` | — | — | — | -0.0000001 Ha |

### Timing comparison

| timing | CPU v032/v100 | GPU v032/v100 |
|---|---:|---:|
| `gw/hf` | 0.9724x | — |
| `gw/total` | 3.4206x | 2.4265x |

## si

### Results differences

| observable | v032 CPU-GPU | v100 CPU-GPU | CPU v032-v100 | GPU v032-v100 |
|---|---:|---:|---:|---:|
| `gf2/e1b` | — | — | -0.0000007 Ha | — |
| `gf2/ecorr` | — | — | -0.0000082 Ha | — |
| `gf2/ehf` | — | — | 0 | — |
| `gw/cbm` | -0.1359644 eV | -0.2991216 eV | 0.1087715 eV | -0.0543857 eV |
| `gw/direct_gap_gamma` | 0.0271929 eV | 1.7947295 eV | 0.2719287 eV | 2.0394654 eV |
| `gw/e1b` | 0 | 0 | 0 | 0 |
| `gw/ecorr` | 0 | 0 | 0 | 0 |
| `gw/ehf` | 0 | 0 | 0 | 0 |
| `gw/indirect_gap` | 0.6526289 eV | -0.4622788 eV | 0.3807002 eV | -0.7342075 eV |
| `gw/vbm` | -0.7885933 eV | 0.1631572 eV | -0.2719287 eV | 0.6798218 eV |
| `hf/e1b` | 0 | 0 | -0.0000007 Ha | -0.0000007 Ha |
| `hf/ecorr` | 0 | 0 | 0 | 0 |
| `hf/ehf` | 0 | 0 | 0 | 0 |

### Timing comparison

| timing | CPU v032/v100 | GPU v032/v100 |
|---|---:|---:|
| `gf2/hf` | 2.0506x | — |
| `gf2/total` | 4.2503x | — |
| `gw/hf` | 2.0979x | — |
| `gw/total` | 4.1755x | 2.1848x |
| `hf/hf` | 1.3465x | — |
