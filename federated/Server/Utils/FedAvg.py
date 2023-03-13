import numpy as np

def aggregate_models(client_weights, total_clients):
    ''' function for aggregating the model weights
    return:
        global_weights: calculated average of all of the participating client weights '''
    scaled_local_weight_list = list()

    for client in client_weights:
        scaling_factor = 1 / total_clients
        scaled_weights = scale_model_weights(client_weights[client], scaling_factor)
        scaled_local_weight_list.append(scaled_weights)

    # to get the average over all the local model, we simply take the sum of the scaled weights
    average_weights = list()
    # sum the scaled weights
    average_weights = sum_scaled_weights(average_weights, scaled_local_weight_list)

    global_weights = average_weights

    return global_weights

def scale_model_weights(weight, scalar):
    ''' function for scaling a models weights
    args:
        weight: original weight value
        scalar: weight attributed to client based on the number of data points
    return:
        weight_final: scaled weight according to the scalar value '''

    weight_final = []
    steps = len(weight)
    for i in range(steps):
        weights = np.array(weight[i])
        weight_final.append(scalar * weights)
    return weight_final

def sum_scaled_weights(avg_grad, scaled_weight_list):
    import tensorflow as tf
    '''Return the sum of the listed scaled weights. The is equivalent to scaled avg of the weights
    args:
        scaled_weight_list: scalet weights list of each client
    return:
        average of the weights'''

    #get the average grad accross all client gradients
    for grad_list_tuple in zip(*scaled_weight_list):
        layer_mean = tf.math.reduce_sum(grad_list_tuple, axis=0)
        avg_grad.append(np.array(layer_mean))
        
    return avg_grad