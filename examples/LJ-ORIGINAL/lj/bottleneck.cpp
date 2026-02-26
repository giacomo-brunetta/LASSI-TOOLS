#include "bottleneck.h"
#include <cmath>

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
    
    // Main computation loop over atoms
    for (ii = 0; ii < inum; ii++) {
        i = ilist[ii];
        xtmp = x[i][0];
        ytmp = x[i][1];
        ztmp = x[i][2];
        itype = type[i];
        jlist = firstneigh[i];
        jnum = numneigh[i];
        
        // Inner loop over neighbors
        for (jj = 0; jj < jnum; jj++) {
            j = jlist[jj];
            factor_lj = special_lj[sbmask(j)];
            j &= NEIGHMASK;
            
            delx = xtmp - x[j][0];
            dely = ytmp - x[j][1];
            delz = ztmp - x[j][2];
            rsq = delx * delx + dely * dely + delz * delz;
            jtype = type[j];
            
            if (rsq < cutsq[itype][jtype]) {
                r2inv = 1.0 / rsq;
                r6inv = r2inv * r2inv * r2inv;
                forcelj = r6inv * (lj1[itype][jtype] * r6inv - lj2[itype][jtype]);
                fpair = factor_lj * forcelj * r2inv;
                
                f[i][0] += delx * fpair;
                f[i][1] += dely * fpair;
                f[i][2] += delz * fpair;
                if (newton_pair || j < nlocal) {
                    f[j][0] -= delx * fpair;
                    f[j][1] -= dely * fpair;
                    f[j][2] -= delz * fpair;
                }
                
                if (eflag) {
                    evdwl = r6inv * (lj3[itype][jtype] * r6inv - lj4[itype][jtype]) - offset[itype][jtype];
                    evdwl *= factor_lj;
                } else {
                    evdwl = 0.0;
                }
                
                if (evflag) {
                    ev_tally_inline(i, j, nlocal, newton_pair, evdwl, 0.0, fpair, delx, dely, delz,
                                   eflag_either, eflag_global, eflag_atom,
                                   vflag_either, vflag_global, vflag_atom,
                                   eng_vdwl, eng_coul, virial, eatom, vatom);
                }
            }
        }
    }
    
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