#!/bin/sh
# properties = {"type": "single", "rule": "run_checkm2_per_sample_all_bins", "local": false, "input": ["/home/projects/cpr_10006/projects/aamb/tests/test_workflow_no_mapping/avamb_outdir/avamb/bins/S21", "/home/projects/cpr_10006/projects/aamb/tests/test_workflow_no_mapping/avamb_outdir/avamb/tmp/checkm2_all"], "output": ["/home/projects/cpr_10006/projects/aamb/tests/test_workflow_no_mapping/avamb_outdir/avamb/tmp/checkm2_all_S21_bins_finished.log"], "wildcards": {"sample": "S21"}, "params": {"walltime": "86400", "nodes": "1", "ppn": "15", "mem": "20gb"}, "log": [], "threads": 15, "resources": {"mem_mb": 1000, "disk_mb": 1000, "tmpdir": "/tmp"}, "jobid": 11, "cluster": {}}
cd '/home/projects/cpr_10006/projects/aamb/avamb/workflow_avamb_nomapping' && /home/projects/cpr_10006/people/paupie/aae_new/anaconda_new/envs/checkm2/bin/python3.9 -m snakemake --snakefile '/home/projects/cpr_10006/projects/aamb/avamb/workflow_avamb_nomapping/avamb.snake.conda.py' '/home/projects/cpr_10006/projects/aamb/tests/test_workflow_no_mapping/avamb_outdir/avamb/tmp/checkm2_all_S21_bins_finished.log' --allowed-rules 'run_checkm2_per_sample_all_bins' --cores 'all' --attempt 1 --force-use-threads  --resources 'mem_mb=1000' 'disk_mb=1000' --wait-for-files '/home/projects/cpr_10006/projects/aamb/avamb/workflow_avamb_nomapping/.snakemake/tmp.k96yy6ky' '/home/projects/cpr_10006/projects/aamb/tests/test_workflow_no_mapping/avamb_outdir/avamb/bins/S21' '/home/projects/cpr_10006/projects/aamb/tests/test_workflow_no_mapping/avamb_outdir/avamb/tmp/checkm2_all' --force --keep-target-files --keep-remote --max-inventory-time 0 --nocolor --notemp --no-hooks --nolock --ignore-incomplete --rerun-triggers 'mtime' 'input' 'code' 'params' 'software-env' --skip-script-cleanup  --conda-frontend 'mamba' --wrapper-prefix 'https://github.com/snakemake/snakemake-wrappers/raw/' --configfiles '/home/projects/cpr_10006/projects/aamb/avamb/workflow_avamb_nomapping/config.json' --latency-wait 60 --scheduler 'ilp' --scheduler-solver-path '/home/projects/cpr_10006/people/paupie/aae_new/anaconda_new/envs/checkm2/bin' --default-resources 'mem_mb=max(2*input.size_mb, 1000)' 'disk_mb=max(2*input.size_mb, 1000)' 'tmpdir=system_tmpdir' --mode 2 && touch '/home/projects/cpr_10006/projects/aamb/avamb/workflow_avamb_nomapping/.snakemake/tmp.k96yy6ky/11.jobfinished' || (touch '/home/projects/cpr_10006/projects/aamb/avamb/workflow_avamb_nomapping/.snakemake/tmp.k96yy6ky/11.jobfailed'; exit 1)

