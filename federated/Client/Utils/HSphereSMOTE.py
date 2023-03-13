import numpy as np
import math
import torch
from sklearn.neighbors import NearestNeighbors


def dist(a, b):
    return math.sqrt(np.power(a - b, 2).sum())


def largest_indices(array: np.ndarray, n: int) -> tuple:
    """Returns the n largest indices from a numpy array.
    Arguments:
        array {np.ndarray} -- data array
        n {int} -- number of elements to select
    Returns:
        tuple[np.ndarray, np.ndarray] -- tuple of ndarray
        each ndarray is index
    """
    flat = array.flatten()
    indices = np.argpartition(flat, -n)[-n:]
    indices = indices[np.argsort(-flat[indices])]
    return np.unravel_index(indices, array.shape)

def least_indices(array: np.ndarray, n: int) -> tuple:
    """Returns the n least indices from a numpy array.
    Arguments:
        array {np.ndarray} -- data array
        n {int} -- number of elements to select
    Returns:
        tuple[np.ndarray, np.ndarray] -- tuple of ndarray
        each ndarray is index
    """
    flat = array.flatten()
    indices = np.argpartition(flat, n)[:n]
    indices = indices[np.argsort(flat[indices])]
    return np.unravel_index(indices, array.shape)



def NNSMOTE(sample, orgdata, k, ns, nf):
    """
    Find k nearest neighbors for specific sample
    """
    synth = orgdata
    for s in sample:
        id = 0
        distlist = np.zeros(len(orgdata))
        for m in orgdata:
            d = dist(s, m)
            distlist[id] = d
            id += 1

        inds = least_indices(distlist, k)
        #indsten = torch.from_numpy(inds[0])

        neighbor = np.take(orgdata, inds, axis=0)
        neighbor = np.squeeze(neighbor, axis=0)


        # For one synethic, we calculate the linear interpolation from its neighbors
        x_c = np.expand_dims(s, axis=0)

        distance = []
        for n in neighbor:
            x_c = x_c + np.random.beta(2,2)*np.absolute(s-n)
            dis = np.absolute(s-n)
            distance.append(dis)

        x_c = x_c/k

        dist_array = np.array(distance)
        max_inds = largest_indices(dist_array, 1)
        radius = np.absolute(s-neighbor[max_inds])

        syn = np.random.normal(x_c, radius, (ns,nf))
        synth = np.concatenate((synth, syn), axis = 0)


    size = orgdata.shape[0]
    synth = synth[size:, :]

    return synth



def Sampling(Xtr, Ytr, ratio, k):

    Xtr = torch.FloatTensor(Xtr)
    Ytr = torch.FloatTensor(Ytr)
    
    #Split the data according to the class
    n1 = int(Ytr.sum())
    # Total number of the dataset
    n = len(Ytr)
    idx0 = (Ytr == 0)
    idx1 = (Ytr == 1)
    x0 = Xtr[idx0,:]
    y0 = Ytr[idx0]
    x1 = Xtr[idx1,:]
    y1 = Ytr[idx1]
    # The number of the majority class
    n0 = n - n1
    # The number of the features
    nf = x0.shape[1]

    Xtr2 = np.empty([0,Xtr.size(1)])
    Ytr2 = np.empty(0)
    up = 0
    if n0 > n1:
        #Number of samples for the minority class after upsampling
        # The number should be the same as ratio*n0
        up = math.floor(ratio*n0) - n1

        # Get top k indeies farest from the centroid
        #inds= least_indices(distlist, k)
        inds=np.random.choice(n1, size=k, replace=False)
        indsten = torch.from_numpy(inds)
        sample_top = torch.index_select(x1, 0, indsten)

        samples = sample_top.numpy()
        datas = x1.numpy()

        # The number of synthetic points per chosen sample
        ns = round(up/k)
        Xtr2 = NNSMOTE(samples, datas, 20, ns, nf)
        Ytr2 = np.ones(len(Xtr2))

    else:
        up = math.floor(ratio*n1) - n0
        # Get top k indeies farest from the centroid
        #inds= least_indices(distlist, k)
        inds=np.random.choice(n0, size=k, replace=False)
        indsten = torch.from_numpy(inds)
        sample_top = torch.index_select(x0, 0, indsten)

        samples = sample_top.numpy()
        datas = x0.numpy()

        # The number of synthetic points per chosen sample
        ns = round(up/k)
        Xtr2 = NNSMOTE(samples, datas, 20, ns, nf)
        Ytr2 = np.zeros(len(Xtr2))



    #Create the new dataset
    X_up = torch.from_numpy(Xtr2).float()
    Y_up = torch.from_numpy(Ytr2).float()


    return X_up, Y_up, up, n0, n1
