/**
 *  The MIT License (MIT)
 *
 *  Copyright (c) 2015 Kyle Hollins Wray, University of Massachusetts
 *
 *  Permission is hereby granted, free of charge, to any person obtaining a copy of
 *  this software and associated documentation files (the "Software"), to deal in
 *  the Software without restriction, including without limitation the rights to
 *  use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
 *  the Software, and to permit persons to whom the Software is furnished to do so,
 *  subject to the following conditions:
 *
 *  The above copyright notice and this permission notice shall be included in all
 *  copies or substantial portions of the Software.
 *
 *  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 *  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
 *  FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
 *  COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
 *  IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
 *  CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 */


#include "mdp_vi.h"

#include <cmath>
#include <stdio.h>

// This is determined by hardware, so what is below is a 'safe' guess. If this is
// off, the program might return 'nan' or 'inf'.
#define FLT_MAX 1e+35

__global__ void nova_mdp_bellman_update(unsigned int n, unsigned int m, const float *T,
        const float *R, float gamma, const float *V, float *VPrime, unsigned int *pi)
{
    // The current state as a function of the blocks and threads.
    int s;

    // The intermediate Q(s, a) value.
    float Qsa;

    // Compute the index of the state. Return if it is beyond the state.
    s = blockIdx.x * blockDim.x + threadIdx.x;
    if (s >= n) {
        return;
    }

    // Nvidia GPUs follow IEEE floating point standards, so this should be safe.
    VPrime[s] = -FLT_MAX;

    // Compute max_{a in A} Q(s, a).
    for (int a = 0; a < m; a++) {
        // Compute Q(s, a) for this action.
        Qsa = R[s * m + a];
        for (int sp = 0; sp < n; sp++) {
            Qsa += gamma * T[s * m * n + a * n + sp] * V[sp];
        }

        if (a == 0 || Qsa > VPrime[s]) {
            VPrime[s] = Qsa;
            pi[s] = a;
        }
    }
}

int nova_mdp_vi(unsigned int n, unsigned int m, const float *T, const float *R,
        float gamma, unsigned int horizon, unsigned int numThreads, float *V, unsigned int *pi)
{
    // The device pointers for the MDP: T and R.
    float *d_T;
    float *d_R;

    // The host and device pointers for the value functions: V and VPrime.
    float *d_V;
    float *d_VPrime;

    // The device pointer for the final policy: pi.
    unsigned int *d_pi;

    // The number of blocks
    unsigned int numBlocks;

    // First, ensure data is valid.
    if (n == 0 || m == 0 || T == nullptr || R == nullptr ||
            gamma < 0.0f || gamma >= 1.0f || horizon < 1 ||
            V == nullptr || pi == nullptr) {
        return 1;
    }

    // Ensure threads are correct.
    if (numThreads % 32 != 0) {
        fprintf(stderr, "Error[value_iteration]: %s", "Invalid number of threads.");
        return 2;
    }

    numBlocks = (unsigned int)((float)n / (float)numThreads) + 1;

    // Allocate the device-side memory.
    if (cudaMalloc(&d_T, n * m * n * sizeof(float)) != cudaSuccess) {
        fprintf(stderr, "Error[value_iteration]: %s",
                "Failed to allocate device-side memory for the state transitions.");
        return 2;
    }
    if (cudaMalloc(&d_R, n * m * sizeof(float)) != cudaSuccess) {
        fprintf(stderr, "Error[value_iteration]: %s",
                "Failed to allocate device-side memory for the rewards.");
        return 3;
    }

    if (cudaMalloc(&d_V, n * sizeof(float)) != cudaSuccess) {
        fprintf(stderr, "Error[value_iteration]: %s",
                "Failed to allocate device-side memory for the value function.");
        return 4;
    }
    if (cudaMalloc(&d_VPrime, n * sizeof(float)) != cudaSuccess) {
        fprintf(stderr, "Error[value_iteration]: %s",
                "Failed to allocate device-side memory for the value function (prime).");
        return 5;
    }

    if (cudaMalloc(&d_pi, n * sizeof(unsigned int)) != cudaSuccess) {
        fprintf(stderr, "Error[value_iteration]: %s",
                "Failed to allocate device-side memory for the policy (pi).");
        return 6;
    }

    /*
    // Assume that V and pi are initialized *properly* (either 0, or, with MPI, perhaps
    // with previous V values).

    for (int s = 0; s < n; s++) {
        V[s] = 0.0f;
        pi[s] = 0;
    }
    //*/

    // Copy the data from host to device.
    if (cudaMemcpy(d_T, T, n * m * n * sizeof(float), cudaMemcpyHostToDevice) != cudaSuccess) {
        fprintf(stderr, "Error[value_iteration]: %s",
                "Failed to copy memory from host to device for the state transitions.");
        return 7;
    }
    if (cudaMemcpy(d_R, R, n * m * sizeof(float), cudaMemcpyHostToDevice) != cudaSuccess) {
        fprintf(stderr, "Error[value_iteration]: %s",
                "Failed to copy memory from host to device for the rewards.");
        return 8;
    }

    if (cudaMemcpy(d_V, V, n * sizeof(float), cudaMemcpyHostToDevice) != cudaSuccess) {
        fprintf(stderr, "Error[value_iteration]: %s",
                "Failed to copy memory from host to device for the value function.");
        return 9;
    }
    if (cudaMemcpy(d_VPrime, V, n * sizeof(float), cudaMemcpyHostToDevice) != cudaSuccess) {
        fprintf(stderr, "Error[value_iteration]: %s",
                "Failed to copy memory from host to device for the value function (prime).");
        return 10;
    }

    if (cudaMemcpy(d_pi, pi, n * sizeof(unsigned int), cudaMemcpyHostToDevice) != cudaSuccess) {
        fprintf(stderr, "Error[value_iteration]: %s",
                "Failed to copy memory from host to device for the policy (pi).");
        return 11;
    }

    // Execute value iteration for these number of iterations. For each iteration, however,
    // we will run the state updates in parallel.
    for (int i = 0; i < horizon; i++) {
        printf("Iteration %d / %d\n", i, horizon);

        if (i % 2 == 0) {
            nova_mdp_bellman_update<<< numBlocks, numThreads >>>(n, m, d_T, d_R, gamma, d_V, d_VPrime, d_pi);
        } else {
            nova_mdp_bellman_update<<< numBlocks, numThreads >>>(n, m, d_T, d_R, gamma, d_VPrime, d_V, d_pi);
        }
    }

    // Copy the final result, both V and pi, from device to host.
    if (horizon % 2 == 1) {
        if (cudaMemcpy(V, d_V, n * sizeof(float), cudaMemcpyDeviceToHost) != cudaSuccess) {
            fprintf(stderr, "Error[value_iteration]: %s",
                    "Failed to copy memory from device to host for the value function.");
            return 12;
        }
    } else {
        if (cudaMemcpy(V, d_VPrime, n * sizeof(float), cudaMemcpyDeviceToHost) != cudaSuccess) {
            fprintf(stderr, "Error[value_iteration]: %s",
                    "Failed to copy memory from device to host for the value function (prime).");
            return 13;
        }
    }
    if (cudaMemcpy(pi, d_pi, n * sizeof(unsigned int), cudaMemcpyDeviceToHost) != cudaSuccess) {
        fprintf(stderr, "Error[value_iteration]: %s",
                "Failed to copy memory from device to host for the policy (pi).");
        return 14;
    }

    // Free the device-side memory.
    cudaFree(d_T);
    cudaFree(d_R);

    cudaFree(d_V);
    cudaFree(d_VPrime);

    cudaFree(d_pi);

    return 0;
}