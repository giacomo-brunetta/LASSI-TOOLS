#include "bottleneck.h"
#include <cmath>
#include <algorithm>

// Inline implementation of ev_init logic from LAMMPS Pair class
static void ev_init_inline(int eflag, int vflag,
                           int& evflag, int& eflag_either, int& eflag_global, int& eflag_atom,
                           int& vflag_either, int& vflag_global, int& vflag_atom, int& vflag_fdotr)
{
    if (eflag || vflag) evflag = 1;
    else evflag = 0;
    
    if (eflag) {
        eflag_either = eflag_global = 1;
        eflag_atom = 0;
    } else {
        eflag_either = eflag_global = eflag_atom = 0;
    }
    
    // vflag = 0: no virial
    // vflag = 1: virial_global (standard virial computation during loop)
    // vflag = 2: virial_fdotr (force-dot-r method at end, NOT during loop)
    if (vflag == 1) {
        vflag_either = vflag_global = 1;
        vflag_atom = vflag_fdotr = 0;
    } else if (vflag == 2) {
        vflag_fdotr = 1;
        vflag_either = vflag_global = vflag_atom = 0;  // No virial during loop
    } else {
        vflag_either = vflag_global = vflag_atom = vflag_fdotr = 0;
    }
}

// Inline implementation of ev_tally logic from LAMMPS Pair class
static void ev_tally_inline(int i, int j, int nlocal, int newton_pair,
                            double evdwl, double ecoul, double fpair,
                            double delx, double dely, double delz,
                            int eflag_either, int eflag_global, int eflag_atom,
                            int vflag_either, int vflag_global, int vflag_atom,
                            double& eng_vdwl, double& eng_coul, double* virial,
                            double* eatom, double** vatom)
{
    double v[6];
    
    if (eflag_either) {
        if (eflag_global) {
            if (newton_pair) {
                eng_vdwl += evdwl;
                eng_coul += ecoul;
            } else {
                double half = 0.5;
                if (i < nlocal) {
                    eng_vdwl += half * evdwl;
                    eng_coul += half * ecoul;
                }
                if (j < nlocal) {
                    eng_vdwl += half * evdwl;
                    eng_coul += half * ecoul;
                }
            }
        }
        if (eflag_atom) {
            double half = 0.5;
            if (newton_pair || i < nlocal) eatom[i] += half * evdwl + half * ecoul;
            if (newton_pair || j < nlocal) eatom[j] += half * evdwl + half * ecoul;
        }
    }
    
    if (vflag_either) {
        v[0] = delx * delx * fpair;
        v[1] = dely * dely * fpair;
        v[2] = delz * delz * fpair;
        v[3] = delx * dely * fpair;
        v[4] = delx * delz * fpair;
        v[5] = dely * delz * fpair;
        
        if (vflag_global) {
            if (newton_pair) {
                virial[0] += v[0];
                virial[1] += v[1];
                virial[2] += v[2];
                virial[3] += v[3];
                virial[4] += v[4];
                virial[5] += v[5];
            } else {
                if (i < nlocal) {
                    virial[0] += 0.5 * v[0];
                    virial[1] += 0.5 * v[1];
                    virial[2] += 0.5 * v[2];
                    virial[3] += 0.5 * v[3];
                    virial[4] += 0.5 * v[4];
                    virial[5] += 0.5 * v[5];
                }
                if (j < nlocal) {
                    virial[0] += 0.5 * v[0];
                    virial[1] += 0.5 * v[1];
                    virial[2] += 0.5 * v[2];
                    virial[3] += 0.5 * v[3];
                    virial[4] += 0.5 * v[4];
                    virial[5] += 0.5 * v[5];
                }
            }
        }
        
        if (vflag_atom) {
            if (newton_pair || i < nlocal) {
                vatom[i][0] += 0.5 * v[0];
                vatom[i][1] += 0.5 * v[1];
                vatom[i][2] += 0.5 * v[2];
                vatom[i][3] += 0.5 * v[3];
                vatom[i][4] += 0.5 * v[4];
                vatom[i][5] += 0.5 * v[5];
            }
            if (newton_pair || j < nlocal) {
                vatom[j][0] += 0.5 * v[0];
                vatom[j][1] += 0.5 * v[1];
                vatom[j][2] += 0.5 * v[2];
                vatom[j][3] += 0.5 * v[3];
                vatom[j][4] += 0.5 * v[4];
                vatom[j][5] += 0.5 * v[5];
            }
        }
    }
}

// Refactored bottleneck function - functionally pure
void compute_lj_cut(
    int eflag,
    int vflag,
    int nlocal,
    int nmax,
    int inum,
    int newton_pair,
    int ntypes,
    double** x,
    int* type,
    double* special_lj,
    int* ilist,
    int* numneigh,
    int** firstneigh,
    double** cutsq,
    double** lj1,
    double** lj2,
    double** lj3,
    double** lj4,
    double** offset,
    double** f,
    double& eng_vdwl,
    double& eng_coul,
    double* virial,
    int& evflag,
    int& eflag_either,
    int& eflag_global,
    int& eflag_atom,
    int& vflag_either,
    int& vflag_global,
    int& vflag_atom,
    int& vflag_fdotr,
    double* eatom,
    double** vatom)
{
    int i, j, ii, jj, jnum, itype, jtype;
    double xtmp, ytmp, ztmp, delx, dely, delz, evdwl, fpair;
    double rsq, r2inv, r6inv, forcelj, factor_lj;
    int *jlist;

    const bool do_energy = (eflag != 0);
    const bool do_newton = (newton_pair != 0);
    
    // Initialize outputs
    eng_vdwl = 0.0;
    eng_coul = 0.0;
    for (int k = 0; k < 6; k++) {
        virial[k] = 0.0;
    }
    
    // Initialize flags (inline ev_init)
    ev_init_inline(eflag, vflag,
                   evflag, eflag_either, eflag_global, eflag_atom,
                   vflag_either, vflag_global, vflag_atom, vflag_fdotr);
    const bool pair_tally_needed = (eflag_either != 0) || (vflag_either != 0);
    const bool fast_force_only_path = !pair_tally_needed;
    const bool energy_global_only_path = (eflag_global != 0) && (eflag_atom == 0) && (vflag_either == 0);

    // P-B: one-time scratch allocation for neighbor predecode buffers
    int max_jnum = 0;
    for (ii = 0; ii < inum; ii++) {
        const int idx = ilist[ii];
        max_jnum = std::max(max_jnum, numneigh[idx]);
    }
    int* neigh_j = (max_jnum > 0) ? new int[max_jnum] : nullptr;
    double* neigh_factor = (max_jnum > 0) ? new double[max_jnum] : nullptr;

    // P-C: per-itype local staging tables
    double* cutsq_t = new double[ntypes + 1];
    double* lj1_t = new double[ntypes + 1];
    double* lj2_t = new double[ntypes + 1];
    double* lj3_t = new double[ntypes + 1];
    double* lj4_t = new double[ntypes + 1];
    double* offset_t = new double[ntypes + 1];
    
    // Main computation loop over atoms
    if (fast_force_only_path) {
        // Priority A fast path: force-only pair loop (no per-pair tally work)
        for (ii = 0; ii < inum; ii++) {
            i = ilist[ii];
            xtmp = x[i][0];
            ytmp = x[i][1];
            ztmp = x[i][2];
            itype = type[i];
            jlist = firstneigh[i];
            jnum = numneigh[i];

            double* fi = f[i];
            double* cutsq_i = cutsq[itype];
            double* lj1_i = lj1[itype];
            double* lj2_i = lj2[itype];

            for (int t = 1; t <= ntypes; t++) {
                cutsq_t[t] = cutsq_i[t];
                lj1_t[t] = lj1_i[t];
                lj2_t[t] = lj2_i[t];
            }

            for (jj = 0; jj < jnum; jj++) {
                const int encoded = jlist[jj];
                neigh_j[jj] = encoded & NEIGHMASK;
                neigh_factor[jj] = special_lj[sbmask(encoded)];
            }

            double fix = fi[0];
            double fiy = fi[1];
            double fiz = fi[2];

            for (jj = 0; jj < jnum; jj++) {
                j = neigh_j[jj];
                factor_lj = neigh_factor[jj];

                double* xj = x[j];
                delx = xtmp - xj[0];
                dely = ytmp - xj[1];
                delz = ztmp - xj[2];
                rsq = delx * delx + dely * dely + delz * delz;
                jtype = type[j];

                // Priority D: early reject path
                if (rsq >= cutsq_t[jtype]) continue;

                r2inv = 1.0 / rsq;
                r6inv = r2inv * r2inv * r2inv;
                forcelj = r6inv * (lj1_t[jtype] * r6inv - lj2_t[jtype]);
                fpair = factor_lj * forcelj * r2inv;

                // Priority E: reuse products
                const double dfx = delx * fpair;
                const double dfy = dely * fpair;
                const double dfz = delz * fpair;
                fix += dfx;
                fiy += dfy;
                fiz += dfz;
                if (do_newton || j < nlocal) {
                    double* fj = f[j];
                    fj[0] -= dfx;
                    fj[1] -= dfy;
                    fj[2] -= dfz;
                }
            }

            fi[0] = fix;
            fi[1] = fiy;
            fi[2] = fiz;
        }
    } else if (energy_global_only_path) {
        // Priority A energy-only path: update global energy directly, skip ev_tally
        for (ii = 0; ii < inum; ii++) {
            i = ilist[ii];
            xtmp = x[i][0];
            ytmp = x[i][1];
            ztmp = x[i][2];
            itype = type[i];
            jlist = firstneigh[i];
            jnum = numneigh[i];

            double* fi = f[i];
            double* cutsq_i = cutsq[itype];
            double* lj1_i = lj1[itype];
            double* lj2_i = lj2[itype];
            double* lj3_i = lj3[itype];
            double* lj4_i = lj4[itype];
            double* offset_i = offset[itype];

            for (int t = 1; t <= ntypes; t++) {
                cutsq_t[t] = cutsq_i[t];
                lj1_t[t] = lj1_i[t];
                lj2_t[t] = lj2_i[t];
                lj3_t[t] = lj3_i[t];
                lj4_t[t] = lj4_i[t];
                offset_t[t] = offset_i[t];
            }

            for (jj = 0; jj < jnum; jj++) {
                const int encoded = jlist[jj];
                neigh_j[jj] = encoded & NEIGHMASK;
                neigh_factor[jj] = special_lj[sbmask(encoded)];
            }

            double fix = fi[0];
            double fiy = fi[1];
            double fiz = fi[2];

            for (jj = 0; jj < jnum; jj++) {
                j = neigh_j[jj];
                factor_lj = neigh_factor[jj];

                double* xj = x[j];
                delx = xtmp - xj[0];
                dely = ytmp - xj[1];
                delz = ztmp - xj[2];
                rsq = delx * delx + dely * dely + delz * delz;
                jtype = type[j];

                if (rsq >= cutsq_t[jtype]) continue;

                r2inv = 1.0 / rsq;
                r6inv = r2inv * r2inv * r2inv;
                forcelj = r6inv * (lj1_t[jtype] * r6inv - lj2_t[jtype]);
                fpair = factor_lj * forcelj * r2inv;

                const double dfx = delx * fpair;
                const double dfy = dely * fpair;
                const double dfz = delz * fpair;
                fix += dfx;
                fiy += dfy;
                fiz += dfz;
                if (do_newton || j < nlocal) {
                    double* fj = f[j];
                    fj[0] -= dfx;
                    fj[1] -= dfy;
                    fj[2] -= dfz;
                }

                evdwl = r6inv * (lj3_t[jtype] * r6inv - lj4_t[jtype]) - offset_t[jtype];
                evdwl *= factor_lj;
                if (do_newton) {
                    eng_vdwl += evdwl;
                } else {
                    if (i < nlocal) eng_vdwl += 0.5 * evdwl;
                    if (j < nlocal) eng_vdwl += 0.5 * evdwl;
                }
            }

            fi[0] = fix;
            fi[1] = fiy;
            fi[2] = fiz;
        }
    } else {
        // Priority A full tally path: preserve existing ev_tally semantics
        for (ii = 0; ii < inum; ii++) {
            i = ilist[ii];
            xtmp = x[i][0];
            ytmp = x[i][1];
            ztmp = x[i][2];
            itype = type[i];
            jlist = firstneigh[i];
            jnum = numneigh[i];

            double* fi = f[i];
            double* cutsq_i = cutsq[itype];
            double* lj1_i = lj1[itype];
            double* lj2_i = lj2[itype];
            double* lj3_i = lj3[itype];
            double* lj4_i = lj4[itype];
            double* offset_i = offset[itype];

            for (int t = 1; t <= ntypes; t++) {
                cutsq_t[t] = cutsq_i[t];
                lj1_t[t] = lj1_i[t];
                lj2_t[t] = lj2_i[t];
                lj3_t[t] = lj3_i[t];
                lj4_t[t] = lj4_i[t];
                offset_t[t] = offset_i[t];
            }

            for (jj = 0; jj < jnum; jj++) {
                const int encoded = jlist[jj];
                neigh_j[jj] = encoded & NEIGHMASK;
                neigh_factor[jj] = special_lj[sbmask(encoded)];
            }

            double fix = fi[0];
            double fiy = fi[1];
            double fiz = fi[2];

            for (jj = 0; jj < jnum; jj++) {
                j = neigh_j[jj];
                factor_lj = neigh_factor[jj];

                double* xj = x[j];
                delx = xtmp - xj[0];
                dely = ytmp - xj[1];
                delz = ztmp - xj[2];
                rsq = delx * delx + dely * dely + delz * delz;
                jtype = type[j];

                if (rsq >= cutsq_t[jtype]) continue;

                r2inv = 1.0 / rsq;
                r6inv = r2inv * r2inv * r2inv;
                forcelj = r6inv * (lj1_t[jtype] * r6inv - lj2_t[jtype]);
                fpair = factor_lj * forcelj * r2inv;

                const double dfx = delx * fpair;
                const double dfy = dely * fpair;
                const double dfz = delz * fpair;
                fix += dfx;
                fiy += dfy;
                fiz += dfz;
                if (do_newton || j < nlocal) {
                    double* fj = f[j];
                    fj[0] -= dfx;
                    fj[1] -= dfy;
                    fj[2] -= dfz;
                }

                if (do_energy) {
                    evdwl = r6inv * (lj3_t[jtype] * r6inv - lj4_t[jtype]) - offset_t[jtype];
                    evdwl *= factor_lj;
                } else {
                    evdwl = 0.0;
                }

                ev_tally_inline(i, j, nlocal, newton_pair, evdwl, 0.0, fpair, delx, dely, delz,
                               eflag_either, eflag_global, eflag_atom,
                               vflag_either, vflag_global, vflag_atom,
                               eng_vdwl, eng_coul, virial, eatom, vatom);
            }

            fi[0] = fix;
            fi[1] = fiy;
            fi[2] = fiz;
        }
    }

    delete[] neigh_j;
    delete[] neigh_factor;
    delete[] cutsq_t;
    delete[] lj1_t;
    delete[] lj2_t;
    delete[] lj3_t;
    delete[] lj4_t;
    delete[] offset_t;
    
    // Compute virial using force-dot-position method if vflag_fdotr is set
    if (vflag_fdotr) {
        // virial_fdotr_compute: sum over ALL atoms that received forces
        // With newton_pair=1, this includes both local and ghost atoms
        // We sum over nmax since forces on unused atoms are zero
        for (int i = 0; i < nmax; i++) {
            virial[0] += f[i][0] * x[i][0];
            virial[1] += f[i][1] * x[i][1];
            virial[2] += f[i][2] * x[i][2];
            virial[3] += f[i][1] * x[i][0];
            virial[4] += f[i][2] * x[i][0];
            virial[5] += f[i][2] * x[i][1];
        }
    }
}
