"""
Compares classic Linearized Bregman to modified Linearized Bregman
@authors: Jimmy Singh and Janice Lee
@date: June 6th, 2019
"""
import numpy as np
import numpy.random as random
import numpy.linalg as la
np.random.seed(0)

import init_problem as init
import plot

def get_residual(A, x, y):
    residual = np.dot(A, x) - y
    return residual

def get_gradient(A, residual):
    gradient = np.dot(A.T, residual)
    return gradient

def lb_compare(m, n, num_samp, max_iter, sparse=True, noise=False):
    """
    Compares classic LB to modified LB
    params:
        m (int):
        n (int):
        num_samp (int):
        max_iter (int):
    returns:
    """
    # ------ SETTING PARAMETERS ------
    # initializes the Ax = y problem 
    problem = init.init_l1(m, n, num_samp, max_iter, sparse, noise)
    A = problem[0]
    x_true = problem[1]
    y = problem[2]
    
    # current values of x and z
    # column 0: classic, column 1: modified, column 2: modified + no threshold
    x_lb = np.zeros((n, 3), dtype=float)
    z_lb = np.zeros((n, 3), dtype=float)

    t_k_old = np.zeros((max_iter,3), dtype=float)
    t_k_new = np.zeros((n, 1), dtype=float)
    t_k_new2 = np.zeros((n, 1))

    # threshold parameter
    lambda_lb = 4.0;
    m_flag = np.zeros((1, n), dtype=int)
    
    # thresholding function 
    S = lambda x, lmda: np.multiply(np.maximum(np.absolute(x) - lmda, 0), np.sign(x))
    
    # arrays to hold results 
    residual = np.zeros((max_iter, 3), dtype=float)
    onenorm = np.zeros((max_iter, 3), dtype=float)
    moder = np.zeros((max_iter, 3), dtype=float)    # model error 

    # arrays to track the nonzero values of x and z
    idx_nonzero = np.argwhere(x_true != 0)
    nonzero_x_true = x_true[idx_nonzero]
    nonzero_x_lb = np.zeros((max_iter, len(nonzero_x_true)))
    nonzero_z_lb = np.zeros((max_iter, len(nonzero_x_true)))
    
    # ------ MAIN LOOP ------
    for i in range(1, max_iter+1):
        print("iteration: " + str(i))
        
        # ------ SAMPLING ------
        # choosing random rows of A
        idx = random.permutation(n)

        # getting the corresponding rows of A and y
        A_sub = A[idx[:num_samp], :]
        y_sub = y[idx[:num_samp]]
        # TODO: FIX THIS LOL 
        # y_sub = y[0, idx[:num_samp]]

        # why is this here?
        t_lb = np.repeat(1/la.norm(A_sub, 2), 3)

        # ------ RESIDUAL AND GRADIENT ------
        # get residual
        r_lb = np.zeros((num_samp, 3))
        r_lb[:, 0] = get_residual(A_sub, x_lb[:, 0], y_sub)
        r_lb[:, 1] = get_residual(A_sub, x_lb[:, 1], y_sub)
        r_lb[:, 2] = get_residual(A_sub, x_lb[:, 2], y_sub)

        # getting gradient
        g_lb = np.zeros((n, 3))
        g_lb[:, 0] = get_gradient(A_sub, r_lb[:, 0])
        g_lb[:, 1] = get_gradient(A_sub, r_lb[:, 1])
        g_lb[:, 2] = get_gradient(A_sub, r_lb[:, 2])

        # ------ STEP SIZE ------
        # getting the step size
        t_lb[0] = la.norm(r_lb[:, 0], 2)**2/la.norm(g_lb[:, 0], 2)**2
        t_lb[1] = la.norm(r_lb[:, 1], 2)**2/la.norm(g_lb[:, 1], 2)**2
        t_lb[2] = la.norm(r_lb[:, 2], 2)**2/la.norm(g_lb[:, 2], 2)**2

        t_k_old[i-1, :] = t_lb
        t_k_new = t_k_new + np.sign(-g_lb[:,1]).reshape(n, 1)
        t_k_new2 = t_k_new2 + np.sign(-g_lb[:,2].reshape(n, 1))

        # ------ THRESHOLDING ------
        # finding the indices in m_flag that are zero
        ind_flag = np.argwhere(m_flag == 0)[:, 1]
        # finding the indices in the second column (modified) of z_lb 
        # that are greater than the threshold
        ind_c = np.argwhere(np.absolute(z_lb[ind_flag, 1]) > lambda_lb)
        # flagging indices that are above the threshold
        # m_flag[ind_flag[ind_c]] = 1
        m_flag[0, ind_c] = 1
        
        # eliminate flipping depending on flag 
        ind_elim = np.argwhere(m_flag == 1)[:, 1]
        ind_nelim = np.argwhere(m_flag == 0)[:, 1]
        
        # ------ CALCULATING X AND Z  ------
        # classic 
        z_lb[:, 0] = z_lb[:, 0] - t_lb[0]*g_lb[:, 0]
        
        # modified 
        step_size_elim = (t_lb[1]*np.absolute(t_k_new[ind_elim])/i).T
        z_lb[ind_elim, 1] = z_lb[ind_elim, 1] - np.multiply(step_size_elim, g_lb[ind_elim, 1]) 
        z_lb[ind_nelim, 1] = z_lb[ind_nelim, 1] - t_lb[1]*g_lb[ind_nelim, 1]
            
        # modified + no threshold detection
        step_size = (t_lb[2]*np.absolute(t_k_new2)/i).T
        z_lb[:, 2] = z_lb[:, 2] - np.multiply(step_size, g_lb[:, 2])
        
        x_lb[:, :] = S(z_lb[:, :], lambda_lb)
        
        # ------ RESULTS ------
        residual[i-1, 0] = la.norm(get_residual(A_sub, x_lb[:, 0], y_sub), 2) / la.norm(y_sub, 2)
        residual[i-1, 1] = la.norm(get_residual(A_sub, x_lb[:, 1], y_sub), 2) / la.norm(y_sub, 2)
        residual[i-1, 2] = la.norm(get_residual(A_sub, x_lb[:, 2], y_sub), 2) / la.norm(y_sub, 2)
        
        onenorm[i-1, 0] = la.norm(x_lb[:, 0], 1)
        onenorm[i-1, 1] = la.norm(x_lb[:, 1], 1)
        onenorm[i-1, 2] = la.norm(x_lb[:, 2], 1)
        
        moder[i-1, 0] = la.norm(x_true - x_lb[:, 0], 2) / la.norm(x_true, 2)
        moder[i-1, 1] = la.norm(x_true - x_lb[:, 1], 2) / la.norm(x_true, 2)
        moder[i-1, 2] = la.norm(x_true - x_lb[:, 2], 2) / la.norm(x_true, 2)
        
        nonzero_x_lb[i-1, :] = x_lb[idx_nonzero, 1].reshape(len(nonzero_x_true,))
        nonzero_z_lb[i-1, :] = x_lb[idx_nonzero, 1].reshape(len(nonzero_x_true,))
    
    return residual, onenorm, moder, nonzero_x_true, nonzero_x_lb, nonzero_z_lb

def main():
    # ------ CONFIGURE PARAMETERS ------
    m = 20000         # rows of A 
    n = 1000          # columns of A (rows of x_true and y_true)
    num_samp = 200    # rows of A and y to sample, num_samp < n
    max_iter = 300
    sparse = True 
    noise = True
    
    plot_residual = True
    plot_onenorm = True
    plot_moder = True 
    plot_nonzero = True 
    # ------ EXECUTE ------
    results = lb_compare(m, n, num_samp, max_iter, sparse, noise)
    
    # print(results[0])
    # print(results[1])
    # print(results[2])
    
    if (plot_residual):
        plot.plot_residual(max_iter, results[0], sparse, noise, "lb")
    if (plot_onenorm):
        plot.plot_onenorm(max_iter, results[1], sparse, noise, "lb")
    if (plot_moder):
        plot.plot_moder(max_iter, results[2], sparse, noise, "lb")
    # if (plot_nonzero):
    #     plot.plot_lb(max_iter, results[5], sparse, noise, "nonzeros")
        
if __name__ == "__main__":
    main()    
