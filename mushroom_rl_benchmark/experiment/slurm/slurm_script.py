import os


def create_slurm_script(slurm_path, slurm_script_name='slurm.sh', **slurm_params):
    """
    Function to create a slurm script in a specific directory

    Args:
        slurm_path (str): path to locate the slurm script

    Kwargs:
        slurm_script_name (str): name of the slurm script (Default: slurm.sh)
        **slurm_params (dict): parameters for generating the slurm file content
    """
    code = generate_slurm(**slurm_params)

    os.makedirs(slurm_path, exist_ok=True)
    slurm_path = os.path.join(slurm_path, slurm_script_name)

    with open(slurm_path, "w") as file:
        file.write(code)

    return slurm_path


def generate_slurm(exp_name, exp_dir_slurm, python_file, project_name=None, n_exp=1, max_concurrent_runs=None, memory=2000, hours=24, minutes=0, seconds=0):
    """
    Function to generate the slurm file content.

    Args:
        exp_name (str): name of the experiment
        exp_dir_slurm (str): directory where the slurm log files are located
        python_file (str): path to the python file that should be executed
    
    Kwargs:
        project_name (str): name of the slurm project (Default: None)
        n_exp (int): number of experiments in the slurm array (Default: 1)
        max_concurrent_runs (int): maximum number of runs that should be executed in parallel on the SLURM cluster (Default: None)
        memory (int): memory limit in mega bytes (MB) for the slurm jobs (Default: 2000)
        hours (int): maximum number of execution hours for the slurm jobs (Default: 24)
        minutes (int): maximum number of execution minutes for the slurm jobs (Default: 0)
        seconds (int): maximum number of execution seconds for the slurm jobs (Default: 0)
    """
    duration = to_duration(hours, minutes, seconds) 
    code = """\
#!/usr/bin/env bash

###############################################################################
# SLURM Configurations
"""
    if project_name:
        code += '#SBATCH -A ' + project_name + '\n'
    code += '#SBATCH -J ' + exp_name + '\n'
    if n_exp > 1:
        code += '#SBATCH -a 0-' + str(n_exp-1) + ('%{}'.format(max_concurrent_runs) if max_concurrent_runs is not None else '') + '\n'
    code += '#SBATCH -t ' + duration + '\n'
    code += """\
#SBATCH -n 1
#SBATCH -c 1
"""
    code += '#SBATCH --mem-per-cpu=' + str(memory) + '\n'
    if n_exp > 1:
        code += '#SBATCH -o ' + exp_dir_slurm + '/%A_%a.out\n'
        code += '#SBATCH -e ' + exp_dir_slurm + '/%A_%a.err\n'
    else:
        code += '#SBATCH -o ' + exp_dir_slurm + '/%A.out\n'
        code += '#SBATCH -e ' + exp_dir_slurm + '/%A.err\n'
    code += """\
###############################################################################
# Your PROGRAM call starts here
echo "Starting Job $SLURM_JOB_ID, Index $SLURM_ARRAY_TASK_ID"

# Program specific arguments
"""
    code += 'CMD="python3 ' + python_file + ' \\\n'
    code += "\t\t${@:1}\\\n"

    if n_exp > 1:
        code += '\t\t--seed $SLURM_ARRAY_TASK_ID'
    else:
        code += '\t\t--seed 0'
    
    code += '"\n\n'
    code += 'echo "$CMD"\n'
    code += 'eval $CMD\n'

    return code


def to_duration(hours, minutes, seconds):
    h = "0" + str(hours) if hours < 10 else str(hours)
    m = "0" + str(minutes) if minutes < 10 else str(minutes)
    s = "0" + str(seconds) if seconds < 10 else str(seconds)

    return h + ":" + m + ":" + s