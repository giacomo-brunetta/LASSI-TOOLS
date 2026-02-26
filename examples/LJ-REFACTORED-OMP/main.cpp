#include "bottleneck.h"
#include <iostream>
#include <fstream>
#include <cmath>
#include <cstdlib>
#include <iomanip>

// Tolerance for numerical comparison from workload1/tolerance.md
const double ABS_TOL = 1e-3;
const double REL_TOL = 1e-2;

// Floating-point comparison with tolerance
bool doubles_equal(double a, double b, double abs_tol = ABS_TOL, double rel_tol = REL_TOL) {
    double abs_diff = std::abs(a - b);
    if (abs_diff < abs_tol) return true;
    double max_val = std::max(std::abs(a), std::abs(b));
    if (max_val < 1e-15) return true;  // Both near zero
    return abs_diff / max_val < rel_tol;
}

// Allocate 2D array
template<typename T>
T** allocate_2d(int rows, int cols) {
    T** arr = new T*[rows];
    for (int i = 0; i < rows; i++) {
        arr[i] = new T[cols];
    }
    return arr;
}

// Deallocate 2D array
template<typename T>
void deallocate_2d(T** arr, int rows) {
    for (int i = 0; i < rows; i++) {
        delete[] arr[i];
    }
    delete[] arr;
}

int main() {
    std::cout << "=== PairLJCut Test Harness ===" << std::endl;
    
    // ========== READ INPUT SNAPSHOT ==========
    const char* input_file = "/home/gbrun/lj-refactor/lammps_ljcut_32K.bin";
    std::ifstream ifs(input_file, std::ios::binary);
    if (!ifs) {
        std::cerr << "ERROR: Cannot open input snapshot file: " << input_file << std::endl;
        return 1;
    }
    
    std::cout << "Reading input snapshot from " << input_file << "..." << std::endl;
    
    // Read metadata
    int eflag, vflag, nlocal, nmax, inum, newton_pair, ntypes;
    ifs.read((char*)&eflag, sizeof(int));
    ifs.read((char*)&vflag, sizeof(int));
    ifs.read((char*)&nlocal, sizeof(int));
    ifs.read((char*)&nmax, sizeof(int));
    ifs.read((char*)&inum, sizeof(int));
    ifs.read((char*)&newton_pair, sizeof(int));
    ifs.read((char*)&ntypes, sizeof(int));
    
    std::cout << "  nlocal=" << nlocal << ", nmax=" << nmax << ", inum=" << inum << std::endl;
    std::cout << "  ntypes=" << ntypes << ", newton_pair=" << newton_pair << std::endl;
    std::cout << "  eflag=" << eflag << ", vflag=" << vflag << std::endl;
    
    // Allocate arrays
    double** x = allocate_2d<double>(nmax, 3);
    int* type = new int[nmax];
    double* special_lj = new double[4];
    int* ilist = new int[inum];
    int* numneigh = new int[nlocal];
    int** firstneigh = new int*[nlocal];
    
    // Allocate LJ coefficient matrices [ntypes+1][ntypes+1]
    int matrix_size = ntypes + 1;
    double** cutsq = allocate_2d<double>(matrix_size, matrix_size);
    double** lj1 = allocate_2d<double>(matrix_size, matrix_size);
    double** lj2 = allocate_2d<double>(matrix_size, matrix_size);
    double** lj3 = allocate_2d<double>(matrix_size, matrix_size);
    double** lj4 = allocate_2d<double>(matrix_size, matrix_size);
    double** offset = allocate_2d<double>(matrix_size, matrix_size);
    
    // Allocate output arrays
    double** f = allocate_2d<double>(nmax, 3);
    double* virial = new double[6];
    
    // Initialize forces to zero (they get accumulated)
    for (int i = 0; i < nmax; i++) {
        f[i][0] = 0.0;
        f[i][1] = 0.0;
        f[i][2] = 0.0;
    }
    
    // Read positions x[nmax][3]
    for (int i = 0; i < nmax; i++) {
        ifs.read((char*)&x[i][0], sizeof(double));
        ifs.read((char*)&x[i][1], sizeof(double));
        ifs.read((char*)&x[i][2], sizeof(double));
    }
    
    // Read types type[nmax]
    for (int i = 0; i < nmax; i++) {
        ifs.read((char*)&type[i], sizeof(int));
    }
    
    // Read special_lj[4]
    for (int i = 0; i < 4; i++) {
        ifs.read((char*)&special_lj[i], sizeof(double));
    }
    
    // Read ilist[inum]
    for (int i = 0; i < inum; i++) {
        ifs.read((char*)&ilist[i], sizeof(int));
    }
    
    // Read numneigh[nlocal]
    for (int i = 0; i < nlocal; i++) {
        ifs.read((char*)&numneigh[i], sizeof(int));
    }
    
    // Read variable-size neighbor lists
    for (int i = 0; i < nlocal; i++) {
        int nn;
        ifs.read((char*)&nn, sizeof(int));
        if (nn != numneigh[i]) {
            std::cerr << "ERROR: Neighbor count mismatch for atom " << i << std::endl;
            return 1;
        }
        firstneigh[i] = new int[nn];
        for (int j = 0; j < nn; j++) {
            ifs.read((char*)&firstneigh[i][j], sizeof(int));
        }
    }
    
    // Read LJ coefficient matrices
    for (int i = 0; i < matrix_size; i++) {
        for (int j = 0; j < matrix_size; j++) {
            ifs.read((char*)&cutsq[i][j], sizeof(double));
        }
    }
    for (int i = 0; i < matrix_size; i++) {
        for (int j = 0; j < matrix_size; j++) {
            ifs.read((char*)&lj1[i][j], sizeof(double));
        }
    }
    for (int i = 0; i < matrix_size; i++) {
        for (int j = 0; j < matrix_size; j++) {
            ifs.read((char*)&lj2[i][j], sizeof(double));
        }
    }
    for (int i = 0; i < matrix_size; i++) {
        for (int j = 0; j < matrix_size; j++) {
            ifs.read((char*)&lj3[i][j], sizeof(double));
        }
    }
    for (int i = 0; i < matrix_size; i++) {
        for (int j = 0; j < matrix_size; j++) {
            ifs.read((char*)&lj4[i][j], sizeof(double));
        }
    }
    for (int i = 0; i < matrix_size; i++) {
        for (int j = 0; j < matrix_size; j++) {
            ifs.read((char*)&offset[i][j], sizeof(double));
        }
    }
    
    ifs.close();
    std::cout << "Input snapshot loaded successfully." << std::endl;
    
    // ========== CALL BOTTLENECK FUNCTION ==========
    std::cout << "\nCalling bottleneck function..." << std::endl;
    
    double eng_vdwl, eng_coul;
    int evflag, eflag_either, eflag_global, eflag_atom;
    int vflag_either, vflag_global, vflag_atom, vflag_fdotr;
    double* eatom = nullptr;
    double** vatom = nullptr;
    
    compute_lj_cut(
        eflag, vflag, nlocal, nmax, inum, newton_pair, ntypes,
        x, type, special_lj, ilist, numneigh, firstneigh,
        cutsq, lj1, lj2, lj3, lj4, offset,
        f, eng_vdwl, eng_coul, virial,
        evflag, eflag_either, eflag_global, eflag_atom,
        vflag_either, vflag_global, vflag_atom, vflag_fdotr,
        eatom, vatom
    );
    
    std::cout << "Bottleneck function completed." << std::endl;
    std::cout << "  eng_vdwl = " << std::scientific << std::setprecision(15) << eng_vdwl << std::endl;
    std::cout << "  eng_coul = " << std::scientific << std::setprecision(15) << eng_coul << std::endl;
    
    // ========== READ OUTPUT SNAPSHOT ==========
    const char* output_file = "output.snapshot";
    std::ifstream ofs(output_file, std::ios::binary);
    if (!ofs) {
        std::cerr << "ERROR: Cannot open output snapshot file: " << output_file << std::endl;
        return 1;
    }
    
    std::cout << "\nReading output snapshot from " << output_file << "..." << std::endl;
    
    // Read and verify nmax
    int nmax_read;
    ofs.read((char*)&nmax_read, sizeof(int));
    if (nmax != nmax_read) {
        std::cerr << "ERROR: nmax mismatch: " << nmax << " vs " << nmax_read << std::endl;
        return 1;
    }
    
    // Read expected forces
    double** f_expected = allocate_2d<double>(nmax, 3);
    for (int i = 0; i < nmax; i++) {
        ofs.read((char*)&f_expected[i][0], sizeof(double));
        ofs.read((char*)&f_expected[i][1], sizeof(double));
        ofs.read((char*)&f_expected[i][2], sizeof(double));
    }
    
    // Read expected energies
    double eng_vdwl_expected, eng_coul_expected;
    ofs.read((char*)&eng_vdwl_expected, sizeof(double));
    ofs.read((char*)&eng_coul_expected, sizeof(double));
    
    // Read expected virial
    double virial_expected[6];
    for (int i = 0; i < 6; i++) {
        ofs.read((char*)&virial_expected[i], sizeof(double));
    }
    
    // Read flags
    int evflag_exp, eflag_either_exp, eflag_global_exp, eflag_atom_exp;
    int vflag_either_exp, vflag_global_exp, vflag_atom_exp, vflag_fdotr_exp;
    
    ofs.read((char*)&evflag_exp, sizeof(int));
    ofs.read((char*)&eflag_either_exp, sizeof(int));
    ofs.read((char*)&eflag_global_exp, sizeof(int));
    ofs.read((char*)&eflag_atom_exp, sizeof(int));
    ofs.read((char*)&vflag_either_exp, sizeof(int));
    ofs.read((char*)&vflag_global_exp, sizeof(int));
    ofs.read((char*)&vflag_atom_exp, sizeof(int));
    ofs.read((char*)&vflag_fdotr_exp, sizeof(int));
    
    ofs.close();
    std::cout << "Output snapshot loaded successfully." << std::endl;
    
    // ========== VERIFY ALL OUTPUTS ==========
    std::cout << "\n=== VERIFICATION RESULTS ===" << std::endl;
    
    bool all_passed = true;
    int force_mismatches = 0;
    double max_force_error = 0.0;
    double avg_force_error = 0.0;
    int force_count = 0;
    
    // Verify forces (ALL components, ALL atoms)
    std::cout << "\n1. Verifying forces for " << nmax << " atoms..." << std::endl;
    for (int i = 0; i < nmax; i++) {
        for (int j = 0; j < 3; j++) {
            double computed = f[i][j];
            double expected = f_expected[i][j];
            double error = std::abs(computed - expected);
            
            avg_force_error += error;
            force_count++;
            
            if (error > max_force_error) {
                max_force_error = error;
            }
            
            if (!doubles_equal(computed, expected)) {
                if (force_mismatches < 10) {  // Print first 10 mismatches
                    std::cerr << "  MISMATCH: f[" << i << "][" << j << "] = " 
                              << std::scientific << std::setprecision(15)
                              << computed << " vs expected " << expected 
                              << " (error=" << error << ")" << std::endl;
                }
                force_mismatches++;
                all_passed = false;
            }
        }
    }
    
    avg_force_error /= force_count;
    
    if (force_mismatches == 0) {
        std::cout << "  ✓ PASSED: All " << force_count << " force components match within tolerance" << std::endl;
    } else {
        std::cout << "  ✗ FAILED: " << force_mismatches << " of " << force_count << " force components exceed tolerance" << std::endl;
    }
    std::cout << "  Max force error: " << std::scientific << std::setprecision(6) << max_force_error << std::endl;
    std::cout << "  Avg force error: " << std::scientific << std::setprecision(6) << avg_force_error << std::endl;
    
    // Verify energy (eng_vdwl)
    std::cout << "\n2. Verifying van der Waals energy..." << std::endl;
    std::cout << "  Computed: " << std::scientific << std::setprecision(15) << eng_vdwl << std::endl;
    std::cout << "  Expected: " << std::scientific << std::setprecision(15) << eng_vdwl_expected << std::endl;
    std::cout << "  Error:    " << std::scientific << std::setprecision(6) << std::abs(eng_vdwl - eng_vdwl_expected) << std::endl;
    
    if (doubles_equal(eng_vdwl, eng_vdwl_expected)) {
        std::cout << "  ✓ PASSED: eng_vdwl matches within tolerance" << std::endl;
    } else {
        std::cout << "  ✗ FAILED: eng_vdwl exceeds tolerance" << std::endl;
        all_passed = false;
    }
    
    // Verify Coulombic energy (should be zero for LJ)
    std::cout << "\n3. Verifying Coulombic energy..." << std::endl;
    std::cout << "  Computed: " << std::scientific << std::setprecision(15) << eng_coul << std::endl;
    std::cout << "  Expected: " << std::scientific << std::setprecision(15) << eng_coul_expected << std::endl;
    
    if (doubles_equal(eng_coul, eng_coul_expected)) {
        std::cout << "  ✓ PASSED: eng_coul matches within tolerance" << std::endl;
    } else {
        std::cout << "  ✗ FAILED: eng_coul exceeds tolerance" << std::endl;
        all_passed = false;
    }
    
    // Verify virial (ALL 6 components)
    std::cout << "\n4. Verifying virial tensor (6 components)..." << std::endl;
    const char* virial_names[6] = {"xx", "yy", "zz", "xy", "xz", "yz"};
    int virial_mismatches = 0;
    
    for (int i = 0; i < 6; i++) {
        double computed = virial[i];
        double expected = virial_expected[i];
        double error = std::abs(computed - expected);
        
        std::cout << "  virial[" << virial_names[i] << "]: computed=" 
                  << std::scientific << std::setprecision(15) << computed
                  << ", expected=" << expected
                  << ", error=" << std::setprecision(6) << error << std::endl;
        
        if (!doubles_equal(computed, expected)) {
            std::cout << "    ✗ MISMATCH exceeds tolerance" << std::endl;
            virial_mismatches++;
            all_passed = false;
        }
    }
    
    if (virial_mismatches == 0) {
        std::cout << "  ✓ PASSED: All 6 virial components match within tolerance" << std::endl;
    } else {
        std::cout << "  ✗ FAILED: " << virial_mismatches << " of 6 virial components exceed tolerance" << std::endl;
    }
    
    // Verify flags
    std::cout << "\n5. Verifying flags..." << std::endl;
    std::cout << "  evflag:       computed=" << evflag << ", expected=" << evflag_exp << std::endl;
    std::cout << "  eflag_either: computed=" << eflag_either << ", expected=" << eflag_either_exp << std::endl;
    std::cout << "  eflag_global: computed=" << eflag_global << ", expected=" << eflag_global_exp << std::endl;
    std::cout << "  eflag_atom:   computed=" << eflag_atom << ", expected=" << eflag_atom_exp << std::endl;
    std::cout << "  vflag_either: computed=" << vflag_either << ", expected=" << vflag_either_exp << std::endl;
    std::cout << "  vflag_global: computed=" << vflag_global << ", expected=" << vflag_global_exp << std::endl;
    std::cout << "  vflag_atom:   computed=" << vflag_atom << ", expected=" << vflag_atom_exp << std::endl;
    std::cout << "  vflag_fdotr:  computed=" << vflag_fdotr << ", expected=" << vflag_fdotr_exp << std::endl;
    
    bool flags_match = (evflag == evflag_exp) &&
                       (eflag_either == eflag_either_exp) &&
                       (eflag_global == eflag_global_exp) &&
                       (eflag_atom == eflag_atom_exp) &&
                       (vflag_either == vflag_either_exp) &&
                       (vflag_global == vflag_global_exp) &&
                       (vflag_atom == vflag_atom_exp) &&
                       (vflag_fdotr == vflag_fdotr_exp);
    
    if (flags_match) {
        std::cout << "  ✓ PASSED: All flags match" << std::endl;
    } else {
        std::cout << "  ✗ FAILED: Flag mismatches detected" << std::endl;
        all_passed = false;
    }
    
    // ========== FINAL RESULT ==========
    std::cout << "\n=== FINAL VERIFICATION RESULT ===" << std::endl;
    if (all_passed) {
        std::cout << "✓✓✓ SUCCESS: All outputs verified successfully! ✓✓✓" << std::endl;
        std::cout << "The harness produces numerically identical results to the original implementation." << std::endl;
    } else {
        std::cout << "✗✗✗ FAILURE: Some outputs do not match the snapshot. ✗✗✗" << std::endl;
        std::cout << "Review the mismatches above and debug the bottleneck implementation." << std::endl;
    }
    
    // ========== CLEANUP ==========
    deallocate_2d(x, nmax);
    deallocate_2d(f, nmax);
    deallocate_2d(f_expected, nmax);
    deallocate_2d(cutsq, matrix_size);
    deallocate_2d(lj1, matrix_size);
    deallocate_2d(lj2, matrix_size);
    deallocate_2d(lj3, matrix_size);
    deallocate_2d(lj4, matrix_size);
    deallocate_2d(offset, matrix_size);
    
    delete[] type;
    delete[] special_lj;
    delete[] ilist;
    delete[] numneigh;
    delete[] virial;
    
    for (int i = 0; i < nlocal; i++) {
        delete[] firstneigh[i];
    }
    delete[] firstneigh;
    
    return all_passed ? 0 : 1;
}
