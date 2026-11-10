"""Bounded, single-threaded training entry point (cross-platform)."""
import os,subprocess,sys

def main():
    env=dict(os.environ)
    for name in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:
        env[name]='1'
    try:
        result=subprocess.run([sys.executable,'-m','personality.train',*sys.argv[1:]],env=env,timeout=4*60*60)
        raise SystemExit(result.returncode)
    except subprocess.TimeoutExpired:
        raise SystemExit('Stopped: training reached the four-hour limit.')
if __name__=='__main__':main()
