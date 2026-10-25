"""Build the paper's full timing-scope table from the frozen experiment exports."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
INPUTS={
    'timings':ROOT/'docs/experiments/accelerator-transfer-timing-20261025/latencies.csv',
    'gpu_active':ROOT/'docs/experiments/gpu-active-timing-20261025/gpu-active-latencies.csv',
    'cs3_stream':ROOT/'docs/experiments/cs3-timing-estimates-20261025/cs3-latency-estimates.csv',
    'cs3_native':ROOT/'docs/experiments/cs3-resident-estimates-20261025/cs3-resident-estimates.csv',
}
LABELS={'polybench-bicg':'BICG','polybench-mvt':'MVT','polybench-gesummv':'GESUMMV',
    'polybench-gemm':'GEMM','iir-filter-bank':'IIR filter bank','lorenz-rk4':'Lorenz RK4',
    'low-rank-compression':'Low-rank','poisson-cg':'Poisson CG','polybench-doitgen':'DOITGEN',
    'polybench-syr2k':'SYR2K','polybench-trmm':'TRMM'}
COLUMNS=['a100_inclusive_s','a100_resident_s','a100_active_s','groq_inclusive_s','groq_schedule_s',
    'graphcore_inclusive_s','graphcore_active_s','cs3_stream_interval_s','cs3_first_iteration_s',
    'cs3_native_budget_s','cs3_native_plus_context_s']


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read_csv(p):return list(csv.DictReader(Path(p).open()))


def write_csv(p,rows):
    with p.open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def collect():
    files=dict(INPUTS)
    measured=read_csv(files['timings'])
    active={r['id']:r for r in read_csv(files['gpu_active'])}
    stream={r['id']:r for r in read_csv(files['cs3_stream'])}
    native={r['id']:r for r in read_csv(files['cs3_native'])}
    assert stream.keys()==native.keys()
    cases={r['id']:(r['kernel'],r['candidate']) for r in measured}
    cases.update({r['id']:(r['kernel'],r['candidate']) for r in stream.values()})
    by_key={(r['backend'],r['id']):r for r in measured}
    assert len(by_key)==len(measured)
    supplemental_gpu={}
    # CS3-only cases can reuse a qualified archived GPU measurement, but do not
    # acquire an active profile from another source or an unmeasured precision.
    for identifier in stream.keys()-{r['id'] for r in measured if r['backend']=='a100'}:
        result_path=ROOT/'runs/cerebras-sol-porting-20261024/cases'/identifier/'result.json'
        result=json.loads(result_path.read_text())
        source=result['entry']['source_sha256']
        files['cs3_lineage_'+identifier]=result_path
        for campaign in ['gpu-transfer-timing-20261024','gpu-transfer-timing-supplements-20261024']:
            path=ROOT/'runs'/campaign/'timings.csv'
            matches=[r for r in read_csv(path) if r['source_sha256']==source and r['precision']=='fp16'
                and r['verified']=='True' and r['valid']=='True' and float(r['relative_l2'])<=.01
                and r['host_to_host_s'] and r['resident_s']]
            if not matches:continue
            match=matches[0]
            evidence_path=ROOT/'runs'/campaign/'results.json'
            evidence=json.loads(evidence_path.read_text())[match['job_id']]
            assert evidence['input_verified'] and evidence['transfer_timing_verified']
            assert evidence['host_source_hash_matches'] and evidence['source_sha256']==source
            assert evidence['observation']['metrics']['relative_l2']<=.01
            a=evidence['observation']['timings']
            assert math.isclose(float(match['resident_s']),a['resident_execution']['median_s'],rel_tol=1e-12)
            assert math.isclose(float(match['host_to_host_s']),a['host_to_host']['median_s'],rel_tol=1e-12)
            supplemental_gpu[identifier]=dict(source_sha256=source,inclusive_s=match['host_to_host_s'],
                onchip_s=match['resident_s'],inclusive_kind='measured_host_to_host_with_PCIe_IO',
                onchip_kind='measured_resident_CUDA_graph_device_stream',job_id=match['job_id'])
            files['gpu_supplement_timings_'+identifier]=path
            files['gpu_supplement_result_'+identifier]=evidence_path
            break
    rows=[]
    for identifier,(kernel,candidate) in sorted(cases.items(),key=lambda item:(list(LABELS).index(item[1][0]),item[1][1],item[0])):
        r=dict(id=identifier,kernel=kernel,candidate=candidate,precision='fp16',dataset='large',**{c:None for c in COLUMNS})
        for backend in ['a100','groq','graphcore']:
            point=by_key.get((backend,identifier))
            if backend=='a100' and point is None:point=supplemental_gpu.get(identifier)
            if point is None:
                r[backend+'_source_sha256']=None
                continue
            assert not point.get('precision') or point['precision']=='fp16'
            r[backend+'_source_sha256']=point['source_sha256']
            r[backend+'_inclusive_s']=float(point['inclusive_s'])
            metric={'a100':'a100_resident_s','groq':'groq_schedule_s','graphcore':'graphcore_active_s'}[backend]
            r[metric]=float(point['onchip_s'])
        profile=active.get(identifier)
        if profile:
            assert profile['source_sha256']==r['a100_source_sha256']
            r['a100_active_s']=float(profile['active_s'])
        r['a100_profile_anomaly']=bool(profile and profile['profiling_anomaly']=='True')
        if identifier in stream:
            s,n=stream[identifier],native[identifier]
            assert s['source_sha256']==n['source_sha256'] and s['cache_compile']==n['cache_compile']
            r.update(cs3_stream_interval_s=float(s['compiler_steady_interval_s']),
                cs3_first_iteration_s=float(s['compiler_first_iteration_estimate_s']),
                cs3_native_budget_s=float(n['ideal_resident_active_estimate_s']),
                cs3_native_plus_context_s=float(n['resident_data_with_context_estimate_s']))
            r['cs3_source_sha256']=s['source_sha256']
            r['cs3_host_helpers_uncosted']=n['host_helpers_require_resident_remap']=='True'
        else:
            r['cs3_source_sha256']=None
            r['cs3_host_helpers_uncosted']=False
        for c in COLUMNS:
            assert r[c] is None or math.isfinite(r[c]) and r[c]>0
        rows.append(r)
    assert len({(r['kernel'],r['candidate']) for r in rows})==len(rows)
    return rows,files


def number(value,marker=''):
    if value is None:return r'--'
    formatted=f'{1000*value:.5g}'
    if marker:formatted+=r'\textsuperscript{'+marker+'}'
    return formatted


def render(rows):
    lines=[r'% Generated by LASSI-TOOLS/docs/experiments/accelerator-performance-table-20261025/build_table.py.',
        r'% All displayed durations are milliseconds; the accompanying CSV stores seconds.',
        r'\begin{table*}[t]',r'  \centering',
        r'  \caption{\ai{Transfer-inclusive timings and resident/active execution evidence for LARGE FP16 cases (all values in milliseconds). M: measured; P: profile-derived estimate; C: compiler-reported schedule estimate; D: derived native-cycle budget. Distinct timing scopes are retained rather than pooled into a common speedup.}}',
        r'  \label{tab:accelerator-performance}',r'  \ai{\fontsize{7}{8.7}\selectfont',
        r'  \setlength{\tabcolsep}{2.0pt}',r'  \renewcommand{\arraystretch}{1.12}',
        r'  \begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}llrrrrrrrrrrr@{}}',r'    \toprule',
        r'    & & \multicolumn{3}{c}{NVIDIA A100} & \multicolumn{2}{c}{Groq} & \multicolumn{2}{c}{Graphcore IPU} & \multicolumn{4}{c}{Cerebras CS-3} \\',
        r'    \cmidrule(lr){3-5}\cmidrule(lr){6-7}\cmidrule(lr){8-9}\cmidrule(lr){10-13}',
        r'    Kernel & Case & \shortstack{I/O+\\M} & \shortstack{Resident\\M} & \shortstack{Active\\P} & \shortstack{I/O+\\M} & \shortstack{Schedule\\C} & \shortstack{I/O+\\M} & \shortstack{Active\\P} & \shortstack{Stream\\C} & \shortstack{First\\C} & \shortstack{Native\\D} & \shortstack{Native+ctx\\D} \\',r'    \midrule']
    previous=None
    for r in rows:
        if previous is not None and previous!=r['kernel']:lines.append(r'    \addlinespace[1.5pt]')
        label=LABELS[r['kernel']] if previous!=r['kernel'] else ''
        cells=[label,r['candidate']]
        for c in COLUMNS:
            marker='a' if c=='a100_active_s' and r['a100_profile_anomaly'] else ('b' if c.startswith('cs3_native') and r['cs3_host_helpers_uncosted'] else '')
            cells.append(number(r[c],marker))
        lines.append('    '+' & '.join(cells)+r' \\')
        previous=r['kernel']
    lines += [r'    \bottomrule',r'  \end{tabular*}',r'  \par\vspace{3pt}',r'  \begin{minipage}{\textwidth}\fontsize{7}{8.4}\selectfont',
        r'  \textit{Timing boundaries.} I/O+ is a measured serialized host-to-host call, including input/output transfers and invocation, with setup excluded. A100/Groq use PCIe; Graphcore uses the deployed IPU fabric. A100 Resident is CUDA-event elapsed time for a captured graph with device-resident tensors (including HBM access); Active is the union of profiled kernel/device-memory intervals with idle gaps excluded. Groq Schedule is the successful executable\textquotesingle s compiler cycle estimate. IPU Active reconstructs compute, internal exchange and internal synchronization phases.',
        r'  \par\smallskip',
        r'  \textit{CS-3 estimates.} Stream is the predicted steady-state interval with modeled streaming stalls; First is the predicted first compiled iteration. Neither is a measured host-to-host call. Native sums the compiler\textquotesingle s wafer-native operation cycles assuming preloaded data/layouts, resident code and serial operations; Native+ctx also retains the original context-switch cycle budget. Both D columns are conditional component budgets, not predictions from a newly compiled resident executable or proof of memory-placement feasibility.',
        r'  \par\smallskip',
        r'  \textsuperscript{a} IIR profiling perturbs timing; its active estimate exceeds the same process\textquotesingle s capture-disabled resident interval and is diagnostic only. \textsuperscript{b} CS-3 has uncosted host helpers (MVT addition; GESUMMV/GEMM reduction/distribution), so the D columns omit required remapping costs. Independent runs and instrumentation can also make active estimates exceed archived elapsed medians; differences are not isolated transfer costs. -- denotes unavailable qualified timing evidence, not zero latency. Case IDs and source hashes are recorded in the accompanying CSV.',
        r'  \end{minipage}}',r'\end{table*}','']
    return '\n'.join(lines)


def main(paper=None):
    rows,files=collect()
    tex=render(rows)
    (HERE/'accelerator-performance.tex').write_text(tex)
    write_csv(HERE/'accelerator-performance.csv',rows)
    provenance=dict(rows=len(rows),applications=len({r['kernel'] for r in rows}),precision='fp16',dataset='large',
        display_units='milliseconds',csv_units='seconds',columns=COLUMNS,
        nonempty_cells={c:sum(r[c] is not None for r in rows) for c in COLUMNS},
        case_ids=[r['id'] for r in rows],excluded_profile_only_aliases=['14882e83f7d350a7'],
        source_files={str(p.relative_to(ROOT)):sha(p) for p in files.values()},
        a100_profile_anomaly_ids=[r['id'] for r in rows if r['a100_profile_anomaly']],
        cs3_uncosted_host_helper_ids=[r['id'] for r in rows if r['cs3_host_helpers_uncosted']],
        compiler_or_profile_estimates_are_measured_calls=False,new_hardware_jobs=0,
        generator_sha256=sha(__file__))
    (HERE/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    if paper:
        paper=Path(paper)
        for name in ['accelerator-performance.tex','accelerator-performance.csv','provenance.json']:
            destination='accelerator-performance-provenance.json' if name=='provenance.json' else name
            shutil.copyfile(HERE/name,paper/'tables'/destination)
    print(json.dumps({k:provenance[k] for k in ['rows','applications','nonempty_cells']}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--paper',type=Path);a=p.parse_args();main(a.paper)
