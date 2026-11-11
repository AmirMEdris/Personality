"""CPU-only child process with one numerical thread and a four-hour hard timeout."""
import os
import subprocess
import sys

def main():
    env=dict(os.environ)
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):env[key]='1'
    try:
        r=subprocess.run([sys.executable,'-m','personality.workbench',*sys.argv[1:]],env=env,timeout=14400)
    except subprocess.TimeoutExpired:
        raise SystemExit('Stopped at four-hour resource limit. Partial run is not a completed result.')
    raise SystemExit(r.returncode)
if __name__=='__main__':main()
