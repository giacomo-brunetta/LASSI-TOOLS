#ifndef BOTTLENECK_H
#define BOTTLENECK_H

#include <cstddef>

// Type definitions
typedef int tagint;
typedef int bigint;
typedef int imageint;

// Mask for neighbor list - from LAMMPS neighbor.h
#define NEIGHMASK 0x3FFFFFFF

// Function to extract special bond mask - from LAMMPS pair.h
inline int sbmask(int j) {
  return j >> 30 & 3;
}

// Bottleneck function signature
// This is the functionally pure version of PairLJCut::compute
void compute_lj_cut(
    // Function parameters
    int eflag,
    int vflag,
    
    // Scalar dimensions
    int nlocal,
    int nmax,
    int inum,
    int newton_pair,
    int ntypes,
    
    // Input arrays
    double** x,              // positions [nmax][3]
    int* type,               // atom types [nmax]
    double* special_lj,      // special bond scaling [4]
    int* ilist,              // atom index list [inum]
    int* numneigh,           // neighbor counts [nlocal]
    int** firstneigh,        // neighbor lists [nlocal][variable]
    double** cutsq,          // cutoff squared [ntypes+1][ntypes+1]
    double** lj1,            // LJ coefficient 1 [ntypes+1][ntypes+1]
    double** lj2,            // LJ coefficient 2 [ntypes+1][ntypes+1]
    double** lj3,            // LJ coefficient 3 [ntypes+1][ntypes+1]
    double** lj4,            // LJ coefficient 4 [ntypes+1][ntypes+1]
    double** offset,         // energy offset [ntypes+1][ntypes+1]
    
    // Output arrays (modified in place)
    double** f,              // forces [nmax][3]
    double& eng_vdwl,        // van der Waals energy (output)
    double& eng_coul,        // Coulombic energy (output)
    double* virial,          // virial[6] (output)
    
    // Output flags (for verification)
    int& evflag,
    int& eflag_either,
    int& eflag_global,
    int& eflag_atom,
    int& vflag_either,
    int& vflag_global,
    int& vflag_atom,
    int& vflag_fdotr,
    
    // Optional output arrays
    double* eatom,           // per-atom energies [nmax] (if eflag_atom)
    double** vatom           // per-atom virials [nmax][6] (if vflag_atom)
);

#endif // BOTTLENECK_H