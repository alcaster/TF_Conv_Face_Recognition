import tensorflow as tf

from utils.tensorboard import variable_summaries


def new_weights(shape):
    return tf.get_variable("W", shape=shape,
                           initializer=tf.contrib.layers.xavier_initializer())


def new_biases(length):
    return tf.get_variable("b1", shape=[length],
                           initializer=tf.constant_initializer(0.05))


def new_conv_layer(input, num_input_channels, filter_size, num_filters, use_pooling=True, scope="conv"):
    with tf.variable_scope(scope):
        shape = [filter_size, filter_size, num_input_channels, num_filters]
        weights = new_weights(shape=shape)
        biases = new_biases(length=num_filters)
        variable_summaries(weights)
        variable_summaries(biases)

        layer = tf.nn.conv2d(input=input,
                             filter=weights,
                             strides=[1, 1, 1, 1],
                             padding='SAME')
        layer += biases

        if use_pooling:
            layer = tf.nn.max_pool(value=layer,
                                   ksize=[1, 2, 2, 1],
                                   strides=[1, 2, 2, 1],
                                   padding='SAME')
        layer = tf.nn.relu(layer)
        return layer, weights


def flatten_layer(layer, scope="flatten"):
    with tf.variable_scope(scope):
        layer_shape = layer.get_shape()
        num_features = layer_shape[1:4].num_elements()
        layer_flat = tf.reshape(layer, [-1, num_features])
        return layer_flat, num_features


def new_fc_layer(input, num_inputs, num_outputs, use_relu=True, scope="fully_connected"):
    with tf.variable_scope(scope):
        weights = new_weights(shape=[num_inputs, num_outputs])
        biases = new_biases(length=num_outputs)
        variable_summaries(weights)
        variable_summaries(biases)

        layer = tf.matmul(input, weights) + biases

        if use_relu:
            layer = tf.nn.relu(layer)

        return layer
