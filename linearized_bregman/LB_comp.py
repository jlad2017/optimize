"""
Compares classic Linearized Bregman to modified Linearized Bregman
@authors: Jimmy Singh and Janice Lee
@date: June 6th, 2019
"""
import numpy as np
import numpy.random as random
import numpy.linalg as la
import matplotlib.pyplot as plt
import string
np.random.seed(0)

def rand_exp_decay(n, a, b):
    """
    Creates a random semi-sparse array with exponentially decreasing elements
    params:
        n (int): desired number of elements in the array
        a (float): ???
        b (float): ???
    returns:
        R (numpy array): array with exponentially decreasing elements
    """
    A = np.log(a)
    B = np.log(b)
    R1 = A + (B-A) * random.rand(n)
    R = np.exp(R1*2)
    idx = random.permutation(n)
    for i in idx[0:int(np.floor(n/2))]:
        R[i] = -R[i]
    return R

def rand_sparse(n, frac):
    """
    Creates a random sparse array
    params:
        n (int): desired number of elements in the array
        frac (int): 1/frac gives the fraction of non-zero elements in the array
    returns:
        R (numpy array): sparse array
    """
    R = np.zeros(n, dtype=float)
    idx = random.permutation(n)
    for i in idx[0:int(n/frac)]:
        R[i] = random.rand(1)
    return R
    
def add_awgn_noise(x, snr_dB):
    """
    Function to add AWGN to a given signal 
    Original function authored by Mathuranathan Viswanathan for MatLab/Octave
    """
    l = x.size
    snr = 10 ** (snr_dB/10)
    e_sym = np.sum(np.square(x)) / l
    n0 = e_sym / snr
    if (np.isreal(x).all()):
        noise_sigma = np.sqrt(n0)
        n = noise_sigma * random.randn(1, l) 
    else:
        noise_sigma = np.sqrt(n0/2)
        n = noise_sigma * (random.randn(1, l) + 1j*random.randn(1, l))
    y = x + n
    return y
        
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
    # true value of x (x*, solution)
    if (sparse):
        x_true = rand_sparse(n, 20)
    else:
        x_true = rand_exp_decay(n, 0.0001, np.sqrt(5))

    # true values of A and y
    A = random.randn(m, n)
    y_true = np.dot(A, x_true)

    if (noise):
        y = y_true + random.normal(0, 1, y_true.shape)
        #TODO: FIX THIS LOL 
        # y = add_awgn_noise(y_true, -20)
    else:
        y = y_true

    # current values of x and z
    # column 0: classic, column 1: modified, column 2: modified + no threshold
    x_lb = np.zeros((n, 3), dtype=float)
    z_lb = np.zeros((n, 3), dtype=float)

    t_k_old = np.zeros((max_iter,3), dtype=float)
    t_k_new = np.zeros((n, 1), dtype=float)
    t_k_new2 = np.zeros((n, 1), dtype=float)

    # threshold parameter
    lambda_lb = 4.0;
    m_flag = np.zeros((1, n), dtype=int)
    
    # thresholding function 
    S = lambda x, lmda: np.multiply(np.maximum(np.absolute(x) - lmda, 0), np.sign(x))
    
    # arrays to hold results 
    residual = np.zeros((max_iter, 3), dtype=float)
    onenorm = np.zeros((max_iter, 3), dtype=float)
    moder = np.zeros((max_iter, 3), dtype=float)    # model error 

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
        ind_c = np.argwhere(np.absolute(z_lb[ind_flag, 2]) > lambda_lb)
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
        
    return residual, onenorm, moder
    
def get_title(sparse, noise, type):
    title = "Classic vs. Modified LB ("
    # get sparse title 
    if (sparse): 
        title += "sparse soln, "
    else:
        title += "exponentally decaying soln, "
    # get noise title 
    if (noise):
        title += "w/noise) - "
    else: 
        title += "w/out noise) - "
    title += type.upper()
    return title 

def get_filename(sparse, noise, type):
    filename = "../plots/" + type
    # get sparse filename 
    if (sparse): 
        filename += "_sparse_"
    else:
        filename += "_randExpDecay_"
    # get noise filename 
    if (noise):
        filename += "noise.png"
    else: 
        filename += "noNoise.png"
    return filename

def plot(max_iter, data, title, filename):
    plt.clf()
    plt.plot(range(1, max_iter+1), data)
    plt.legend(["Classic", "Modified", "Modified w/out threshold"])
    plt.xlabel("Number of iterations")
    plt.ylabel("Data values")
    plt.title(title)
    plt.savefig(filename)

def main():
    # ------ CONFIGURE PARAMETERS ------
    m = 20000         # rows of A 
    n = 1000          # columns of A (rows of x_true and y_true)
    num_samp = 200    # rows of A and y to sample, num_samp < n
    max_iter = 250
    sparse = True 
    noise = False
    
    plot_residual = True
    plot_onenorm = True
    plot_moder = True 
    # ------ EXECUTE ------
    results = lb_compare(m, n, num_samp, max_iter, sparse, noise)
    
    # print(results[0])
    # print(results[1])
    # print(results[2])
    
    if (plot_residual):
        title = get_title(sparse, noise, "residual")
        filename = get_filename(sparse, noise, "residual")
        plot(max_iter, results[0], title, filename)
    if (plot_onenorm):
        title = get_title(sparse, noise, "1-norm")
        filename = get_filename(sparse, noise, "1-norm")
        plot(max_iter, results[1], title, filename)
    if (plot_moder):
        title = get_title(sparse, noise, "model-error")
        filename = get_filename(sparse, noise, "model-error")
        plot(max_iter, results[2], title, filename)
        
if __name__ == "__main__":
    main()    
