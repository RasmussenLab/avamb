#!/usr/bin/env python

import re
import os
from vamb.vambtools import concatenate_fasta

def get_config(name, default, regex):
    res = config.get(name, default).strip()
    m = re.match(regex, res)
    if m is None:
        raise ValueError(
            f"Config option \"{name}\" is \"{res}\", but must conform to regex \"{regex}\"")
    return res

SNAKEDIR = os.path.dirname(workflow.snakefile)

# set configurations
CONTIGS = get_config("contigs_file_path", "contigs.flt.fna.gz", r".*") 
BAM = get_config("bam_files_path", "bam_sorted/", r".*")

AVAMB_MEM = get_config("avamb_mem", "20gb", r"[1-9]\d*gb$")
AVAMB_PPN = get_config("avamb_ppn", "10", r"[1-9]\d*(:gpus=[1-9]\d*)?$")

CHECKM_MEM = get_config("checkm2_mem", "10gb", r"[1-9]\d*gb$")
CHECKM_PPN = get_config("checkm2_ppn", "10", r"[1-9]\d*$")
CHECKM_MEM_r = get_config("checkm2_mem_r", "30gb", r"[1-9]\d*gb$")
CHECKM_PPN_r = get_config("checkm2_ppn_r", "30", r"[1-9]\d*$")

MIN_COMP=str((int(get_config("min_completeness", "90", r"[1-9]\d*$"))/100))
MAX_CONT= str((int(get_config("min_completeness", "5", r"[1-9]\d*$"))/100))

AVAMB_PARAMS = get_config("avamb_params"," -o C --minfasta 200000 -m 2000 ", r".*")
AVAMB_PRELOAD = get_config("avamb_preload", "", r".*")

OUTDIR= get_config("outdir", "outdir_avamb", r".*")

try:
    os.makedirs(os.path.join(OUTDIR,"log"), exist_ok=True)
except FileExistsError:
    pass
except:
    raise


# parse if GPUs is needed #
avamb_threads, sep, avamb_gpus = AVAMB_PPN.partition(":gpus=")
AVAMB_PPN = avamb_threads
CUDA = len(avamb_gpus) > 0

# target
rule target_rule:
    input:
        os.path.join(OUTDIR,'avamb/tmp/workflow_finished_avamb.log')
        #contigs=os.path.join(OUTDIR,"contigs.flt.fna.gz"),
        #bam_files=expand(os.path.join(OUTDIR,"mapped/{sample}.sort.bam"), sample=IDS)



# Run avamb
rule run_avamb:
    input:
        #contigs=contigs_file,
        #bam_files=bam_path
        contigs=CONTIGS,
        bam_files=BAM
    output:
        outdir_avamb=directory(os.path.join(OUTDIR,"avamb")),
        clusters_aae_z=os.path.join(OUTDIR,"avamb/aae_z_clusters.tsv"),
        clusters_aae_y=os.path.join(OUTDIR,"avamb/aae_y_clusters.tsv"),
        clusters_vamb=os.path.join(OUTDIR,"avamb/vae_clusters.tsv"),
        contignames=os.path.join(OUTDIR,"avamb/contignames"),
        contiglenghts=os.path.join(OUTDIR,"avamb/lengths.npz")
    params:
        walltime="86400",
        nodes="1",
        ppn=AVAMB_PPN,
        mem=AVAMB_MEM,
        cuda="--cuda" if CUDA else ""
    threads:
        int(avamb_threads)
    
    log:
        os.path.join(OUTDIR,"avamb/tmp/avamb_finished.log")

    #conda:
        #"envs/avamb.yaml"
    shell:
        "rm -r {output.outdir_avamb}  && " 
        "{AVAMB_PRELOAD}"
        "vamb --outdir {output.outdir_avamb} --fasta {input.contigs} --bamfiles {input.bam_files}/*.bam {params.cuda} {AVAMB_PARAMS}; "
        "touch {log}"

checkpoint samples_with_bins:
    input:        
        os.path.join(OUTDIR,"avamb/tmp/avamb_finished.log")
    output:
        os.path.join(OUTDIR,"avamb/tmp/samples_with_bins.txt")
    params:
        walltime="300",
        nodes="1",
        ppn="1",
        mem="1gb"
    threads:
        1
    shell:
        "find {OUTDIR}/avamb/bins/*/ -type d ! -empty |sed 's=.*bins/==g'  |sed 's=/==g'  > {output}"


def samples_with_bins_f(wildcards):
    # decision based on content of output file
    with checkpoints.samples_with_bins.get().output[0].open() as f:
        samples_with_bins = [sample.strip() for sample in f.readlines()]
        samples_with_bins_paths=expand(os.path.join(OUTDIR,"avamb/tmp/checkm2_all_{sample}_bins_finished.log"),sample=samples_with_bins)
        return samples_with_bins_paths

        
rule run_checkm2_per_sample_all_bins:
    input:
        bins_dir_sample=os.path.join(OUTDIR,"avamb/bins/{sample}"),
        out_dir_checkm2=os.path.join(OUTDIR,"avamb/tmp/checkm2_all")
    output:
        out_log_file=os.path.join(OUTDIR,"avamb/tmp/checkm2_all_{sample}_bins_finished.log")
    params:
        walltime="86400",
        nodes="1",
        ppn=CHECKM_PPN,
        mem=CHECKM_MEM
    threads:
        int(CHECKM_PPN)
    #conda :
        #"envs/checkm2.yaml" # not functional since CheckM2 cannot be installed with #conda at the moment (20/12/2022).
    shell:
        "checkm2 predict --threads {threads} --input {input.bins_dir_sample}/*.fna --output-directory {input.out_dir_checkm2}/{wildcards.sample} 2> {output.out_log_file}"

rule cat_checkm2_all:
    input:
        samples_with_bins_f
    output: 
        os.path.join(OUTDIR,"avamb/tmp/checkm2_finished.txt")
    params:
        walltime="86400",
        nodes="1",
        ppn="2",
        mem="5gb"
    threads:
        1
    shell:
        "touch {output}"
            
rule create_cluster_scores_bin_path_dictionaries:
    input:
        checkm2_finished_log_file=os.path.join(OUTDIR,"avamb/tmp/checkm2_finished.txt"),
       
    output:
        cluster_score_dict_path_avamb=os.path.join(OUTDIR,"avamb/tmp/cs_d_avamb.json"),
        bin_path_dict_path_avamb=os.path.join(OUTDIR,"avamb/tmp/bp_d_avamb.json"),
    params:
        path=os.path.join(os.path.dirname(SNAKEDIR), "src", "create_cluster_scores_bin_path_dict.py"),
        walltime="86400",
        nodes="1",
        ppn="5",
        mem="10gb"
    threads:
        5
    #conda:
        #"envs/avamb.yaml"

    shell:
        "python {params.path}  --s {OUTDIR}/avamb/tmp/checkm2_all --b {OUTDIR}/avamb/bins --cs_d {output.cluster_score_dict_path_avamb} --bp_d {output.bin_path_dict_path_avamb} "


rule run_drep_manual_vamb_z_y:
    input:
        cluster_score_dict_path_avamb=os.path.join(OUTDIR,"avamb/tmp/cs_d_avamb.json"),
        contignames=os.path.join(OUTDIR,"avamb/contignames"),
        contiglengths=os.path.join(OUTDIR,"avamb/lengths.npz"),
        clusters_aae_z=os.path.join(OUTDIR,"avamb/aae_z_clusters.tsv"),
        clusters_aae_y=os.path.join(OUTDIR,"avamb/aae_y_clusters.tsv"),
        clusters_vamb=os.path.join(OUTDIR,"avamb/vae_clusters.tsv")

    output:
        clusters_avamb_manual_drep=os.path.join(OUTDIR,"avamb/tmp/avamb_manual_drep_clusters.tsv")
    params:
        path=os.path.join(os.path.dirname(SNAKEDIR), "src", "manual_drep_JN.py"),
        walltime="86400",
        nodes="1",
        ppn="5",
        mem="10gb"
    threads:
        5
    #conda:
        #"envs/avamb.yaml"
  
    shell:
        "python {params.path}  --cs_d  {input.cluster_score_dict_path_avamb} --names {input.contignames}  --lengths {input.contiglengths}  --output {output.clusters_avamb_manual_drep}  --clusters {input.clusters_aae_z} {input.clusters_aae_y} {input.clusters_vamb} --comp {MIN_COMP} --cont {MAX_CONT}"


checkpoint create_ripped_bins_avamb:
    input:
        path_avamb_manually_drep_clusters=os.path.join(OUTDIR,"avamb/tmp/avamb_manual_drep_clusters.tsv"),
        bin_path_dict_path=os.path.join(OUTDIR,"avamb/tmp/bp_d_avamb.json")
        
    output:
        path_avamb_manually_drep_clusters_ripped=os.path.join(OUTDIR,"avamb/tmp/avamb_manual_drep_not_ripped_clusters.tsv"),
        name_bins_ripped_file=os.path.join(OUTDIR,"avamb/tmp/bins_ripped_avamb.log")
    params:
        path=os.path.join(os.path.dirname(SNAKEDIR), "src", "rip_bins.py"),
        walltime="86400",
        nodes="1",
        ppn="5",
        mem="10gb"
    threads:
        5
    #conda:
        #"envs/avamb.yaml"
 
    shell: 
        "python {params.path} -r {OUTDIR}/avamb/ --ci {input.path_avamb_manually_drep_clusters}  --co  {output.path_avamb_manually_drep_clusters_ripped}  -l {OUTDIR}/avamb/lengths.npz -n {OUTDIR}/avamb/contignames --bp_d {input.bin_path_dict_path} --br {OUTDIR}/avamb/tmp/ripped_bins --bin_separator C --log_nc_ripped_bins {output.name_bins_ripped_file} "          

rule nc_clusters_and_bins_from_mdrep_clusters_avamb:
    input:
        clusters_avamb_manual_drep=os.path.join(OUTDIR,"avamb/tmp/avamb_manual_drep_clusters.tsv"),   
        cluster_score_dict_path_avamb=os.path.join(OUTDIR,"avamb/tmp/cs_d_avamb.json"),
        nc_bins_path=os.path.join(OUTDIR,"avamb/NC_bins")
    output:
        clusters_avamb_after_drep_disjoint=os.path.join(OUTDIR,"avamb/avamb_manual_drep_disjoint_clusters.tsv")
    log:
        os.path.join(OUTDIR,"avamb/tmp/avamb_nc_clusters_and_bins_from_mdrep_clusters.log")

    params:
        path=os.path.join(os.path.dirname(SNAKEDIR), "src", "mv_bins_from_mdrep_clusters.py"),
        walltime="86400",
        nodes="1",
        ppn="5",
        mem="10gb"
    threads:
        5
    #conda:
        #"envs/avamb.yaml"
    shell:
        "python {params.path} --c {input.clusters_avamb_manual_drep}  --cf  {output.clusters_avamb_after_drep_disjoint}  --b {OUTDIR}/avamb/bins --cs_d  {input.cluster_score_dict_path_avamb} --d  {input.nc_bins_path} --bin_separator C 2> {log}  --comp {MIN_COMP} --cont {MAX_CONT} "
        
    
    
def ripped_bins_avamb_check_output_f(wildcards):
    # decision based on content of output file
    with checkpoints.create_ripped_bins_avamb.get().output[1].open() as f:
        n_ripped_bins=int(f.readline())
        if n_ripped_bins == 0 :
            return os.path.join(OUTDIR,"avamb/tmp/avamb_nc_clusters_and_bins_from_mdrep_clusters.log")
        else:
            return os.path.join(OUTDIR,"avamb/tmp/final_avamb_clusters_written.log")


rule run_checkm2_ripped_bins_avamb:
    input:
        os.path.join(OUTDIR,"avamb/log/bins_ripped_avamb.log")
    output:
        os.path.join(OUTDIR,"avamb/tmp/ripped_bins/checkm2_out/quality_report.tsv")
    log:
        os.path.join(OUTDIR,"avamb/tmp/checkm2_ripped_avamb_run_finished.log")
    params:
        walltime="86400",
        nodes="1",
        ppn=CHECKM_PPN_r,
        mem=CHECKM_MEM_r
    threads:
        int(CHECKM_PPN_r)
#    #conda:
#        #"envs/checkm2.yaml" # not available at the moment.
    shell:
        "checkm2 predict --threads {CHECKM_PPN_r} --input {input} --output-directory {output}/checkm2_out 2> {log}"

rule update_cs_d_avamb:
    input:
        scores_bins_ripped=os.path.join(OUTDIR,"avamb/tmp/ripped_bins/checkm2_out/quality_report.tsv"),
        cluster_score_dict_path_avamb=os.path.join(OUTDIR,"avamb/tmp/cs_d_avamb.json")
    output:
        cs_updated_log=os.path.join(OUTDIR,"avamb/tmp/cs_d_avamb_updted.log")
    params:
        path=os.path.join(os.path.dirname(SNAKEDIR), "src", "update_cluster_scores_dict_after_ripping.py"),
        walltime="86400",
        nodes="1",
        ppn="5",
        mem="10gb"
    threads:
        5
    #conda:
        #"envs/avamb.yaml"
    shell:
        "python {params.path} --s {input.scores_bins_ripped}  --cs_d {input.cluster_score_dict_path_avamb} 2> {output}"


rule aggregate_nc_bins_avamb:
    input:
        cs_updated_log=os.path.join(OUTDIR,"avamb/tmp/cs_d_avamb_updted.log"),
        drep_clusters=os.path.join(OUTDIR,"avamb/tmp/avamb_manual_drep_clusters.tsv"),
        drep_clusters_not_ripped=os.path.join(OUTDIR,"avamb/tmp/avamb_manual_drep_not_ripped_clusters.tsv"),
        scores_bins_ripped=os.path.join(OUTDIR,"avamb/tmp/ripped_bins','checkm2_out','quality_report.tsv"),
        cluster_scores_dict_path_avamb=os.path.join(OUTDIR,"avamb/tmp/cs_d_avamb.json"),
        bin_path_dict_path_avamb=os.path.join(OUTDIR,"avamb/tmp/bp_d_avamb.json"),
        path_bins_ripped=os.path.join(OUTDIR,"avamb/tmp/ripped_bins"),
        checkm_finished_file=os.path.join(OUTDIR,"avamb/tmp/checkm2_ripped_avamb_run_finished.log")
    output:
        os.path.join(OUTDIR,"avamb/tmp/contigs_transfer_finished_avamb.log")
    params:
        path=os.path.join(os.path.dirname(SNAKEDIR), "src", "transfer_contigs_and_aggregate_all_nc_bins.py"),
        walltime="86400",
        nodes="1",
        ppn="5",
        mem="10gb"
    threads:
        5
    #conda:
        #"envs/avamb.yaml"

    shell:
        "python {params.path} -r {OUTDIR}/avamb/ --c {input.drep_clusters} --cnr {input.drep_clusters_not_ripped} --sbr {input.scores_bins_ripped} --cs_d {input.cluster_scores_dict_path_avamb} --bp_d {input.bin_path_dict_path_avamb} --br {input.path_bins_ripped} -d{OUTDIR}/avamb/NC_bins --bin_separator C   --comp {MIN_COMP} --cont {MAX_CONT} 2>  {output}"



rule write_clusters_from_nc_folders:
    input:
        contigs_transfered_log=os.path.join(OUTDIR,"avamb/tmp/contigs_transfer_finished_avamb.log"),
        nc_bins=os.path.join(OUTDIR,"avamb/NC_bins")
               
    output:
        os.path.join(OUTDIR,"avamb/avamb_manual_drep_disjoint_clusters.tsv")
    log:
        os.path.join(OUTDIR,"avamb/tmp/final_avamb_clusters_written.log"),
    params:
        path=os.path.join(os.path.dirname(SNAKEDIR), "src", "write_clusters_from_dereplicated_and_ripped_bins.sh"),
        walltime="86400",
        nodes="1",
        ppn="5",
        mem="10gb"
    threads:
        5
    #conda:
        #"envs/avamb.yaml"
    
    shell:
        "sh {params.path} -d {input.nc_bins} -o {output} 2> {log} "

rule workflow_finished:
    input:
        ripped_bins_avamb_check_output_f
    output:
        os.path.join(OUTDIR,"avamb/tmp/workflow_finished_avamb.log")
    params:
        walltime="86400",
        nodes="1",
        ppn="1",
        mem="1gb"
    threads:
        1
    shell:
        "touch {output}"
